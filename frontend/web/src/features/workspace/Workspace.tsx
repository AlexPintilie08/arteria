'use client';

import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { MapPinned, Layers3, ScanLine, GitCompareArrows, Route } from 'lucide-react';
import {
  neighborhoods, layers, createDemoAnalysis,
  demoIssuesByNeighborhood, type DemoStudyIssue
} from '@arteria/shared/fixtures';
import type { AnalyzeResponse, LayerId, Area, AlternativeLevel } from '@arteria/shared/contracts';
import { ConnectedWorkspace } from './ConnectedWorkspace';
import { api, demoMode } from '../../lib/api';
import { AnalysisPanel } from '../analysis/AnalysisPanel';
import { ScenarioPanel, type ScenarioTuningParams } from '../scenarios/ScenarioPanel';
import { ComparisonPanel } from '../comparison/ComparisonPanel';
import { NeighborhoodExplorer } from '../neighborhoods/NeighborhoodExplorer';
import { controlledAnalysisMessage, placeCenter, type SourcedPlace } from '../neighborhoods/sim-geography';

const MapViewport = dynamic(() => import('../map/MapViewport'), {
  ssr: false,
  loading: () => <div className="map-loading" role="status">Se încarcă motorul hărții…</div>,
});

const sections = [
  { id: 'analysis', label: 'Explorează', icon: MapPinned },
  { id: 'scenarios', label: 'Scenarii', icon: Route },
  { id: 'comparison', label: 'Compară', icon: GitCompareArrows },
] as const;

type Section = typeof sections[number]['id'];

export function App() {
  return demoMode ? <PreviewApp /> : <ConnectedWorkspace />;
}

