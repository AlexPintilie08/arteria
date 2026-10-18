# ARTERIA — cercetare completă, revizie V2 după sincronizarea Git

Actualizat la 18 octombrie 2026, Europe/Bucharest. Sursa curentă: checkout-ul rezultat după integrarea `origin/main` (`60fe2ee`) în `master`, commit de integrare `00cf80c`. Confirmarea echipei provine direct din cerința V2 a utilizatorului. Auditul V1 și cercetarea V2 înainte de sincronizare sunt păstrate în `docs/ppt/archive/v1/` și `docs/ppt/archive/v2-before-sync/`; afirmațiile lor despre lipsa endpoint-urilor și motorul SIM doar smoke sunt **istorice și înlocuite de această revizie**.

## 1. Rezumat executiv

ARTERIA by ARION propune un laborator de planificare urbană pentru specialiști în mobilitate. Repository-ul actual are mai mult decât o interfață: FastAPI oferă un flux coerent de analiză–propunere–evaluare pentru semaforizare **sintetică**, cu validare Pydantic și persistență SQLite. Un flux separat pentru grafuri pietonale conectează backendul la SIM v3 prin subprocess, calculează alternative pe același baseline, verifică propunerile și livrează dovezi. OSM, geometriile și eșantioanele de rute au limitări explicite. Motorul SIM conține pregătire și execuție SUMO condiționată de binare, dar API-ul și UI-ul nu lansează evaluări SUMO; nu există rezultate de trafic calibrat validate.

Frontendul are mod conectat implicit și păstrează interfața de hartă demonstrativă numai prin configurare explicită. Android rămâne scaffold. Cloud LLM nu este integrat; propunerile actuale sunt deterministe. Aceste distincții trebuie să rămână vizibile în pitch: un calcul real pe date sintetice nu este o observație a traficului din Iași, iar o comparație de graf nu dovedește fezabilitatea unei construcții.

## 2. Metodă și evidență

După cererea de sincronizare s-au executat `git fetch --all --prune` și integrarea `origin/main`, fără conflicte. Lucrul PPT existent a fost păstrat. Au fost reverificate sursele actualizate: `backend/main.py`, modelele, adaptorul sintetic, stocarea, routerul și workerul spațial; fișierele SIM de analiză, candidați, impact, propuneri și SUMO; workspace-ul conectat, API-ul shared, panoul spațial și geografia frontend; testele și documentele noi. A fost citit `sim/AGENTS.md`. Nu s-au modificat algoritmii aplicației.

Statuturi: **implementat** = cod prezent și inspectat; **verificat la audit** = comandă/probă executată aici; **raportat anterior** = document de predare fără echivalare cu o nouă rulare; **planificat** = lipsă din implementare; **ipoteză** = afirmație de produs/business fără validare utilizatori. Rezultatele comenzilor se păstrează în `docs/ppt/reports/`.

Nu s-au publicat secrete sau valori din `.env`. Dependențele necesare verificărilor au fost instalate în directorul ignorat `docs/ppt/reports/.qa/runtime`, fără schimbarea manifestelor sau instalării globale. Acest runtime folosește intervalele din pyproject și nu este o sincronizare exactă `uv.lock`; versiunile și rezultatul testelor trebuie declarate ca atare.

## 3. Contextul hackathonului și șablonul

Backup-ul original rămâne `docs/ppt/archive/original-backup/Template-Pitch-Hackathon.backup.pptx`, SHA-256 `56133b4d2fe6946ff4c5a246e4d0f8be0baa0ac2f6638a6e25f969994695d170`. Are 16 pagini, incluzând ghidaj. Cere zece secțiuni în ordinea: titlu, omul și durerea, alternative/dovezi, soluție, demo, construcție, business, piață, echipa, cererea; apoi anexe. Ghidajul trebuie eliminat. Sunt descrise variante de trei și cinci minute; aceasta nu dovedește durata oficială a evenimentului. Pentru trei minute piața poate fi sărită.

Deck-ul rămâne 13 slide-uri (10+3), 13⅓×7½ inch, română, cu responsabilitățile echipei reproduse exact în engleză conform instrucțiunii V2. Nu există un regulament oficial separat sau grilă numerică de jurizare în checkout. Nu s-au identificat logo-uri instituționale obligatorii. Numele autorului template-ului, Andrei Margelatu, este păstrat în note ca atribuire.

