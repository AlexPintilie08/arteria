import * as THREE from 'three';
import {
  getGeometry,
  junction,
  roadEdges,
  markPolygon,
  arrowPoints,
  type Layout,
  type Intervention,
  type Road,
  type Point,
} from './intersection';

export interface UrbanModel {
  setState(layout: Layout, selected: Intervention, reveal: boolean, animate?: boolean): void;
  setVisible(visible: boolean): void;
  setReducedMotion(reduced: boolean): void;
  dispose(): void;
}

/** No continuous animation loop. The shared road geometry is projected into both renderers. */
export function createUrbanModel(host: HTMLDivElement, onFailure: () => void): UrbanModel {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
  renderer.setClearColor('#f2f3ee', 1);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-45, 45, 30, -30, 0.1, 200);
  camera.position.set(...junction.camera.position);
  camera.lookAt(...junction.camera.target);

  scene.add(new THREE.HemisphereLight('#fff9ee', '#a7b7bf', 2.5));
  const sun = new THREE.DirectionalLight('#fff5df', 2.6);
  sun.position.set(-25, 55, 20);
  sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  Object.assign(sun.shadow.camera, { left: -50, right: 50, top: 35, bottom: -35, near: 1, far: 140 });
  sun.shadow.normalBias = 0.035;
  sun.shadow.bias = -0.00015;
  scene.add(sun);

  const geometries = new Set<THREE.BufferGeometry>(), materials = new Set<THREE.Material>();
  const mat = (color: string) => {
    const m = new THREE.MeshStandardMaterial({ color, roughness: 0.96, side: THREE.DoubleSide });
    materials.add(m);
    return m;
  };

  const soil = mat('#dbddcf'), walk = mat('#f3f0e4'), road = mat('#758994'), paint = mat('#fff9e8');
  const wall = mat('#b5bdb7'), house = mat('#e9e6db'), roof = mat('#cfd5cf'), glass = mat('#a9b9b9'), leaf = mat('#a1b79d');
  const teal = mat('#027f82'), rail = mat('#c4d3d4'), amber = mat('#d8b774');

  const groups = { existing: new THREE.Group(), proposed: new THREE.Group() };
  scene.add(groups.existing, groups.proposed);

  const cut = new THREE.Group();
  groups.proposed.add(cut);

  const highlights: THREE.MeshStandardMaterial[] = [];

  function mesh(geometry: THREE.BufferGeometry, material: THREE.Material, parent: THREE.Object3D) {
    geometries.add(geometry);
    const m = new THREE.Mesh(geometry, material);
    m.castShadow = true;
    m.receiveShadow = true;
    parent.add(m);
    return m;
  }

  function box(x: number, z: number, w: number, d: number, bottom: number, height: number, material: THREE.Material, parent: THREE.Object3D) {
    const m = mesh(new THREE.BoxGeometry(w, height, d), material, parent);
    m.position.set(x, bottom + height / 2, z);
    return m;
  }

  function polygon(points: readonly Point[], material: THREE.Material, parent: THREE.Object3D) {
    const shape = new THREE.Shape(points.map(p => new THREE.Vector2(p.x, -p.z)));
    const m = mesh(new THREE.ShapeGeometry(shape), material, parent);
    m.rotation.x = -Math.PI / 2;
    m.position.y = points[0]?.y ?? 0;
    return m;
  }

  function ribbon(r: Road, material: THREE.Material, parent: THREE.Object3D, extra = 0, lift = 0) {
    const positions: number[] = [], indices: number[] = [];
    roadEdges(r, extra).forEach(([a, b], i) => {
      positions.push(a.x, a.y + lift, a.z, b.x, b.y + lift, b.z);
      if (i < r.points.length - 1) {
        const n = i * 2;
        indices.push(n, n + 1, n + 2, n + 1, n + 3, n + 2);
      }
    });
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    g.setIndex(indices);
    g.computeVertexNormals();
    return mesh(g, material, parent);
  }

  function cylinder(radius: number, height: number, y: number, material: THREE.Material, parent: THREE.Object3D, thetaStart = 0, thetaLength = Math.PI * 2) {
    const m = mesh(new THREE.CylinderGeometry(radius, radius, height, 72, 1, false, thetaStart, thetaLength), material, parent);
    m.position.y = y;
    return m;
  }

  const removable = (base: THREE.MeshStandardMaterial) => {
    const m = base.clone();
    m.transparent = true;
    materials.add(m);
    return m;
  };

  function trackPart(z1: number, z2: number, parent: THREE.Object3D, height: number) {
    box(0, (z1 + z2) / 2, junction.tramBedWidth, z2 - z1, height, 0.015, parent === cut ? removable(glass) : glass, parent);
    for (const x of [-junction.railOffset, junction.railOffset]) {
      box(x, (z1 + z2) / 2, 0.05, z2 - z1, height + 0.02, 0.02, parent === cut ? removable(rail) : rail, parent);
    }
  }

  // Build 3D environments for both layouts
  for (const layout of ['existing', 'proposed'] as const) {
    const parent = groups[layout], g = getGeometry(layout);

    if (layout === 'existing') {
      box(0, 0, junction.bounds.x * 2, junction.bounds.z * 2, -3.3, 3.22, soil, parent);
    } else {
      const h = junction.trenchHalfWidth, rs = junction.rampStart;
      const bx = junction.bounds.x, bz = junction.bounds.z;
      // Soil blocks framing the open underpass trench:
      box(0, -(bz + h) / 2, bx * 2, bz - h, -3.3, 3.22, soil, parent);
      box(0, (bz + h) / 2, bx * 2, bz - h, -3.3, 3.22, soil, parent);
      box(-(bx + rs) / 2, 0, bx - rs, h * 2, -3.3, 3.22, soil, parent);
      box((bx + rs) / 2, 0, bx - rs, h * 2, -3.3, 3.22, soil, parent);
    }

    // Context buildings and trees
    for (const b of g.buildings) {
      box(b.x, b.z, b.w + 0.4, b.d + 0.4, -0.08, 0.14, walk, parent);
      box(b.x, b.z, b.w, b.d, 0.06, b.h, house, parent);
      box(b.x, b.z, b.w + 0.1, b.d + 0.1, b.h + 0.06, 0.13, roof, parent);
      for (let level = 0.7; level < b.h; level += 0.8) {
        for (let dx = -b.w / 2 + 0.5; dx < b.w / 2 - 0.2; dx += 0.85) {
          box(b.x + dx, b.z + b.d / 2 + 0.015, 0.36, 0.025, level, 0.3, glass, parent);
        }
      }
    }
    for (const [x, z] of g.trees) {
      const t = mesh(new THREE.IcosahedronGeometry(0.8, 1), leaf, parent);
      t.position.set(x, 0.9, z);
    }

    // Roads & ribbons
    for (const r of g.roads) {
      if (r.sidewalk) ribbon(r, walk, parent, junction.sidewalk * 2, -0.025);

      if (layout === 'proposed' && r.kind === 'lower') {
        ribbon(r, wall, parent, junction.tunnelInnerHalf * 2 - junction.roadWidth, -0.09);
        ribbon(r, teal, parent);
      } else if (layout === 'proposed' && g.connectors.some(c => c.id === r.id)) {
        const m = mat('#758994');
        highlights.push(m);
        ribbon(r, m, parent);
      } else {
        ribbon(r, road, parent);
      }

      // Centerline marks
      if (!r.id.includes('approach')) {
        for (let i = 0; i < r.points.length - 1; i += 2) {
          const a = r.points[i]!, b = r.points[Math.min(i + 1, r.points.length - 1)]!;
          const t: Road = { ...r, points: [a, b], width: 0.06 };
          if (r.points.length > 2) ribbon(t, paint, parent, 0, 0.015);
        }
      }
    }

    if (layout === 'existing') {
      cylinder(junction.curbRadius, 0.1, -0.04, walk, parent);
      cylinder(junction.outerRadius, 0.03, 0.015, road, parent);
      cylinder(junction.islandRadius, 0.16, 0.12, walk, parent);
      cylinder(2.42, 0.02, 0.21, leaf, parent);
      trackPart(-20, 20, parent, 0.23);
      const points = Array.from({ length: 97 }, (_, i) => ({
        x: Math.sin(i / 96 * Math.PI * 2) * junction.ringMarkRadius,
        y: 0.04,
        z: Math.cos(i / 96 * Math.PI * 2) * junction.ringMarkRadius,
      }));
      for (let i = 0; i < points.length - 1; i += 2) {
        ribbon({ id: 'ring-mark', points: [points[i]!, points[i + 1]!], width: 0.065, sidewalk: false, kind: 'surface' }, paint, parent);
      }
    } else {
      const p = junction.portal, h = junction.trenchHalfWidth;

      // Structural bridge deck slab over the underpass
      box(0, -h / 2, p * 2, h, -junction.deckThickness, junction.deckThickness - 0.025, wall, parent);
      box(0, h / 2, p * 2, h, -junction.deckThickness, junction.deckThickness - 0.025, removable(wall), cut);

      // Portals at x = -p and x = p
      for (const px of [-p, p]) {
        box(px, -h / 2, 0.22, h, -junction.deckThickness, junction.deckThickness, wall, parent);
        box(px, h / 2, 0.22, h, -junction.deckThickness, junction.deckThickness, removable(wall), cut);
        box(px, -h / 2, 0.16, h, 0, 0.42, wall, parent);
        box(px, h / 2, 0.16, h, 0, 0.42, removable(wall), cut);
      }

      // Surface Roundabout on the deck structure:
      // North half (z <= 0) stays in parent; South half (z >= 0) in cut for cutaway reveal
      const roundMat = mat('#758994');
      highlights.push(roundMat);

      // Roundabout roadway ring: outer radius 5.4, inner radius 2.7
      // North half (angle Math.PI to 2*Math.PI)
      cylinder(junction.curbRadius, 0.08, -0.03, walk, parent, Math.PI, Math.PI);
      cylinder(junction.outerRadius, 0.03, 0.015, roundMat, parent, Math.PI, Math.PI);
      cylinder(junction.islandRadius, 0.14, 0.12, walk, parent, Math.PI, Math.PI);
      cylinder(2.45, 0.02, 0.20, leaf, parent, Math.PI, Math.PI);

      // South half in cut group (angle 0 to Math.PI)
      cylinder(junction.curbRadius, 0.08, -0.03, removable(walk), cut, 0, Math.PI);
      cylinder(junction.outerRadius, 0.03, 0.015, removable(roundMat), cut, 0, Math.PI);
      cylinder(junction.islandRadius, 0.14, 0.12, removable(walk), cut, 0, Math.PI);
      cylinder(2.45, 0.02, 0.20, removable(leaf), cut, 0, Math.PI);

      // Tram tracks crossing north-south
      trackPart(-junction.bounds.z, 0, parent, 0.21);
      trackPart(0, junction.bounds.z, cut, 0.21);

      // Retaining walls flanking approach ramps
      const lower = g.roads.find(r => r.kind === 'lower')!;
      for (const side of [-1, 1]) {
        const target = side === 1 ? cut : parent;
        const positions: number[] = [], indices: number[] = [];
        const inner = side * junction.tunnelInnerHalf;
        const outer = side * (junction.tunnelInnerHalf + junction.wallThickness);
        const wallPoints = lower.points.filter(v => Math.abs(v.x) <= junction.rampStart);

        wallPoints.forEach((v, i) => {
          const top = Math.abs(v.x) <= p ? -junction.deckThickness : 0.12;
          positions.push(v.x, v.y - 0.09, inner, v.x, top, inner, v.x, v.y - 0.09, outer, v.x, top, outer);
          if (i < wallPoints.length - 1) {
            const n = i * 4;
            indices.push(
              n, n + 1, n + 4,  n + 1, n + 5, n + 4,
              n + 2, n + 6, n + 3,  n + 3, n + 6, n + 7,
              n + 1, n + 3, n + 5,  n + 3, n + 7, n + 5
            );
          }
        });

        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geo.setIndex(indices);
        geo.computeVertexNormals();
        mesh(geo, side === 1 ? removable(wall) : wall, target);
      }
    }

    // Direction arrows
    for (const arrow of g.arrows) polygon(arrowPoints(arrow.point, arrow.yaw), paint, parent);

    // Crosswalks and stop lines
    for (const mark of g.marks) {
      const n = mark.kind === 'crossing' ? Math.floor(mark.width / 0.45) : 1;
      for (let i = 0; i < n; i++) {
        const corners = markPolygon(
          mark,
          mark.kind === 'crossing' ? -mark.width / 2 + 0.2 + i * 0.45 : 0,
          mark.kind === 'crossing' ? 0.22 : mark.width,
        ).split(' ').map(v => {
          const [x, z] = v.split(',').map(Number);
          return { x: x!, y: mark.point.y, z: z! };
        });
        polygon(corners, mark.kind === 'stop' ? amber : paint, parent);
      }
      if (mark.kind === 'stop') {
        const x = mark.point.x + Math.cos(mark.yaw) * 1.35;
        const z = mark.point.z - Math.sin(mark.yaw) * 1.35;
        box(x, z, 0.065, 0.065, 0, 1, glass, parent);
        box(x, z, 0.24, 0.18, 0.8, 0.4, wall, parent);
      }
    }
  }

  let disposed = false, failed = false, visible = false, reduced = false, frame = 0;
  let revealAmount = 0, target = 0, from = 0, start = 0;

  const cutMaterials = new Set<THREE.Material>();
  cut.traverse(o => {
    if (o instanceof THREE.Mesh) {
      (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => cutMaterials.add(m));
    }
  });

  function apply() {
    cut.visible = revealAmount < 0.999;
    cutMaterials.forEach(m => {
      m.opacity = 1 - revealAmount;
      (m as THREE.MeshStandardMaterial).depthWrite = revealAmount < 0.01;
    });
  }

  function schedule() {
    if (!frame && visible && !disposed && !failed) frame = requestAnimationFrame(draw);
  }

  function draw(time: number) {
    frame = 0;
    if (!visible || disposed || failed) return;
    if (revealAmount !== target) {
      if (!start) start = time;
      const t = reduced ? 1 : Math.min((time - start) / 280, 1);
      revealAmount = from + (target - from) * (1 - (1 - t) ** 3);
      if (t === 1) revealAmount = target;
    }
    apply();
    try {
      renderer.render(scene, camera);
    } catch {
      failed = true;
      onFailure();
      return;
    }
    if (revealAmount !== target) schedule();
  }

  function resize() {
    const w = host.clientWidth, h = host.clientHeight;
    if (!w || !h || disposed) return;
    const aspect = w / h;
    const half = Math.max(junction.camera.halfHeight, junction.camera.halfWidth / aspect);
    camera.left = -half * aspect;
    camera.right = half * aspect;
    camera.top = half;
    camera.bottom = -half;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
    schedule();
  }

  function lost(e: Event) {
    e.preventDefault();
    failed = true;
    onFailure();
  }

  renderer.domElement.addEventListener('webglcontextlost', lost);
  host.appendChild(renderer.domElement);

  const observer = new ResizeObserver(resize);
  observer.observe(host);
  resize();

  return {
    setState(layout, selected, reveal, animate = true) {
      groups.existing.visible = layout === 'existing';
      groups.proposed.visible = layout === 'proposed';
      target = layout === 'proposed' && reveal ? 1 : 0;
      from = revealAmount;
      start = 0;
      if (!animate || reduced || !visible) revealAmount = target;
      highlights.forEach(m => m.color.set(selected === 'surface' ? '#4b9792' : '#758994'));
      schedule();
    },
    setVisible(next) {
      visible = next;
      if (!next) {
        cancelAnimationFrame(frame);
        frame = 0;
        revealAmount = target;
        apply();
      } else {
        schedule();
      }
    },
    setReducedMotion(next) {
      reduced = next;
      if (next) {
        revealAmount = target;
        schedule();
      }
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      cancelAnimationFrame(frame);
      observer.disconnect();
      renderer.domElement.removeEventListener('webglcontextlost', lost);
      geometries.forEach(g => g.dispose());
      materials.forEach(m => m.dispose());
      sun.shadow.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      renderer.domElement.remove();
      scene.clear();
    },
  };
}
