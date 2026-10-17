# Prompt pentru AI-ul care implementează interfața

Copiază textul de mai jos într-un agent cu acces la acest repository. Dacă nu vede fișierele, atașează README-ul principal, `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.md`, brief-ul și structura `frontend`.

---

Ești designer de produs senior și inginer frontend. Continuă ARTERIA by ARION din repository și construiește o interfață premium coerentă pentru web și Android. Lucrează în cod până când experiența este verificabilă. Extinde baza existentă, păstrează contractele și repară problemele descoperite. Nu regenera arbitrar proiectul.

## Citește înainte să scrii cod

1. `README.md`, documentele din `docs/`, README/STATUS din `frontend`, `backend`, `sim`.
2. `docs/frontend/DESIGN_BRIEF.md` și `docs/frontend/IMPLEMENTATION.md`.
3. `frontend/package.json`, aplicațiile web/mobile și pachetele shared.
4. Orice `AGENTS.md` aplicabil. Instrucțiunile utilizatorului au prioritate.

Backendul și simularea sunt inițial doar documentate. Nu pretinde că funcționează deja.

Folosește skillurile `frontend-design`, `ui-ux-pro-max`, `vercel-react-best-practices`, `vercel-react-native-skills`, dacă sunt disponibile, și `webapp-testing` pentru QA. Pentru skilluri absente consultă sursele publice:
- https://github.com/anthropics/skills/tree/main/skills/frontend-design
- https://github.com/vercel-labs/agent-skills

Inspectează skillurile înainte de utilizare; nu executa scripturi online necunoscute. Absența unui skill nu împiedică urmarea brief-ului local. Nu modifica instalările globale pentru a termina interfața.

## Produs

ARTERIA este un laborator de planificare urbană asistată de AI. Primul oraș este Iași, România. Utilizatorul explorează cartiere, inspectează mobilitatea și infrastructura, selectează o problemă susținută de date, cere alternative, validează un scenariu și compară efectele cu situația inițială.

Există exact trei componente principale: `frontend`, `backend`, `sim`. Webul și Androidul sunt în frontend. Nu adăuga un alt backend sau acces LLM în client.

## Stack și limite

- Web: React + TypeScript + Next.js App Router + MapLibre GL JS, Lucide, CSS cu tokenuri. Tailwind opțional, fără rescriere inutilă.
- Android: Expo + React Native + TypeScript, native-stack existent. Componente native, safe areas, Back nativ, minimum 48dp. Nu împacheta site-ul într-un WebView ca înlocuitor pentru aplicația nativă.
- Comun: `shared/core` pentru contracte/API/fixtures și `shared/tokens` pentru design. Fără DOM sau dependențe native în core. O singură versiune React compatibilă în workspace.
- Harta web este lazy-loaded. Configurează un stil autorizat și atribuirea lui; nu folosi tiles fără licență.
- `MapPlaceholder` este limita adaptorului nativ. Verifică MapLibre React Native față de Expo/RN instalate. Poate necesita development build; nu presupune suport Expo Go. Documentează pluginul, configurația și pașii.
- Fără secrete în `NEXT_PUBLIC_*` sau `EXPO_PUBLIC_*`.

## Direcție vizuală

„Atelier cartografic nocturn”: albastru mineral, contrast bun, hartă dominantă și inspector contextual. Urmează brief-ul și tokenurile existente. Manrope pentru citire, Space Grotesk pentru titluri; fonturi locale/gestionate, cu fallback.

Aspect specific Iașului și analizei urbane: străzi, cartiere, rețele, accesibilitate, dovezi și intervenții. Inspiră-te din organizarea GIS Felt, explorarea analitică kepler.gl și comparația ArcGIS Wayback. Consultă referințele înainte să susții că le-ai analizat; extrage principii, fără copierea identității.

Fără template AI: gradient mov-albastru decorativ, neon, sticlă peste tot, carduri identice, emoji de navigație, titluri umflate, formulări comerciale goale, cifre inventate sau animații pe fiecare element. Harta este elementul memorabil. În versiunea finală mută textul introductiv amplu din workspace după onboarding, ca să eliberezi harta.

Înainte de implementare, formulează un plan vizual scurt: compoziție, tipografie, culori și stări. Critică-l față de brief și corectează alegerile generice. Apoi implementează, fără oprire la plan.

## Ecrane și flux