## 4. Problema, analiza nevoii și publicul

Utilizator vizat: specialistul în mobilitate/urbanism care trebuie să compare intervenții pe aceeași zonă și să explice compromisuri, surse și limite. Cumpărător posibil: administrație locală sau consultanță. Locuitorii, pietonii, bicicliștii și utilizatorii transportului public sunt beneficiari potențiali. Primăria și CTP Iași sunt posibili interlocutori, nu parteneri sau clienți confirmați.

Nevoia de a pregăti o comparație explicabilă este o ipoteză de utilizare bine definită în README și arhitectură, dar nu există interviuri, măsurători ale timpului economisit ori disponibilitate de plată confirmate. Nu se reproduce citatul anonim al unui inginer din vechiul deck. Nu se folosesc ca fapte cifrele istorice 42 min/navetist, reducere 34%, pierderi de milioane sau marjă 95%.

Context extern primar, consultat în auditul inițial și păstrat numai pentru afirmații stabile:

- [Primăria Iași — consultare PMUD](https://www.primaria-iasi.ro/dm_iasi/portal.nsf/pagini/consultare%2Bpublica%2Bplanul%2Bde%2Bmobilitate%2Burbana%2Bdurabila%2Bpentru%2Bpolul%2Bde%2Bcrestere%2Biasi%2Bpmud%2Biasi-0002E4D6?Open%3FOpen=): context de planificare, nu dovadă de cerere pentru ARTERIA.
- [QGIS overview](https://www.qgis.org/project/overview/): alternativă de lucru GIS; fără benchmark de inferioritate.
- [SUMO Documentation](https://sumo.dlr.de/docs/): alternativă și componentă tehnică pentru simulare microscopică.
- [SUMO Calibrator](https://sumo.dlr.de/docs/Simulation/Calibrator.html): calibrarea fluxurilor/vitezelor poate folosi măsurători. Nu validează ARTERIA.

Diferențiator propus: parcursul comun zonă→alternative→comparație cu dovezi și incertitudini. Nu se pretinde un algoritm superior QGIS/SUMO sau un cost de studiu competitiv măsurat.

## 5. Soluția și parcursurile utilizatorului

### Flux conectat de semaforizare sintetică

`frontend/web/src/lib/api.ts` activează preview-ul numai dacă `NEXT_PUBLIC_DEMO_MODE === true`; altfel `ConnectedWorkspace.tsx` apelează API-ul. Utilizatorul alege un context de zonă, cere analiza, selectează problema, solicită trei ajustări deterministe ale verdelui sau o valoare proprie, apoi evaluează exact alternativa emisă de server. ID-urile și baseline-ul sunt returnate de backend. Comparația poate arăta îmbunătățire pe o direcție și înrăutățire pe cealaltă. Schimbarea selecției anulează cererea și invalidează rezultatele dependente.

Aceste calcule sunt implementate, dar intrările sunt sintetice; reperele și limitele din acest flux nu devin măsurători locale sau analiză spațială. Termenul transformative desemnează ajustarea integrală a verdelui, nu un pasaj ori reamenajare de infrastructură.

### Flux spațial pietonal

`SpatialPanel.tsx` creează un studiu fixture sau OSM prin `/api/v1/spatial/studies`, examinează candidați și cere comparația unui candidat emis de server pe același baseline. Backendul execută SIM v3 din checkout prin worker cu timeout, verifică schema răspunsului și păstrează rezultatul. Compararea ulterioară folosește rezultatul calculat la crearea studiului, nu pretinde o nouă simulare. Candidatul trebuie să aibă validare `candidate_backed_evaluated`.

### Hartă și Android

Workspace-ul original cu MapLibre, probleme și scenarii conceptuale rămâne preview explicit; nu trebuie confundat cu fluxul conectat. Catalogul geografic OSM are 24 Polygon/MultiPolygon și 7 puncte, separat de cele cinci bookmark-uri demo. Android are navigație și ecrane de bază, hartă placeholder și nu apelează API-ul conectat.

## 6. Inventar de funcționalități și stare

| Funcție | Stare actuală | Sursă / limită |
|---|---|---|
| Marketing și intersecție conceptuală 3D | Implementat | `frontend/web/src/app/page.tsx`, marketing Three.js; nu model cadastral |
| MapLibre și catalog geografic | Implementat | `MapViewport.tsx`, `NeighborhoodExplorer.tsx`, `sim-geography.ts`; limite OSM parțiale |
| Flux HTTP analyze/propose/evaluate | Implementat, conectat | `backend/main.py`, `ConnectedWorkspace.tsx`; model sintetic |
| Pydantic și erori uniforme | Implementat | `backend/models.py`, `engine_contract.py`; nu certificare fizică |
| Persistență rezultate | Implementat | `backend/storage.py`: SQLite JSON, namespace, ID imutabil, capacitate |
| Catalog demo și recuperare rezultate | Implementat | areas, analyses, proposals, evaluations GET |
| Studii pietonale / candidați / evaluare | Implementat | `spatial_routes.py`, `spatial_worker.py`, SIM v3 |
| Analiză OSM și cache pe mod | Implementat | `sim/geo.py`, `analysis.py`; rețea externă și acoperire limitate |
| Modificare ipotetică graf și impact | Implementat | `scenario.py`, `impact.py`; eșantioane de noduri, nu populație |
| Catalog/evidence/validare propuneri | Implementat determinist | `proposal_catalog.py`, `proposal_context.py`, `proposal_validation.py`, `proposals.py` |
| Pregătire și runner local SUMO | Implementat condiționat | `sim/sumo_engine.py`; necesită netconvert/sumo, nu API/UI SUMO integrat |
| LLM cloud | Planificat | Niciun provider apelat de aplicație |
| Auth/autorizare, job/SSE SUMO | Planificate | Nu există rute complete pentru acestea |
| Mobile conectat | Planificat | Expo scaffold, fără apeluri API curente |
| Export JSON/GeoJSON | Utilitare SIM și preview local | Nu se declară export PDF municipal sau colaborare completă |

## 7. Arhitectura reală

Cele trei componente rămân frontend, backend, sim. FastAPI este serverul autoritativ unic; `backend/server.py` este acum launcher compatibil Uvicorn, nu server fixture independent. Frontendul conectat apelează API-ul; backendul apelează modelul sintetic direct și SIM spațial într-un subprocess. SQLite păstrează analize, propuneri, evaluări și studii. Providerul LLM rămâne o dependență viitoare, deci legătura spre AI este întreruptă în diagramă.

Legăturile frontend→backend și backend→SIM spațial sunt acum implementate și trebuie arătate ca atare, fără a sugera că SUMO sau cloud AI sunt integrate. Diagrama separă graful pietonal de demo-ul de semaforizare. Documentele de predare care încă descriu snapshot extern fixat la 752c92d sunt parțial depășite: `SpatialAdapter.configuration()` folosește implicit repository-ul curent și hash-ul HEAD, cu override explicit `ARTERIA_SIM_ROOT`/REVISION. Codul curent are prioritate față de descrieri istorice.

## 8. Backend detaliat

`backend/main.py` v0.3.0 are GET /health, POST /analyze, /propose, /evaluate, recuperare /analyses/{id}, /proposals/{id}, /evaluations/{id}, GET /api/v1/areas și include routerul spațial. Validarea Pydantic, erorile 400/404/409/422/502/503/504, request ID și CORS GET/POST/OPTIONS pentru dezvoltare sunt implementate.

Analiza verifică bookmark-ul, unele constrângeri ale ariei, intrările și indisponibilitatea datelor istorice; baseline-ul și ID-urile sunt derivate determinist din cerere/versiune. /propose verifică analiza/problema și calculează ajustări ale duratei verzi spre repartizare proporțională cererii. /evaluate cere baseline, analiză, propunere și intervenție exact compatibile; compară indicatorii pe aceleași intrări, exceptând parametrul schimbat. Cererile SUMO în acest flux returnează explicit 503, fără fallback ascuns.

`SimulationAdapter.indicators()` implementează un model ilustrativ: întârziere uniformă R²/(2C), plus 60 secunde înmulțite cu excesul raportului cerere/capacitate; debit de saturație sintetic 1800 veh/oră. Rezultatul nu este model calibrat de trafic din Iași și nu este SUMO. Formula este cod real, nu tabelul literal din V1.

`Store` creează tabele SQLite, folosește tranzacții BEGIN IMMEDIATE, returnează obiectul existent la retry și aplică limite per namespace. Erorile filesystem/SQLite sunt capturate. Nu este un sistem complet de proiecte, conturi, partajare sau autorizare. Rutele de recuperare există, nu o interfață generală de ștergere publică.

## 9. Contracte și flux spațial

`spatial_routes.py` prefix /api/v1/spatial expune POST /studies, GET /studies/{id}, GET /studies/{id}/candidates și POST /studies/{id}/evaluate. Se verifică apartenența baseline-ului, identitatea candidatului, echivalența exactă a intervenției și validarea SIM. Studiul înregistrează engine_revision, sursa fixture/OSM, analiza, alternativele, opțiunile și pachetul de dovezi.

`SpatialAdapter` limitează la un studiu simultan în proces cu BoundedSemaphore și timeout 90 s. Workerul primește JSON, încarcă SIM din root-ul configurat și nu substituie rezultate la eșec. Pentru fixture folosește `sim.demo.fixture_snapshot`; pentru OSM verifică eligibilitatea catalogului și cere rețeaua walk cu limite 5 km²/5 km și fără achiziția de features în acel flux. Nu se inventează limite pentru puncte.

Workerul rulează analyze_snapshot, evaluate_candidates pe eșantion comun, prepare_candidate_options, validate_proposal_set și build_proposal_context. EngineResult și reject_nonfinite protejează ieșirea înaintea persistării. Codul shared a fost actualizat și există un test de flux backend/frontend. Specificațiile auth/job/SSE sau exemplele vechi din api-specs nu devin endpoint-uri implementate numai prin existența documentelor.

## 10. Frontend, geografie și performanță

Next.js 16.4.2, React 19.3.0, MapLibre 6.14.0 și Three 0.186.1 sunt versiunile declarate în manifeste, nu o afirmație despre ultimele versiuni publice. Shared include tipuri și client HTTP cu timeout/anulare. TypeScript nu validează singur JSON la runtime; backendul aplică scheme. ConnectedWorkspace gestionează baseline, alternativă exactă, reglaje și reseturi, iar SpatialPanel adaptează studiile pietonale separat.

Catalogul local derivă din `sim/iasi-neighborhoods.geojson`; frontendul importă un export de date și metadata de eligibilitate. `sim-geography.ts` păstrează Point ca Point, calculează bounds doar din geometriile existente și permite căutare fără diacritice. 24 contururi și 7 puncte nu înseamnă granițe legale certificate sau acoperire completă a orașului.

Nu există benchmark FPS, latență end-to-end, test de sarcină sau audit WCAG complet curent. Arhitectura are timeout/caching/zone bounded, dar nu dovedește scară de producție. Controalele accesibile și reduced motion sunt implementări utile, fără a declara conformitate certificată.

## 11. SIM: analiză și scenarii

`geo.py` normalizează Polygon/MultiPolygon, bbox și GeoDataFrame, validează mărimea, folosește CRS metric și output WGS84, achiziție OSMnx independentă walk/bike/drive și cache cu metadata de proveniență. `analysis.py` normalizează/proiectează grafuri, calculează conectivitate, rute și indicatori cu surse/unități și produce GeoJSON/issues deterministe.

`scenario.py` aplică legături pietonale ipotetice pe copii ale baseline-ului, cu verificări de endpoint și lungime. `candidates.py` ecranează un pool bounded și elimină conflicte materiale cu clădiri cunoscute. Absența unei intersecții pe date incomplete nu este dovadă de fezabilitate. `impact.py` folosește același eșantion de perechi nod–nod pentru comparație și ranking; diagnosticele locale specifice candidatului sunt separate.

`proposal_validation.py` tratează propunerile ca input neîncrezător: compară identitate/acțiune, coordonate, unități, citări, metrici pretinse observate, costuri, run IDs și afirmații fizice. JSON valid nu înseamnă proiect realizabil. Opțiunile candidate-backed și pachetul evidence există fără un LLM; categoriile de planificare rămân neclasificate când nu pot fi susținute.

## 12. SUMO: implementare versus execuție

`sim/sumo_engine.py` conține prepare_sumo_network și run_real_area_simulation. Pregătește plain XML metric, maparea ID-urilor sursă, GeoJSON și rute OD sintetice bounded cu seed. Când binarele există, poate apela netconvert și sumo headless, verifica exit/timeout și extrage tripinfo. Outputul refuză suprascrierea unor rezultate existente și păstrează accounting-ul vehiculelor.

Aceasta este o capacitate implementată local, nu doar smoke. Totuși API-ul `SimulationAdapter.require_sumo()` încă refuză integrarea de scenariu SUMO, iar UI-ul nu apelează acest runner. STATUS SIM raportează pregătirea pe cache Iași oprită la netconvert absent, fără măsurători de trafic. O rulare viitoare cu cerere sintetică ar descrie ipotezele ei, nu o predicție calibrată a orașului. Smoke-ul TraCI sintetic rămâne distinct de runner și de evaluarea urbană.

## 13. AI și inovație

Nu există provider cloud, apel LLM, RAG sau fine-tuning implementat. Propunerile de semaforizare și cele candidate-backed pe graf sunt deterministe. Planul: backendul trimite dovezi/cataloage limitate unui LLM, validează propunerea independent și cere evaluarea calculată; modelul nu produce măsurători. Acest principiu este deja parțial susținut de catalog/evidence/validator SIM, dar legătura cu providerul rămâne viitoare.

Argumente apărabile: flux HTTP coerent, baseline imutabil, diferențiere între sintetic și OSM, comparații de graf pe eșantion comun, propuneri verificate față de candidații evaluați și tratarea explicită a indisponibilității. Nu se revendică algoritm nou superior, optimizare garantată sau procent verificabil al codului scris de AI.

## 14. Teste și rezultate

După sincronizare, `npm test` a trecut **9/9**: cinci transport/fixtures și patru geografie. Typecheck web/mobile/shared și build-ul Next au trecut. Cele 24 contururi și 7 puncte sunt susținute de catalog și de testele de geografie, fără extrapolare la limite legale.

Testele Python/SIM ale checkout-ului sincronizat au trecut: **138 passed, 1 warning în 15,75 s**, fără skip-uri, în runtime-ul QA izolat. Avertismentul este o depreciere Starlette/httpx. Rezultatul este consemnat în `docs/ppt/reports/project-tests.log` și raportul QA. Documentele de predare raportează anterior 60 teste backend și 78 teste SIM/proiect în ramuri diferite: nu se adună aceste numere și nu se prezintă ca o nouă rulare. Nu există procent code coverage măsurat.

Nu există beneficiu real de trafic validat. Comparațiile numerice pe fixture sunt calcul real pe input sintetic; comparațiile OSM pe graf sunt estimări condiționate de snapshot, eșantion și metodă, nu efecte măsurate pe rezidenți. Datele brute de senzori din vechiul demo nu au devenit verificate prin sincronizare.

## 15. Securitate, confidențialitate și fiabilitate

Îmbunătățiri reale față de V1: scheme și răspunsuri validate, erori uniforme, ID-uri legate de baseline, respingerea intervențiilor modificate, SQLite și retry imutabil, limită de capacitate, worker bounded și timeout fără fallback. Nu există auth/autorizare sau izolare multi-tenant completă, coadă distribuită SUMO, rate limit general ori infrastructură de producție demonstrată. GET /health este liveness, nu o verificare de readiness completă a datelor/workerului.

Sursele OSM depind de licență, acoperire și actualizare; atribuirea ODbL trebuie păstrată. Punctele nu sunt poligoane. Dacă în viitor sunt folosite ANPR/video/traiectorii, sunt necesare minimizare, drepturi de acces și guvernanță; această integrare nu este confirmată. Secretele providerilor vor rămâne pe server. Nu se afirmă conformitate legală sau audit de securitate certificat.

## 16. Impact, model economic și piață

Beneficiu potențial: pregătirea unei comparații explicabile și reproducibile pentru un specialist. Trebuie măsurate timpul de pregătire, sursele verificabile, reproducerea pe aceleași intrări și utilitatea compromisurilor. Nicio economie de timp sau îmbunătățire de mobilitate nu este deja măsurată cu utilizatori.

Abonamentul 1.500 euro/lună provine din pitch-ul anterior și rămâne **ipoteză nevalidată**. 18.000 euro/an = 12×1.500, iar 10×18.000 = 180.000 euro/an este numai exercițiul în care toate zece organizații ar cumpăra. Nu este ARR, TAM/SAM sau pipeline confirmat. Lista celor zece organizații trebuie construită; costurile de date/calcul/suport și disponibilitatea de plată sunt necunoscute. Nu se declară marjă, prag juridic sau pilot semnat.

## 17. Echipa confirmată

- **Iustin Fagateanu — Frontend and web experience**
- **Alex Pintilie — Bootstrap and simulation foundation**
- **Fagateanu Eusebiu — Backend**

Aceste nume și responsabilități sunt confirmate direct de utilizator în V2. Git-ul sincronizat include commitul de predare backend `6f59b22` al autorului Făgăteanu Dumitru-Eusebiu, dar deck-ul păstrează exact numele solicitat **Fagateanu Eusebiu**. Nu se presupune autorie exclusivă asupra fiecărui fișier adus prin merge și nu se inventează funcții individuale. Rolurile de scenă și angajamentul de continuare nu au fost confirmate.

## 18. Contradicții și corecții după Git

| Afirmație istorică | Cod curent | Tratament în pitch |
|---|---|---|
| FastAPI doar /health, stdlib separat | FastAPI unic cu flux și storage; server.py launcher | API conectat și Pydantic/SQLite |
| Alternative numai literali | Calcul sintetic determinist și candidați SIM | Propuneri deterministe, nu LLM |
| SIM numai smoke | Analiză, cache, candidați, impact, evidence, runner condiționat | Motor de graf implementat; SUMO UI neintegrat |
| UI numai fixtures | ConnectedWorkspace implicit; preview explicit | Captură nouă a modului conectat |
| Toate legăturile arhitecturale viitoare | Frontend→API→worker SIM există | Linii continue pentru implementat, întreruptă numai integrarea AI |
| Roster necunoscut | Confirmat de utilizator, trei membri | Trei profiluri egale |
| Snapshot extern fixat obligatoriu | SpatialAdapter folosește implicit HEAD curent | Codul actual are prioritate față de handoff vechi |
| Nicio validare geometrică/persistență | Validări Pydantic/SIM și SQLite prezente | Nu se mai descriu ca total absente; fezabilitatea fizică rămâne necunoscută |

## 19. Roadmap și cererea către juriu

1. Un caz OSM bounded cu aria/snapshotul/metoda documentate; verificarea calității și a comparației pe eșantion comun.
2. Test cu un specialist al parcursului conectat și măsurarea timpului de pregătire/trasabilității.
3. Integrarea opțională a LLM pe pachetul de dovezi, cu validator independent și limite explicite.
4. Conectarea runnerului SUMO la API doar cu rețea, cerere și binare valide, plus rezultate versionate; calibrarea rămâne etapă separată.
5. Autorizare, readiness, persistență de proiecte/export și test Android, în funcție de prioritatea utilizatorilor.

Cerere: o introducere către un specialist și acces la un set de date local pentru validarea unui caz. Nu un acord existent sau un termen garantat. Menținem ordinea pitch-ului și cererea concretă, înlocuind promisiunea veche „construim primul API” cu validarea fluxului deja implementat.

## 20. Registru de afirmații și dovezi

| ID / Afirmație | Dovadă → sursă | Certitudine / stare |
|---|---|---|
| C01 Planificare urbană pentru mobilitate | README și arhitectură → `README.md`, `docs/ARCHITECTURE.md` | Ridicat / produs propus |
| C02 Flux conectat de comparație | API calls și ID-uri → `frontend/web/src/features/workspace/ConnectedWorkspace.tsx` | Ridicat / implementat, sintetic |
| C03 Catalog 24 contururi + 7 puncte | GeoJSON și tests → `sim/iasi-neighborhoods.geojson`, `frontend/web/tests/sim-geography.test.ts` | Ridicat / OSM parțial, nu legal |
| C04 Propuneri deterministe | formule și opțiuni candidate-backed → `backend/main.py`, `sim/proposals.py` | Ridicat / implementat, fără LLM |
| C05 Comparație legată de baseline | verificări exacte și delta → `backend/main.py`, `backend/spatial_routes.py` | Ridicat / implementat |
| C06 FastAPI cu endpoint-uri complete demo | decoratori și modele → `backend/main.py`, `backend/models.py` | Ridicat / implementat |
| C07 Server unic și SQLite | launcher/storage → `backend/server.py`, `backend/storage.py` | Ridicat / implementat |
| C08 Cloud AI absent | lipsă provider; opțiuni deterministe → `backend/main.py`, `sim/proposals.py` | Ridicat / provider planificat |
| C09 Worker SIM integrat | subprocess și engine schema → `backend/spatial_adapter.py`, `spatial_worker.py`, `engine_contract.py` | Ridicat / implementat bounded |
| C10 SUMO runner condiționat | prepare/run/tripinfo → `sim/sumo_engine.py` | Ridicat / implementat, execuție dependentă de binare; neintegrat API |
| C11 Analiză/candidați/impact de graf | metode și baseline immutable → `sim/analysis.py`, `candidates.py`, `impact.py`, `scenario.py` | Ridicat / calcul condiționat |
| C12 Nouă teste Node trecute | comandă npm test → `frontend/shared/tests/api.test.ts`, `frontend/web/tests/sim-geography.test.ts` | Verificat după sincronizare |
| C13 Typecheck și build trecute | comenzi locale → `frontend/package.json` | Verificat după sincronizare |
| C14 Android scaffold | componente native placeholder → `frontend/mobile/src/features/` | Ridicat / API neconectat |
| C15 Dovezi și validare propuneri | verificări citări/unități/candidate → `sim/proposal_context.py`, `sim/proposal_validation.py` | Ridicat / implementat, nu fezabilitate fizică |
| C16 Preț nevalidat | ipoteză din deck istoric → `docs/ppt/archive/pre-audit/Template-Pitch-Hackathon.pre-audit.pptx` | Ipoteză |
| C17 Trei membri și rolurile exacte | confirmare explicită utilizator, cerința V2, 18 octombrie 2026 | Confirmat; fără autorie granulară presupusă |
| C18 Zece secțiuni + anexe | instrucțiunile template-ului → `docs/ppt/archive/original-backup/Template-Pitch-Hackathon.backup.pptx` | Ridicat |
| C19 Fără impact real de trafic validat | model sintetic, API SUMO indisponibil, limitări SIM → `simulation_adapter.py`, `sim/STATUS.md` | Ridicat în limitele checkout-ului |
| C20 PMUD context instituțional | pagina oficială Primăria Iași citată în §4 | Context, nu adopție |

## 21. Surse inspectate și limite de confirmare

Documente noi: `docs/DEMO_API.md`, `docs/BACKEND_AUDIT.md`, `docs/MACBOOK_HANDOFF.md`, `backend/README.md`, `backend/STATUS.md`, `backend/PREDARE_BACKEND.md`, `backend/SPATIAL_API.md`, `backend/FRONTEND_HANDOFF.md`, `sim/AGENTS.md`, `sim/STATUS.md`, `sim/ARCHITECTURE.md`, `sim/APPLICATION_INTEGRATION.md`, `sim/NEIGHBORHOODS_LICENSE.md`, `frontend/STATUS.md`, `frontend/README.md` și testele noi. Descrierile istorice de handoff sunt comparate cu codul și nu luate automat drept comportament curent.

De confirmat înainte de depunere: durata/grila oficială și condițiile AI, rolurile de scenă, disponibilitatea echipei după eveniment, interviuri și preț, date locale și licență, contact/demo URL public și eventuale măsurători externe neincluse în repository. Roster-ul de trei membri este acum confirmat. Nu se certifică eligibilitate sau impact urban real pe baza unei prezentări.
