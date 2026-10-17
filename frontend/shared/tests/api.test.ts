import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createApiClient, ApiError } from '../core/api.ts';
import { createDemoAnalysis, emptyIndicators } from '../core/fixtures.ts';
import type { AnalyzeRequest } from '../core/contracts.ts';
const request: AnalyzeRequest = {
  area: { city_id: 'iasi-ro', area_id: 'test-area', boundary: null, boundary_source: 'known_area', crs: 'EPSG:4326' },
  layers: ['walking'], analysis: { network_modes: ['walk'], accessibility_thresholds: [] }, data_as_of: null,
};
test('analysis preserves wire names and backend evidence', async () => {
  const result = createDemoAnalysis(request.area);
  const client = createApiClient('https://backend.example/', { fetch: async (url, init) => {
    assert.equal(url, 'https://backend.example/analyze'); assert.equal(init?.method, 'POST');
    assert.deepEqual(JSON.parse(String(init?.body)), request);
    return Response.json(result);
  } });
  assert.deepEqual(await client.analyze(request), result);
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
test('cancelling a request aborts its transport', async () => {
  const abort = new AbortController();
  const client = createApiClient('https://backend.example', { fetch: async (_url, init) => {
    assert.equal(init?.signal?.aborted, true); throw new DOMException('Aborted', 'AbortError');
  } });
  abort.abort(); await assert.rejects(client.analyze(request, abort.signal), { name: 'AbortError' });
});
test('demo has unknown values and no fabricated issues', () => {
  assert.ok(emptyIndicators().every((item) => item.value === null && item.status === 'unknown' && item.provenance.length === 0));
  assert.deepEqual(createDemoAnalysis(request.area).issues, []);
});
