# ARTERIA — cercetare completă pentru pitch

Audit al checkout-ului local, 17–18 octombrie 2026. Produs: **ARTERIA by ARION**. Limbă de prezentare: română, păstrată din ambele prezentări și din ghidul de pitch. Acest document precedă reconstrucția PPTX și este sursa de adevăr pentru conținut. Nu reprezintă o certificare inginerească sau o validare de piață.

## 1. Rezumat executiv

ARTERIA propune un laborator de planificare urbană pentru echipele de mobilitate: alegerea unei zone din Iași, examinarea problemelor, compararea intervențiilor și, în viitor, evaluarea lor pe date geografice și simulări reproductibile. Ideea centrală este să explici o decizie înainte de implementarea fizică. Beneficiarii indirecți pot fi locuitorii și utilizatorii transportului public; utilizatorul profesional vizat este specialistul în mobilitate/urbanism. Nu există interviuri sau acorduri de pilot verificate.

Checkout-ul conține un **prototip de interfață web funcțional**, o bază Android, un API FastAPI minimal, un server demonstrativ separat și utilitare de verificare geospațială/SUMO. Fluxul web explorează repere, selectează probleme predefinite, schimbă alternative și ajustează valori prin aritmetică locală. Nu există un flux urban real complet de la OSM → analiză → LLM → validare geometrică → scenariu → evaluare SUMO.

Constatarea decisivă: mai multe fișiere STATUS și prezentarea veche confundă valori scrise în cod cu observații și rezultate calculate pe o rețea reală. Auditul nu a găsit fișiere de măsurători, grafuri Iași pregătite, rapoarte de calibrare sau artefacte de rulare care să susțină acele etichete. Prezentarea finală trebuie să arate produsul și planul, cu statutul demonstrativ vizibil, fără procente de reducere a traficului, venituri realizate sau parteneriate declarate.

## 2. Metodă, acoperire și limite

S-au inspectat README-ul principal; toate cele 24 de fișiere Markdown de produs/configurație enumerate în repository înaintea acestei livrări; `.github/workflows/ci.yml`; skill-ul local `.agents/skills/pptx/SKILL.md`; configurațiile Python/npm/Expo/Next; toate modulele Python din backend, sim și tests; scripturile de bootstrap/check/dev; contractele și fixtures shared; componentele web de hartă, analiză, scenarii, comparație și marketing; ecranele mobile; prezentările și generatorul existent. Fișierele mari de lock au fost folosite ca metadate de dependențe, nu ca implementare. Au fost excluse `node_modules`, `.next`, cache-uri și pachete generate din auditul surselor.

Citirea a urmărit dependențele reale și apelurile, nu doar formulările din documente. S-au inspectat toate cele 16 slide-uri ale șablonului prin export PowerPoint și toate cele 16 previzualizări existente ale versiunii populate; s-a extras textul slide cu slide în fișierele `*.inspection.json`. Nu s-au citit valori din fișiere private `.env` și nu s-au inclus secrete în documente.

Niveluri de certitudine: **ridicat** = cod direct inspectat sau comandă executată; **documentat** = afirmație de proiect fără jurnal independent curent; **ipoteză** = propunere de produs/business; **neconfirmat** = lipsesc sursa și/sau validarea. „Implementat” descrie codul disponibil, fără a implica utilizare în producție.

## 3. Contextul hackathonului și regulile de pitch

Nu există în checkout un regulament oficial separat, o grilă de punctaj sau o confirmare a duratei alocate echipei. Numele evenimentului provine din repository și din prezentarea existentă; nu a fost validat independent ca denumire oficială.

Backup-ul `docs/ppt/Template-Pitch-Hackathon.backup.pptx` este un ghid în română realizat de Andrei Margelatu. Slide-ul 2 cere copierea slide-urilor de pitch în aceeași ordine, **zece slide-uri plus anexe**, înlocuirea parantezelor și eliminarea ghidajului. Slide-ul 3 spune că ordinea nu se negociază, doar timpul se ajustează. Ordinea: titlu; omul și durerea; dovezi și alternative; soluție; demo; construcție; cine plătește; piață și primii clienți; echipa; ce urmează și cererea. Pentru varianta de trei minute, piața poate fi sărită/mutată în anexe; pentru cinci minute se păstrează. Duratele sunt prescripții ale ghidului, nu dovada programului real al evenimentului.

