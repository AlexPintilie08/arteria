import type { SpatialPlanningResult, SpatialStudy } from '@arteria/shared/contracts';

export type JsonRecord = Record<string, unknown>;

export function isJsonRecord(value: unknown): value is JsonRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function jsonArray(value: unknown): JsonRecord[] {
  return Array.isArray(value) ? value.filter(isJsonRecord) : [];
}

export function studyProblems(study: SpatialStudy): JsonRecord[] {
  const currentProblems = study.urban_issues?.problems;
  if (Array.isArray(currentProblems)) return jsonArray(currentProblems);
  // Stored studies from before urban_issues retain the same graph findings in analysis.issues.
  return jsonArray(study.analysis.issues).flatMap((issue) => {
    const problemId = issue.problem_id ?? issue.issue_id ?? issue.id;
    if (typeof problemId !== 'string' || !problemId) return [];
    return [{ ...issue, problem_id: problemId, problem_type: issue.problem_type ?? issue.type }];
  });
}

export function simSolutions(study: SpatialStudy): JsonRecord[] {
  return jsonArray(study.solution_plan?.solutions);
}

export function validatedRecommendations(result: SpatialPlanningResult | null): SpatialPlanningResult['recommended_solutions'] {
  if (!result || !result.ai_generated) return [];
  if (!['completed', 'completed_with_rejections'].includes(result.provider_status)) return [];
  const validationStatus = result.validation?.status;
  if (!['validated', 'completed_with_rejections'].includes(String(validationStatus))) return [];
  return result.recommended_solutions.filter((item) =>
    typeof item.solution_id === 'string'
    && typeof item.candidate_id === 'string'
    && item.authoritative_sim_solution?.candidate_id === item.candidate_id
  );
}

export interface SafeMapGeometry {
  type: 'Point' | 'LineString' | 'MultiLineString' | 'Polygon' | 'MultiPolygon';
  coordinates: unknown;
}

export interface SafeMapFeature {
  type: 'Feature';
  id?: string | number;
  geometry: SafeMapGeometry;
  properties: JsonRecord;
}

export interface SafeMapFeatureCollection {
  type: 'FeatureCollection';
  features: SafeMapFeature[];
}

function position(value: unknown): value is [number, number] {
  return Array.isArray(value)
    && value.length >= 2
    && typeof value[0] === 'number'
    && Number.isFinite(value[0])
    && value[0] >= -180 && value[0] <= 180
    && typeof value[1] === 'number'
    && Number.isFinite(value[1])
    && value[1] >= -90 && value[1] <= 90;
}

function line(value: unknown): value is [number, number][] {
  return Array.isArray(value) && value.length >= 2 && value.every(position);
}

function ring(value: unknown): value is [number, number][] {
  return line(value) && value.length >= 4
    && value[0]![0] === value[value.length - 1]![0]
    && value[0]![1] === value[value.length - 1]![1];
}

function polygon(value: unknown): value is [number, number][][] {
  return Array.isArray(value) && value.length > 0 && value.every(ring);
}

export function isSafeMapGeometry(value: unknown): value is SafeMapGeometry {
  if (!isJsonRecord(value)) return false;
  if (value.type === 'Point') return position(value.coordinates);
  if (value.type === 'LineString') return line(value.coordinates);
  if (value.type === 'MultiLineString') return Array.isArray(value.coordinates) && value.coordinates.length > 0 && value.coordinates.every(line);
  if (value.type === 'Polygon') return polygon(value.coordinates);
  if (value.type === 'MultiPolygon') return Array.isArray(value.coordinates) && value.coordinates.length > 0 && value.coordinates.every(polygon);
  return false;
}

export function safeFeatureCollection(value: unknown): SafeMapFeatureCollection {
  if (!isJsonRecord(value) || value.type !== 'FeatureCollection' || !Array.isArray(value.features)) {
    return { type: 'FeatureCollection', features: [] };
  }
  const features = value.features.flatMap((item): SafeMapFeature[] => {
    if (!isJsonRecord(item) || item.type !== 'Feature' || !isSafeMapGeometry(item.geometry)) return [];
    return [{
      type: 'Feature',
      ...(typeof item.id === 'string' || typeof item.id === 'number' ? { id: item.id } : {}),
      geometry: item.geometry,
      properties: isJsonRecord(item.properties) ? item.properties : {},
    }];
  });
  return { type: 'FeatureCollection', features };
}

export function geometryFeatureCollection(value: unknown, featureId = 'candidate'): SafeMapFeatureCollection {
  const collection = safeFeatureCollection(value);
  if (collection.features.length || !isJsonRecord(value)) return collection;
  const geometry = value.type === 'Feature' ? value.geometry : value;
  if (!isSafeMapGeometry(geometry)) return { type: 'FeatureCollection', features: [] };
  return {
    type: 'FeatureCollection',
    features: [{ type: 'Feature', id: featureId, geometry, properties: {} }],
  };
}

export function returnedAggregate(value: unknown): JsonRecord | null {
  if (!isJsonRecord(value)) return null;
  if (isJsonRecord(value.aggregate)) return value.aggregate;
  return value;
}
