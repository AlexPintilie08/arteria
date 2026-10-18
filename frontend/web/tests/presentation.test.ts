import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ApiContractError, ApiError, ApiTimeoutError } from '@arteria/shared/api';
import { formatTimestamp, presentError, source } from '../src/features/workspace/presentation.ts';

test('source labels distinguish synthetic fixtures from OSM', () => {
  assert.equal(source('fixture'), 'Date demonstrative');
  assert.equal(source('osm'), 'OpenStreetMap');
  assert.equal(source('synthetic-demo'), 'Date demonstrative');
});

test('provenance timestamps preserve missing capture times as unavailable', () => {
  assert.equal(formatTimestamp(null), 'Nedisponibil în răspuns');
  assert.equal(formatTimestamp(undefined), 'Nedisponibil în răspuns');
  assert.match(formatTimestamp('2026-10-18T10:00:00Z'), /18 oct\./);
});

test('known API error codes receive specific user-facing explanations and keep request IDs', () => {
  const error = new ApiError('area unavailable', 404, { error: { code: 'unknown_neighborhood', message: 'server details', details: [], request_id: 'req-123' } });
  const result = presentError(error);
  assert.match(result.title, /catalogul SIM/);
  assert.equal(result.detail, 'server details');
  assert.equal(result.requestId, 'req-123');
});

test('unknown API error codes keep a safe generic title while retaining backend detail', () => {
  const error = new ApiError('safe detail', 503, { error: { code: 'future_code', message: 'safe detail', details: [], request_id: 'req-456' } });
  const result = presentError(error);
  assert.equal(result.title, 'API-ul nu a putut procesa cererea.');
  assert.equal(result.detail, 'safe detail');
});

test('all implemented backend error codes have an intentional readable fallback', () => {
  const known = ['unknown_neighborhood', 'study_area_rejected', 'spatial_failure', 'spatial_unavailable', 'spatial_timeout', 'validation_error', 'invalid_request', 'unknown_resource', 'incompatible_scenario', 'capacity_unavailable', 'storage_unavailable', 'sumo_unavailable'];
  for (const code of known) {
    const result = presentError(new ApiError('backend detail', 503, { error: { code, message: 'backend detail', details: [], request_id: 'req' } }));
    assert.notEqual(result.title, 'API-ul nu a putut procesa cererea.', `missing mapping for ${code}`);
    assert.equal(result.requestId, 'req');
  }
});

test('network, timeout, and invalid-response failures stay distinct and never present results', () => {
  assert.match(presentError(new TypeError('fetch failed')).title, /contacta serviciul API/);
  assert.match(presentError(new ApiTimeoutError()).title, /nu a răspuns/);
  const invalid = presentError(new ApiContractError('spatialStudy', 'response.source invalid'));
  assert.match(invalid.title, /Nu am afișat rezultate/);
  assert.match(invalid.detail, /spatialStudy/);
});
