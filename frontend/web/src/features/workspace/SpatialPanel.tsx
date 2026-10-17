'use client';
import { useEffect, useRef, useState } from 'react';
import type { SpatialEvaluation, SpatialStudy } from '@arteria/shared/contracts';
import { spatialApi } from '../../lib/api';
import styles from './ConnectedWorkspace.module.css';
import { label, source, formatNumber } from './presentation';

export function SpatialPanel() {
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
  return <section className={styles.card}>
    <h1>Trasee pietonale mai accesibile</h1>
    <p>Explorează cum ar putea ajuta o nouă legătură pietonală. Exemplul folosește o rețea sintetică; propunerile necesită verificări în teren înainte de orice lucrare.</p>
    <button disabled={busy} onClick={() => { setStudy(null); void request(async signal => {
      const result = await spatialApi.spatialStudy(signal); if (!signal.aborted) setStudy(result);
    }); }}>Explorează traseele</button>
    {busy && <p role="status">Căutăm posibile îmbunătățiri…</p>}
    {error && <div role="alert" className={styles.error}>Nu am putut analiza traseele. Reîncearcă în câteva momente.<details><summary>Detalii despre problemă</summary>{error}</details></div>}
    {study && <>
      <p>Sursă: {source(study.source)} · Alternative: {study.alternatives.ranked_candidates.length}</p>
      <details><summary>Despre date și limitele analizei</summary><ul>{study.warnings.map(w => <li key={w}>{w}</li>)}</ul></details>
      {!study.alternatives.ranked_candidates.length && <p>Nu am găsit o legătură potrivită în acest exemplu.</p>}
      {study.alternatives.ranked_candidates.map((candidate, index) => <article key={candidate.candidate_id} className={styles.card}>
        <h2>Legătură ipotetică {index + 1}</h2>
        <p>Compară această legătură cu traseele existente și vezi ce devine mai accesibil.</p><details><summary>Cum a fost aleasă propunerea</summary><ul>{candidate.evaluation_rationale.map(r => <li key={r}>{r}</li>)}</ul><p>{candidate.ranking_explanation}</p></details>
        <button disabled={busy} onClick={() => void request(async signal => {
          const result = await spatialApi.spatialEvaluate(study.study_id, {
            baseline_id: study.baseline_id, candidate_id: candidate.candidate_id, intervention: candidate.intervention,
          }, signal);
          if (!signal.aborted) setEvaluation(result);
        })}>Compară legătura {index + 1}</button>
      </article>)}
    </>}
    {evaluation && <section aria-label="Rezultate pietonale"><h2>Cum se schimbă traseele</h2>
      <p>Comparație salvată · {source(evaluation.source)}. Calculată la {new Date(evaluation.evaluated_at).toLocaleString('ro-RO')}.</p>
      <dl>{[
        ['evaluated_pair_count', 'Trasee comparate'], ['improved_count', 'Trasee îmbunătățite'],
        ['regressed_count', 'Trasee înrăutățite'], ['newly_reachable_count', 'Trasee devenite accesibile'],
        ['newly_unreachable_count', 'Trasee devenite inaccesibile'],
        ['total_distance_savings_m', 'Distanță economisită pe traseele comparabile (metri)'],
      ].map(([key, title]) => <div key={key}><dt>{title}</dt><dd>{formatNumber(evaluation.impact.aggregate[key!] ?? null)}</dd></div>)}</dl>
      <div className={styles.scroll}><table className={styles.table}><caption>Trasee din exemplu, nu călătorii observate</caption><thead><tr><th>Rută</th><th>Efect</th><th>Diferență distanță (m)</th></tr></thead><tbody>{evaluation.impact.routes.map((r, i) => <tr key={i}><td>{r.origin_node_id} → {r.destination_node_id}</td><td>{label(r.outcome, 'Vezi detaliile analizei')}</td><td>{r.distance_delta_m === null ? 'Necomparabil' : r.distance_delta_m.toFixed(2)}</td></tr>)}</tbody></table></div>
      <details><summary>Detalii și limitele comparației</summary><ul>{evaluation.warnings.map(w => <li key={w}>{w}</li>)}</ul></details>
    </section>}
  </section>;
}
