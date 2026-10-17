'use client';

import { useEffect, useRef, useState } from 'react';
import { interventions, type Intervention, type Layout } from './intersection';
import { JunctionPlan, UnderpassSection } from './JunctionPlan';
import styles from './UrbanScene.module.css';
import type { UrbanModel } from './urban-model';

export function UrbanScene() {
  const mount = useRef<HTMLDivElement>(null);
  const model = useRef<UrbanModel | null>(null);
  const state = useRef<{ layout: Layout; selected: Intervention; reveal: boolean }>({ layout: 'existing', selected: 'underpass', reveal: false });
  const [layout, setLayout] = useState<Layout>('existing');
  const [selected, setSelected] = useState<Intervention>('underpass');
  const [reveal, setReveal] = useState(false);
  const [status, setStatus] = useState<'loading' | 'ready' | 'fallback'>('loading');

  useEffect(() => {
    const host = mount.current;
    if (!host) return;
    let cancelled = false;
    let started = false;
    let visible = false;
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    const updateVisibility = () => model.current?.setVisible(visible && !document.hidden);
    const updateMotion = () => model.current?.setReducedMotion(motion.matches);
    const observer = new IntersectionObserver(entries => {
      visible = entries[0]?.isIntersecting ?? false;
      updateVisibility();
      if (!visible || started) return;
      started = true;
      import('./urban-model').then(({ createUrbanModel }) => {
        if (cancelled) return;
        try {
          model.current = createUrbanModel(host, () => {
            model.current?.dispose();
            model.current = null;
            if (!cancelled) setStatus('fallback');
          });
          model.current.setReducedMotion(motion.matches);
          model.current.setState(state.current.layout, state.current.selected, state.current.reveal, false);
          updateVisibility();
          setStatus('ready');
        } catch {
          if (!cancelled) setStatus('fallback');
        }
      }).catch(() => { if (!cancelled) setStatus('fallback'); });
    }, { threshold: 0.05 });
    observer.observe(host);
    document.addEventListener('visibilitychange', updateVisibility);
    motion.addEventListener('change', updateMotion);
    return () => {
      cancelled = true;
      observer.disconnect();
      document.removeEventListener('visibilitychange', updateVisibility);
      motion.removeEventListener('change', updateMotion);
      model.current?.dispose();
      model.current = null;
    };
  }, []);

  function changeLayout(next: Layout) {
    setLayout(next);
    const nextReveal = next === 'existing' ? false : state.current.reveal;
    setReveal(nextReveal);
    state.current = { ...state.current, layout: next, reveal: nextReveal };
    model.current?.setState(next, state.current.selected, nextReveal);
  }

  function selectIntervention(next: Intervention) {
    const cutaway = next === 'underpass';
    setSelected(next);
    setLayout('proposed');
    setReveal(cutaway);
    state.current = { layout: 'proposed', selected: next, reveal: cutaway };
    model.current?.setState('proposed', next, cutaway);
  }

  function toggleReveal() {
    const next = !reveal;
    setReveal(next);
    state.current.reveal = next;
    model.current?.setState(layout, selected, next);
  }

  return (
    <figure className={styles.figure} aria-label="Intersecție ilustrativă interactivă">
      <div className={styles.toolbar}>
        <span className={styles.modelLabel}>
          Studiu de intersecție <span>01 / Focus Iași</span>
        </span>
        <fieldset className={styles.switch}>
          <legend className={styles.srOnly}>Configurație stradală</legend>
          {(['existing', 'proposed'] as const).map(value => (
            <label className={styles.option} key={value}>
              <input
                type="radio"
                name="hero-layout"
                value={value}
                checked={layout === value}
                onChange={() => changeLayout(value)}
              />
              <span>{value === 'existing' ? 'Existent' : 'Propunere'}</span>
            </label>
          ))}
        </fieldset>
      </div>

      <div className={styles.viewport} data-scene-state={status}>
        <div className={styles.fallback} aria-hidden="true">
          <JunctionPlan layout={layout} reveal={reveal} selected={layout === 'proposed' ? selected : undefined} />
        </div>
        <div ref={mount} className={`${styles.canvasHost} ${status === 'ready' ? styles.ready : ''}`} aria-hidden="true" />
        <span className={styles.viewLabel}>
          {status === 'ready'
            ? (reveal ? 'Secțiune · Jumătatea dinspre privitor este ascunsă' : 'Vedere izometrică · Cameră fixă')
            : status === 'loading'
              ? 'Se încarcă vizualizarea 3D · Plan disponibil'
              : 'Plan 2D · Vizualizare 3D indisponibilă'}
        </span>
        <span className={styles.orientation} aria-hidden="true">
          {status === 'ready' ? 'N ↗' : 'N ↑'}
        </span>
      </div>

      <div className={styles.interventions} role="group" aria-label="Inspectează o intervenție">
        {(Object.keys(interventions) as Intervention[]).map((key, index) => (
          <button
            type="button"
            key={key}
            aria-pressed={layout === 'proposed' && selected === key}
            aria-controls="intervention-description"
            onClick={() => selectIntervention(key)}
          >
            <span className={styles.number}>{index + 1}</span>
            {interventions[key].label}
          </button>
        ))}
      </div>

      <div className={styles.revealRow}>
        <button
          className={styles.revealButton}
          type="button"
          disabled={layout === 'existing'}
          aria-pressed={layout === 'proposed' && reveal}
          aria-controls="underpass-cutaway"
          onClick={toggleReveal}
        >
          Dezvăluie pasajul subteran <span>{reveal ? 'Pornit' : 'Oprit'}</span>
        </button>
        <span>Secțiunea îndepărtează structura doar vizual, nu și din propunere.</span>
      </div>

      <div id="underpass-cutaway" hidden={layout !== 'proposed' || !reveal}>
        <UnderpassSection />
      </div>

      <p className={styles.explanation} id="intervention-description" aria-live="polite">
        {layout === 'existing'
          ? 'Situație existentă: sensul giratoriu la sol cu cale de tramvai Nord–Sud și treceri de pietoni la nivel. Ambele coridoare principale se întâlnesc la nivelul solului.'
          : interventions[selected].description}
      </p>

      <figcaption className={styles.caption}>
        Sens giratoriu denivelat ilustrativ · Necesită evaluare inginerească; fără pretenții de performanță sau fezabilitate
      </figcaption>
    </figure>
  );
}
