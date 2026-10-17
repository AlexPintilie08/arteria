# ARTERIA — direcție vizuală

## Produs

ARTERIA by ARION este un instrument de planificare urbană pentru explorarea Iașului, examinarea dovezilor și compararea intervențiilor. Public: echipe de urbanism, mobilitate și administrație, plus participanții la demonstrația de hackathon. Site-ul de prezentare este la `/`, cu acces clar la produs. Spațiul de lucru geografic este la `/app`, separat de mesajele de prezentare.

## Concept: atelier cartografic nocturn

Hartă mare, suprafețe de control din albastru mineral, tipografie precisă și o singură culoare de selecție. Personalitatea vine din geometria Iașului, ierarhia străzilor, numele locurilor și intervențiile inspectabile. Semnul ARTERIA actual este un placeholder geometric, nu o identitate de brand finală.

Paleta: fundal `#101820`, panou `#18232E`, suprafață ridicată `#213140`, text `#EDF2F6`, text secundar `#A8BAC9`, selecție `#8BC9ED`, contur `#42596A`, avertismente `#EFC47C`. Definite în `shared/tokens`; CSS și TypeScript se actualizează împreună.

Tipografie: Space Grotesk 500 pentru titluri scurte; Manrope 400/600 pentru conținut și controale, servite local pe web prin Fontsource. Native folosește momentan fonturile sistemului; versiunea finală poate încărca aceleași familii prin Expo Font.

Spațiere 4/8/16/24/32/48; rază controale 8, panouri 16, badge-uri capsulă. Controalele Android au minimum 48dp. Iconografie web Lucide, o singură grosime; native va primi o familie vectorială consecventă.

## Compoziție

Desktop: antet discret, navigație compactă în stânga, Dock de Control Stânga (320px) pentru configurare zonă și straturi, Hartă dominantă centrală, și Deck Orizontal de Telemetrie & Inspecție pe toată lățimea sub hartă (stil Remix/Kepler.gl). Se elimină bara înghesuită pe dreapta. Pe ecrane mici: dock-ul stânga și deck-ul orizontal se adaptează într-un flux vertical fără defilare orizontală.

```text
┌ ARTERIA                 Iași, România                     mod date ┐
├───────┬─────────────────┬──────────────────────────────────────────┤
│       │ DOCK STÂNGA     │         CANVAS CENTRAL DIGITAL TWIN      │
│ Explor│ (320px)         │               (Hartă Iași)               │
│       │                 │                                          │
│ Scenar│ - Selecție zonă │                                          │
│       │ - Straturi date ├──────────────────────────────────────────┤
│ Compar│ - Buton Diagnoză│ DECK ORIZONTAL TELEMETRIE & REZULTATE     │
│       │                 │ [Indicatori] | [Senzori] | [Probleme]    │
└───────┴─────────────────┴──────────────────────────────────────────┘
```

Android: explorare cu hartă, selectare zonă, indicatori, scenarii și comparație în ecrane native. Navigație înapoi reală și deep links. Nu importa DOM sau `maplibre-gl` în React Native. Limbaj vizual comun, implementări separate pe platforme.

## Date și comportament

- `observed`, `calculated`, `estimated`, `unknown` au etichetă textuală; culoarea este suplimentară.
- Lipsa unei valori apare ca „—” și motiv, niciodată `0` sau progres inventat.
- Indicatorii permit inspectarea sursei, metodei, datei, unității și incertitudinii.
- Alternativele minimală / moderată / transformatoare rămân ipoteze până la validare și evaluare.
- Replay, rulare live, calcul geografic și estimare AI sunt distincte.
- Stări reale: inițial, încărcare, eroare cu reîncercare, date parțiale, succes, indisponibil. Fără fallback automat din live în demo.
- Schimbarea zonei anulează cererea și elimină rezultatele vechi.

## Ce eliminăm

Gradient mov-albastru decorativ, neon, glassmorphism peste tot, bento cu carduri identice, titluri de marketing peste hartă, all-caps excesiv, emoji ca iconuri, testimoniale inventate, procente de impact fabricate, animații permanente, umbre sub fiecare element și butoane fără efect. Mișcarea explică acțiunile utilizatorului.

## Referințe cercetate

- [Felt](https://felt.com/): organizarea experienței GIS în jurul hărții; nu copia brandingul sau afirmațiile comerciale.
- [kepler.gl](https://kepler.gl/) și [ArcGIS Wayback](https://livingatlas.arcgis.com/wayback/): referințe de explorat pentru analiză și comparație temporală. Paginile dinamice nu au oferit detalii UI prin cercetarea textuală; consultă-le vizual înainte de a atribui un comportament concret.
- [Anthropic Frontend Design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) și [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills): surse publice de skilluri pentru agentul care continuă.
- [Expo monorepos](https://docs.expo.dev/guides/monorepos/) și [MapLibre React Native](https://maplibre.org/maplibre-react-native/docs/setup/getting-started/): integrare tehnică.

Skillurile locale Frontend Design, UI/UX Pro Max, React Best Practices și React Native Skills au fost consultate. Prima căutare UI/UX Pro Max a întors greșit un sistem pentru nunți și a fost respinsă. Căutarea restrânsă pe produs a identificat Analytics Dashboard, recomandând explorare detaliată, comparație și hărți termice; aceste principii sunt relevante. Paleta și fonturile sunt decizii proprii bazate pe brief, nu un rezultat validat al bazei de date.

## Criterii pentru versiunea finală

Verifică 375/768/1440px, landscape, tastatură, cititor de ecran, text nativ mărit, safe areas și reduced motion. Contrast minimum 4.5:1 pentru text obișnuit și 3:1 pentru controale. Oferă informația esențială a hărții și în panouri. Păstrează atribuirea furnizorului. Exportul Metro nu înlocuiește testul Android pe dispozitiv.
