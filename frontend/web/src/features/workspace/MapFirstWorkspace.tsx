'use client';

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { AlternativeLevel, SpatialEvaluation, SpatialPlanningResult, SpatialStudy } from '@arteria/shared/contracts';
import { spatialApi } from '../../lib/api';
import { controlledAnalysisMessage, loadSimCatalog, searchSimPlaces, type LoadedSimCatalog, type SourcedPlace } from '../neighborhoods/sim-geography';
import { ConnectedInterventionEditor, type ConnectedInterventionType, type ConnectedProblemOption, type ConnectedSolutionOption } from '../scenarios/ScenarioPanel';
import { formatTimestamp, presentError, source, type PresentedError } from './presentation';
import { geometryFeatureCollection, isJsonRecord, jsonArray, returnedAggregate, safeFeatureCollection, simSolutions, studyProblems, validatedRecommendations, type JsonRecord } from './map-first-data';
import styles from './MapFirstWorkspace.module.css';

const CatalogMap = dynamic(() => import('../map/NeighborhoodCatalogMap'), {
  ssr: false,
  loading: () => <div className={styles.mapLoading} role="status">Se încarcă harta Iașului…</div>,
});

type BusyAction = 'study' | 'planning' | 'evaluation' | null;
interface ActiveCandidate { candidateId: string; geometry: unknown }
const interventionPreferenceKey = 'arteria.map-first-intervention-preferences.v1';
const knownInterventionTypes: ConnectedInterventionType[] = [
  'add_pedestrian_connection', 'set_connection_enabled', 'traffic_signal_retiming', 'new_lane',
  'public_transport_priority', 'major_road_reconstruction', 'roundabout', 'underpass',
];

function stringValue(value: unknown, fallback: string): string {
  return typeof value === 'string' && value.trim() ? value : fallback;
}

function formatValue(value: unknown): string {
  if (typeof value === 'number' && Number.isFinite(value)) return value.toLocaleString('ro-RO', { maximumFractionDigits: 2 });
  if (value === null || value === undefined) return 'Necunoscut';
  if (typeof value === 'string') return value;
  return 'Necunoscut';
}

function properties(place: SourcedPlace): JsonRecord {
  return isJsonRecord(place.feature.properties) ? place.feature.properties : {};
}

function geometryFromSolution(value: unknown): unknown {
  if (!isJsonRecord(value)) return null;
  return value.geometry ?? null;
}

function lineGeometry(value: unknown): unknown {
  if (!isJsonRecord(value)) return null;
  const before = isJsonRecord(value.before) ? value.before : null;
  const after = isJsonRecord(value.after) ? value.after : null;
  return after?.geometry ?? before?.geometry ?? null;
}

function getMapCandidateGeometry(study: SpatialStudy, planning: SpatialPlanningResult | null, candidateId: string): unknown {
  const recommendation = validatedRecommendations(planning).find((item) => item.candidate_id === candidateId);
  const aiGeometry = recommendation?.authoritative_sim_solution?.geometry;
  if (aiGeometry) return aiGeometry;
  const solution = simSolutions(study).find((item) => item.candidate_id === candidateId);
  const geometry = geometryFromSolution(solution);
  if (geometry) return geometry;
  const candidate = study.alternatives.ranked_candidates.find((item) => item.candidate_id === candidateId);
  const candidateRecord = candidate as unknown as JsonRecord | undefined;
  return candidate?.intervention.geometry ?? candidateRecord?.geometry ?? null;
}

function Aggregate({ value }: { value: unknown }) {
  const aggregate = returnedAggregate(value);
  if (!aggregate) return <p className={styles.muted}>SIM nu a returnat impact agregat pentru această soluție.</p>;
  const entries = Object.entries(aggregate).filter(([, amount]) =>
    amount === null || (typeof amount === 'number' && Number.isFinite(amount))
  );
  if (!entries.length) return <p className={styles.muted}>SIM nu a returnat valori numerice pentru acest indicator.</p>;
  const labels: Record<string, string> = {
    evaluated_pair_count: 'Perechi de rute comparate', improved_count: 'Rute îmbunătățite',
    unchanged_count: 'Neschimbate', regressed_count: 'Rute înrăutățite',
    newly_reachable_count: 'Nou accesibile', newly_unreachable_count: 'Nou inaccesibile',
    total_distance_savings_m: 'Diferență agregată de distanță (m)',
    average_distance_savings_m: 'Diferență medie de distanță (m)',
    total_estimated_time_savings_s: 'Diferență estimată de timp (s)',
  };
  return <dl className={styles.aggregate}>{entries.map(([key, amount]) => <div key={key}><dt>{labels[key] ?? key.replaceAll('_', ' ')}</dt><dd>{formatValue(amount)}</dd></div>)}</dl>;
}

