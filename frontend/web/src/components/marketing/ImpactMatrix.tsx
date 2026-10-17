import { interventions } from './intersection';
import styles from './ImpactMatrix.module.css';

const rows = [
  {
    name: interventions.underpass.label,
    existing: 'Vehiculele de pe direcțiile Est–Vest și Nord–Sud se întâlnesc în sensul giratoriu la nivel. Liniile de tramvai Nord–Sud traversează insula centrală.',
    proposed: 'Traficul de tranzit Est–Vest coboară într-un pasaj subteran direct sub intersecție, eliminând conflictul de tranzit la suprafață.',
    question: 'Evaluează pantele rampelor, gabaritul util al vehiculelor, capacitatea portantă a plăcii, sarcinile dinamice ale tramvaiului, condițiile geotehnice, devierea utilităților, drenajul pluvial și etapizarea șantierului.',
  },
  {
    name: interventions.surface.label,
    existing: 'Toate vehiculele care virează și cele de tranzit împart același sens giratoriu de suprafață.',
    proposed: 'Sensul giratoriu compact de suprafață amplasat pe placa podului acomodează toate virajele la stânga, la dreapta, întoarcerile și trecerile de tramvai în lățimea culoarului existent.',
    question: 'Evaluează capacitatea inelului giratoriu, cerințele de semaforizare în orele de vârf, vizibilitatea în curbă și siguranța traversărilor pietonale pe bretelele de acces.',
  },
];

export function ImpactMatrix() {
  return (
    <div className={styles.matrix}>
      <div className={styles.header}>
        <h3 className={styles.title}>Aceeași intersecție. Compromisuri explicite.</h3>
        <span className={styles.badge}>Comparație conceptuală · Efecte neevaluate</span>
      </div>
      <div className={styles.rows}>
        {rows.map(row => (
          <article className={styles.row} key={row.name}>
            <h4 className={styles.name}>{row.name}</h4>
            <dl className={styles.comparison}>
              <div>
                <dt>Situație existentă</dt>
                <dd>{row.existing}</dd>
              </div>
              <div>
                <dt>Propunere</dt>
                <dd>{row.proposed}</dd>
              </div>
            </dl>
            <p className={styles.question}>
              <span>De evaluat</span>
              {row.question}
            </p>
          </article>
        ))}
      </div>
      <p className={styles.footnote}>
        Sens giratoriu denivelat ilustrativ care necesită evaluare inginerească. Nici beneficiile de trafic, nici economiile de costuri sau fezabilitatea nu sunt stabilite din oficiu.
      </p>
    </div>
  );
}
