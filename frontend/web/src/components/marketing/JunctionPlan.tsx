import {
  getGeometry,
  junction,
  roadPolygon,
  markPolygon,
  arrowPoints,
  type Intervention,
  type Layout,
} from './intersection';
import styles from './JunctionPlan.module.css';

export function JunctionPlan({
  layout,
  reveal = false,
  selected,
}: {
  layout: Layout;
  reveal?: boolean;
  selected?: Intervention;
}) {
  const g = getGeometry(layout), proposed = layout === 'proposed';
  const p = junction.portal, h = junction.trenchHalfWidth, rs = junction.rampStart;
  const rw = junction.roadWidth, sw = junction.sidewalk;

  return (
    <svg
      className={styles.plan}
      viewBox={`${-junction.bounds.x - 1} ${-junction.bounds.z - 1} ${junction.bounds.x * 2 + 2} ${junction.bounds.z * 2 + 2}`}
      role="img"
      aria-label={
        proposed
          ? 'Sens giratoriu denivelat: calea de tranzit subterană Est–Vest trece pe sub un inel de sens giratoriu compact la sol. Giratoriul de suprafață acomodează toate virajele la stânga, la dreapta și trecerea tramvaiului.'
          : 'Sens giratoriu existent ca linie de bază, cu cale de tramvai Nord–Sud și treceri de pietoni la nivel.'
      }
      data-geometry={layout}
    >
      {/* Suprafața sitului */}
      <rect
        x={-junction.bounds.x}
        y={-junction.bounds.z}
        width={junction.bounds.x * 2}
        height={junction.bounds.z * 2}
        rx=".6"
        fill="#ecede5"
      />

      {/* Clădiri context */}
      {g.buildings.map((b, i) => (
        <rect
          key={i}
          x={b.x - b.w / 2}
          y={b.z - b.d / 2}
          width={b.w}
          height={b.d}
          fill="#d5dddc"
          stroke="#bdc9c9"
          strokeWidth=".12"
        />
      ))}

      {/* Arbori */}
      {g.trees.map(([x, z], i) => (
        <circle key={i} cx={x} cy={z} r=".65" fill="#a1b7a0" />
      ))}

      {/* Trotuare pentru drumurile de suprafață */}
      {g.roads.filter(r => r.sidewalk).map(r => (
        <polygon key={`${r.id}-walk`} points={roadPolygon(r, sw * 2)} fill="#faf7ec" />
      ))}

      {/* Suprafețe carosabile */}
      {g.roads.map(r => {
        if (r.kind === 'lower') {
          return (
            <polygon
              key={r.id}
              data-road={r.id}
              points={roadPolygon(r)}
              fill="#027f82"
            />
          );
        }
        return (
          <polygon
            key={r.id}
            data-road={r.id}
            points={roadPolygon(r)}
            fill={selected === 'surface' && g.connectors.some(c => c.id === r.id) ? '#4b9792' : '#81949e'}
          />
        );
      })}

      {/* Sens giratoriu existent la sol */}
      {!proposed && (
        <>
          <circle r={junction.curbRadius} fill="#f5f1e6" />
          <circle r={junction.outerRadius} fill="#81949e" />
          <circle r={junction.islandRadius} fill="#b1c7aa" stroke="#faf7ec" strokeWidth=".15" />
          <circle
            r={junction.ringMarkRadius}
            fill="none"
            stroke="#faf7ec"
            strokeWidth=".08"
            strokeDasharray=".5 .5"
          />
        </>
      )}

      {/* Propunere: Sens giratoriu denivelat */}
      {proposed && (
        <>
          {/* Placă structurală pod */}
          <rect
            x={-p}
            y={-h}
            width={p * 2}
            height={h * 2}
            fill="#b5bdb7"
          />

          {/* Secțiune cutaway: jumătatea sudică deschisă */}
          {reveal && (
            <>
              <rect x={-p} y="0" width={p * 2} height={h} fill="#ecede5" />
              <rect x={-p} y="0" width={p * 2} height={rw / 2} fill="#027f82" />
            </>
          )}

          {/* Indicator linie punctată pasaj subteran acoperit */}
          {!reveal && (
            <path
              d={`M${-p} ${-rw / 2}H${p}M${-p} ${rw / 2}H${p}M${-p} 0H${p}`}
              stroke="#027f82"
              strokeDasharray=".6 .45"
              strokeWidth=".16"
              fill="none"
            />
          )}

          {/* Inelul sensului giratoriu de la suprafață */}
          <g>
            <path
              d={`M${-junction.curbRadius} 0A${junction.curbRadius} ${junction.curbRadius} 0 0 1 ${junction.curbRadius} 0Z`}
              fill="#f5f1e6"
            />
            <path
              d={`M${-junction.outerRadius} 0A${junction.outerRadius} ${junction.outerRadius} 0 0 1 ${junction.outerRadius} 0Z`}
              fill={selected === 'surface' ? '#4b9792' : '#81949e'}
            />
            <path
              d={`M${-junction.islandRadius} 0A${junction.islandRadius} ${junction.islandRadius} 0 0 1 ${junction.islandRadius} 0Z`}
              fill="#b1c7aa"
              stroke="#faf7ec"
              strokeWidth=".15"
            />

            {!reveal && (
              <>
                <path
                  d={`M${-junction.curbRadius} 0A${junction.curbRadius} ${junction.curbRadius} 0 0 0 ${junction.curbRadius} 0Z`}
                  fill="#f5f1e6"
                />
                <path
                  d={`M${-junction.outerRadius} 0A${junction.outerRadius} ${junction.outerRadius} 0 0 0 ${junction.outerRadius} 0Z`}
                  fill={selected === 'surface' ? '#4b9792' : '#81949e'}
                />
                <path
                  d={`M${-junction.islandRadius} 0A${junction.islandRadius} ${junction.islandRadius} 0 0 0 ${junction.islandRadius} 0Z`}
                  fill="#b1c7aa"
                  stroke="#faf7ec"
                  strokeWidth=".15"
                />
                <circle
                  r={junction.ringMarkRadius}
                  fill="none"
                  stroke="#faf7ec"
                  strokeWidth=".08"
                  strokeDasharray=".5 .5"
                />
              </>
            )}
          </g>

          {/* Portaluri și pereți de sprijin */}
          {[-1, 1].map(sign => (
            <g key={sign}>
              <path
                d={`M${sign * p} ${-h}V${reveal ? 0 : h}`}
                stroke="#425b67"
                strokeWidth=".35"
              />
              <path
                d={`M${sign * p} ${-junction.tunnelInnerHalf - junction.wallThickness / 2}H${sign * rs}`}
                stroke="#6b807f"
                strokeWidth={junction.wallThickness}
              />
              {!reveal && (
                <path
                  d={`M${sign * p} ${junction.tunnelInnerHalf + junction.wallThickness / 2}H${sign * rs}`}
                  stroke="#6b807f"
                  strokeWidth={junction.wallThickness}
                />
              )}
            </g>
          ))}
        </>
      )}

      {/* Șine de tramvai Nord–Sud */}
      {(proposed && reveal
        ? [[-junction.bounds.z, 0], [h, junction.bounds.z]]
        : [[-junction.bounds.z, junction.bounds.z]]
      ).map(([from, to], i) => (
        <g key={i}>
          <path
            d={`M0 ${from}V${to}`}
            stroke="#b6c6c6"
            strokeWidth={junction.tramBedWidth}
          />
          <path
            d={`M${-junction.railOffset} ${from}V${to}M${junction.railOffset} ${from}V${to}`}
            stroke="#e6eeec"
            strokeWidth=".1"
          />
        </g>
      ))}

      {/* Marcaje: Treceri de pietoni și linii de cedare/oprire */}
      {g.marks.map((m, i) => (
        <g key={i}>
          {m.kind === 'stop' ? (
            <polygon points={markPolygon(m)} fill="#edce87" />
          ) : (
            Array.from({ length: Math.floor(m.width / 0.45) }, (_, j) => (
              <polygon
                key={j}
                points={markPolygon(m, -m.width / 2 + 0.2 + j * 0.45, 0.22)}
                fill="#fffbed"
              />
            ))
          )}
        </g>
      ))}

      {/* Badge-uri numerotate */}
      {proposed && (
        <g fill="#fff" stroke="#027f82" strokeWidth=".12">
          {(['underpass', 'surface'] as const).map((key, i) => (
            <g key={key}>
              <circle cx={g.anchors[key].x} cy={g.anchors[key].z} r=".85" />
              <text
                x={g.anchors[key].x}
                y={g.anchors[key].z + 0.3}
                fill="#025a63"
                stroke="none"
                fontSize=".8"
                textAnchor="middle"
              >
                {i + 1}
              </text>
            </g>
          ))}
        </g>
      )}

      {/* Săgeți de direcție a traficului */}
      {g.arrows.map((a, i) => (
        <polygon
          key={i}
          points={arrowPoints(a.point, a.yaw).map(pt => `${pt.x},${pt.z}`).join(' ')}
          fill="#faf7ec"
        />
      ))}

      {/* Indicator de selecție activă pe badge */}
      {selected && (
        <circle
          cx={g.anchors[selected].x}
          cy={g.anchors[selected].z}
          r="1.2"
          fill="none"
          stroke="#027f82"
          strokeWidth=".15"
        />
      )}
    </svg>
  );
}

