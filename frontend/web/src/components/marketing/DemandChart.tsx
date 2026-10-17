'use client';

import { useState } from 'react';
import styles from './DemandChart.module.css';

export function DemandChart() {
  const [peak, setPeak] = useState<'morning' | 'evening'>('morning');
  return (
    <figure className={styles.figure}>
      <div className={styles.header}>
        <div>
          <h3 className={styles.title}>O singură intersecție. Cereri diferite.</h3>
          <p className={styles.subtitle}>Tipar zilnic schematic la accesul sudic</p>
        </div>
        <div className={styles.legend}>
          <span className={styles.demand}>Cerere de mobilitate</span>
          <span className={styles.delay}>Întârziere potențială</span>
        </div>
      </div>
      <div className={styles.controls} role="group" aria-label="Inspectează un vârf de cerere">
        <button
          type="button"
          aria-pressed={peak === 'morning'}
          aria-controls="peak-description"
          onClick={() => setPeak('morning')}
        >
          Vârf de dimineață <span>08:30</span>
        </button>
        <button
          type="button"
          aria-pressed={peak === 'evening'}
          aria-controls="peak-description"
          onClick={() => setPeak('evening')}
        >
          Vârf de seară <span>17:30</span>
        </button>
      </div>
      <p className={styles.scale}>Intensitate schematică · Fără scară măsurată</p>
      <div
        className={styles.plot}
        role="img"
        aria-label="Cererea ilustrativă de călătorie și întârzierile potențiale cresc la orele de vârf de dimineață și seară, apoi revin spre linia de bază. Fără date măsurate."
      >
        <svg className={styles.svg} viewBox="0 0 1000 240" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0 45H1000M0 100H1000M0 155H1000M0 220H1000" fill="none" stroke="#e2e8eb" strokeWidth="1" />
          <path
            d="M0 220C80 220 130 205 170 140S215 45 240 55S285 180 350 190S450 155 500 160S620 200 670 140S730 28 760 40S810 150 850 180S950 220 1000 220L1000 220H0Z"
            fill="#1b49651a"
          />
          <path
            d="M0 220C80 220 130 205 170 140S215 45 240 55S285 180 350 190S450 155 500 160S620 200 670 140S730 28 760 40S810 150 850 180S950 220 1000 220"
            fill="none"
            stroke="#1b4965"
            strokeWidth="2.5"
            vectorEffect="non-scaling-stroke"
          />
          <path
            d="M0 220C140 220 170 200 205 110S240 75 260 125S300 215 420 215S620 200 700 75S760 80 790 140S860 218 1000 220"
            fill="none"
            stroke="#b66306"
            strokeWidth="2.5"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
        <div className={`${styles.cursor} ${peak === 'evening' ? styles.evening : ''}`} aria-hidden="true" />
      </div>
      <div className={styles.axis} aria-hidden="true">
        <span>06:00</span>
        <span>08:30</span>
        <span>12:00</span>
        <span>17:30</span>
        <span>21:00</span>
      </div>
      <p className={styles.explanation} id="peak-description" aria-live="polite">
        {peak === 'morning'
          ? 'Vârf de dimineață · O creștere ipotetică a fluxului de sosiri dinspre sud. Orice plan de organizare la suprafață trebuie să coreleze virajele, circulația tramvaielor și traversările pietonale.'
          : 'Vârf de seară · Un al doilea vârf ipotetic de cerere. Ipotezele de cerere sunt esențiale pentru dimensionarea pasajului subteran și a capacității giratoriului de suprafață; nu este asumat niciun rezultat din oficiu.'}
      </p>
      <figcaption className={styles.caption}>
        Cerere ilustrativă de trafic · Nu reprezintă măsurători de trafic reale sau rezultate de simulare validate
      </figcaption>
    </figure>
  );
}
