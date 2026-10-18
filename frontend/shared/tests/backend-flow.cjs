// Requires the real API on :8000 and Next.js in connected mode on :3000.
// PLAYWRIGHT_MODULE may point to an external installation (no project dependency required).
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome' });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(`${process.env.FRONTEND_URL || 'http://localhost:3000'}/app`);
    await page.getByRole('button', { name: 'Analizează zona', exact: true }).waitFor();
    const response = path => page.waitForResponse(r => new URL(r.url()).pathname === path && r.request().method() === 'POST');
    const analysisPromise = response('/analyze');
    await page.getByRole('button', { name: 'Analizează zona', exact: true }).click();
    const analysisResponse = await analysisPromise;
    assert.equal(analysisResponse.status(), 200);
    const analysis = await analysisResponse.json();
    await page.getByRole('button', { name: 'Vezi propuneri' }).click();
    const proposalPromise = response('/propose');
    await page.getByRole('button', { name: 'Vezi propunerile' }).click();
    const proposalResponse = await proposalPromise;
    const proposal = await proposalResponse.json();
    assert.equal(proposalResponse.request().postDataJSON().issue_id, analysis.issues[0].id);
    await page.getByRole('button', { name: 'Moderată', exact: true }).click();
    const evaluatePromise = response('/evaluate');
    await page.getByRole('button', { name: 'Compară rezultatele' }).click();
    const evaluated = await evaluatePromise;
    assert.equal(evaluated.status(), 200);
    const payload = evaluated.request().postDataJSON();
    assert.equal(payload.baseline_id, analysis.baseline_id);
    assert.deepEqual(payload.interventions, proposal.alternatives.find(a => a.level === 'moderate').interventions);
    const result = await evaluated.json();
    await page.getByRole('table', { name: 'Situația actuală și propunerea aleasă' }).waitFor();
    for (const row of result.comparisons) {
      const label = { ns_delay: 'Timp de așteptare · nord–sud', ew_delay: 'Timp de așteptare · est–vest', mean_delay: 'Timp mediu de așteptare' }[row.indicator_id];
      const displayed = page.getByRole('row').filter({ has: page.getByRole('rowheader', { name: label, exact: true }) });
      assert.ok((await displayed.innerText()).includes(row.delta.value.toLocaleString('ro-RO', { maximumFractionDigits: 2 })));
    }
    await page.getByRole('button', { name: 'Scenarii', exact: true }).click();
    await page.getByLabel('Ajustează durata verdelui').check();
    await page.getByLabel(/Verde nord–sud/).fill('55');
    const tunedPromise = response('/propose');
    await page.getByRole('button', { name: 'Vezi propunerile' }).click();
    assert.equal((await tunedPromise).request().postDataJSON().parameters.ns_green_seconds, 55);
    const tunedEvaluation = response('/evaluate');
    await page.getByRole('button', { name: 'Compară rezultatele' }).click();
    assert.equal((await (await tunedEvaluation).json()).scenario_inputs.ns_green_seconds, 55);

    await page.getByRole('button', { name: 'Explorează', exact: true }).click();
    await page.getByLabel('Alege zona').selectOption('tatarasi');
    await page.getByRole('button', { name: 'Compară', exact: true }).click();
    assert.equal(await page.getByRole('table').count(), 0, 'Area change must clear comparisons');
    await page.getByRole('button', { name: 'Explorează', exact: true }).click();
    await page.route('**/analyze', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: { code: 'test_unavailable', message: 'API indisponibil pentru test', details: [], request_id: 'test' } }) }));
    await page.getByRole('button', { name: 'Analizează zona', exact: true }).click();
    await page.getByRole('alert').filter({ hasText: 'API indisponibil pentru test' }).waitFor();
    assert.equal(await page.getByRole('button', { name: 'Vezi propuneri' }).count(), 0, 'No fixture fallback');
    await page.unroute('**/analyze');

    let release, finished;
    const gate = new Promise(resolve => { release = resolve; });
    const routed = new Promise(resolve => { finished = resolve; });
    await page.route('**/analyze', async route => {
      await gate;
      try { await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(analysis) }); }
      catch { /* An aborted browser request may already be gone. */ }
      finally { finished(); }
    });
    const pending = page.waitForRequest(r => new URL(r.url()).pathname === '/analyze');
    await page.getByRole('button', { name: 'Analizează zona', exact: true }).click();
    await pending;
    await page.getByLabel('Alege zona').selectOption('centru');
    release(); await routed;
    await page.getByRole('heading', { name: 'Începe cu o zonă.' }).waitFor();
    assert.equal(await page.getByRole('button', { name: 'Vezi propuneri' }).count(), 0, 'Stale area response must not restore analysis');
    await page.unroute('**/analyze');

    await page.getByRole('button', { name: 'Acces pietonal', exact: true }).click();
    await page.getByRole('button', { name: 'Explorează traseele' }).click();
    await page.getByRole('button', { name: 'Compară legătura 1', exact: true }).waitFor({ timeout: 100000 });
    await page.getByRole('button', { name: 'Compară legătura 1', exact: true }).click();
    await page.getByRole('heading', { name: 'Cum se schimbă traseele' }).waitFor();
    for (const width of [375, 768, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `Overflow at ${width}`);
    }
    assert.deepEqual(errors, []);
    console.log('PASS: real API flow, exact intervention/baseline, tuning, reset, stale-response cancellation, failure without fallback, spatial flow, responsive widths, no browser exceptions.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
