import assert from 'node:assert/strict';
import test from 'node:test';
import { ApiContractError, createApiClient } from '../core/api.ts';

const planning = {
  planning_id: 'planning-1', study_id: 'study/one', baseline_id: 'base-1', source: 'osm', area_id: 'osm-w-1',
  engine_revision: 'rev-1', calculation: 'pedestrian_graph', evidence_packet_sha256: 'b'.repeat(64),
  provider_status: 'provider_unavailable', provider: null, model_id: null, ai_generated: false, summary: null,
  identified_problems: [], recommended_solutions: [], validation: null, error_code: 'provider_disabled',
  created_at: '2026-10-18T10:00:00Z', warnings: ['No cloud response.'],
};

test('AI planning POST preserves idempotency and rejects non-AI result data', async () => {
  let requestUrl = '';
  let requestInit: RequestInit | undefined;
  const client = createApiClient('https://backend.example/', {
    fetch: async (url, init) => { requestUrl = String(url); requestInit = init; return Response.json(planning); },
  });
  const result = await client.spatialPlanning('study/one', 'stable-retry-key');
  assert.equal(requestUrl, 'https://backend.example/api/v1/spatial/studies/study%2Fone/planning');
  assert.equal(requestInit?.method, 'POST');
  assert.equal(new Headers(requestInit?.headers).get('Idempotency-Key'), 'stable-retry-key');
  assert.equal(result.ai_generated, false);
  assert.deepEqual(result.recommended_solutions, []);

  const invalid = createApiClient('https://backend.example', {
    fetch: async () => Response.json({ ...planning, recommended_solutions: [{ solution_id: 'fake', candidate_id: 'fake' }] }),
  });
  await assert.rejects(invalid.spatialPlanning('study-1', 'key'), ApiContractError);
});

test('saved planning GET uses encoded IDs and validates its persisted response', async () => {
  let requestUrl = '';
  let requestMethod = '';
  const client = createApiClient('https://backend.example', {
    fetch: async (url, init) => { requestUrl = String(url); requestMethod = String(init?.method); return Response.json({ ...planning, planning_id: 'planning-2' }); },
  });
  const result = await client.getSpatialPlanning('study one', 'planning/2');
  assert.equal(requestUrl, 'https://backend.example/api/v1/spatial/studies/study%20one/planning/planning%2F2');
  assert.equal(requestMethod, 'GET');
  assert.equal(result.planning_id, 'planning-2');
});