export function UnderpassSection() {
  const half = junction.tunnelInnerHalf;
  const bottom = -junction.floor;
  const deck = junction.deckThickness;
  const clearHeight = junction.clearance;

  return (
    <div className={styles.section}>
      <p className={styles.sectionTitle}>
        Secțiune prin placa giratoriului <span>Placa de suprafață este îndepărtată doar în modul secțiune</span>
      </p>
      <svg
        className={styles.sectionDrawing}
        viewBox="-4 -0.5 8 3.3"
        role="img"
        aria-label="Secțiune transversală: o placă structurală susține inelul giratoriului de suprafață deasupra unui spațiu liber; calea de tranzit Est–Vest trece pe dedesubt între pereți de sprijin. Proporții pur ilustrative."
      >
        {/* Context sol */}
        <path
          d={`M-4 0H4V2.65H-4ZM${-half - junction.wallThickness} ${deck}H${half + junction.wallThickness}V${bottom + 0.2}H${-half - junction.wallThickness}Z`}
          fill="#d5d7c8"
          fillRule="evenodd"
        />
        {/* Placă structurală pod */}
        <rect
          x={-half - junction.wallThickness}
          y="0"
          width={half * 2 + junction.wallThickness * 2}
          height={deck}
          fill="#8c9c9d"
        />
        {/* Pereți de sprijin */}
        <rect
          x={-half - junction.wallThickness}
          y={deck}
          width={junction.wallThickness}
          height={bottom - deck}
          fill="#8c9c9d"
        />
        <rect
          x={half}
          y={deck}
          width={junction.wallThickness}
          height={bottom - deck}
          fill="#8c9c9d"
        />
        {/* Cale de rulare inferioară */}
        <rect
          x={-junction.roadWidth / 2}
          y={bottom}
          width={junction.roadWidth}
          height="0.14"
          fill="#027f82"
        />
        {/* Zonă liberă utilă */}
        <rect
          x="-1.8"
          y={deck + 0.14}
          width="3.6"
          height={clearHeight - 0.28}
          fill="#e7f2ed"
          stroke="#78998c"
          strokeWidth="0.025"
          strokeDasharray=".1 .1"
        />
        {/* Cotă gabarit util */}
        <path
          d={`M-3.1 ${deck}V${bottom}m-.15-.15.15.15.15-.15M-3.25 ${deck + 0.15}l.15-.15.15.15`}
          stroke="#607b79"
          strokeWidth="0.03"
          fill="none"
        />
      </svg>
      <div className={styles.sectionLegend}>
        <span>Placă structurală giratoriu (0,35 m)</span>
        <span>Zonă liberă utilă (gabarit 1,45 m)</span>
        <span>Cale inferioară de tranzit (lățime 4,8 m)</span>
      </div>
      <p className={styles.sectionNote}>
        Alternativă compactă de sens giratoriu pe două niveluri. Virajele la stânga, la dreapta și tramvaiul circulă la nivelul solului, în timp ce tranzitul Est–Vest trece pe dedesubt fără oprire. Proporții ilustrative; necesită studiu de fezabilitate și proiectare tehnică.
      </p>
    </div>
  );
}
