import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import {
  featureBounds,
  loadSimCatalog,
  searchSimPlaces,
  type SimFeature,
} from '../src/features/neighborhoods/sim-geography.ts';

const dataDirectory = new URL('../public/data/', import.meta.url);

async function catalog() {
  const [catalogText, validationText] = await Promise.all([
    readFile(new URL('iasi-neighborhoods.geojson', dataDirectory), 'utf8'),
    readFile(new URL('iasi-neighborhood-validation.json', dataDirectory), 'utf8'),
  ]);
  return loadSimCatalog(JSON.parse(catalogText), JSON.parse(validationText));
}

test('SIM catalog includes 24 polygon and 7 point-only records', async () => {
  const result = await catalog();
  assert.equal(result.places.length, 31);
  assert.equal(result.places.filter((place) => place.geometryType === 'Polygon' || place.geometryType === 'MultiPolygon').length, 24);
  assert.equal(result.places.filter((place) => place.geometryType === 'Point').length, 7);
  assert.equal(result.metadata.license, 'ODbL-1.0');
});

test('malformed features are skipped without throwing', () => {
  assert.doesNotThrow(() => loadSimCatalog({
    type: 'FeatureCollection',
    features: [
      { type: 'Feature', properties: { name: 'Broken', neighborhood_id: 'broken' }, geometry: { type: 'Polygon', coordinates: [[['NaN', 47], [27, 47], [27, 48], ['NaN', 47]]] } },
      null,
    ],
  }, { records: {} }));
  const result = loadSimCatalog({
    type: 'FeatureCollection',
    features: [
      { type: 'Feature', properties: { name: 'Broken', neighborhood_id: 'broken' }, geometry: { type: 'Polygon', coordinates: [[['NaN', 47], [27, 47], [27, 48], ['NaN', 47]]] } },
      null,
    ],
  }, { records: {} });
  assert.equal(result.places.length, 0);
  assert.equal(result.skippedCount, 2);
});

test('search is accent insensitive and polygon bounds include the source extent', async () => {
  const result = await catalog();
  const place = searchSimPlaces(result.places, 'tatarasi')[0];
  assert.equal(place?.name, 'Tătărași');

  const polygon = result.places.find((entry) => entry.name === 'Păcurari');
  assert.ok(polygon);
  assert.equal(polygon.geometryType, 'Polygon');
  const bounds = featureBounds(polygon.feature);
  assert.ok(bounds);
  const points = (polygon.feature.geometry as Extract<SimFeature['geometry'], { type: 'Polygon' }>).coordinates.flat();
  assert.equal(bounds[0][0], Math.min(...points.map((point) => point[0])));
  assert.equal(bounds[0][1], Math.min(...points.map((point) => point[1])));
  assert.equal(bounds[1][0], Math.max(...points.map((point) => point[0])));
  assert.equal(bounds[1][1], Math.max(...points.map((point) => point[1])));
});

test('points keep Point geometry and over-limit polygons require controlled analysis', async () => {
  const result = await catalog();
  const point = result.places.find((entry) => entry.name === 'Bucium');
  assert.equal(point?.geometryType, 'Point');
  assert.equal(point?.feature.geometry.type, 'Point');
  assert.equal(point?.validation.status, 'point_only');

  const large = result.places.filter((entry) => entry.validation.status === 'requires_controlled_analysis');
  assert.deepEqual(large.map((entry) => entry.name).sort(), ['Păcurari', 'Zona Industrială']);
});