function PreviewApp() {
  const [section, setSection] = useState<Section>('analysis');
  const [selectedId, setSelectedId] = useState('copou');
  const selected = neighborhoods.find((item) => item.id === selectedId) ?? neighborhoods[0]!;
  const [selectedSourcedPlace, setSelectedSourcedPlace] = useState<SourcedPlace | null>(null);
  const [fillSourcedArea, setFillSourcedArea] = useState(false);
  const [requestedLayers, setRequestedLayers] = useState<LayerId[]>(['walking']);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Selected issue & alternative for scenarios
  const [selectedIssue, setSelectedIssue] = useState<DemoStudyIssue | null>(null);
  const [activeAlternativeLevel, setActiveAlternativeLevel] = useState<AlternativeLevel>('moderate');
  const [hasAppliedScenario, setHasAppliedScenario] = useState(false);
  const [tuningParams, setTuningParams] = useState<ScenarioTuningParams>({
    greenPhaseSec: 75,
    ctpPriority: true,
    laneWidthM: 2.5,
  });

  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);

  function changeArea(id: string) {
    controller.current?.abort();
    setLoading(false);
    setSelectedId(id);
    setSelectedSourcedPlace(null);
    setFillSourcedArea(false);
    setResult(null);
    setError('');
    setSelectedIssue(null);
    setHasAppliedScenario(false);
  }

  function handleSelectIssue(issue: DemoStudyIssue) {
    setSelectedIssue(issue);
    setHasAppliedScenario(false);
  }

  function handleApplyScenario(params?: ScenarioTuningParams) {
    if (params) setTuningParams(params);
    setHasAppliedScenario(true);
    setSection('comparison');
  }

  async function analyze() {
    if (selectedSourcedPlace) return;
    controller.current?.abort();
    const active = new AbortController();
    controller.current = active;
    setLoading(true);
    setError('');
    setResult(null);
    setSelectedIssue(null);
    setHasAppliedScenario(false);

    // Bookmarks are not verified area IDs. Live integration is deliberately gated below.
    const area: Area = {
      city_id: 'iasi-ro',
      area_id: `preview-${selected.id}`,
      boundary: null,
      boundary_source: 'known_area',
      crs: 'EPSG:4326',
    };

    try {
      const response = demoMode
        ? createDemoAnalysis(area)
        : await api.analyze(
            {
              area,
              layers: requestedLayers,
              analysis: {
                network_modes: ['walk', 'bike'],
                accessibility_thresholds: [{ value: 15, unit: 'minute', mode: 'walk' }],
              },
              data_as_of: null,
            },
            active.signal
          );
      if (!active.signal.aborted) {
        setResult(response);
        // Pre-select first local issue for intuitive experience
        const neighborhoodIssues = demoIssuesByNeighborhood[selected.id];
        if (neighborhoodIssues && neighborhoodIssues.length > 0 && neighborhoodIssues[0]) {
          setSelectedIssue(neighborhoodIssues[0]);
        }
      }
    } catch (cause) {
      if (!active.signal.aborted) {
        setError(cause instanceof Error ? cause.message : 'Analiza nu a putut fi încărcată. Reîncearcă.');
      }
    } finally {
      if (!active.signal.aborted) setLoading(false);
    }
  }

  function handleSelectSourcedPlace(place: SourcedPlace) {
    controller.current?.abort();
    setLoading(false);
    setResult(null);
    setError('');
    setSelectedIssue(null);
    setHasAppliedScenario(false);
    setSelectedSourcedPlace(place);
    setFillSourcedArea(false);
    setSection('analysis');
  }

  function clearSourcedPlace() {
    setSelectedSourcedPlace(null);
    setFillSourcedArea(false);
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#workspace">
        Sari la spațiul de lucru
      </a>
      <header className="topbar">
        <a className="brand" href="/" aria-label="ARTERIA, pagina principală">
          <span className="brand-mark" aria-hidden="true">
            <i /><i /><i />
          </span>
          <span>
            ARTERIA<small>by ARION</small>
          </span>
        </a>
        <div className="city-heading">
          <span>Laborator urban</span>
          <strong>Iași, România</strong>
        </div>
        <span className="mode-label">
          {demoMode ? 'Previzualizare de interfață' : 'Conexiune API'}
        </span>
      </header>
      <nav className="rail" aria-label="Navigație principală">
        {sections.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={section === id ? 'rail-item active' : 'rail-item'}
            aria-current={section === id ? 'page' : undefined}
            onClick={() => setSection(id)}
          >
            <Icon size={22} aria-hidden="true" />
            <span>{label}</span>
          </button>
        ))}
        <span className="rail-foot">ARION</span>
      </nav>
      <main id="workspace" className="workspace" style={section === 'comparison' ? { gridTemplateColumns: '1fr' } : section === 'scenarios' ? { gridTemplateColumns: 'minmax(0, 1.1fr) minmax(380px, 480px)' } : { gridTemplateColumns: '320px minmax(0, 1fr)' }}>
        {/* VIEW 1: EXPLOREAZĂ (Dock Stânga de Control + Canvas Hartă & Deck Orizontal de Telemetrie) */}
        {section === 'analysis' && (
          <>
            {/* DOCK STÂNGA: FILTRE, ZONE & STRATURI */}
            <aside className="inspector" aria-label="Panou Control Diagnoză" style={{ borderLeft: 0, borderRight: '1px solid #42596a', padding: '24px 20px', display: 'flex', flexDirection: 'column', minWidth: 0, overflowY: 'auto' }}>
              <div className="inspector-heading" style={{ marginBottom: '16px' }}>
                <div>
                  <p style={{ margin: 0, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.8px', color: '#a8bac9', fontWeight: 600 }}>Zona de studiu</p>
                  <h2 style={{ margin: '4px 0 0', fontSize: '22px' }}>{selectedSourcedPlace?.name ?? selected.name}</h2>
                </div>
                <MapPinned aria-hidden="true" size={24} style={{ color: '#8bc9ed' }} />
              </div>

              <label htmlFor="area" style={{ fontSize: '12px', color: '#a8bac9', marginBottom: '6px', fontWeight: 600 }}>
                Repere demo salvate
              </label>
              <select id="area" value={selectedId} onChange={(event) => changeArea(event.target.value)} style={{ marginBottom: '8px' }}>
                {neighborhoods.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
              <p className="supporting" style={{ marginTop: 0, marginBottom: '16px', fontSize: '11px' }}>
                Cele cinci repere demo existente. Catalogul OSM este separat mai jos.
              </p>

              <NeighborhoodExplorer
                selectedPlace={selectedSourcedPlace}
                onSelect={handleSelectSourcedPlace}
                onClear={clearSourcedPlace}
                fillEnabled={fillSourcedArea}
                onFillChange={setFillSourcedArea}
              />

              <details className="layer-settings" style={{ margin: '0 0 16px', padding: '12px 0' }}>
                <summary style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <Layers3 size={16} aria-hidden="true" style={{ color: '#8bc9ed' }} />
                  <span style={{ fontSize: '13px', fontWeight: 600 }}>Straturi pentru analiză</span>
                  <span style={{ marginLeft: 'auto', fontSize: '11px', background: '#213140', padding: '2px 6px', borderRadius: '4px' }}>{requestedLayers.length}</span>
                </summary>
                <p className="supporting" style={{ fontSize: '11px', margin: '8px 0' }}>Selecția pregătește cererea API. Nu afișează straturi geografice.</p>
                <div className="layer-list" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {layers.map((layer) => (
                    <label key={layer.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={requestedLayers.includes(layer.id)}
                        onChange={() => {
                          controller.current?.abort();
                          setLoading(false);
                          setResult(null);
                          setRequestedLayers((items) =>
                            items.includes(layer.id)
                              ? items.filter((id) => id !== layer.id)
                              : [...items, layer.id]
                          );
                        }}
                      />
                      {layer.label}
                    </label>
                  ))}
                </div>
              </details>

              {selectedSourcedPlace ? (
                <p className="notice" role="status">
                  Selecția OSM este disponibilă numai pentru navigare pe hartă. Alege un reper demo pentru previzualizarea existentă.
                </p>
              ) : (
                <button
                  className="primary-button"
                  onClick={analyze}
                  disabled={loading || requestedLayers.length === 0}
                  style={{ width: '100%', marginBottom: '12px' }}
                >
                  <ScanLine size={18} aria-hidden="true" />
                  {loading
                    ? 'Se analizează…'
                    : demoMode
                    ? 'Explorează previzualizarea'
                    : 'Lansează Diagnoza Teritorială'}
                </button>
              )}

              {!demoMode && (
                <p className="notice" style={{ fontSize: '11px', margin: 0 }}>
                  Conectează identificatorii reali ai zonelor înainte de activarea analizei.
                </p>
              )}
              {error && (
                <p className="error" role="alert" style={{ fontSize: '11px' }}>
                  {error}
                </p>
              )}

              <footer className="inspector-footer" style={{ marginTop: 'auto', paddingTop: '16px' }}>
                Date transparente. Decizii informate.
                <span>SUMO: nicio rulare</span>
              </footer>
            </aside>

            {/* ZONĂ PRINCIPALĂ: HARTĂ DIGITAL TWIN (SUS) + DECK ORIZONTAL TELEMETRIE & PROBLEME (JOS) */}
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minWidth: 0, overflow: 'hidden' }}>
              <div className="map-region" style={{ flex: 1, minHeight: '380px', position: 'relative' }}>
                <MapViewport
                  neighborhoodId={selected.id}
                  center={selectedSourcedPlace ? placeCenter(selectedSourcedPlace) ?? selected.center : selected.center}
                  selectedIssueId={selectedIssue?.id ?? null}
                  sourcedPlace={selectedSourcedPlace}
                  fillSourcedArea={fillSourcedArea}
                  onSelectIssue={(issue) => {
                    setSelectedIssue(issue);
                    if (!result) analyze();
                  }}
                  scenarioApplied={hasAppliedScenario}
                />
                <div className="map-heading" style={{ top: '20px', left: '20px', padding: '14px 18px', background: 'rgba(24, 35, 46, 0.94)', backdropFilter: 'blur(8px)', border: '1px solid #42596a' }}>
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.8px', color: '#8bc9ed', fontWeight: 600 }}>
                    {selectedSourcedPlace ? 'Catalog geografic SIM · OpenStreetMap' : 'Digital Twin Mobilitate Iași'}
                  </span>
                  <h1 style={{ fontSize: '22px', margin: '4px 0 0', fontFamily: 'Space Grotesk' }}>
                    {selectedSourcedPlace ? `${selectedSourcedPlace.name} · previzualizare geografică` : 'Înțelege locul. Modelează viitorul.'}
                  </h1>
                </div>
              </div>

              {/* PANOU ORIZONTAL DE DIRECȚIE ȘI TELEMETRIE (FULL-WIDTH SUB HARTĂ) */}
              <div style={{ background: '#101820', borderTop: '1px solid #42596a', maxHeight: '350px', overflowY: 'auto', padding: '16px 24px' }}>
                <div className="panel-content" aria-live="polite" aria-busy={loading} style={{ padding: 0 }}>
                  {selectedSourcedPlace ? (
                    <div className="empty-state sourced-analysis-state" role="status">
                      <h3>Analiza nu este conectată</h3>
                      <p>Harta arată geometria sursă pentru navigare. Nu s-a calculat accesibilitate, trafic sau alt rezultat pentru {selectedSourcedPlace.name}.</p>
                    </div>
                  ) : (
                    <AnalysisPanel
                      result={result}
                      selectedNeighborhoodId={selected.id}
                      selectedIssueId={selectedIssue?.id ?? null}
                      onSelectIssue={handleSelectIssue}
                      onGoToScenarios={() => setSection('scenarios')}
                    />
                  )}
                </div>
              </div>
            </div>
          </>
        )}

        {/* VIEW 2: SCENARII (Editor dedicat cu previzualizare focalizată pe intervenție și panou larg de alternative) */}
        {section === 'scenarios' && selectedSourcedPlace && (
          <section className="sourced-section-gate" aria-label="Previzualizare geografică fără scenarii">
            <div className="sourced-gate-map">
              <MapViewport
                neighborhoodId={selected.id}
                center={placeCenter(selectedSourcedPlace) ?? selected.center}
                selectedIssueId={null}
                sourcedPlace={selectedSourcedPlace}
                fillSourcedArea={fillSourcedArea}
              />
            </div>
            <div className="sourced-gate-copy">
              <span>Scenarii · catalog OSM</span>
              <h2>Previzualizare geografică numai</h2>
              <p>Geometria pentru {selectedSourcedPlace.name} poate fi explorată pe hartă. Catalogul geografic nu este conectat la motorul de analiză sau la scenarii, deci nu afișăm rezultate simulate pentru această zonă.</p>
              {selectedSourcedPlace.validation.status === 'requires_controlled_analysis' && (
                <p className="notice">{controlledAnalysisMessage(selectedSourcedPlace)}</p>
              )}
              <button className="primary-button" type="button" onClick={() => setSection('analysis')}>Înapoi la harta și catalogul geografic</button>
            </div>
          </section>
        )}

        {section === 'scenarios' && !selectedSourcedPlace && (
          <>
            <div className="map-region" style={{ background: '#141d26' }}>
              <MapViewport
                neighborhoodId={selected.id}
                center={selectedIssue ? selectedIssue.coordinates : selected.center}
                selectedIssueId={selectedIssue?.id ?? null}
                onSelectIssue={handleSelectIssue}
                scenarioApplied={hasAppliedScenario}
              />
              <div
                style={{
                  position: 'absolute',
                  top: '24px',
                  left: '24px',
                  background: 'rgba(24, 35, 46, 0.94)',
                  backdropFilter: 'blur(8px)',
                  padding: '16px 20px',
                  borderRadius: '10px',
                  border: '1px solid #42596a',
                  maxWidth: '420px',
                  pointerEvents: 'none',
                }}
              >
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.8px', color: '#8bc9ed', fontWeight: 600 }}>
                  Editor Scenarii & Recomandări
                </span>
                <h2 style={{ fontSize: '20px', margin: '4px 0 6px', color: '#edf2f6', fontFamily: 'Space Grotesk' }}>
                  {selectedIssue ? selectedIssue.title : 'Selectează o problemă din analiză'}
                </h2>
                <p style={{ margin: 0, fontSize: '12px', color: '#a8bac9' }}>
                  {selectedIssue ? selectedIssue.locationName : 'Alege o intervenție din catalog pentru a genera scenariul virtual.'}
                </p>
              </div>
            </div>

            <aside className="inspector" aria-label="Editor Scenarii" style={{ minWidth: 0 }}>
              <div className="inspector-heading" style={{ marginBottom: '14px' }}>
                <div>
                  <p>Catalog de Intervenții</p>
                  <h2>Scenarii</h2>
                </div>
                <Route aria-hidden="true" size={24} style={{ color: '#8bc9ed' }} />
              </div>
              <div className="panel-content" style={{ padding: '8px 0 20px' }}>
                <ScenarioPanel
                  selectedIssue={selectedIssue}
                  activeAlternativeLevel={activeAlternativeLevel}
                  onSelectAlternative={setActiveAlternativeLevel}
                  onApplyScenario={handleApplyScenario}
                  hasAppliedScenario={hasAppliedScenario}
                  onSelectIssue={handleSelectIssue}
                  tuningParams={tuningParams}
                  onUpdateTuningParams={setTuningParams}
                />
              </div>
              <footer className="inspector-footer">
                Model: Catalog-1 Pydantic · Valori verificate
                <span>SUMO: nicio rulare</span>
              </footer>
            </aside>
          </>
        )}

        {/* VIEW 3: COMPARĂ (Ecran tehnic amplu: Matricea de Performanță Înainte / După, fără aglomerare în sidebar) */}
        {section === 'comparison' && selectedSourcedPlace && (
          <section className="sourced-section-gate" aria-label="Comparație indisponibilă pentru catalogul OSM">
            <div className="sourced-gate-map">
              <MapViewport
                neighborhoodId={selected.id}
                center={placeCenter(selectedSourcedPlace) ?? selected.center}
                selectedIssueId={null}
                sourcedPlace={selectedSourcedPlace}
                fillSourcedArea={fillSourcedArea}
              />
            </div>
            <div className="sourced-gate-copy">
              <span>Comparație · catalog OSM</span>
              <h2>Nu există rezultate de comparat</h2>
              <p>Selecția {selectedSourcedPlace.name} oferă doar navigare geografică. Niciun baseline, scenariu sau efect nu a fost calculat pentru acest loc.</p>
              {selectedSourcedPlace.validation.status === 'requires_controlled_analysis' && (
                <p className="notice">{controlledAnalysisMessage(selectedSourcedPlace)}</p>
              )}
              <button className="primary-button" type="button" onClick={() => setSection('analysis')}>Înapoi la harta și catalogul geografic</button>
            </div>
          </section>
        )}

        {section === 'comparison' && !selectedSourcedPlace && (
          <div style={{ display: 'flex', flexDirection: 'column', padding: '32px 48px', overflowY: 'auto', background: '#101820' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', borderBottom: '1px solid #42596a', paddingBottom: '20px' }}>
              <div>
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px', color: '#8bc9ed', fontWeight: 700 }}>
                  Evaluare Comparativă · Matrice de Performanță
                </span>
                <h1 style={{ fontSize: '32px', margin: '6px 0', fontFamily: 'Space Grotesk', color: '#edf2f6' }}>
                  Înainte. După. Cu dovezi.
                </h1>
                <p style={{ margin: 0, color: '#a8bac9', fontSize: '14px' }}>
                  Comparație între Situația Inițială (Baseline 2024) și Scenariul Virtual Evaluat pe aceeași rețea topologică.
                </p>
              </div>
              <button
                className="primary-button"
                onClick={() => setSection('scenarios')}
                style={{ padding: '8px 16px', minHeight: '38px', fontSize: '12px' }}
              >
                ← Modifică Scenariul
              </button>
            </div>

            <div style={{ maxWidth: '960px', width: '100%' }}>
              <ComparisonPanel
                selectedIssue={selectedIssue}
                activeAlternativeLevel={activeAlternativeLevel}
                hasAppliedScenario={hasAppliedScenario}
                tuningParams={tuningParams}
                onSelectAlternative={setActiveAlternativeLevel}
                onSelectIssue={handleSelectIssue}
                onQuickApply={(issue) => {
                  setSelectedIssue(issue);
                  setHasAppliedScenario(true);
                }}
                onGoToScenarios={() => setSection('scenarios')}
              />
            </div>

            <footer style={{ marginTop: 'auto', paddingTop: '32px', borderTop: '1px solid #42596a', fontSize: '12px', color: '#a8bac9', display: 'flex', justifyContent: 'space-between' }}>
              <span>ARTERIA Civic Intelligence Platform · Iași, România</span>
              <span>SUMO Seed: 4092 (nelansat) · Calcule grafe OSM deterministe</span>
            </footer>
          </div>
        )}
      </main>
    </div>
  );
}
