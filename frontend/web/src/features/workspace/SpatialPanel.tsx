'use client';

import dynamic from 'next/dynamic';
import { useEffect, useRef, useState } from 'react';
import type { SourcedPlace } from '../neighborhoods/sim-geography';
import { NeighborhoodExplorer } from '../neighborhoods/NeighborhoodExplorer';
import { placeCenter } from '../neighborhoods/sim-geography';
import type { SpatialEvaluation, SpatialProposalOption, SpatialStudy } from '@arteria/shared/contracts';
import { spatialApi } from '../../lib/api';
import styles from './ConnectedWorkspace.module.css';
import { label, source, formatNumber } from './presentation';

const SpatialMap = dynamic(() => import('../map/MapViewport'), {
  ssr: false,
  loading: () => <div className="map-loading" role="status">Se încarcă motorul hărții…</div>,
});

type Mode = 'fixture' | 'osm';

export function SpatialPanel() {
  const [mode, setMode] = useState<Mode>('fixture');
  const [selectedPlace, setSelectedPlace] = useState<SourcedPlace | null>(null);
  const [fillArea, setFillArea] = useState(false);
  const [study, setStudy] = useState<SpatialStudy | null>(null);
  const [evaluation, setEvaluation] = useState<SpatialEvaluation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);

  async function request(action: (signal: AbortSignal) => Promise<void>) {
    controller.current?.abort();
    const active = new AbortController(); controller.current = active;
    setBusy(true); setError(''); setEvaluation(null);
    try { await action(active.signal); }
    catch (cause) { if (!active.signal.aborted) setError(cause instanceof Error ? cause.message : 'Motorul nu este disponibil.'); }
    finally { if (!active.signal.aborted) setBusy(false); }
  }

  function selectMode(next: Mode) {
    controller.current?.abort();
    setBusy(false); setError(''); setStudy(null); setEvaluation(null); setMode(next);
  }

  function selectPlace(place: SourcedPlace) {
    controller.current?.abort();
    setBusy(false); setError(''); setStudy(null); setEvaluation(null); setSelectedPlace(place);
  }

  function runFixture() {
    setStudy(null);
    void request(async signal => {
      const result = await spatialApi.spatialStudy(signal);
      if (!signal.aborted) setStudy(result);
    });
  }

  function runSourcedArea() {
    if (!selectedPlace || selectedPlace.geometryType === 'Point' || selectedPlace.validation.status !== 'valid') return;
    setStudy(null);
    void request(async signal => {
      const result = await spatialApi.spatialNeighborhoodStudy(selectedPlace.id, signal);
      if (!signal.aborted) setStudy(result);
    });
  }

  const validation = study?.proposal_validation;
  const acceptedIds = new Set(validation?.results
    .filter(result => result.status === 'candidate_backed_evaluated' && result.candidate_id)
    .map(result => result.candidate_id as string) ?? []);
  const proposalOptions = (study?.proposal_options ?? [])
    .filter((option): option is SpatialProposalOption => acceptedIds.has(option.candidate_id));
  const mapCenter = selectedPlace ? placeCenter(selectedPlace) ?? [27.59, 47.16] as [number, number] : [27.59, 47.16] as [number, number];

  return <section className={styles.card}>
    <h1>Acces pietonal și geografie SIM</h1>
    <p>Motorul SIM analizează grafuri pietonale și compară legături ipotetice. Nu calculează fluxuri auto, măsurători observate sau fezabilitate de construcție.</p>

    <div className={styles.row} role="group" aria-label="Sursa studiului pietonal">
      <button type="button" aria-pressed={mode === 'fixture'} onClick={() => selectMode('fixture')}>Exemplu SIM sintetic</button>
      <button type="button" aria-pressed={mode === 'osm'} onClick={() => selectMode('osm')}>Catalog OSM Iași</button>
    </div>

    {mode === 'fixture' ? <>
      <p>Exemplul folosește o rețea sintetică locală; nu reprezintă infrastructură sau trasee observate din Iași.</p>
      <button disabled={busy} onClick={runFixture}>Analizează exemplul pietonal</button>
    </> : <>
      <NeighborhoodExplorer
        selectedPlace={selectedPlace}
        onSelect={selectPlace}
        onClear={() => { controller.current?.abort(); setSelectedPlace(null); setStudy(null); setEvaluation(null); }}
        fillEnabled={fillArea}
        onFillChange={setFillArea}
        analysisEnabled
      />
      {selectedPlace && <>
        <div style={{ position: 'relative', height: 'min(48vh, 440px)', minHeight: '280px', overflow: 'hidden', borderRadius: '12px', margin: '16px 0' }}>
          <SpatialMap
            neighborhoodId="copou"
            center={mapCenter}
            selectedIssueId={null}
            sourcedPlace={selectedPlace}
            fillSourcedArea={fillArea}
            sourcedAnalysisStatus={study?.source === 'osm' ? 'completed' : 'available'}
          />
        </div>
        <p>Poligoanele OSM sunt extinderi de locuri mapate, nu limite administrative oficiale. Punctele rămân puncte. Sursă: © OpenStreetMap contributors · ODbL-1.0.</p>
        <button
          disabled={busy || selectedPlace.geometryType === 'Point' || selectedPlace.validation.status !== 'valid'}
          onClick={runSourcedArea}
        >
          Analizează cu SIM v3
        </button>
        <p className={styles.muted}>Se folosește geometria canonică din catalogul SIM de pe server. Cererea descarcă date OpenStreetMap pentru zona selectată; rezultatele rămân analiză de graf pietonal.</p>
      </>}
    </>}

    {busy && <p role="status">Pregătim analiza grafului pietonal…</p>}
    {error && <div role="alert" className={styles.error}>Analiza nu a putut fi finalizată.<details><summary>Detalii despre problemă</summary>{error}</details></div>}
    {study && <>
      <h2>Studiu SIM v3</h2>
      <p>Sursă: {source(study.source)} · Revizie SIM: <code>{study.engine_revision}</code> · Alternative validate: {proposalOptions.length}</p>
      <details><summary>Dovezi și limite</summary>
        <ul>{study.warnings.map(w => <li key={w}>{w}</li>)}</ul>
        <p>Evaluarea propunerilor: {validation?.status ?? 'indisponibilă'} · Acceptate: {validation?.summary.accepted_count ?? 0} · Respinse: {validation?.summary.rejected_count ?? 0}</p>
        {typeof study.evidence_packet.schema_version === 'string' && <p>Context de dovezi: {study.evidence_packet.schema_version} · geometrie cu hash SHA-256 · dimensiune serializată {String((study.evidence_packet.truncation as Record<string, unknown> | undefined)?.serialized_bytes ?? 'necunoscută')} octeți.</p>}
        <p>SIM nu a apelat un serviciu AI extern. Costul, siguranța, proprietatea, accesibilitatea și aprobarea pentru construcție rămân neevaluate.</p>
      </details>
      {!proposalOptions.length && <p>Nicio alternativă nu a trecut validarea candidate-backed SIM pentru această rețea.</p>}
      {proposalOptions.map((option, index) => <article key={option.candidate_id} className={styles.card}>
        <h3>Legătură ipotetică {index + 1}</h3>
        <p>{option.summary}</p>
        <p>Categoria de intervenție: neclasificată · Fezabilitate fizică: necunoscută · Cost: neevaluat.</p>
        <p>Rută sample: {formatNumber(option.modeled_impact.aggregate.evaluated_pair_count ?? null)} · Îmbunătățite: {formatNumber(option.modeled_impact.aggregate.improved_count ?? null)} · Înrăutățite: {formatNumber(option.modeled_impact.aggregate.regressed_count ?? null)}</p>
        <details><summary>Verificări pentru această propunere</summary>
          <ul>{option.screening.missing_evidence.map(item => <li key={item}>{item}</li>)}{option.screening.warnings.map((item, i) => <li key={`${i}-${item}`}>{item}</li>)}</ul>
        </details>
        <button disabled={busy} onClick={() => void request(async signal => {
          const candidate = study.alternatives.ranked_candidates.find(item => item.candidate_id === option.candidate_id);
          if (!candidate) throw new Error('Candidatul nu mai există în evaluarea SIM salvată.');
          const result = await spatialApi.spatialEvaluate(study.study_id, {
            baseline_id: study.baseline_id, candidate_id: candidate.candidate_id, intervention: candidate.intervention,
          }, signal);
          if (!signal.aborted) setEvaluation(result);
        })}>Compară legătura {index + 1}</button>
      </article>)}
    </>}

    {evaluation && <section aria-label="Rezultate pietonale">
      <h2>Comparație pe același baseline</h2>
      <p>Comparație calculată de SIM din graf și eșantioane de rute, nu călătorii observate. Validare: {evaluation.proposal_validation.status} · fezabilitate fizică: necunoscută.</p>
      <dl>{[
        ['evaluated_pair_count', 'Perechi de trasee comparate'], ['improved_count', 'Perechi îmbunătățite'],
        ['regressed_count', 'Perechi înrăutățite'], ['newly_reachable_count', 'Perechi devenite accesibile'],
        ['newly_unreachable_count', 'Perechi devenite inaccesibile'],
        ['total_distance_savings_m', 'Diferență agregată de distanță (metri)'],
      ].map(([key, title]) => <div key={key}><dt>{title}</dt><dd>{formatNumber(evaluation.impact.aggregate[key!] ?? null)}</dd></div>)}</dl>
      <div className={styles.scroll}><table className={styles.table}><caption>Rute simulate în graful OpenStreetMap, nu trasee observate</caption><thead><tr><th>Rută</th><th>Efect</th><th>Diferență distanță (m)</th></tr></thead><tbody>{evaluation.impact.routes.map((route, index) => <tr key={index}><td>{route.origin_node_id} → {route.destination_node_id}</td><td>{label(route.outcome, 'Vezi detaliile analizei')}</td><td>{route.distance_delta_m === null ? 'Necomparabil' : route.distance_delta_m.toFixed(2)}</td></tr>)}</tbody></table></div>
      <details><summary>Detalii și limitele comparației</summary><ul>{evaluation.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul></details>
    </section>}
  </section>;
}
