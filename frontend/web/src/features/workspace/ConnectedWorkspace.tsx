'use client';

import { useEffect, useRef, useState } from 'react';
import type { AlternativeLevel, AnalyzeResponse, EvaluateResponse, Issue, LayerId, ProposeResponse } from '@arteria/shared/contracts';
import { alternativeLabels, layers, neighborhoods } from '@arteria/shared/fixtures';
import { api } from '../../lib/api';
import { SpatialPanel } from './SpatialPanel';
import styles from './ConnectedWorkspace.module.css';
import { label, unit, source, formatNumber as number } from './presentation';

type Section = 'analysis' | 'scenarios' | 'comparison' | 'spatial';
const labels: Record<Section, string> = { analysis: 'Explorează', scenarios: 'Scenarii', comparison: 'Compară', spatial: 'Acces pietonal' };

export function ConnectedWorkspace() {
  const [section, setSection] = useState<Section>('analysis');
  const [area, setArea] = useState('copou');
  const [requestedLayers, setLayers] = useState<LayerId[]>(['roads']);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [issue, setIssue] = useState<Issue | null>(null);
  const [proposal, setProposal] = useState<ProposeResponse | null>(null);
  const [level, setLevel] = useState<AlternativeLevel>('minimal');
  const [evaluation, setEvaluation] = useState<EvaluateResponse | null>(null);
  const [green, setGreen] = useState(40);
  const [tuned, setTuned] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);

  function cancel() { controller.current?.abort(); setBusy(false); setError(''); }
  function clearSelection() { cancel(); setProposal(null); setEvaluation(null); }
  function reset() { clearSelection(); setAnalysis(null); setIssue(null); setTuned(false); }
  async function request(action: (signal: AbortSignal) => Promise<void>) {
    cancel();
    const active = new AbortController(); controller.current = active; setBusy(true);
    try { await action(active.signal); }
    catch (cause) {
      if (!active.signal.aborted) setError(cause instanceof Error ? cause.message : 'Cererea a eșuat. Reîncearcă.');
    } finally { if (!active.signal.aborted) setBusy(false); }
  }
  const selected = proposal?.alternatives.find(a => a.level === level);
  const maxGreen = analysis?.inputs ? analysis.inputs.cycle_seconds - analysis.inputs.lost_seconds - 10 : 70;

  function analyze() {
    reset();
    void request(async signal => {
      const result = await api.analyze({
        area: { city_id: 'iasi-ro', area_id: `preview-${area}`, boundary: null, boundary_source: 'known_area', crs: 'EPSG:4326' },
        layers: requestedLayers,
        analysis: { network_modes: ['walk', 'bike'], accessibility_thresholds: [{ value: 15, unit: 'minute', mode: 'walk' }] },
        data_as_of: null,
      }, signal);
      if (signal.aborted) return;
      if (!result.baseline_id) throw new Error('Backend-ul nu a returnat baseline_id. Verifică versiunea API-ului.');
      setAnalysis(result); setIssue(result.issues[0] ?? null);
      setGreen(result.inputs?.ns_green_seconds ?? 40);
    });
  }
  function propose() {
    if (!analysis || !issue) return;
    clearSelection();
    void request(async signal => {
      const result = await api.propose({ analysis_id: analysis.analysis_id,
        area: { city_id: analysis.area.city_id, area_id: analysis.area.area_id }, issue_id: issue.id,
        intervention_catalog_version: 'catalog-1', constraints: { max_affected_area: { value: 3.5, unit: 'hectare' } },
        requested_alternatives: tuned ? ['minimal'] : ['minimal', 'moderate', 'transformative'],
        ...(tuned ? { parameters: { ns_green_seconds: green } } : {}),
      }, signal);
      if (signal.aborted) return;
      setProposal(result); setLevel(result.alternatives[0]?.level ?? 'minimal');
    });
  }
  function evaluate() {
    if (!analysis || !proposal || !selected) return;
    setEvaluation(null);
    void request(async signal => {
      const result = await api.evaluate({ analysis_id: analysis.analysis_id, baseline_id: analysis.baseline_id,
        area: { city_id: analysis.area.city_id, area_id: analysis.area.area_id }, proposal_set_id: proposal.proposal_set_id,
        alternative_level: selected.level, interventions: selected.interventions,
        evaluation: { indicators: analysis.indicators.map(i => i.id), traffic_simulation: { requested: false, mode: 'none', replay_id: null } },
      }, signal);
      if (signal.aborted) return;
      setEvaluation(result); setSection('comparison');
    });
  }

  return <div className={styles.root}>
    <a className="skip-link" href="#workspace">Sari la spațiul de lucru</a>
    <header className={styles.header}><a href="/">ARTERIA <small>by ARION</small></a><span className={styles.badge}>Semaforizare demo · graf pietonal SIM v3</span></header>
    <nav className={styles.nav} aria-label="Navigație principală">{(Object.keys(labels) as Section[]).map(key =>
      <button key={key} aria-current={section === key ? 'page' : undefined} onClick={() => setSection(key)}>{labels[key]}</button>)}</nav>
    <main id="workspace" className={styles.main}>
      {busy && <p role="status">Pregătim rezultatele…</p>}
      {error && <div className={styles.error} role="alert">Nu am putut obține rezultatele. Reîncearcă în câteva momente.<details><summary>Detalii despre problemă</summary>{error}</details></div>}
      {section === 'analysis' && <>
        <section className={styles.card}><h1>Analiza zonei</h1>
          <p>Explorează o zonă și compară posibile îmbunătățiri. În această demonstrație folosim date sintetice, nu măsurători reale din Iași.</p>
          <div className={styles.row}><label htmlFor="api-area">Alege zona</label><select id="api-area" value={area} onChange={e => { reset(); setArea(e.target.value); }}>
            {neighborhoods.map(n => <option key={n.id} value={n.id}>{n.name}</option>)}
          </select></div>
          <details><summary>Ce vrei să explorezi?</summary><div className={styles.row}>{layers.map(l => <label key={l.id}><input type="checkbox" checked={requestedLayers.includes(l.id)} onChange={() => { reset(); setLayers(old => old.includes(l.id) ? old.filter(id => id !== l.id) : [...old, l.id]); }} />{l.label}</label>)}</div></details>
          <div className={styles.row}><button className="primary-button" disabled={busy || !requestedLayers.length} onClick={analyze}>Analizează zona</button></div>
        </section>
        {!analysis ? <section className={styles.card}><h2>Începe cu o zonă.</h2><p>Alege zona care te interesează, apoi pornește analiza.</p></section> : <>
          <section className={styles.card}><h2>Situația actuală</h2><div className={styles.grid}>{analysis.indicators.map(i => <article key={i.id}><h3>{label(i.id, i.label)}</h3><strong>{number(i.value)} {unit(i.unit)}</strong><p className={styles.muted}>{label(i.status)} · {i.provenance.map(p => source(p.source)).join(', ')}</p></article>)}</div>
            {analysis.layer_availability.map(l => <p className={styles.muted} key={l.layer}>{label(l.layer)}: {label(l.status)}</p>)}
          </section>
          <section className={styles.card}><h2>Ce putem îmbunătăți?</h2>{analysis.issues.length === 0 && <p>Nu am identificat propuneri pentru această analiză.</p>}
            {analysis.issues.map(i => <button key={i.id} aria-pressed={issue?.id === i.id} onClick={() => { clearSelection(); setIssue(i); }}>{label(i.id, i.label)}</button>)}
            <div className={styles.row}><button disabled={!issue} onClick={() => setSection('scenarios')}>Vezi propuneri</button></div>
            <Warnings items={analysis.warnings} />
          </section></>}
      </>}
      {section === 'scenarios' && <section className={styles.card}><h1>Propuneri de îmbunătățire</h1>
        {!analysis || !issue ? <p>Începe cu analiza unei zone, apoi alege ce vrei să îmbunătățești.</p> : <>
          <h2>{label(issue.id, issue.label)}</h2><p>Compară ajustări ale semafoarelor. Mai mult timp verde pe o direcție poate crește așteptarea pe cealaltă.</p>
          <label><input type="checkbox" checked={tuned} onChange={e => { clearSelection(); setTuned(e.target.checked); }} />Ajustează durata verdelui</label>
          {tuned && <div className={styles.row}><label htmlFor="green">Verde nord–sud: {green} secunde</label><input id="green" type="range" min={10} max={maxGreen} step={1} value={green} onChange={e => { clearSelection(); setGreen(Number(e.target.value)); }} /></div>}
          <div className={styles.row}><button disabled={busy} onClick={propose}>Vezi propunerile</button></div>
          {proposal && <><Warnings items={proposal.warnings} /><p className={styles.muted}>Propunerile modifică doar durata semafoarelor. Nu presupun lucrări de infrastructură.</p>
            <div className={styles.grid}>{proposal.alternatives.map(a => <article className={styles.card} key={a.level}>
              <button aria-pressed={level === a.level} onClick={() => { cancel(); setEvaluation(null); setLevel(a.level); }}>{alternativeLabels[a.level]}</button>
              <h3>{a.interventions[0]?.type === 'signal_timing' ? 'Ajustarea timpului verde' : a.summary}</h3><p>{label(a.validation.status)}</p>
              {a.interventions.map((i, index) => <div key={index}><strong>{label(i.type, 'Intervenție propusă')}</strong><ul>{Object.entries(i.parameters).map(([key, value]) => <li key={key}>{label(key, 'Parametru')}: {typeof value === 'number' ? number(value) : String(value)} {unit(i.parameter_units?.[key] ?? '')}</li>)}</ul></div>)}
              <details><summary>Ipoteze și explicații</summary><p>{a.rationale}</p><ul>{a.assumptions.map(x => <li key={x}>{x}</li>)}</ul></details>
              <ul>{a.expected_impacts.map(x => <li key={x.indicator_id}>{label(x.indicator_id)}: {label(x.direction)} (estimare)</li>)}</ul>
            </article>)}</div>
            {!proposal.alternatives.length && <p>Nicio alternativă disponibilă.</p>}
            <button disabled={busy || !selected || selected.validation.status !== 'accepted'} onClick={evaluate}>Compară rezultatele</button>
          </>}
        </>}
      </section>}
      {section === 'comparison' && <section className={styles.card}><h1>Înainte. După. Cu dovezi.</h1>
        {!evaluation ? <p>Selectează o propunere și apasă „Compară rezultatele”.</p> : <>
          <p>Comparăm situația actuală cu propunerea aleasă, păstrând aceleași condiții de trafic.</p>
          <div className={styles.scroll}><table className={styles.table}><caption>Situația actuală și propunerea aleasă</caption><thead><tr><th>Indicator</th><th>Înainte</th><th>După</th><th>Diferență</th></tr></thead><tbody>
            {evaluation.comparisons.map(c => <tr key={c.indicator_id}><th>{label(c.indicator_id, analysis?.indicators.find(i => i.id === c.indicator_id)?.label)}</th><td>{number(c.baseline.value)} {unit(c.baseline.unit)}</td><td>{number(c.scenario.value)} {unit(c.scenario.unit)}</td><td className={c.delta.value !== null && c.delta.value < 0 ? styles.good : styles.bad}>{number(c.delta.value)} {unit(c.delta.unit)}</td></tr>)}
          </tbody></table></div><p>Pentru întârziere, o diferență negativă înseamnă îmbunătățire; o diferență pozitivă înseamnă înrăutățire.</p>
          <p className={styles.muted}>{evaluation.simulation.status === 'not_requested' ? 'Rezultate estimate pe date demonstrative. Nu s-a rulat o simulare de trafic.' : 'Vezi detaliile calculului în secțiunea de mai jos.'}</p><Warnings items={evaluation.warnings} />
          <details><summary>Surse și ipoteze</summary>{evaluation.comparisons.map(c => <p key={c.indicator_id}>{c.indicator_id}: {c.scenario.status} · {c.scenario.provenance.map(p => `${p.source} / ${p.method}`).join('; ')} · {c.scenario.uncertainty.description}</p>)}<p>Referința analizei: {evaluation.baseline.id}</p></details>
        </>}
      </section>}
      {section === 'spatial' && <SpatialPanel />}
    </main>
  </div>;
}

export function Warnings({ items }: { items: string[] }) { return items.length ? <details className={styles.muted}><summary>Despre date și limitele analizei</summary><ul>{items.map((w, i) => <li key={i}>{w}</li>)}</ul></details> : null; }