Separarea rutelor este deja implementată: `/` pentru site-ul de prezentare, `/app` pentru produsul web. Păstrează-le în același proiect Next.js din `frontend/web`. Aplicația React Native este în `frontend/mobile`. Codul comun minim este în `frontend/shared`; documentația în `docs/frontend`. Nu recrea directoare `apps` sau `packages` și nu muta produsul peste pagina de prezentare. Prioritizează fluxul web complet; aplicația Android rămâne separată și se extinde ulterior.

### Web

1. Explorare: hartă Iași, selecție cartier/zonă validată, căutare în zonele disponibile, straturi și legendă. Desktop cu inspector lateral; mobil cu sheet accesibil sau panou în flux.
2. Analiză: indicatori cu valoare/unitate, status, sursă, metodă, dată și incertitudine. Probleme selectabile, localizabile pe hartă, care actualizează inspectorul.
3. Propuneri: minimală, moderată, transformatoare — intervenții, raționament, ipoteze, prerechizite și validare. Alternativele respinse sau indisponibile nu pot fi aplicate.
4. Scenariu: revizuirea intervențiilor acceptate, baseline imuabil, sumar modificări și solicitare de evaluare. Acțiuni dezactivate cu motiv când lipsesc datele obligatorii.
5. Comparație: baseline/scenariu cu același viewport și legendă, tabel cu valori, unități și delta reale. Slider numai pentru date comparabile, cu alternativă accesibilă la drag.
6. Simulare/replay: numai pentru înregistrări reale de la backend; mod, ID, timestamp și ipoteze vizibile. Playback-ul nu este o rulare nouă.

### Android

Aceleași sarcini cu ergonomie nativă: explorare, analiză, propuneri, scenariu și comparație. Aceeași ierarhie, paletă și vocabular, cu densitate și navigație adaptate. Fără miniaturizarea desktopului. Respectă rotația, fontul mărit, cititorul de ecran și Back.

## API și date

Folosește clientul tipizat și `docs/API_CONTRACT.md`:
- `POST /analyze`: zonă, straturi, parametri → indicatori, probleme, disponibilitate.
- `POST /propose`: analiză + problemă + catalog + constrângeri → alternative validate.
- `POST /evaluate`: baseline + intervenții acceptate → comparații și metadate de simulare.

Contractul este draft. `Issue` și metadatele extinse de simulare sunt provizorii. Cartierelor din baza UI le corespund repere de viewport, nu limite administrative verificate. Obține ID-urile reale din backend; nu trimite `preview-*` în live. Baseline-ul trebuie furnizat de backend printr-un contract agreat, nu dedus din ID-ul analizei. Adaugă validare runtime când schema backend este stabilă.

Păstrează `observed`, `calculated`, `estimated`, `unknown` distincte prin text și culoare. `null` apare cu motiv, niciodată ca `0`. Nu inventa scoruri, emisii, economii, încredere numerică sau rezultate SUMO. Estimările AI sunt ipoteze. Lipsa unui strat nu dovedește lipsa infrastructurii.

În demo poți adăuga fixtures deterministe pentru fluxul complet, dar ecranele trebuie marcate „Date demonstrative, nevalidate”. Nu pretinde că au fost calculate sau generate live. În live, eroarea API rămâne eroare, fără fallback ascuns la demo.

Implementează stările inițial/loading/empty/error/partial/unavailable/success. Anulează cererile depășite la schimbarea zonei; păstrează erorile lângă acțiune și oferă reîncercare. Fără butoane active care nu fac nimic.

## Verificare și livrare

- HTML semantic, focus vizibil, etichete și tastatură, anunțuri accesibile, informație textuală alternativă hărții.
- Contrast minimum 4.5:1 text, 3:1 controale. Statusurile nu depind doar de culoare.
- Fără overflow orizontal la 375px; verifică 768/1440px, landscape, text nativ mărit și safe areas.
- Mișcare scurtă, care explică schimbări; reduced motion. Fără progres numeric fals.
- Nu recrea harta la fiecare selecție; încarcă progresiv și virtualizează liste mari. Dependențele native rămân în aplicația mobilă.
- Rulează din `frontend`: `npm run check` și `npm run export:android --workspace @arteria/mobile`.
- Verifică webul în browser și fluxurile de navigație. Testează Android pe dispozitiv/emulator dacă este disponibil; precizează dacă ai validat doar TypeScript/Metro.
- Actualizează README/STATUS: ce merge, ce este demo și ce depinde de backend. Livrează codul și comenzile de pornire. Nu publica și nu crea servicii externe pentru această cerere locală.

Rezultatul cerut este interfața implementată și verificată în proiectul existent, nu o descriere sau o imagine.
