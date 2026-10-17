import Link from 'next/link';
import { ArrowDown, ArrowRight, Clock3, Info, Network, Ruler, Scale } from 'lucide-react';
import type { ReactNode } from 'react';
import { UrbanScene } from '../components/marketing/UrbanScene';
import { DemandChart } from '../components/marketing/DemandChart';
import { JunctionPlan, UnderpassSection } from '../components/marketing/JunctionPlan';
import { ImpactMatrix } from '../components/marketing/ImpactMatrix';
import styles from './page.module.css';

function AppLink() {
  return (
    <Link href="/app" className={styles.primary}>
      Deschide aplicația <ArrowRight size={18} aria-hidden="true" />
    </Link>
  );
}

function Brand() {
  return (
    <a href="#overview" className={styles.brand}>
      ARTERIA <span className={styles.byline}>by ARION</span>
    </a>
  );
}

function Navigation({ footer = false }: { footer?: boolean }) {
  return (
    <nav className={footer ? styles.footerNav : styles.navigation} aria-label={footer ? 'Navigație subsol' : 'Navigație principală'}>
      <a className={styles.navLink} href="#overview">Prezentare generală</a>
      <a className={styles.navLink} href="#workflow">Flux de lucru</a>
      <a className={styles.navLink} href="#evidence">Fundamente & Dovezi</a>
      {footer && <a className={styles.navLink} href="#development">Note de dezvoltare</a>}
    </nav>
  );
}

function Chapter({ label, title, children }: { label: string; title: string; children: ReactNode }) {
  return (
    <div className={styles.chapterIntro}>
      <p className={styles.eyebrow}>{label}</p>
      <h2 className={styles.sectionTitle}>{title}</h2>
      <p className={styles.description}>{children}</p>
    </div>
  );
}

const foundations = [
  {
    Icon: Ruler,
    title: '1. Geometrie observată a rețelei',
    text: 'Pornește de la datele disponibile despre străzi și clădiri. Fluxul planificat înregistrează sursa, acoperirea și data colectării, astfel încât geometria lipsă să rămână vizibilă în loc să devină o presupunere.',
  },
  {
    Icon: Clock3,
    title: '2. Scenarii sintetice de cerere',
    text: 'Explorează ipoteze despre navetiști, ore de vârf școlare și transport public. Cererea sintetică trebuie etichetată cu ipotezele sale; nu reprezintă o observare a traficului real.',
  },
  {
    Icon: Network,
    title: '3. Simulare cu feedback de rețea',
    text: 'Evaluarea planificată combină indicatori geografici cu simulare de trafic opțională când rețeaua și cererea o susțin. Rezultatele vor include metodele, incertitudinile și detaliile de rulare.',
  },
];

