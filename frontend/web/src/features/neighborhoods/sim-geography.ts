import type { Feature, FeatureCollection, Geometry, Position } from 'geojson';

export type SimGeometry = Extract<Geometry, { type: 'Point' | 'Polygon' | 'MultiPolygon' }>;
export type SimFeature = Feature<SimGeometry, Record<string, unknown>>;

export interface SimValidationRecord {
  id: string;
  status: 'valid' | 'point_only' | 'requires_controlled_analysis' | 'invalid';
  analysis_eligible: boolean;
  reason?: string | null;
  area_km2?: number | null;
  configured_limits?: { max_area_km2: number; max_extent_km: number };
}

export interface SourcedPlace {
  id: string;
  name: string;
  aliases: string[];
  feature: SimFeature;
  geometryType: 'Point' | 'Polygon' | 'MultiPolygon';
  validation: SimValidationRecord;
}

export interface SimCatalogMetadata {
  source?: string;
  source_snapshot_at?: string;
  retrieved_at?: string;
  license?: string;
  attribution?: string;
  attribution_url?: string;
  coverage?: string;
  limitations?: string[];
}

export interface LoadedSimCatalog {
  places: SourcedPlace[];
  metadata: SimCatalogMetadata;
  skippedCount: number;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isPosition(value: unknown): value is Position {
  return Array.isArray(value)
    && value.length >= 2
    && typeof value[0] === 'number'
    && typeof value[1] === 'number'
    && Number.isFinite(value[0])
    && Number.isFinite(value[1])
    && value[0] >= -180 && value[0] <= 180
    && value[1] >= -90 && value[1] <= 90;
}

function samePosition(left: Position, right: Position): boolean {
  return left[0] === right[0] && left[1] === right[1];
}

function isLinearRing(value: unknown): value is Position[] {
  return Array.isArray(value)
    && value.length >= 4
    && value.every(isPosition)
    && samePosition(value[0]!, value[value.length - 1]!);
}

function isPolygonCoordinates(value: unknown): value is Position[][] {
  return Array.isArray(value) && value.length > 0 && value.every(isLinearRing);
}

export function isSupportedSimGeometry(value: unknown): value is SimGeometry {
  if (!isRecord(value)) return false;
  if (value.type === 'Point') return isPosition(value.coordinates);
  if (value.type === 'Polygon') return isPolygonCoordinates(value.coordinates);
  if (value.type === 'MultiPolygon') {
    return Array.isArray(value.coordinates)
      && value.coordinates.length > 0
      && value.coordinates.every(isPolygonCoordinates);
  }
  return false;
}

function normalizeSearch(value: string): string {
  return value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase().trim();
}

export function loadSimCatalog(catalogValue: unknown, validationValue: unknown): LoadedSimCatalog {
  if (!isRecord(catalogValue) || catalogValue.type !== 'FeatureCollection' || !Array.isArray(catalogValue.features)) {
    throw new Error('Catalogul geografic SIM nu are format GeoJSON FeatureCollection.');
  }
  const validationRecords = isRecord(validationValue) && isRecord(validationValue.records)
    ? validationValue.records
    : {};
  const places: SourcedPlace[] = [];
  let skippedCount = 0;

  for (const candidate of catalogValue.features) {
    if (!isRecord(candidate) || candidate.type !== 'Feature' || !isRecord(candidate.properties)) {
      skippedCount += 1;
      continue;
    }
    const properties = candidate.properties;
    const id = properties.neighborhood_id ?? properties.place_point_id ?? candidate.id;
    const name = properties.name;
    const geometry = candidate.geometry;
    if (typeof id !== 'string' || !id.trim() || typeof name !== 'string' || !name.trim() || !isSupportedSimGeometry(geometry)) {
      skippedCount += 1;
      continue;
    }
    const aliases = Array.isArray(properties.alternative_names)
      ? properties.alternative_names.filter((alias): alias is string => typeof alias === 'string')
      : [];
    const validation = isRecord(validationRecords[id])
      ? validationRecords[id] as unknown as SimValidationRecord
      : {
          id,
          status: geometry.type === 'Point' ? 'point_only' : 'invalid',
          analysis_eligible: false,
          reason: 'Lipsește validarea implicită din SIM.',
        } satisfies SimValidationRecord;
    places.push({
      id,
      name,
      aliases,
      feature: candidate as unknown as SimFeature,
      geometryType: geometry.type,
      validation,
    });
  }

  return {
    places,
    metadata: isRecord(catalogValue.metadata) ? catalogValue.metadata as SimCatalogMetadata : {},
    skippedCount,
  };
}

export function searchSimPlaces(places: SourcedPlace[], query: string): SourcedPlace[] {
  const needle = normalizeSearch(query);
  if (!needle) return places;
  const matches = places.filter((place) => [place.id, place.name, ...place.aliases]
    .some((field) => normalizeSearch(field).includes(needle)));
  return matches.sort((left, right) => {
    const leftExact = [left.id, left.name, ...left.aliases].some((field) => normalizeSearch(field) === needle);
    const rightExact = [right.id, right.name, ...right.aliases].some((field) => normalizeSearch(field) === needle);
    return Number(rightExact) - Number(leftExact);
  });
}

export function featureBounds(feature: SimFeature): [[number, number], [number, number]] | null {
  const geometry = feature.geometry;
  if (!isSupportedSimGeometry(geometry)) return null;
  let west = Infinity;
  let south = Infinity;
  let east = -Infinity;
  let north = -Infinity;
  const visit = (value: unknown): boolean => {
    if (isPosition(value)) {
      const longitude = value[0]!;
      const latitude = value[1]!;
      west = Math.min(west, longitude);
      south = Math.min(south, latitude);
      east = Math.max(east, longitude);
      north = Math.max(north, latitude);
      return true;
    }
    if (!Array.isArray(value)) return false;
    return value.every(visit);
  };
  if (!visit(geometry.coordinates) || !Number.isFinite(west) || !Number.isFinite(north)) return null;
  return [[west, south], [east, north]];
}

export function placeCenter(place: SourcedPlace): [number, number] | null {
  if (place.geometryType === 'Point') {
    const coordinates = place.feature.geometry.coordinates;
    return isPosition(coordinates) ? [coordinates[0]!, coordinates[1]!] : null;
  }
  const bounds = featureBounds(place.feature);
  return bounds ? [(bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2] : null;
}

export function controlledAnalysisMessage(place: SourcedPlace): string {
  const limits = place.validation.configured_limits;
  const reason = place.validation.reason?.toLocaleLowerCase() ?? '';
  if (limits && reason.includes('extent must not exceed')) {
    return `Extinderea poligonului depășește limita SIM implicită de ${limits.max_extent_km} km. Este necesară o analiză controlată.`;
  }
  if (limits && reason.includes('no larger') && typeof place.validation.area_km2 === 'number') {
    const area = place.validation.area_km2.toLocaleString('ro-RO', { maximumFractionDigits: 2 });
    return `Suprafața poligonului este ${area} km², peste limita SIM implicită de ${limits.max_area_km2} km². Este necesară o analiză controlată.`;
  }
  return 'Poligonul depășește limitele SIM implicite și necesită o analiză controlată.';
}
