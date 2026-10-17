/** Geometrie de prezentare. Coordonatele sunt ilustrative, nu dimensiuni de inginerie.
 * x = est, z = sud, y = cotă/elevație; toate randările consumă aceleași definiții comune.
 */
export type Point = Readonly<{ x: number; y: number; z: number }>;
export type Layout = 'existing' | 'proposed';
export type Intervention = 'underpass' | 'surface';
export type Road = { id: string; points: readonly Point[]; width: number; kind: 'surface' | 'lower'; sidewalk: boolean };
export type Mark = { point: Point; yaw: number; width: number; length: number; kind: 'crossing' | 'stop' };

export const junction = {
  bounds: { x: 40, z: 20 },
  roadWidth: 4.8,
  laneWidth: 2.4,
  outerRadius: 5.4,
  curbRadius: 6.0,
  islandRadius: 2.7,
  ringMarkRadius: 4.05,
  tramBedWidth: 0.92,
  railOffset: 0.36,
  tunnelInnerHalf: 2.4,
  sidewalk: 0.7,
  trenchHalfWidth: 2.7,
  rampStart: 28,
  portal: 5.8,
  floor: -1.8,
  deckThickness: 0.35,
  clearance: 1.45,
  wallThickness: 0.25,
  camera: { position: [39, 47, 62] as const, target: [0, -0.5, 0] as const, halfWidth: 45, halfHeight: 30 },
  buildings: [
    { x: -16, z: -12, w: 7, d: 4, h: 3.3 }, { x: -24, z: -10, w: 4, d: 5, h: 2.1 },
    { x: 15, z: 13, w: 6, d: 4.5, h: 3.1 }, { x: 24, z: 11, w: 4, d: 5, h: 2.2 },
    { x: -15, z: 14, w: 6, d: 3.5, h: 2.6 }, { x: 15, z: -14, w: 6, d: 3.5, h: 2.6 },
  ],
  trees: [[-10, -10], [-21, -15], [9, 13], [21, 16], [-9, 16], [9, -16]] as const,
};

export const interventions = {
  underpass: {
    label: 'Pasaj subteran Est–Vest',
    description: 'Calea directă de tranzit subteran ocolește complet intersecția. Deschide secțiunea pentru a inspecta calea inferioară, portalurile și gabaritul util sub sensul giratoriu de suprafață.',
  },
  surface: {
    label: 'Giratoriu de suprafață & viraje la stânga',
    description: 'Sensul giratoriu compact de suprafață, amplasat pe placa structurală, acomodează toate virajele la stânga, la dreapta, întoarcerile și traversarea tramvaiului fără teren urban suplimentar.',
  },
} as const;

export const point = (x: number, y: number, z: number): Point => ({ x, y, z });

export function elevation(x: number): number {
  const ax = Math.abs(x);
  if (ax >= junction.rampStart) return 0;
  if (ax <= junction.portal) return junction.floor;
  const t = (junction.rampStart - ax) / (junction.rampStart - junction.portal);
  return junction.floor * t;
}

function straight(id: string, a: Point, b: Point, width = junction.roadWidth, kind: Road['kind'] = 'surface', sidewalk = true): Road {
  return { id, points: [a, b], width, kind, sidewalk };
}

/** Generează bretele fluide de suprafață ce conectează accesul Est-Vest la sensul giratoriu */
function slipLane(id: string, startX: number, startZ: number, endX: number, endZ: number): Road {
  const midX = (startX + endX) / 2;
  const p0 = [startX, startZ], p1 = [midX, startZ], p2 = [midX, endZ], p3 = [endX, endZ];
  const points: Point[] = [];
  const steps = 24;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps, s = 1 - t;
    const x = s * s * s * p0[0]! + 3 * s * s * t * p1[0]! + 3 * s * t * t * p2[0]! + t * t * t * p3[0]!;
    const z = s * s * s * p0[1]! + 3 * s * s * t * p1[1]! + 3 * s * t * t * p2[1]! + t * t * t * p3[1]!;
    points.push(point(x, 0, z));
  }
  return { id, points, width: junction.laneWidth, kind: 'surface', sidewalk: true };
}

export function roadEdges(road: Road, extraWidth = 0): readonly [Point, Point][] {
  return road.points.map((p, i) => {
    const a = road.points[Math.max(0, i - 1)]!, b = road.points[Math.min(road.points.length - 1, i + 1)]!;
    const dx = b.x - a.x, dz = b.z - a.z, length = Math.hypot(dx, dz) || 1, half = (road.width + extraWidth) / 2;
    return [
      point(p.x - (dz / length) * half, p.y, p.z + (dx / length) * half),
      point(p.x + (dz / length) * half, p.y, p.z - (dx / length) * half),
    ] as const;
  });
}

export function roadPolygon(road: Road, extraWidth = 0): string {
  const edges = roadEdges(road, extraWidth);
  return [...edges.map(e => e[0]), ...edges.map(e => e[1]).reverse()].map(p => `${p.x},${p.z}`).join(' ');
}

