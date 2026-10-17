// Run with PLAYWRIGHT_MODULE pointing to a local Playwright installation.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome' });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    const mapErrors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => { if (message.text().startsWith('MapLibre:')) mapErrors.push(message.text()); });
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    await page.getByRole('heading', { name: 'Un oraș se schimbă. Mai întâi, îl înțelegem.' }).waitFor();
    assert.equal(await page.locator('.map-canvas').count(), 0, 'Presentation must not mount the product map');
    fs.mkdirSync('.qa', { recursive: true });
    await page.screenshot({ path: '.qa/presentation-desktop.png', fullPage: true });
    await page.setViewportSize({ width: 375, height: 812 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({ path: '.qa/presentation-mobile.png', fullPage: true });
    await page.getByRole('link', { name: 'Deschide aplicația', exact: true }).click();
    await page.waitForURL('**/app');
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.waitForLoadState('networkidle');
    await page.getByRole('heading', { name: 'Începe cu o zonă.' }).waitFor();
    await page.getByRole('button', { name: 'Explorează previzualizarea' }).click();
    await page.getByText('Acces pietonal la servicii', { exact: true }).waitFor();
    assert.equal(await page.locator('.evidence--unknown').count(), 3);
    await page.getByText('Straturi pentru analiză', { exact: false }).click();
    await page.getByLabel('Mers pe jos', { exact: true }).uncheck();
    assert.equal(await page.getByRole('button', { name: 'Explorează previzualizarea' }).isDisabled(), true);
    await page.getByLabel('Biciclete', { exact: true }).check();
    await page.getByRole('button', { name: 'Explorează previzualizarea' }).click();
    await page.getByLabel('Cartier / reper de navigare').selectOption('tatarasi');
    await page.getByRole('heading', { name: 'Începe cu o zonă.' }).waitFor();
    await page.getByRole('button', { name: 'Scenarii', exact: true }).click();
    await page.getByRole('heading', { name: 'O schimbare, trei perspective.' }).waitFor();
    await page.getByRole('button', { name: 'Compară', exact: true }).click();
    await page.getByRole('heading', { name: 'Înainte. După. Cu dovezi.' }).waitFor();
    await page.getByRole('button', { name: 'Explorează', exact: true }).click();
    await page.getByText('Straturi pentru analiză', { exact: false }).click();
    fs.mkdirSync('.qa', { recursive: true });
    await page.screenshot({ path: '.qa/web-desktop.png', fullPage: true });
    for (const [width, height] of [[375, 812], [768, 1024], [812, 375]]) {
      await page.setViewportSize({ width, height });
      await page.emulateMedia({ reducedMotion: 'reduce' });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `Overflow at ${width}px`);
      await page.screenshot({ path: `.qa/web-${width}.png`, fullPage: true });
    }
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement?.textContent), 'Sari la spațiul de lucru');
    assert.deepEqual(errors, []);
    assert.deepEqual(mapErrors, []);
    console.log('PASS: presentation, /app entry, navigation, preview, evidence, layers, area reset, responsive widths, reduced motion, keyboard, no page errors.');
  } finally { await browser.close(); }
})().catch((error) => { console.error(error); process.exitCode = 1; });