export default function HomePage() {
  return (
    <div className={styles.site} lang="ro">
      <a className={styles.skip} href="#presentation">Sari la prezentare</a>

      <header className={styles.header}>
        <div className={styles.headerInner}>
          <Brand />
          <Navigation />
          <AppLink />
        </div>
      </header>

      <main id="presentation" tabIndex={-1}>
        <section className={styles.hero} id="overview" aria-labelledby="hero-title">
          <div className={`${styles.container} ${styles.heroGrid}`}>
            <div className={styles.heroIntro}>
              <h1 id="hero-title" className={styles.heroTitle}>Un oraș se schimbă. Mai întâi, îl înțelegem.</h1>
              <p className={styles.heroDescription}>
                Explorează modele de trafic, testează modificări geometrice pe străzi și intersecții și compară scenarii înainte de șantier.
              </p>
              <div className={styles.actions}>
                <AppLink />
                <a className={styles.secondary} href="#workflow">
                  Vezi cum funcționează <ArrowDown size={18} aria-hidden="true" />
                </a>
              </div>
              <p className={styles.status}>Prototip de planificare · Analiza și simularea sunt în dezvoltare.</p>
            </div>
            <UrbanScene />
          </div>
        </section>

        <section className={styles.section} id="workflow">
          <div className={styles.container}>
            <Chapter label="Capitolul 01 — Tipare zilnice" title="Înțelege când și unde se aglomerează traficul.">
              Condițiile de trafic se schimbă pe parcursul zilei. Fluxul de lucru explorează cererea de dimineață și de seară pentru a examina unde un coridor își atinge capacitatea.
            </Chapter>
            <DemandChart />
          </div>
        </section>

        <section className={`${styles.section} ${styles.alternate}`}>
          <div className={styles.container}>
            <Chapter label="Capitolul 02 — Sandbox geometric" title="Explorează o geometrie diferită.">
              Aceeași intersecție, în plan și secțiune. Sensul giratoriu la sol existent servește drept bază; alternativa ilustrativă coboară traficul de tranzit Est–Vest într-un pasaj subteran sub un giratoriu compact de suprafață ce permite toate virajele la stânga, la dreapta și întoarcerile.
            </Chapter>
            <div className={styles.junctionGrid}>
              <figure className={styles.junctionCard}>
                <div className={styles.cardHeader}>
                  <h3 className={styles.panelTitle}>Situație existentă (Baseline)</h3>
                  <span className={styles.smallLabel}>Geometrie curentă</span>
                </div>
                <p className={styles.cardDescription}>
                  Ambele artere principale se întâlnesc în sensul giratoriu existent la nivelul solului. Liniile de tramvai Nord–Sud traversează insula centrală. Trotuarele și trecerile de pietoni la nivel deservesc fiecare acces.
                </p>
                <div className={styles.planFrame}>
                  <JunctionPlan layout="existing" />
                </div>
                <figcaption className={styles.caption}>
                  <span>Aceeași intersecție · Vedere în plan</span>
                  <span>Geometrie de bază</span>
                </figcaption>
              </figure>
              <figure className={`${styles.junctionCard} ${styles.proposal}`}>
                <div className={styles.cardHeader}>
                  <h3 className={styles.panelTitle}>Sens giratoriu denivelat</h3>
                  <span className={styles.smallLabel}>Giratoriu pe două niveluri</span>
                </div>
                <p className={styles.cardDescription}>
                  1. Pasaj subteran Est–Vest: două rampe de acces coboară într-o cale de tranzit subterană ce ocolește complet intersecția. 2. Sens giratoriu de suprafață: inel compact amplasat pe placa podului ce acomodează toate virajele la stânga și trecerea tramvaiului fără teren urban suplimentar.
                </p>
                <div className={styles.planFrame}>
                  <JunctionPlan layout="proposed" />
                </div>
                <UnderpassSection />
                <figcaption className={styles.caption}>
                  <span className={styles.tealText}>1. Pasaj subteran Est–Vest · 2. Giratoriu de suprafață & viraje la stânga</span>
                  <span>Necesită evaluare inginerească</span>
                </figcaption>
              </figure>
            </div>
          </div>
        </section>

        <section className={`${styles.section} ${styles.dark}`}>
          <div className={styles.container}>
            <Chapter label="Capitolul 03 — Compromisuri obiective" title="Compară consecințele.">
              Separarea fluxurilor de tranzit schimbă structura intersecției, accesul și fluxurile pietonale. Compară ce este ilustrat cu ce necesită evaluare inginerească; niciun beneficiu nu este asumat din oficiu.
            </Chapter>
            <ImpactMatrix />
            <div className={styles.modelingNote}>
              <Scale size={24} aria-hidden="true" />
              <div>
                <h3 className={styles.noteTitle}>Principiul modelării oneste</h3>
                <p className={styles.noteText}>
                  O propunere AI este o ipoteză, nu o măsurătoare. Doar calculele validate sau rulările de simulare înregistrate pot stabili un efect evaluat.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className={styles.section} id="evidence">
          <div className={styles.container}>
            <Chapter label="Fundamente" title="Dovezi și ipoteze de modelare.">
              O planificare utilă pornește de la geometrie observată și ipoteze transparente. Datele observate, calculele, estimările și necunoscutele trebuie să rămână distincte.
            </Chapter>
            <div className={styles.foundations}>
              {foundations.map(({ Icon, title, text }) => (
                <article key={title}>
                  <div className={styles.iconBox}>
                    <Icon size={24} aria-hidden="true" />
                  </div>
                  <h3 className={styles.foundationTitle}>{title}</h3>
                  <p className={styles.foundationText}>{text}</p>
                </article>
              ))}
            </div>
            <aside className={styles.prototypeNote} id="development">
              <Info size={24} aria-hidden="true" />
              <div>
                <h3 className={styles.noteTitle}>Prototip activ de planificare</h3>
                <p className={styles.noteText}>
                  ARTERIA este în dezvoltare, cu Iașul ca prim oraș pilot. Spațiul de lucru conectează SIM v3 pentru analiza pietonală a grafurilor OpenStreetMap și compararea unor legături ipotetice. Propunerile AI în cloud, măsurătorile reale de trafic și simularea SUMO pentru zone reale nu sunt disponibile. Diagramele și comparațiile de pe această pagină sunt ilustrative; nu este implicată o integrare municipală sau o performanță măsurată.
                </p>
              </div>
            </aside>
          </div>
        </section>

        <section className={`${styles.section} ${styles.alternate} ${styles.cta}`}>
          <div className={styles.ctaInner}>
            <h2 className={styles.ctaTitle}>Ești gata să explorezi spațiul de planificare?</h2>
            <p className={styles.heroDescription}>
              Explorează spațiul de lucru inițial și fundamentele unui proces de planificare mai transparent.
            </p>
            <AppLink />
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <div className={styles.container}>
          <div className={styles.footerTop}>
            <div className={styles.footerAbout}>
              <Brand />
              <p className={styles.footerDescription}>
                Un prototip de planificare urbană pentru explorarea intervențiilor geometrice și a compromisurilor de rețea.
              </p>
            </div>
            <Navigation footer />
          </div>
          <div className={styles.footerBottom}>
            <span>© 2026 ARION · Toate modelele sunt ilustrative.</span>
            <span>Primul oraș: Iași, România</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