Se recomandă păstrarea tuturor celor zece secțiuni într-un pitch de cinci minute și trei anexe după încheiere. Nu se păstrează paginile de instruire ca slide-uri pentru juriu. Nu s-au identificat logo-uri obligatorii de organizatori, reguli de master sau un număr total impus de 16: cele 16 pagini includ ghidaj. Pictogramele mici din template sunt decor/instrucțiuni, nu identitate instituțională. Se păstrează dimensiunile de 13⅓ × 7½ inch, ordinea și structura P·R·O·B·A. Lipsesc dovada obligatorie a trei urme independente de nevoie, interviul real, prețul validat și lista de zece clienți. Aceste lipsuri se declară; nu se completează fictiv.

## 4. Problema și dovezile disponibile

### Problema propusă

Un specialist care discută o intervenție urbană trebuie să compare efectele în aceeași zonă și să explice sursa datelor, metoda și limitele. Documentele proiectului urmăresc accesibilitatea, continuitatea velo, transportul public, parcarea și spațiile verzi, nu numai semaforizarea. Reducerea produsului la un optimizator de semafoare, cum face deck-ul populat, pierde scopul README-ului și nu este susținută de implementare.

### De ce contează

Deciziile de infrastructură afectează grupuri cu nevoi diferite. O comparație inspectabilă poate ajuta discuția dintre administrație, consultanți și operatori, dar nu există în repository o măsurare a timpului economisit sau a calității deciziei. Consultarea PMUD publicată de Primăria Iași confirmă existența unui proces local de planificare a mobilității; nu dovedește că specialiștii ar cumpăra ARTERIA.

Surse primare consultate online la audit:

- [Primăria Iași — consultare publică PMUD](https://www.primaria-iasi.ro/dm_iasi/portal.nsf/pagini/consultare%2Bpublica%2Bplanul%2Bde%2Bmobilitate%2Burbana%2Bdurabila%2Bpentru%2Bpolul%2Bde%2Bcrestere%2Biasi%2Bpmud%2Biasi-0002E4D6?Open%3FOpen=): context instituțional, nu statistici de congestie și nici dovadă de adopție.
- [QGIS — overview](https://www.qgis.org/project/overview/): alternativă GIS pentru vizualizarea și analiza datelor geografice. Nu s-a efectuat un benchmark comparativ.
- [Eclipse SUMO — documentație](https://sumo.dlr.de/docs/): simulator de trafic, utilizabil și independent de ARTERIA.
- [SUMO — Calibrator](https://sumo.dlr.de/docs/Simulation/Calibrator.html): explică adaptarea fluxurilor și vitezelor la măsurători. Susține necesitatea unor intrări/calibrări explicite, nu performanța produsului nostru.

Nu s-au găsit surse verificabile pentru 42 min/navetist, 12 milioane euro pierderi, emisii de 3,2 ori mai mari, 85→56 secunde, reducere de 34%, economie de 32.000 euro, costuri generale SCADA sau studii de 18 luni. Nu se reproduc ca fapte. Citatul unui presupus inginer din deck nu are interviu, dată, consimțământ sau sursă; este eliminat.

## 5. Public, actori și alternative

Utilizator primar vizat: inginer/analist de mobilitate sau urbanist care pregătește o comparație. Cumpărător posibil: administrație locală sau birou de consultanță. Operatorul de transport poate furniza cerințe/date. Locuitorii, pietonii și bicicliștii sunt beneficiari potențiali, nu utilizatori validați. Primăria Iași și CTP sunt ținte de conversație, fără acord comercial sau tehnic demonstrat.

Alternative reale: QGIS pentru lucru GIS, SUMO pentru modelare microscopică, procese de studiu și documentare PMUD pentru evaluări instituționale. Nu se afirmă că QGIS/SUMO nu pot compara scenarii sau că toate studiile sunt lente. Diferențierea propusă este integrarea unui parcurs de decizie accesibil, cu surse și incertitudini, nu inventarea unor algoritmi superiori. Fluxurile actuale ale utilizatorilor, costul integrării manuale și disponibilitatea de plată trebuie cercetate prin interviuri.

## 6. Soluția și parcursul real al utilizatorului

Viziune: utilizatorul alege o zonă, vede dovezi, cere alternative constrânse, aplică intervenția și compară indicatori. Propunerile AI ar trebui tratate ca ipoteze până la validare și evaluare.

Parcursul web existent (`frontend/web/src/features/workspace/Workspace.tsx`):

1. `/` prezintă produsul și un model conceptual de intersecție; `/app` deschide spațiul de lucru.
2. Utilizatorul alege un reper din Copou, Centru, Podu Roș, Tătărași, Alexandru cel Bun. Acestea nu sunt limite administrative verificate.
3. Checkbox-urile selectează straturi pentru cererea viitoare; nu activează seturi analitice corespunzătoare pe hartă.
4. În mod implicit `demoMode` este activ dacă `NEXT_PUBLIC_DEMO_MODE` nu este exact `false`. Analiza demonstrativă returnează indicatori necunoscuți, iar problemele sunt apoi selectate din fixtures locale.
5. Selectarea problemei permite inspectarea a trei alternative predefinite. Sliderele modifică parametrii locali.
6. Aplicarea scenariului schimbă starea React și deschide comparația. Nu creează o rețea urbană modificată pe server.
7. Comparația folosește tabelul static al problemei și ajustări aritmetice locale. Copierea raportului și exportul JSON sunt funcții browser; nu există PDF/GeoJSON generat pe backend.

Browserul a fost deschis pe build-ul local, s-au selectat Podu Roș și previzualizarea, apoi editorul de scenarii. Etichetele observate includ „Previzualizare de interfață” și „SUMO: nicio rulare”, dar și „Date Observate”, „Catalog validat” și afirmații despre măsurători. Aceste ultime formulări depășesc dovezile din cod. Capturile rămân autentice; deck-ul adaugă explicit că datele sunt demonstrative.

## 7. Inventar complet de funcționalități

| Funcționalitate | Stare reală | Dovezi și limite |
|---|---|---|
| Site de prezentare | Implementat | `frontend/web/src/app/page.tsx`; model conceptual Three.js, tabele și grafice ilustrative |
| Hartă web | Implementat ca vizualizare | `features/map/MapViewport.tsx`: raster OSM, pitch, navigare, contururi/coridoare/pini din fixtures |
| Cinci repere Iași | Implementat | `frontend/shared/core/fixtures.ts`; orientative, nu cadastru |
| Selectarea straturilor | UI + cerere | `Workspace.tsx`; nu analiză independentă pentru fiecare strat |
| Indicatori cu statut/surse | Model de date + UI parțial | `contracts.ts`, `EvidenceBadge.tsx`, `AnalysisPanel.tsx`; sursele scrise în fixtures nu sunt dovezi de achiziție |
| Probleme și trei niveluri | Catalog demonstrativ | `fixtures.ts`, `ScenarioPanel.tsx`; fără detecție reală sau validare geometrică |
| Reglaje și comparație | Implementat demonstrativ | `ComparisonPanel.tsx`; formule euristice pe valori fixe |
| Export raport | Clipboard + JSON local | `handleCopyReport`, `handleDownloadJson`; nu PDF/GeoJSON persistent |
| Client API | Implementat, tipizat | timeout, anulare, erori; fără validare runtime JSON |
| API FastAPI | `/health` | `backend/main.py`; POST-urile lipsesc intenționat în acest app |
| Server HTTP alternativ | 3 POST demonstrative + health | `backend/server.py`; un singur dataset, fără calcul OSM/LLM |
| AI generativ | Planificat | arhitectură și contracte; zero apeluri provider în implementarea inspectată |
| Reguli Pydantic/geometrie | Planificate | importul/dependența nu constituie validare a intervențiilor |
| NetworkX | Smoke test sintetic | graf a-b-c, 200 m; fără date Iași |
| SUMO/TraCI | Utilitar smoke real condiționat | `sim/sumo_support.py`; o rețea temporară cu un vehicul și un pas; fără legătură UI |
| Android | Scaffold | Expo/RN, navigație/ecrane; hartă placeholder, fără propuneri/evaluări reale |
| Auth, salvare, partajare | Contracte propuse | `api-specs/auth-endpoints.md`, `scenario-persistence-endpoints.md`; fără implementare |
| SSE și replay SUMO | Contract propus | `api-specs/simulation-engine-contract.md`; fără job runner/artefacte replay |
| Accesibilitate | Mecanisme implementate | etichete, focus, slider ARIA, reduced motion; fără audit complet WCAG independent |

## 8. Arhitectura sistemului

Există trei componente principale, conform `docs/ARCHITECTURE.md`: frontend, backend și sim. Web/mobile/shared sunt subcomponente frontend, nu servicii suplimentare. Arhitectura intenționată: frontend → backend → sim, iar backend → provider LLM. Frontendul nu trebuie să calculeze rezultate autoritative și nu trebuie să dețină chei LLM.

Arhitectura actuală are o ruptură explicită: UI-ul web demonstrativ consumă fixtures local; clientul poate apela `/analyze` dacă demo e dezactivat; `/propose` și `/evaluate` există în client, dar nu sunt apelate de componentele scenarii/comparație. FastAPI și serverul stdlib sunt două entry point-uri incompatibile, nu două straturi ale aceluiași API. Backendul nu importă sim pentru analiză/evaluare. Diagrama pitch-ului trebuie să deseneze relațiile viitoare cu linie întreruptă și să numească starea actuală.

## 9. Backend — detalii de implementare

`backend/main.py` creează FastAPI v0.1.0 cu `GET /health`. CORS permite GET/OPTIONS și originile din settings; implicit acestea sunt pe 5173, în timp ce Next rulează pe 3000. Nu există scheme Pydantic de analiză/intervenții, rutare auth, DB, cache, LLM sau jobs în acest fișier.

`backend/server.py` este un HTTPServer stdlib sincron pe portul 8000, bind `0.0.0.0`, CORS `*`. `DATASETS` conține numai cheia `podu-ros`. `_handle_analyze` elimină prefixul `preview-`, dar orice zonă necunoscută primește dataset-ul Podu Roș, păstrând zona cerută în răspuns. Nu validează limite, CRS, geometrie, mărime sau proveniență. `_handle_propose` citește `problem_id`, deși clientul definește `issue_id`; returnează aceleași alternative, metadate `rule-catalog-v1`, zero tokeni și `validation.passed = True` constant. `latency_ms: 15` este literal, nu benchmark. `_handle_evaluate` citește `alternative`, deși contractul clientului folosește `alternative_level`; valorile sunt extrase din tabel, iar delta se calculează prin scădere. O alternativă necunoscută selectează implicit coloana transformatoare. Nu există implementare Webster/HCM în backend.

Cinci probe directe pe handlere au confirmat dataset identic Copou/Podu Roș și faptul că `alternative_level: minimal` selectează `moderate`. Rezultatele brute sunt în `docs/ppt/backend-audit-probes.json`. Acestea sunt **probe la nivel de handler**, nu teste HTTP: socket-ul localhost a fost restricționat în sandbox. Nu se extrapolează la robustețe sau performanță.

## 10. Frontend — detalii și decizii

`frontend/web/package.json` declară Next 16.4.2, React 19.3.0, MapLibre 6.14.0 și Three 0.186.1. TypeScript este ~5.9.3 în workspace. Nu există Tailwind/shadcn în dependențele web inspectate. `frontend/mobile/package.json` declară Expo ~58.0.14 și React Native 0.88.0. Python cerut este >=3.12,<3.13; OSMnx >=2,<3; SUMO/TraCI/sumolib sunt fixate la 1.28.0. Sunt valori declarate ale checkout-ului, nu afirmații despre ultimele versiuni publice.

App Router separă marketingul de produs. Harta este încărcată cu `next/dynamic`, SSR dezactivat. MapLibre primește un worker local, ResizeObserver și cleanup; folosește acum tile-uri raster `tile.openstreetmap.org`, nu stilul OpenFreeMap descris în unele README-uri. Contururile/coridoarele sunt coordonate scrise manual în fixtures. Nu se vede extragere de clădiri 3D sau analiză GIS în acel modul. Three.js desenează o intersecție conceptuală pe pagina de prezentare; aceasta nu este un digital twin cadastral/calibrat.

Clientul shared trimite JSON, elimină slash-ul final din base URL, propagă AbortSignal și timeout de 30 secunde, parsează erorile și nu transformă un HTTP eșuat în succes demo. TypeScript asigură tipuri la compilare; `response.json() as T` nu validează la runtime. Schimbarea reperului anulează analiza și golește rezultatele, dar unele stări/parametri de scenariu persistă. Checkbox-urile nu controlează toate straturile vizuale sugerate.

Comparația pornește din `selectedIssue.comparisonData`. Pentru întârziere/coadă adaugă `(greenDelta * -0.25) - (ctp ? 5.5 : 0)`; pentru debit/capacitate `(greenDelta * 8) + (ctp ? 120 : 0)`; pentru velo `(laneWidth - 2) * 0.12`. Aplică factori de încărcare și limitează minimul. Aceste euristici nu sunt dovada unei implementări validate a formulelor Webster/HCM. Exportul JSON și raportul copiat folosesc tabelul de bază și factorul de încărcare, dar omit ajustările de tuning folosite pe ecran, deci pot diferi de valori afișate. Este o limitare materială pentru un dosar tehnic; nu se modifică aici funcționalitatea produsului.

## 11. AI — ce face și ce nu face

Niciun provider LLM nu este apelat în sursele backend/frontend inspectate. Alternativele sunt catalog fix, iar numele de modele din exemplele `api-specs` nu dovedesc integrare. Nu se declară „AI în producție”, RAG, fine-tuning, învățare din trafic sau generare liberă funcțională. Utilizarea AI la scrierea codului nu poate fi cuantificată sau atribuită pe module din Git; vechiul deck nu este probă pentru procente de autorie.

Planul tehnic bine definit în `docs/ARCHITECTURE.md`: backendul selectează un context minim de dovezi și catalog, cere răspuns structurat cu alternative, validează schema și constrângerile, solicită confirmarea specialistului și calculează efectele separat. Modelul generează ipoteze; sim produce măsurători. Cloud LLM este calea propusă, Qwen local un fallback posibil. Până la implementare, „asistat de AI” descrie direcția produsului. Această lipsă poate afecta eligibilitatea într-un hackathon AI; regulamentul complet nu este disponibil pentru a decide.

## 12. Date, contracte și API-uri

Contractele vizează coordonate `[longitudine, latitudine]`, EPSG:4326 pentru transport, CRS metric potrivit pentru calcule, metadata sursă/versiune/timp/metodă și stări observed/calculated/estimated/unknown. Aceste convenții sunt un avantaj de design; aplicarea lor nu este completă.

Diferențe concrete: clientul așteaptă `proposal_set_id`, `model`, `validation` per alternativă, intervenții obiect și expected_impacts; serverul returnează `proposal_run_id`, `model_metadata`, validare globală și stringuri. Evaluarea clientului așteaptă `comparisons` și metadata simulării; serverul returnează `metrics`. Issue în client are `label`, `indicator_ids`, `geometry` și Evidence; serverul are `title`, `supporting_indicator_id`, `coordinates` fără acea structură. `layer_availability` folosește `available` în server, în afara enumului EvidenceStatus. `api-specs` folosesc și `/api/v1/*`, deși serverele implementează căi fără prefix. Contractele auth/areas/simulation/persistence sunt propuneri, nu endpoint-uri disponibile.

Datele 2180 veh/h, 340 m, 74,2 s/vehicul și impacturile pe cartiere sunt literali. Nu s-au găsit fișiere brute de senzori, licențe/acorduri de acces sau notebook-uri de calcul. Metadata de proveniență și intervalele de încredere din literal nu devin automat măsurători. Ele pot fi arătate numai ca fixtures demonstrative, fără beneficii reale revendicate.

## 13. Componenta sim

`sim/smoke_test.py` importă OSMnx/GeoPandas/Shapely și calculează calea a→b→c pe un graf sintetic, cu lungimi 120, 80 și 300. Rezultatul așteptat este 200 m. Nu se descarcă OSM și nu se calculează conectivitatea cartierelor.

`sim/sumo_support.py` caută `sumo` și `netconvert` în PATH/SUMO_HOME, identifică pachetele Python și, când disponibile, generează o rețea temporară, o rută și un vehicul, rulează netconvert și avansează TraCI un pas. Acesta este un smoke real de simulator, dar nu validează geometria Podu Roș, cererea de vârf sau efecte Before/After. STATUS raportează treceri pe Windows/macOS ARM și fallback Intel; jurnalele CI externe nu au fost recitite. Nu s-a rerulat SUMO în runtime-ul auditului, deoarece pachetele/binarul proiectului nu erau disponibile.

## 14. Teste și validare

La audit au trecut **5/5 teste Node** din `frontend/shared/tests/api.test.ts`: nume wire/dovezi păstrate cu fetch mock, erori și request ID, HTML 503 tratat ca eșec, anulare și fixture unknown. Aceste teste nu probează interoperabilitatea cu serverul demonstrativ. Typecheck a trecut pe web/mobile/shared. Build-ul Next a trecut: `/` și `/app` prerenderate. Prima încercare de build a întâlnit EPERM la scrierea unui director generat; rerularea autorizată în afara sandboxului a trecut.

În Python sunt cinci teste definite: health, absența POST-urilor în FastAPI, CORS local, graf sintetic, discovery SUMO_HOME. Runtime-ul disponibil pentru audit nu are fastapi/httpx/pytest/geospațial/traci și nu există `.venv` în checkout; testele Python nu au fost rerulate. Nu s-au instalat global dependențe și nu s-a pretins o rulare proaspătă. `scripts/health_smoke.py` pornește uvicorn și testează doar health, nu POST-urile stdlib.

`shared/tests/browser-smoke.cjs` este un script existent cu capturi responsive, tastatură și asserts. Nu a fost rerulat integral; unele heading-uri din script nu mai corespund UI-ului actual. Capturile din `frontend/.qa` sunt istorice și nu se folosesc drept dovadă a UI-ului actual. S-au făcut verificări manuale prin browserul conectat pe aplicația locală și capturi noi în `docs/ppt/assets`. Nu există măsurători FPS, latențe end-to-end, test de sarcină, test Android pe dispozitiv sau audit WCAG complet curent.

Nu există un procent de acoperire code coverage măsurat. Cinci teste trecute nu înseamnă „100% din produs verificat”. Nu există un rezultat cantitativ de îmbunătățire a mobilității verificat. Singurele valori numerice folosite ca dovezi în pitch sunt numere de teste/repere și bugete de timp de prezentare etichetate ca atare; orice preț sau scenariu comercial este ipoteză.

## 15. Securitate, confidențialitate și exploatare

Bine definite ca intenție: chei pe server, context LLM minim, intervenții validate, provenance și incertitudine, baseline separat de scenariu. Implementarea stdlib nu impune auth, rate limit, limite de corp cerere sau validare robustă de tipuri. JSON valid de forma listă ori tipuri greșite poate declanșa excepții necontrolate; Content-Length nu este validat. CORS `*` și bind toate interfețele sunt convenabile local, dar nu o configurație demonstrată de producție. Nu se expun chei în deck sau rapoarte.

Dacă viitoarele date includ ANPR/video sau traiectorii individuale, sunt necesare guvernanță, minimizare și reguli de acces; nu există o integrare ANPR actuală verificată. OSM raster depinde de internet și de condițiile serviciului; nu se promite un demo offline complet. Licențele datelor și atribuirea trebuie verificate înaintea distribuirii. `docs/frontend/IMPLEMENTATION.md` menționează un audit npm istoric cu vulnerabilități tranzitive; nu este un audit curent și nu justifică un scor de securitate actual.

Scalare: HTTPServer este sincron, nu există cozi de joburi/worker pool, cache de rețele, stocare scenarii sau scheduler SUMO. Arhitectura cu separarea sim permite extinderea viitoare, dar nu dovedește scalare actuală. Fiabilitate: clientul are anulare și timeout; UI-ul are stări unknown și erori, însă fallback-ul de zonă în server poate întoarce o „reușită” semantic greșită. Calculele/calibrarea și contractele trebuie stabilizate înainte de optimizarea volumului.

## 16. Diferențiatori și inovație

Argumente apărabile: experiență orientată către o zonă și o decizie, compararea intervențiilor de amplitudini diferite, model explicit de dovezi/incertitudine și arhitectură care separă propunerea de măsurare. Interfața web este vizibilă și editabilă prin controale; codul shared menține transportul separat de UI. Nu s-a identificat o metodă nouă de simulare sau un avantaj algoritmic măsurat. Avantajele competitive sunt ipoteze de integrare și utilizabilitate, care cer interviuri și o evaluare comparativă.

## 17. Impact și model economic

Beneficiu așteptat: specialistul poate discuta variante și compromisuri într-un singur spațiu. Măsurarea viitoare recomandată: timpul necesar pregătirii unei comparații explicabile; procentul de indicatori cu sursă verificabilă; reproducerea aceluiași rezultat pe aceleași intrări; rata de respingere corectă a intervențiilor invalide. Acestea sunt obiective de validare, nu rezultate deja obținute.

Model propus: licență/abonament pentru echipe profesionale, pilot cu domeniu restrâns. Prețul de 1.500 euro/lună provine din vechiul deck; poate fi păstrat numai ca **ipoteză de testat**, nu tarif validat. 12 luni × 1.500 = 18.000 euro/an este aritmetică, nu ARR. Un exercițiu comercial cu zece organizații ar însemna 180.000 euro/an dacă toate ar cumpăra la acel preț; zece este o cohortă propusă, nu o listă de clienți ori o estimare a pieței totale. Costul servirii, suportul, CPU-ul SUMO și licențele de date nu sunt măsurate. Nu se declară marjă de 95%, vânzare în 14 zile, fonduri asigurate, eligibilitate de achiziție sau prag legal. Niciun client plătitor identificat prin contract.

## 18. Contradicții care afectează pitch-ul

| Document/afirmație | Ce arată codul | Decizie pentru deck |
|---|---|---|
| STATUS: modele reale și telemetrie | Literali și euristici locale, fără inputuri măsurate | „Date demonstrative”, fără rezultate de trafic |
| ARCHITECTURE/API_CONTRACT: POST inexistente | Corect pentru FastAPI; stdlib separat are fixtures | Explicarea celor două entry point-uri |
| STATUS: cinci cartiere analizate | Dataset unic pe server, fallback Podu Roș | Cinci repere de navigare, nu cinci analize |
| README: OpenFreeMap | MapViewport actual folosește raster OSM | Captură actuală și atribuire OSM |
| IMPLEMENTATION: live gate dezactivat | Butonul actual poate apela analyze în non-demo | Se descrie codul curent; nu integrare completă |
| Deck: Next14, Python3.13, OSMnx1.9, Tailwind | Next16.4.2, Python3.12, OSMnx2.x, CSS | Corectat după manifeste |
| Deck: micromodel city/live 5 secunde | Doar smoke sintetic opțional | Fără latențe sau live SUMO în pitch |
| Deck: echipă de doi, README: trei dezvoltatori | Git confirmă autori Iustin și Alex; roster complet necunoscut | Păstrate numele din deck, fără roluri exclusive inventate |
| Deck: Q1/Q2 2026 viitor | Data auditului este octombrie 2026 | Roadmap relativ după hackathon |
| Spec SUMO 1.21/exemplu rulat | Pin 1.28.0, fără artefact oraș | Numere din spec tratate ca exemple |

## 19. Roadmap recomandat și criterii de ieșire

1. **Date și contract unic.** Alegerea unui entry point backend, armonizarea payload-urilor cu shared, validare runtime, eliminarea fallback-ului de zonă și a etichetelor false. Ieșire: integrare contract testată pozitiv și negativ.
2. **Prima analiză reală.** Zonă bounded, snapshot OSM licențiat, geometrie validată, un indicator reproductibil cu unitate și metodă. Ieșire: aceeași intrare → același rezultat, surse inspectabile.
3. **Intervenție constrânsă.** Catalog mic cu parametri și reguli geometrice; o schimbare aplicată pe o copie baseline. Ieșire: respingere demonstrată a cazurilor invalide și diferență real calculată.
4. **AI structurat.** Provider pe server, context limitat, schema și reguli independente de model, mesaje pentru lipsa modelului. Ieșire: propunere acceptată/respinsă și cost/latency măsurate, fără rezultate simulate de LLM.
5. **Evaluare cu un specialist.** Testarea parcursului și măsurarea timpului de pregătire, fără a modifica trafic real. Ieșire: protocol și observații documentate, acordul organizației.
6. **SUMO aplicat zonei**, numai cu geometrie și cerere justificabile. Ieșire: configurație/seed/version/output, calibrare explicită, comparație cu baseline și etichetare live/offline/replay.
7. **Hardening și mobile.** Auth, limite, jobs/caching după nevoie, hartă nativă, verificare Android, accesibilitate și distribuție.

Ordinea exprimă dependențe, nu promisiuni calendaristice. Nu se prezintă planul ca pilot semnat sau în curs.

## 20. Mesajele recomandate pentru juriu

- ARTERIA vizează comparația explicabilă a intervențiilor urbane pentru specialiști.
- Demonstrația arată un parcurs web real; scenariile și valorile sunt demonstrative.
- AI va propune alternative; regulile și calculele independente trebuie să le verifice.
- Baza tehnică are teste de transport și un build web verificat, dar impactul urban rămâne de validat.
- Cererea utilă este o introducere către un specialist și acces la un set de date pentru prima analiză reproductibilă.

La întrebarea „cât e AI?”, răspunsul corect astăzi este „recomandările generative sunt în plan; demo-ul folosește catalog fix”. La „ce nu merge?”, se numesc integrarea datelor, contractele și evaluarea reală. La „de ce voi?”, se arată artefactele construite și se evită atribuirea unor roluri exclusive sau angajamente de timp neverificate.

## 21. Registru de afirmații → dovezi → surse → statut

| ID / Afirmație | Dovadă | Sursă exactă | Încredere / statut |
|---|---|---|---|
| C01 Produsul vizează planificarea urbană Iași | workflow și arhitectură | `README.md`, `docs/ARCHITECTURE.md` | Ridicat / intenție de produs |
| C02 Web are un parcurs explorare-scenarii-comparație | componente, stare React, browser local | `frontend/web/src/features/workspace/Workspace.tsx` | Ridicat / UI implementat |
| C03 Există cinci repere | lista neighborhoods | `frontend/shared/core/fixtures.ts` | Ridicat / repere, nu zone validate |
| C04 Alternativele sunt predefinite | demoIssuesByNeighborhood | `frontend/shared/core/fixtures.ts`, `features/scenarios/ScenarioPanel.tsx` | Ridicat / demonstrativ |
| C05 Comparația nu este SUMO | tabele și ajustări locale, fără apel sim | `frontend/web/src/features/comparison/ComparisonPanel.tsx` | Ridicat / euristici demo |
| C06 FastAPI expune numai health | decorator unic și teste 404 | `backend/main.py`, `tests/test_backend.py` | Ridicat / cod inspectat |
| C07 Serverul alternativ reutilizează Podu Roș | DATASETS unic, fallback și probe | `backend/server.py`, `docs/ppt/backend-audit-probes.json` | Ridicat / confirmat la handler |
| C08 AI generativ nu este integrat | catalog fix, fără apeluri provider | `backend/server.py`, `docs/ARCHITECTURE.md` | Ridicat / planificat |
| C09 Cele trei POST nu sunt interoperabile complet | câmpuri și forme diferite | `frontend/shared/core/contracts.ts`, `backend/server.py`, `api-specs/*.md` | Ridicat / gap de integrare |
| C10 SUMO smoke generează și avansează scenariu sintetic | cod netconvert și traci | `sim/sumo_support.py` | Ridicat / implementat, nereexecutat la audit |
| C11 Graful smoke are cale 200 m | cod și assert | `sim/smoke_test.py`, `tests/test_spatial_smoke.py` | Ridicat / sintetic, nereexecutat |
| C12 Cinci teste Node au trecut | comandă npm test executată | `frontend/shared/tests/api.test.ts` | Ridicat / verificat la audit |
| C13 Typecheck și build web au trecut | comenzi executate, rute / și /app | `frontend/package.json`, `frontend/web/package.json` | Ridicat / verificat la audit |
| C14 Harta Android e placeholder | text și componentă native | `frontend/mobile/src/features/map/MapPlaceholder.tsx` | Ridicat / scaffold |
| C15 Provenance este convenție proiectată | Evidence și Measurement | `frontend/shared/core/contracts.ts`, `docs/API_CONTRACT.md` | Ridicat / tipuri, aplicare incompletă |
| C16 Prețul 1500/lună este ipoteză | apare în deck-ul anterior, fără clienți | `docs/ppt/Template-Pitch-Hackathon.pre-audit.pptx` | Ipoteză / nevalidat |
| C17 Numele Iustin Fagateanu și Alex Pintilie apar în echipă | deck și autori Git Iustin/Alex | `Template-Pitch-Hackathon.pre-audit.pptx`, istoricul Git | Ridicat pentru textul existent; roster/roluri de confirmat |
| C18 Zece secțiuni în ordine și anexe | instrucțiuni slide 2–3 | `Template-Pitch-Hackathon.backup.pptx` | Ridicat / cerință șablon |
| C19 Nu există efect de trafic validat în checkout | lipsesc inputuri/rulări/calibrare; valori fixe | `backend/server.py`, `sim/`, `frontend/shared/core/fixtures.ts` | Ridicat în limitele checkout-ului |
| C20 PMUD este un context instituțional local | pagina oficială de consultare | Primăria Iași, URL în secțiunea 4, accesat 2026 | Ridicat pentru context; fără validare clienți |

### Index de surse suplimentare inspectate

Documentație de produs: `backend/README.md`, `backend/STATUS.md`, `backend/API_ENDPOINTS.md`, `frontend/README.md`, `frontend/STATUS.md`, `frontend/web/README.md`, `frontend/mobile/README.md`, `sim/README.md`, `sim/STATUS.md`, `docs/ROADMAP.md`, `docs/frontend/DESIGN_BRIEF.md`, `docs/frontend/IMPLEMENTATION.md`, `docs/frontend/AI_INTERFACE_PROMPT.md`.

Contracte: toate cele șapte fișiere `api-specs/analysis-endpoints.md`, `areas-endpoints.md`, `auth-endpoints.md`, `evaluation-endpoints.md`, `proposals-endpoints.md`, `scenario-persistence-endpoints.md`, `simulation-engine-contract.md`.

Cod/config: `backend/settings.py`, `tests/test_sumo_support.py`, `scripts/setup.ps1`, `scripts/setup.sh`, `scripts/check.ps1`, `scripts/check.sh`, `scripts/dev.ps1`, `scripts/dev.sh`, `scripts/health_smoke.py`, `.github/workflows/ci.yml`, `pyproject.toml`, `frontend/package.json`, `frontend/web/package.json`, `frontend/mobile/package.json`, `frontend/shared/package.json`, `frontend/web/next.config.mjs`, `frontend/mobile/app.json`, `frontend/mobile/eas.json`, `frontend/web/AGENTS.md`, `.agents/skills/pptx/SKILL.md`.

Resurse pitch: backup original, versiune pre-audit, `build_deck.pre-audit.py`, `export_preview.ps1`, `apply_transitions.ps1`, extrasele JSON și `preview-template/`. Capturile istorice `frontend/.qa` nu reprezintă validare curentă. Nu există un logo instituțional obligatoriu verificat sau fotografii de echipă confirmate. Nu există o adresă publică demo/contact verificată: nu se distribuie URL-urile inventate anterior.

## 22. Informații care cer confirmare înainte de depunere

Durata oficială de pitch, numele oficial al evenimentului, grila de jurizare și eventualele cerințe AI; roster-ul complet și rolurile echipei (README menționează trei dezvoltatori); angajamentul de continuare; prețul care trebuie testat; o listă reală de organizații de intervievat; existența unor măsurători/rulări externe neincluse în checkout; dreptul de utilizare a datelor; contactul și URL-ul public de demo. Lipsa lor nu împiedică livrarea unui deck onest, dar limitează afirmațiile permise.
