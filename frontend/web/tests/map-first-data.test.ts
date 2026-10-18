import assert from 'node:assert/strict';
import test from 'node:test';
import type { SpatialPlanningResult } from '@arteria/shared/contracts';
import { geometryFeatureCollection, safeFeatureCollection, validatedRecommendations } from '../src/features/workspace/map-first-data.ts';

function planning(overrides: Partial<SpatialPlanningResult> = {}): SpatialPlanningResult {
  return {
    planning_id: 'planning-1', study_id: 'study-1', baseline_id: 'base-1', source: 'osm', area_id: 'osm-w-1',
    engine_revision: 'rev-1', calculation: 'pedestrian_graph', evidence_packet_sha256: 'a'.repeat(64),
    provider_status: 'completed', provider: 'openai', model_id: 'model', ai_generated: true, summary: 'Validated summary.',
    identified_problems: [], recommended_solutions: [{
      solution_id: 'sol-1', candidate_id: 'cand-1', title: 'Validated idea',
      authoritative_sim_solution: { solution_id: 'sol-1', candidate_id: 'cand-1', geometry: { type: 'LineString', coordinates: [[27.58, 47.15], [27.59, 47.16]] } },
    }], validation: { status: 'validated' }, error_code: null, created_at: '2026-10-18T10:00:00Z', warnings: [],
    ...overrides,
  };
}

test('validated AI recommendations require AI provenance, a supported provider status, and SIM validation', () => {
  assert.equal(validatedRecommendations(planning()).length, 1);
  assert.equal(validatedRecommendations(planning({ provider_status: 'provider_unavailable', ai_generated: false })).length, 0);
  assert.equal(validatedRecommendations(planning({ provider_status: 'invalid_response' })).length, 0);
  assert.equal(validatedRecommendations(planning({ validation: { status: 'rejected' } })).length, 0);
  assert.equal(validatedRecommendations(planning({ recommended_solutions: [{ solution_id: 'sol-x', candidate_id: 'cand-x' }] })).length, 0);
});

test('malformed problem geometry is ignored safely and never reaches MapLibre', () => {
  assert.doesNotThrow(() => safeFeatureCollection({
    type: 'FeatureCollection',
    features: [
      { type: 'Feature', geometry: { type: 'Point', coordinates: ['bad', 47] }, properties: {} },
      { type: 'Feature', geometry: null, properties: {} },
      { type: 'Feature', geometry: { type: 'Polygon', coordinates: [[ [27, 47], [28, 47], [28, 48] ]] }, properties: {} },
      { type: 'Feature', geometry: { type: 'Point', coordinates: [27.58, 47.15] }, properties: { id: 'valid' } },
      null,
    ],
  }));
  assert.equal(safeFeatureCollection({ type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: ['bad', 47] }, properties: {} },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [27.58, 47.15] }, properties: {} },
  ] }).features.length, 1);
  assert.equal(geometryFeatureCollection({ type: 'Polygon', coordinates: [[ [27, 47], [28, 47], [28, 48], [27, 47] ]] }).features.length, 1);
  assert.equal(geometryFeatureCollection({ type: 'Point', coordinates: [500, 120] }).features.length, 0);
});