export function getGeometry(layout: Layout) {
  const ew = straight('east-west', point(-junction.bounds.x, 0, 0), point(junction.bounds.x, 0, 0));
  const ns = straight('north-south', point(0, 0, -junction.bounds.z), point(0, 0, junction.bounds.z));

  const xSamples = [...new Set([
    ...Array.from({ length: 129 }, (_, i) => -junction.bounds.x + i * (junction.bounds.x * 2 / 128)),
    -junction.rampStart, -junction.portal, 0, junction.portal, junction.rampStart,
  ])].sort((a, b) => a - b);
  const lower: Road = {
    ...ew,
    id: 'east-west-underpass',
    kind: 'lower',
    sidewalk: false,
    points: xSamples.map(x => point(x, elevation(x), 0)),
  };

  const westEntry = slipLane('west-entry', -junction.rampStart, 1.2, -junction.outerRadius, 2.0);
  const westExit = slipLane('west-exit', -junction.outerRadius, -2.0, -junction.rampStart, -1.2);
  const eastEntry = slipLane('east-entry', junction.rampStart, -1.2, junction.outerRadius, -2.0);
  const eastExit = slipLane('east-exit', junction.outerRadius, 2.0, junction.rampStart, 1.2);

  const northApproach = straight('north-approach', point(0, 0, -junction.bounds.z), point(0, 0, -junction.outerRadius));
  const southApproach = straight('south-approach', point(0, 0, junction.outerRadius), point(0, 0, junction.bounds.z));

  const connectors = layout === 'proposed' ? [westEntry, westExit, eastEntry, eastExit] : [];
  const roads = layout === 'existing'
    ? [ew, ns]
    : [lower, northApproach, southApproach, ...connectors];

  const ewNorthSidewalk: Road = {
    id: 'ew-north-sidewalk',
    points: [point(-junction.bounds.x, 0, -3.1), point(junction.bounds.x, 0, -3.1)],
    width: junction.sidewalk,
    kind: 'surface',
    sidewalk: false,
  };
  const ewSouthSidewalk: Road = {
    id: 'ew-south-sidewalk',
    points: [point(-junction.bounds.x, 0, 3.1), point(junction.bounds.x, 0, 3.1)],
    width: junction.sidewalk,
    kind: 'surface',
    sidewalk: false,
  };

  const marks: Mark[] = [];
  if (layout === 'existing') {
    for (const z of [-8, 8]) marks.push({ point: point(0, 0.03, z), yaw: 0, width: junction.roadWidth, length: 0.65, kind: 'crossing' });
    for (const x of [-8, 8]) marks.push({ point: point(x, 0.03, 0), yaw: Math.PI / 2, width: junction.roadWidth, length: 0.65, kind: 'crossing' });
  } else {
    for (const z of [-7.2, 7.2]) {
      marks.push({ point: point(0, 0.03, z), yaw: 0, width: junction.roadWidth, length: 0.65, kind: 'crossing' });
    }
    for (const r of [westEntry, eastEntry]) {
      const p = r.points[16]!, pPrev = r.points[15]!, pNext = r.points[17]!;
      const yaw = Math.atan2(pNext.x - pPrev.x, pNext.z - pPrev.z) + Math.PI / 2;
      marks.push({ point: point(p.x, 0.04, p.z), yaw, width: r.width, length: 0.65, kind: 'crossing' });
    }
    for (const r of [westEntry, eastEntry]) {
      const p = r.points[r.points.length - 2]!, pPrev = r.points[r.points.length - 3]!, pNext = r.points[r.points.length - 1]!;
      const yaw = Math.atan2(pNext.x - pPrev.x, pNext.z - pPrev.z) + Math.PI / 2;
      marks.push({ point: point(p.x, 0.04, p.z), yaw, width: r.width, length: 0.16, kind: 'stop' });
    }
  }

  const arrows = layout === 'existing' ? [
    { point: point(-20, 0, 1.2), yaw: Math.PI / 2 },
    { point: point(20, 0, -1.2), yaw: -Math.PI / 2 },
    { point: point(-1.2, 0, -13), yaw: 0 },
    { point: point(1.2, 0, 13), yaw: Math.PI },
  ] : [
    { point: point(-16, elevation(-16), 1.2), yaw: Math.PI / 2 },
    { point: point(16, elevation(16), -1.2), yaw: -Math.PI / 2 },
    { point: point(-1.2, 0, -12), yaw: 0 },
    { point: point(1.2, 0, 12), yaw: Math.PI },
    { point: point(-14, 0, 3.6), yaw: Math.PI / 2 },
    { point: point(14, 0, -3.6), yaw: -Math.PI / 2 },
    { point: point(2.8, 0, 2.8), yaw: -Math.PI / 4 },
  ];

  const anchors = {
    underpass: point(-12, elevation(-12), 0),
    surface: point(0, 0, 4.0),
  };

  return {
    roads,
    connectors,
    ewNorthSidewalk,
    ewSouthSidewalk,
    marks,
    arrows,
    anchors,
    buildings: junction.buildings,
    trees: junction.trees,
  };
}

export function markPolygon(mark: Mark, offset = 0, width = mark.width): string {
  const { point: p, yaw, length } = mark;
  const c = Math.cos(yaw), s = Math.sin(yaw);
  return [
    [offset - width / 2, -length / 2],
    [offset + width / 2, -length / 2],
    [offset + width / 2, length / 2],
    [offset - width / 2, length / 2],
  ].map(([x, z]) => `${p.x + x! * c + z! * s},${p.z - x! * s + z! * c}`).join(' ');
}

export function arrowPoints(p: Point, yaw: number): Point[] {
  return [
    [0, 0.8],
    [-0.33, 0.2],
    [-0.10, 0.2],
    [-0.10, -0.8],
    [0.10, -0.8],
    [0.10, 0.2],
    [0.33, 0.2],
  ].map(([x, z]) => point(
    p.x + x! * Math.cos(yaw) + z! * Math.sin(yaw),
    p.y + 0.025,
    p.z - x! * Math.sin(yaw) + z! * Math.cos(yaw),
  ));
}