export function MapFirstWorkspace() {
  const [catalog, setCatalog] = useState<LoadedSimCatalog | null>(null);
  const [catalogError, setCatalogError] = useState('');
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [selectedPlace, setSelectedPlace] = useState<SourcedPlace | null>(null);
  const [fillPolygons, setFillPolygons] = useState(false);
  const [study, setStudy] = useState<SpatialStudy | null>(null);
  const [savedStudyId, setSavedStudyId] = useState('');
  const initialStudyRequested = useRef(false);
  const [planning, setPlanning] = useState<SpatialPlanningResult | null>(null);
  const [evaluation, setEvaluation] = useState<SpatialEvaluation | null>(null);
  const [activeCandidate, setActiveCandidate] = useState<ActiveCandidate | null>(null);
  const [selectedProblemId, setSelectedProblemId] = useState<string | null>(null);
  const [selectedInterventionType, setSelectedInterventionType] = useState<ConnectedInterventionType>('add_pedestrian_connection');
  const [interventionIntensity, setInterventionIntensity] = useState<AlternativeLevel>('moderate');
  const [selectedSolutionId, setSelectedSolutionId] = useState<string | null>(null);
  const [preferencesLoaded, setPreferencesLoaded] = useState(false);
  const [busy, setBusy] = useState<BusyAction>(null);
  const [error, setError] = useState<PresentedError | null>(null);
  const requestController = useRef<AbortController | null>(null);
  const planningKey = useRef<{ studyId: string; key: string } | null>(null);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(interventionPreferenceKey);
      const parsed: unknown = stored ? JSON.parse(stored) : null;
      if (isJsonRecord(parsed)) {
        if (parsed.intensity === 'minimal' || parsed.intensity === 'moderate' || parsed.intensity === 'transformative') {
          setInterventionIntensity(parsed.intensity);
        }
        if (typeof parsed.type === 'string' && knownInterventionTypes.includes(parsed.type as ConnectedInterventionType)) {
          setSelectedInterventionType(parsed.type as ConnectedInterventionType);
        }
      }
    } catch {
      // Preferences are optional; malformed local storage must not block the workspace.
    } finally {
      setPreferencesLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (!preferencesLoaded) return;
    try {
      window.localStorage.setItem(interventionPreferenceKey, JSON.stringify({
        intensity: interventionIntensity,
        type: selectedInterventionType,
      }));
    } catch {
      // The editor remains usable when browser storage is disabled.
    }
  }, [preferencesLoaded, interventionIntensity, selectedInterventionType]);

  useEffect(() => {
    const controller = new AbortController();
    setCatalogLoading(true);
    void Promise.all([
      fetch('/data/iasi-neighborhoods.geojson', { signal: controller.signal }),
      fetch('/data/iasi-neighborhood-validation.json', { signal: controller.signal }),
    ]).then(async ([catalogResponse, validationResponse]) => {
      if (!catalogResponse.ok || !validationResponse.ok) throw new Error('Fișierele catalogului SIM nu au putut fi încărcate.');
      const [catalogData, validationData] = await Promise.all([catalogResponse.json(), validationResponse.json()]);
      setCatalog(loadSimCatalog(catalogData, validationData));
    }).catch((cause: unknown) => {
      if (!controller.signal.aborted) setCatalogError(cause instanceof Error ? cause.message : 'Catalogul SIM nu a putut fi încărcat.');
    }).finally(() => { if (!controller.signal.aborted) setCatalogLoading(false); });
    return () => controller.abort();
  }, []);

  const places = catalog?.places ?? [];
  const results = useMemo(() => searchSimPlaces(places, query), [places, query]);
  const sourcedProblemCollection = safeFeatureCollection(study?.problem_locations_geojson);
  const aiRecommendations = validatedRecommendations(planning);
  const validCandidateIds = useMemo(() => new Set(
    (study?.proposal_validation.results ?? [])
      .filter((result) => result.status === 'candidate_backed_evaluated' && typeof result.candidate_id === 'string')
      .map((result) => result.candidate_id as string),
  ), [study]);
  const selectedCanRun = Boolean(selectedPlace
    && selectedPlace.geometryType !== 'Point'
    && selectedPlace.validation.status === 'valid'
    && selectedPlace.validation.analysis_eligible);

  const resultProblems = useMemo(() => study ? studyProblems(study) : [], [study]);
  const resultSolutions = useMemo(() => study ? simSolutions(study) : [], [study]);
  const connectedProblems = useMemo<ConnectedProblemOption[]>(() => resultProblems.map((problem, index) => ({
    id: stringValue(problem.problem_id, `problem-${index}`),
    title: stringValue(problem.title, stringValue(problem.problem_type, 'Problemă SIM')),
    description: stringValue(problem.description, 'SIM a identificat o problemă în rețeaua pietonală cartografiată.'),
    severity: stringValue(problem.severity, 'necunoscută'),
  })), [resultProblems]);
  const knownProblemIds = useMemo(() => new Set(connectedProblems.map((problem) => problem.id)), [connectedProblems]);
  const connectedSolutions = useMemo<ConnectedSolutionOption[]>(() => {
    if (!study) return [];
    const solutionByCandidate = new Map<string, JsonRecord>();
    for (const solution of resultSolutions) {
      if (typeof solution.candidate_id === 'string') solutionByCandidate.set(solution.candidate_id, solution);
    }
    const options: ConnectedSolutionOption[] = study.alternatives.ranked_candidates.map((candidate) => {
      const candidateId = candidate.candidate_id;
      const candidateRecord = candidate as unknown as JsonRecord;
      const solution = solutionByCandidate.get(candidateId) ?? {};
      const proposal = study.proposal_options.find((item) => item.candidate_id === candidateId) as unknown as JsonRecord | undefined;
      const proposalRationale = proposal && isJsonRecord(proposal.rationale) ? proposal.rationale : {};
      const intervention = isJsonRecord(candidate.intervention) ? candidate.intervention : {};
      const typeId = stringValue(intervention.type, 'unknown');
      const relationValues = [candidateRecord.related_issue_ids, proposalRationale.related_issue_ids, solution.related_issue_ids, solution.related_problem_ids, solution.problem_ids];
      const relatedProblemIds = [...new Set(relationValues.flatMap((value) => Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string' && knownProblemIds.has(item)) : []))];
      const hasExplicitProblemRelation = relatedProblemIds.length > 0;
      const geometry = getMapCandidateGeometry(study, planning, candidateId) ?? candidateRecord.geometry ?? null;
      const rationale = Array.isArray(candidate.evaluation_rationale)
        ? candidate.evaluation_rationale.filter((item): item is string => typeof item === 'string').join(' ')
        : '';
      return {
        id: candidateId,
        candidateId,
        typeId,
        title: stringValue(solution.title, typeId === 'add_pedestrian_connection' ? 'Conexiune pietonală ipotetică' : 'Intervenție SIM'),
        description: stringValue(solution.description, stringValue(solution.rationale, rationale || candidate.ranking_explanation || 'Candidat pregătit și evaluat de SIM pe graful pietonal.')),
        geometry,
        relatedProblemIds,
        hasExplicitProblemRelation,
        canEvaluate: validCandidateIds.has(candidateId),
        hasGeometry: geometryFeatureCollection(geometry).features.length > 0,
      };
    });
    for (const solution of resultSolutions) {
      if (typeof solution.candidate_id === 'string') continue;
      const typeId = stringValue(solution.intervention_type, stringValue(solution.solution_type, 'unknown'));
      if (!knownInterventionTypes.includes(typeId as ConnectedInterventionType)) continue;
      const relationValues = [solution.related_issue_ids, solution.related_problem_ids, solution.problem_ids];
      const relatedProblemIds = [...new Set(relationValues.flatMap((value) => Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string' && knownProblemIds.has(item)) : []))];
      options.push({
        id: stringValue(solution.solution_id, `concept-${options.length}`),
        candidateId: null,
        typeId,
        title: stringValue(solution.title, stringValue(solution.solution_type, 'Concept SIM')),
        description: stringValue(solution.description, stringValue(solution.rationale, 'Concept returnat de SIM fără candidat evaluabil.')),
        geometry: geometryFromSolution(solution),
        relatedProblemIds,
        hasExplicitProblemRelation: relatedProblemIds.length > 0,
        canEvaluate: false,
        hasGeometry: geometryFeatureCollection(geometryFromSolution(solution)).features.length > 0,
      });
    }
    return options;
  }, [study, planning, resultSolutions, validCandidateIds, knownProblemIds]);

  function clearStudyState() {
    requestController.current?.abort();
    requestController.current = null;
    planningKey.current = null;
    setBusy(null);
    setError(null);
    setStudy(null);
    setPlanning(null);
    setEvaluation(null);
    setActiveCandidate(null);
  }

  function selectPlace(place: SourcedPlace) {
    clearStudyState();
    setSelectedProblemId(null);
    setSelectedSolutionId(null);
    setSelectedPlace(place);
  }

  function selectProblem(problemId: string) {
    setSelectedProblemId(problemId);
    setSelectedSolutionId(null);
    setEvaluation(null);
  }

  function selectInterventionType(type: ConnectedInterventionType) {
    setSelectedInterventionType(type);
    setSelectedSolutionId(null);
    setActiveCandidate(null);
    setEvaluation(null);
  }

  function selectConnectedSolution(solution: ConnectedSolutionOption) {
    setSelectedSolutionId(solution.id);
    setActiveCandidate(solution.hasGeometry
      ? { candidateId: solution.candidateId ?? solution.id, geometry: solution.geometry }
      : null);
    setEvaluation(null);
  }

  async function runRequest(action: BusyAction, run: (signal: AbortSignal) => Promise<void>) {
    requestController.current?.abort();
    const controller = new AbortController();
    requestController.current = controller;
    setBusy(action);
    setError(null);
    try {
      await run(controller.signal);
    } catch (cause) {
      if (!controller.signal.aborted) setError(presentError(cause));
    } finally {
      if (!controller.signal.aborted) setBusy(null);
    }
  }

  function createStudy() {
    if (!selectedCanRun || !selectedPlace) return;
    setStudy(null); setPlanning(null); setEvaluation(null); setActiveCandidate(null);
    setSelectedProblemId(null); setSelectedSolutionId(null);
    void runRequest('study', async (signal) => {
      const result = await spatialApi.spatialNeighborhoodStudy(selectedPlace.id, signal);
      if (!signal.aborted) {
        planningKey.current = null;
        setStudy(result);
      }
    });
  }

  function receiveStudy(result: SpatialStudy) {
    planningKey.current = null;
    setPlanning(null);
    setEvaluation(null);
    setActiveCandidate(null);
    const area = isJsonRecord(result.analysis.area) ? result.analysis.area : {};
    const place = places.find((item) => item.id === area.area_id) ?? null;
    setSelectedPlace(result.source === 'osm' ? place : null);
    setQuery(result.source === 'osm' && place ? place.name : '');
    setSelectedProblemId(null);
    setSelectedSolutionId(null);
    setSelectedInterventionType('add_pedestrian_connection');
    setStudy(result);
    setSavedStudyId(result.study_id);
  }

  function loadStoredStudy(id = savedStudyId) {
    if (!id.trim()) return;
    clearStudyState();
    void runRequest('study', async (signal) => {
      const result = await spatialApi.getSpatialStudy(id.trim(), signal);
      if (!signal.aborted) receiveStudy(result);
    });
  }

  function createOfflineStudy() {
    clearStudyState();
    void runRequest('study', async (signal) => {
      const result = await spatialApi.spatialStudy(signal);
      if (!signal.aborted) receiveStudy(result);
    });
  }

  useEffect(() => {
    if (!catalog || initialStudyRequested.current) return;
    initialStudyRequested.current = true;
    const id = new URLSearchParams(window.location.search).get('study');
    if (id) loadStoredStudy(id);
    // The URL is read once after catalog loading so its source area can be matched.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalog]);

  function requestPlanning() {
    if (!study) return;
    if (!planningKey.current || planningKey.current.studyId !== study.study_id) {
      planningKey.current = { studyId: study.study_id, key: crypto.randomUUID() };
    }
    const key = planningKey.current.key;
    void runRequest('planning', async (signal) => {
      const result = await spatialApi.spatialPlanning(study.study_id, key, signal);
      if (!signal.aborted) setPlanning(result);
    });
  }

  function reloadPlanning() {
    if (!study || !planning) return;
    void runRequest('planning', async (signal) => {
      const result = await spatialApi.getSpatialPlanning(study.study_id, planning.planning_id, signal);
      if (!signal.aborted) setPlanning(result);
    });
  }

  function activateSolution(candidateId: string, geometry: unknown) {
    setActiveCandidate({ candidateId, geometry });
    setEvaluation(null);
  }

  function evaluateCandidate(candidateId: string) {
    if (!study || !validCandidateIds.has(candidateId)) return;
    const candidate = study.alternatives.ranked_candidates.find((item) => item.candidate_id === candidateId);
    if (!candidate) return;
    void runRequest('evaluation', async (signal) => {
      const result = await spatialApi.spatialEvaluate(study.study_id, {
        baseline_id: study.baseline_id,
        candidate_id: candidate.candidate_id,
        intervention: candidate.intervention,
      }, signal);
      if (!signal.aborted) {
        setEvaluation(result);
        setActiveCandidate({ candidateId, geometry: getMapCandidateGeometry(study, planning, candidateId) ?? candidate.intervention.geometry });
      }
    });
  }

  const selectedProperties = selectedPlace ? properties(selectedPlace) : {};
  const attribution = stringValue(catalog?.metadata.attribution, '© OpenStreetMap contributors');
  const sourceSnapshot = stringValue(catalog?.metadata.source_snapshot_at, 'indisponibilă');
  const aiCanRender = aiRecommendations.length > 0;
  const aiUnavailable = planning && !aiCanRender;

  return <div className={styles.app}>
    <a className={styles.skipLink} href="#catalog-inspector">Sari la catalog și rezultate</a>
    <header className={styles.header}>
      <Link className={styles.brand} href="/" aria-label="ARTERIA, pagina principală"><span className={styles.brandMark}>A</span><span>ARTERIA<small>by ARION</small></span></Link>
      <div className={styles.city}><span>Laborator urban</span><strong>Iași, România</strong></div>
      <div className={styles.headerActions}><span className={styles.connected}>SIM · graf pietonal</span><Link href="/app/demo" className={styles.demoLink}>Demonstrație semafoare</Link></div>
    </header>
    <main className={styles.workspace}>
      <section className={styles.mapPanel} aria-label="Harta Iași">
        <CatalogMap
          places={places}
          selectedId={selectedPlace?.id ?? null}
          selectedProblemId={selectedProblemId}
          problems={sourcedProblemCollection}
          candidateGeometry={activeCandidate?.geometry ?? null}
          fillPolygons={fillPolygons}
          onSelect={selectPlace}
        />
        <div className={styles.mapSummary}>
          <span>{study?.source === 'fixture' ? 'Demonstrație sintetică SIM · fără observații OSM' : 'Catalog geografic SIM'}</span>
          <strong>{catalogLoading ? 'Se încarcă datele Iașului…' : `${places.filter((place) => place.geometryType !== 'Point').length} zone poligonale · ${places.filter((place) => place.geometryType === 'Point').length} repere punctuale`}</strong>
        </div>
      </section>

      <aside id="catalog-inspector" className={styles.inspector} aria-label="Catalog și analiză SIM">
        <div className={styles.inspectorTitle}>
          <div><p className={styles.eyebrow}>{study?.source === 'fixture' ? 'SIM · fixture sintetic' : 'SIM · OpenStreetMap'}</p><h1>{selectedPlace?.name ?? (study?.source === 'fixture' ? 'Demo sintetic SIM' : 'Alege o zonă')}</h1></div>
          {selectedPlace && <button type="button" className={styles.textButton} onClick={() => { clearStudyState(); setSelectedPlace(null); }}>Șterge</button>}
        </div>

        <section className={styles.sourceNote} aria-label="Studiu salvat sau demonstrație offline">
          <strong>Demo fără descărcare OSM</strong>
          <p>Încarcă un studiu salvat prin ID sau rulează fixture-ul sintetic SIM. Niciuna dintre aceste acțiuni nu descarcă date OSM.</p>
          <label className={styles.searchLabel} htmlFor="saved-study-id">ID studiu salvat</label>
          <input id="saved-study-id" className={styles.search} value={savedStudyId} onChange={(event) => setSavedStudyId(event.target.value)} placeholder="study_…" />
          <div className={styles.buttonRow}>
            <button type="button" className={styles.secondary} disabled={busy !== null || !savedStudyId.trim()} onClick={() => loadStoredStudy()}>Încarcă studiul salvat</button>
            <button type="button" className={styles.secondary} disabled={busy !== null} onClick={createOfflineStudy}>Demo offline sintetic SIM</button>
          </div>
        </section>

        <label className={styles.searchLabel} htmlFor="neighborhood-search">Caută cartier sau reper</label>
        <input id="neighborhood-search" className={styles.search} type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ex. Copou, Tătărași…" />

        <div className={styles.catalogMeta}>
          <span>{catalogLoading ? 'Se încarcă catalogul…' : `${results.length} din ${places.length} înregistrări`}</span>
          <label className={styles.fillToggle}><input type="checkbox" checked={fillPolygons} onChange={(event) => setFillPolygons(event.target.checked)} /> Umplere poligoane</label>
        </div>
        {catalogError && <p className={styles.error} role="alert">{catalogError}</p>}
        <div className={styles.placeList} role="listbox" aria-label="Rezultate catalog SIM">
          {results.map((place) => (
            <button key={place.id} type="button" role="option" aria-selected={selectedPlace?.id === place.id} className={selectedPlace?.id === place.id ? styles.placeSelected : styles.place} onClick={() => selectPlace(place)}>
              <span className={styles.placeMark} aria-hidden="true">{place.geometryType === 'Point' ? '•' : '⌑'}</span>
              <span className={styles.placeName}>{place.name}<small>{place.id}</small></span>
              <span className={place.validation.analysis_eligible ? styles.statusReady : styles.statusLimited}>{place.geometryType === 'Point' ? 'Punct' : place.validation.analysis_eligible ? 'Analizabil' : 'Limitat'}</span>
            </button>
          ))}
          {!catalogLoading && !catalogError && results.length === 0 && <p className={styles.muted}>Nicio înregistrare nu corespunde căutării.</p>}
        </div>

        <div className={styles.sourceNote}>
          <strong>Limitele sunt orientative</strong>
          <p>Poligoanele reprezintă extinderi de loc mapate în OSM, nu limite administrative oficiale. Punctele nu primesc contur. Sursă: {attribution} · ODbL-1.0.</p>
        </div>

        {selectedPlace && <section className={styles.selection} aria-label="Zona selectată">
          <div className={styles.selectionHeader}><h2>{selectedPlace.name}</h2><span className={styles.geometryBadge}>{selectedPlace.geometryType === 'Point' ? 'Reper punctual' : selectedPlace.geometryType}</span></div>
          <p className={styles.placeId}>ID SIM canonic: <code>{selectedPlace.id}</code></p>
          <p className={styles.analysisStatus}>
            {selectedPlace.geometryType === 'Point'
              ? 'Acest loc este înregistrat ca punct OpenStreetMap. Nu are geometrie de zonă, deci nu poate fi folosit drept poligon de analiză.'
              : selectedPlace.validation.analysis_eligible
                ? 'Eligibil pentru un studiu pe graful pietonal SIM.'
                : selectedPlace.validation.status === 'requires_controlled_analysis'
                  ? controlledAnalysisMessage(selectedPlace)
                  : selectedPlace.validation.reason ?? 'Zona nu este eligibilă pentru analiza SIM standard.'}
          </p>
          <dl className={styles.sourceDetails}>
            <div><dt>Sursă</dt><dd>{stringValue(selectedProperties.source, 'OpenStreetMap')}</dd></div>
            <div><dt>Data sursei</dt><dd>{formatTimestamp(stringValue(selectedProperties.source_snapshot_at, sourceSnapshot))}</dd></div>
            <div><dt>Incertitudine</dt><dd>{stringValue(selectedProperties.uncertainty_notes, 'Acoperirea și limitele necesită verificare.')}</dd></div>
            {typeof selectedProperties.source_url === 'string' && <div><dt>Obiect OSM</dt><dd><a href={selectedProperties.source_url} target="_blank" rel="noreferrer">Deschide sursa ↗</a></dd></div>}
          </dl>
          <button className={styles.primary} type="button" disabled={!selectedCanRun || busy !== null} onClick={createStudy}>
            {busy === 'study' ? 'Se calculează studiul SIM…' : 'Rulează studiu pietonal SIM'}
          </button>
          <p className={styles.muted}>Studiul cere date OSM pentru zona selectată. Rezultatele privesc graful pietonal mapat, nu traficul observat. Nu există fallback automat la date sintetice.</p>
        </section>}

        {busy && <p className={styles.progress} role="status">{busy === 'study' ? 'Se încarcă studiul SIM…' : busy === 'planning' ? 'SIM validează interpretarea dovezilor…' : 'Se încarcă comparația de graf…'}</p>}
        {error && <div className={styles.error} role="alert"><strong>{error.title}</strong><details><summary>Detalii</summary><p>{error.detail}</p>{error.requestId && <p>Cerere: <code>{error.requestId}</code></p>}</details></div>}

        {study && <section className={styles.results} aria-label="Rezultatele studiului SIM">
          <div className={styles.sectionHeading}><div><p className={styles.eyebrow}>Rezultat calculat de SIM</p><h2>Studiu pietonal</h2></div><span className={styles.doneBadge}>Salvat</span></div>
          <p className={study.source === 'fixture' ? styles.aiUnavailable : styles.analysisStatus} role="status">{study.source === 'fixture' ? 'DEMONSTRAȚIE SINTETICĂ: graf și probleme de test, fără observații reale ale Iașului. Valorile sunt calcule SIM pe fixture, nu beneficii măsurate.' : 'Studiu OpenStreetMap salvat: rezultatele provin din graful pietonal al zonei sursă; încărcarea după ID nu reia achiziția OSM.'}</p>
          <div className={styles.identityGrid}>
            <div><span>Studiu</span><code>{study.study_id}</code></div>
            <div><span>Baseline</span><code>{study.baseline_id}</code></div>
            <div><span>Area ID</span><code>{String(study.urban_issues?.area_id ?? (isJsonRecord(study.analysis.area) ? study.analysis.area.area_id : null) ?? 'Necunoscut')}</code></div>
            <div><span>Hash dovezi</span><code>{study.evidence_packet_sha256 ?? 'Nedisponibil'}</code></div>
          </div>
          <p className={styles.resultLabel}>Probleme detectate în datele cartografiate ({resultProblems.length})</p>
          {resultProblems.length ? <details className={styles.solutionDetails}><summary>Inspectează toate problemele detectate ({resultProblems.length})</summary><ul className={styles.resultList}>{resultProblems.map((problem, index) => {
            const id = stringValue(problem.problem_id, `problem-${index}`);
            const geometry = problem.geometry;
            return <li key={id}>
              <strong>{stringValue(problem.title, stringValue(problem.problem_type, 'Problemă SIM'))}</strong>
              <p>{stringValue(problem.description, 'SIM a identificat o problemă în rețeaua pietonală cartografiată.')}</p>
              <small>{id} · Severitate: {stringValue(problem.severity, 'necunoscută')} · {geometry ? 'geometria este afișată pe hartă' : 'SIM nu a furnizat geometrie; nu a fost creat marker'}</small>
            </li>;
          })}</ul></details> : <p className={styles.muted}>SIM nu a returnat probleme cu geometrie sau evidență pentru acest studiu.</p>}
          {sourcedProblemCollection.features.length > 0 && <p className={styles.legendNote}>Marcajele roșii de pe hartă provin din `problem_locations_geojson` al SIM.</p>}

          <ConnectedInterventionEditor
            problems={connectedProblems}
            solutions={connectedSolutions}
            selectedProblemId={selectedProblemId}
            onSelectProblem={selectProblem}
            selectedType={selectedInterventionType}
            onSelectType={selectInterventionType}
            intensity={interventionIntensity}
            onSelectIntensity={setInterventionIntensity}
            selectedSolutionId={selectedSolutionId}
            onSelectSolution={selectConnectedSolution}
            onEvaluate={(candidateId) => {
              const solution = connectedSolutions.find((item) => item.candidateId === candidateId);
              if (solution) selectConnectedSolution(solution);
              evaluateCandidate(candidateId);
            }}
            busy={busy !== null}
          />

          {resultSolutions.length > 0 && <details className={styles.solutionDetails}>
            <summary>Detalii tehnice și impacturi SIM ({resultSolutions.length})</summary>
            <ul className={styles.resultList}>{resultSolutions.map((solution, index) => {
            const id = stringValue(solution.solution_id, `solution-${index}`);
            const candidateId = typeof solution.candidate_id === 'string' ? solution.candidate_id : null;
            const status = stringValue(solution.status, 'necunoscut');
            const canEvaluate = candidateId !== null && validCandidateIds.has(candidateId);
            const impacts = solution.shared_sample_impact;
            const geometry = geometryFromSolution(solution);
            return <li key={id}>
              <div className={styles.resultTitle}><strong>{stringValue(solution.title, stringValue(solution.solution_type, 'Soluție SIM'))}</strong><span>{status}</span></div>
              <p>{stringValue(solution.description, stringValue(solution.rationale, 'Opțiune produsă din analiza SIM.'))}</p>
              <small>{candidateId ? `Candidate ID: ${candidateId}` : 'Concept de verificare, fără geometrie executabilă'} · Fezabilitate fizică: necunoscută</small>
              {Array.isArray(solution.evidence_ids) && <p className={styles.evidenceIds}>Dovezi: {solution.evidence_ids.map(String).join(', ') || 'Niciuna returnată'}</p>}
              {canEvaluate && <>
                <Aggregate value={impacts} />
                <div className={styles.buttonRow}>
                  <button type="button" className={styles.secondary} onClick={() => activateSolution(candidateId, geometry)}>Arată candidatul pe hartă</button>
                  <button type="button" className={styles.secondary} disabled={busy !== null} onClick={() => evaluateCandidate(candidateId)}>Compară Înainte / După</button>
                </div>
              </>}
              {candidateId && !canEvaluate && <p className={styles.muted}>SIM nu a aprobat evaluarea acestui candidat pentru comparația de graf.</p>}
            </li>;
          })}</ul>
          </details>}
          {resultSolutions.length === 0 && <p className={styles.muted}>{connectedSolutions.length ? 'Acest studiu mai vechi păstrează candidații evaluați în editor, fără catalogul nou de soluții.' : 'SIM nu a returnat soluții pentru problemele acestui studiu.'}</p>}

          {evaluation && <section className={styles.evaluation} aria-label="Comparație calculată de SIM">
            <p className={styles.eyebrow}>Comparație Înainte / După · graf pietonal</p>
            <h2>{evaluation.candidate_id}</h2>
            <p>Baseline: <code>{evaluation.baseline_id}</code> · evaluat: {formatTimestamp(evaluation.evaluated_at)}. Comparația folosește perechi de noduri eșantionate, nu deplasări observate. SUMO executat: nu.</p>
            <Aggregate value={evaluation.impact.aggregate} />
            <div className={styles.routeTableWrap}><table className={styles.routeTable}><caption>Rute calculate de SIM pe același graf de referință</caption><thead><tr><th>Pereche</th><th>Înainte</th><th>După</th><th>Diferență (m)</th></tr></thead><tbody>{evaluation.impact.routes.map((route, index) => {
              const before = isJsonRecord(route.before) ? route.before : {};
              const after = isJsonRecord(route.after) ? route.after : {};
              return <tr key={`${route.origin_node_id}-${route.destination_node_id}-${index}`}>
                <td>{route.origin_node_id} → {route.destination_node_id}</td>
                <td>{stringValue(before.status, 'Nedisponibil')} · {formatValue(before.network_distance_m)} m</td>
                <td>{stringValue(after.status, 'Nedisponibil')} · {formatValue(after.network_distance_m)} m</td>
                <td>{formatValue(route.distance_delta_m)}</td>
              </tr>;
            })}</tbody></table></div>
            <p className={styles.muted}>Valorile sunt rezultate de model {study.source === 'fixture' ? 'pe un graf sintetic de test' : 'pe rețeaua pietonală OpenStreetMap'}. Nu reprezintă trafic măsurat, economii reale, populație afectată sau fezabilitate fizică.</p>
          </section>}

          <section className={styles.aiPanel} aria-label="Planificare asistată de AI">
            <div className={styles.sectionHeading}><div><p className={styles.eyebrow}>Interpretarea dovezilor</p><h2>Planificare AI</h2></div></div>
            <p className={styles.muted}>Modelul poate explica numai identificatorii și dovezile deja validate de SIM. Geometria și impactul rămân cele calculate de SIM.</p>
            <p className={styles.muted}>Soluțiile din editor sunt recomandări deterministe SIM. Ele rămân disponibile fără AI cloud și nu sunt prezentate ca generate de AI.</p>
            {!study.evidence_packet_sha256 && <p className={styles.aiUnavailable} role="status">AI cloud indisponibil pentru acest studiu salvat: pachetul de dovezi necesar lipsește din versiunea sa. Recomandările deterministe SIM din editor rămân disponibile.</p>}
            <button className={styles.secondary} type="button" disabled={busy !== null || !study.evidence_packet_sha256} onClick={requestPlanning}>{busy === 'planning' ? 'Se solicită…' : planning ? 'Reîncarcă rezultatul salvat' : 'Verifică disponibilitatea AI cloud'}</button>
            {planning && <>
              <p className={planning.ai_generated ? styles.aiAvailable : styles.aiUnavailable} role="status">
                {planning.ai_generated && ['completed', 'completed_with_rejections'].includes(planning.provider_status)
                  ? `Răspuns AI validat de SIM · ${planning.provider ?? 'provider'} · ${planning.model_id ?? 'model indisponibil'}`
                  : `AI indisponibil (${planning.provider_status}). Rezultatele SIM deterministe rămân afișate; nu s-au inventat recomandări.`}
              </p>
              <details><summary>Identificatorii rezultatului</summary><p>Planning ID: <code>{planning.planning_id}</code></p><p>Study ID: <code>{planning.study_id}</code> · Baseline ID: <code>{planning.baseline_id}</code></p><p>Area ID: <code>{planning.area_id}</code> · Hash dovezi: <code>{planning.evidence_packet_sha256}</code></p><p>Validare: {stringValue(planning.validation?.status, 'indisponibilă')}</p>{planning.warnings.map((warning, index) => <p key={index}>{warning}</p>)}<button type="button" className={styles.textButton} onClick={reloadPlanning}>Reîncarcă rezultatul după ID</button></details>
              {planning.summary && aiCanRender && <p>{planning.summary}</p>}
              {aiCanRender && <ul className={styles.resultList}>{aiRecommendations.map((recommendation) => {
                const authoritative = recommendation.authoritative_sim_solution!;
                const geometry = authoritative.geometry ?? null;
                const candidateId = recommendation.candidate_id;
                const canEvaluate = validCandidateIds.has(candidateId);
                return <li key={recommendation.solution_id}>
                  <strong>{recommendation.title ?? 'Recomandare AI validată'}</strong>
                  <p>{recommendation.explanation ?? 'Interpretare bazată pe dovezile legate de SIM.'}</p>
                  <small>{recommendation.solution_id} · candidate: {candidateId}</small>
                  {(() => {
                    const problemIds = recommendation.problem_ids ?? [];
                    const relatedProblems = resultProblems.filter((problem) => problemIds.includes(stringValue(problem.problem_id, '')));
                    return <div className={styles.recommendationEvidence}>
                      <strong>Probleme SIM asociate</strong>
                      {relatedProblems.length > 0
                        ? <ul>{relatedProblems.map((problem, index) => {
                          const problemId = stringValue(problem.problem_id, `problem-${index}`);
                          return <li key={problemId}><button type="button" className={styles.textButton} onClick={() => selectProblem(problemId)}>{stringValue(problem.title, stringValue(problem.problem_type, problemId))}</button><span>{stringValue(problem.description, 'Detaliile problemei provin din studiul SIM.')}</span></li>;
                        })}</ul>
                        : <p>SIM nu a returnat un identificator de problemă asociat acestei recomandări.</p>}
                      <p>Referințe de evidență returnate de SIM: {(recommendation.evidence_ids ?? []).join(', ') || 'niciuna'}</p>
                    </div>;
                  })()}
                  <p className={styles.muted}>Geometria, intervenția și impactul provin din înregistrarea SIM atașată după validare.</p>
                  {authoritative.shared_sample_impact != null && <Aggregate value={authoritative.shared_sample_impact} />}
                  <div className={styles.buttonRow}><button type="button" className={styles.secondary} onClick={() => activateSolution(candidateId, geometry)}>Arată soluția pe hartă</button>{canEvaluate && <button type="button" className={styles.secondary} disabled={busy !== null} onClick={() => evaluateCandidate(candidateId)}>Compară candidatul SIM</button>}</div>
                </li>;
              })}</ul>}
              {aiUnavailable && <p className={styles.muted}>Pentru recomandări cloud este necesar provider configurat pe server. Nu afișăm text demonstrativ ca răspuns AI.</p>}
            </>}
          </section>

          <details className={styles.provenance}><summary>Proveniență și limite ale studiului</summary>
            <p>Sursă: {source(study.source)} · calcul: {study.calculation} · versiune motor: <code>{study.engine_revision}</code> · creat: {formatTimestamp(study.created_at)}.</p>
            <p>Catalog sursă: {attribution} · ODbL-1.0 · snapshot: {sourceSnapshot}.</p>
            {study.warnings.map((warning, index) => <p key={index}>{warning}</p>)}
            {Array.isArray(study.solution_plan?.limitations) && study.solution_plan!.limitations.map((limitation, index) => <p key={index}>{String(limitation)}</p>)}
          </details>
        </section>}

        {!selectedPlace && !study && <div className={styles.emptyHint}><strong>Harta Iașului este gata.</strong><p>Apasă un poligon sau caută un cartier pentru a inspecta sursa și eligibilitatea.</p></div>}
        <footer className={styles.footer}><span>{catalog?.metadata.source ?? 'OpenStreetMap'} · snapshot {sourceSnapshot}</span><Link href="/app/demo">Deschide demonstrația cu cele 5 repere salvate →</Link></footer>
      </aside>
    </main>
  </div>;
}
