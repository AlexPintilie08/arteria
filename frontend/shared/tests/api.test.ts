import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createApiClient, ApiError, ApiContractError, ApiTimeoutError } from '../core/api.ts';
import { createDemoAnalysis, emptyIndicators } from '../core/fixtures.ts';
import type { AnalyzeRequest } from '../core/contracts.ts';
const request: AnalyzeRequest = {
  area: { city_id: 'iasi-ro', area_id: 'test-area', boundary: null, boundary_source: 'known_area', crs: 'EPSG:4326' },
  layers: ['walking'], analysis: { network_modes: ['walk'], accessibility_thresholds: [] }, data_as_of: null,
};
const provenance = [{ source: 'synthetic-demo', source_version: 'demo-2', retrieved_at: '2026-10-18T10:00:00Z', method: 'synthetic estimate', crs: 'EPSG:4326' }];
function apiAnalysis() {
  const result = createDemoAnalysis(request.area);
  return { ...result, mode: 'demo' as const, inputs: { cycle_seconds: 90, lost_seconds: 10, ns_green_seconds: 40 }, provenance,
    indicators: result.indicators.map(item => ({ ...item, provenance, uncertainty: { kind: 'synthetic_model', description: 'Demo only', interval: null, confidence: null } })),
    issues: [{ id: 'signal_balance', label: 'Demo', indicator_ids: ['mean_delay'], geometry: null, provenance, uncertainty: { kind: 'synthetic_model', description: 'Demo only', interval: null, confidence: null } }],
  };
}
function spatialStudy(source: 'fixture' | 'osm') {
  return { study_id: `study-${source}`, baseline_id: 'base-1', created_at: '2026-10-18T10:00:00Z', source, engine_revision: 'engine-abc', calculation: 'pedestrian_graph',
    analysis: { provenance: { source: source === 'fixture' ? 'synthetic-fixture' : 'openstreetmap', source_version: source === 'fixture' ? 'fixture-1' : 'live OSM snapshot', retrieved_at: source === 'fixture' ? null : '2026-10-18T09:00:00Z', working_crs: 'EPSG:32635' } },
    alternatives: { ranked_candidates: [], warnings: [] }, proposal_options: [], proposal_validation: { status: 'completed', summary: { submitted_count: 0, accepted_count: 0, rejected_count: 0, duplicate_count: 0 }, results: [] }, evidence_packet: {}, warnings: [] };
}
test('analysis preserves wire names and backend evidence', async () => {
  const result = apiAnalysis();
  const client = createApiClient('https://backend.example/', { fetch: async (url, init) => {
    assert.equal(url, 'https://backend.example/analyze'); assert.equal(init?.method, 'POST');
    assert.deepEqual(JSON.parse(String(init?.body)), request);
    return Response.json(result);
  } });
  assert.deepEqual(await client.analyze(request), result);
});
test('malformed successful API responses are rejected instead of cast as results', async () => {
  const client = createApiClient('https://backend.example', { fetch: async () => Response.json({ analysis_id: 'partial' }) });
  await assert.rejects(client.analyze(request), ApiContractError);
});
test('spatial fixture and OSM studies preserve source and nullable capture provenance', async () => {
  for (const source of ['fixture', 'osm'] as const) {
    const client = createApiClient('https://backend.example', { fetch: async () => Response.json(spatialStudy(source)) });
    const result = await client.spatialStudy();
    assert.equal(result.source, source);
    assert.equal(result.analysis.provenance?.retrieved_at, source === 'fixture' ? null : '2026-10-18T09:00:00Z');
    assert.equal(result.calculation, 'pedestrian_graph');
  }
});
test('spatial study with an invalid calculation type fails runtime validation', async () => {
  const invalid = { ...spatialStudy('osm'), calculation: 'sumo_simulation' };
  const client = createApiClient('https://backend.example', { fetch: async () => Response.json(invalid) });
  await assert.rejects(client.spatialNeighborhoodStudy('copou'), ApiContractError);
});
test('stored spatial studies load by encoded ID without reacquiring OSM and retain contract validation', async () => {
  const study = spatialStudy('osm');
  const controller = new AbortController();
  const client = createApiClient('https://backend.example/', { fetch: async (url, init) => {
    assert.equal(url, 'https://backend.example/api/v1/spatial/studies/study%2Fwith%20spaces');
    assert.equal(init?.method, 'GET');
    assert.equal(init?.body, undefined);
    assert.equal(init?.signal?.aborted, false);
    return Response.json(study);
  } });
  assert.deepEqual(await client.getSpatialStudy('study/with spaces', controller.signal), study);
  const invalidClient = createApiClient('https://backend.example', { fetch: async () => Response.json({ ...study, calculation: 'sumo_simulation' }) });
  await assert.rejects(invalidClient.getSpatialStudy('study-osm'), ApiContractError);
});
test('missing stored spatial study preserves the API not-found response', async () => {
  const body = { error: { code: 'study_not_found', message: 'Studiul nu există.', details: [], request_id: 'req_study' } };
  const client = createApiClient('https://backend.example', { fetch: async () => Response.json(body, { status: 404 }) });
  await assert.rejects(client.getSpatialStudy('unknown'), (error: unknown) => error instanceof ApiError && error.status === 404 && error.body?.error.code === 'study_not_found');
});
test('spatial evaluation validates its individual candidate validation result', async () => {
  const evaluation = { study_id: 'study-osm', baseline_id: 'base-1', candidate_id: 'candidate-1', source: 'osm', evaluated_at: '2026-10-18T10:00:00Z', execution: 'stored_graph_comparison', sumo_executed: false,
    impact: { aggregate: { evaluated_pair_count: 3, total_distance_savings_m: null }, routes: [] },
    proposal_validation: { status: 'candidate_backed_evaluated', candidate_id: 'candidate-1', physical_feasibility: 'unknown', findings: [] }, warnings: [] };
  const client = createApiClient('https://backend.example', { fetch: async () => Response.json(evaluation) });
  const result = await client.spatialEvaluate('study-osm', { baseline_id: 'base-1', candidate_id: 'candidate-1', intervention: {} });
  assert.equal(result.execution, 'stored_graph_comparison');
  const invalidClient = createApiClient('https://backend.example', { fetch: async () => Response.json({ ...evaluation, proposal_validation: {} }) });
  await assert.rejects(invalidClient.spatialEvaluate('study-osm', { baseline_id: 'base-1', candidate_id: 'candidate-1', intervention: {} }), ApiContractError);
});
test('proposal and evaluation responses require their nested API contract fields', async () => {
  const proposal = { proposal_set_id: 'ps_1', analysis_id: 'an_1', baseline_id: 'base_1', model: { provider: 'deterministic', model_id: 'signal-catalog-1', generated_at: '2026-10-18T10:00:00Z' }, alternatives: [], rejected_alternatives: [], warnings: [] };
  const proposeClient = createApiClient('https://backend.example', { fetch: async () => Response.json(proposal) });
  assert.equal((await proposeClient.propose({} as never)).proposal_set_id, 'ps_1');
  const invalidProposeClient = createApiClient('https://backend.example', { fetch: async () => Response.json({ ...proposal, alternatives: [{}] }) });
  await assert.rejects(invalidProposeClient.propose({} as never), ApiContractError);

  const evaluation = { evaluation_id: 'ev_1', scenario_id: 'sc_1', created_at: '2026-10-18T10:00:00Z', baseline: { id: 'base_1', source_snapshot: 'synthetic-demo-2', intervention_catalog_version: 'catalog-1' }, scenario: { id: 'sc_1', source_snapshot: 'synthetic-demo-2', intervention_catalog_version: 'catalog-1' }, comparisons: [], simulation: { status: 'not_requested', mode: 'none', run_id: null, started_at: null, completed_at: null, simulator: null, configuration: null, measurements: [] }, warnings: [] };
  const evaluateClient = createApiClient('https://backend.example', { fetch: async () => Response.json(evaluation) });
  assert.equal((await evaluateClient.evaluate({} as never)).evaluation_id, 'ev_1');
  const invalidEvaluateClient = createApiClient('https://backend.example', { fetch: async () => Response.json({ ...evaluation, comparisons: [{ indicator_id: 'mean_delay', baseline: { value: 'not-number' } }] }) });
  await assert.rejects(invalidEvaluateClient.evaluate({} as never), ApiContractError);
});
test('validation errors preserve status and request identifier', async () => {
  const body = { error: { code: 'invalid_area', message: 'Zonă invalidă', details: [], request_id: 'req_test' } };
  const client = createApiClient('https://backend.example', { fetch: async () => Response.json(body, { status: 422 }) });
  await assert.rejects(client.analyze(request), (error: unknown) => error instanceof ApiError && error.status === 422 && error.body?.error.request_id === 'req_test');
});
test('HTML proxy failures never become demo success', async () => {
  const client = createApiClient('https://backend.example', { fetch: async () => new Response('<h1>Unavailable</h1>', { status: 503 }) });
  await assert.rejects(client.analyze(request), (error: unknown) => error instanceof ApiError && error.status === 503);
});
test('malformed error envelopes retain the HTTP status without trusting partial error fields', async () => {
  const client = createApiClient('https://backend.example', { fetch: async () => Response.json({ error: { message: 'partial only' } }, { status: 422 }) });
  await assert.rejects(client.analyze(request), (error: unknown) => error instanceof ApiError && error.status === 422 && !error.body && error.message.includes('422'));
});
test('cancelling a request aborts its transport', async () => {
  const abort = new AbortController();
  const client = createApiClient('https://backend.example', { fetch: async (_url, init) => {
    assert.equal(init?.signal?.aborted, true); throw new DOMException('Aborted', 'AbortError');
  } });
  abort.abort(); await assert.rejects(client.analyze(request, abort.signal), { name: 'AbortError' });
});
test('request timeout is distinct from user cancellation', async () => {
  const client = createApiClient('https://backend.example', { timeoutMs: 1, fetch: async (_url, init) => new Promise((_resolve, reject) => {
    init?.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true });
  }) });
  await assert.rejects(client.analyze(request), ApiTimeoutError);
});
test('demo has unknown values and no fabricated issues', () => {
  assert.ok(emptyIndicators().every((item) => item.value === null && item.status === 'unknown' && item.provenance.length === 0));
  assert.deepEqual(createDemoAnalysis(request.area).issues, []);
});
