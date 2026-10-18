# Analiza decalajelor — produs web și backend

**Snapshot:** ed69c2d / origin/codex/ppt-finalized; verificat la 18.10.2026.  
P0 = corectitudine și utilitate în demo; P1 = utilizare profesională după validarea problemei; P2 = operare/producție. Prioritățile sunt propuneri de audit.

## Decalaje confirmate

| ID / prioritate | Funcție sau afirmație | Starea și dovada | Decalaj și efect |
|---|---|---|---|
| G01 / P0 | Sursă în rezultatul spatial | În browser, fixture-ul a produs caption „graful OpenStreetMap”; SpatialPanel.tsx:158 îl fixează. | Fixture-ul este atribuit greșit sursei OSM. |
| G02 / P0 | Analiză geografică prin selectorul de zonă | ConnectedWorkspace.tsx:47–50 trimite preview-* fără boundary; backend/main.py:105–123 întoarce timing sintetic și layers unknown. | Selectorul pare zonă analizată, dar această cale nu calculează geografia cartierului. |
| G03 / P0 | Hartă ca suprafață principală | /app începe cu formularul ConnectedWorkspace; catalogul e în altă secțiune. origin/main:frontend/IMPLEMENTATION_TODO.md P0-01/02 descrie lipsa map-first. | Nu există parcurs unitar zonă→problemă→hartă→rezultat. |
| G04 / P0 | Rezultate SIM pe hartă | SpatialPanel nu trimite studiul/alternativele în MapViewport; worker-ul folosește include_features=False (backend/spatial_worker.py:38–50). | Utilizatorul vede ID-uri/tabel, nu poziția și traseele afectate. |
| G05 / P0 | OSM live | Implementarea există; testele Etapei 1 au rulat fixture offline. Catalogul este snapshot parțial, notat ca extras la 17.10.2026 în sim/STATUS.md. | Disponibilitatea și rezultatele pe zone live rămân necunoscute. |
| G06 / P0 | Inginerie de trafic | simulation_adapter.py:18–29 folosește cerere/ciclu sintetice și formula deterministă de întârziere. | Nu susține timing profesional, LOS, cozi, faze multiple sau coridor măsurat. |
| G07 / P0 | Impact pietonal | SIM compară eșantioane de noduri și link ipotetic; nu reprezintă cerere sau persoane. | Nu poate cuantifica impact asupra locuitorilor fără demand și validare. |
| G08 / P0 | Tipul evaluării | Timing-ul este calcul sintetic; graful returnează comparație stocată din studiul inițial; SUMO nu e în API/UI. | „Evaluare” poate părea rerulare de simulare dacă run state nu este vizibil. |
| G09 / P1 | Proiecte și colaborare | SQLite salvează rezultate (backend/storage.py); lipsesc utilizatorii și ownership. | Fără login, proiecte, partajare, listare, ștergere publică sau export profesional. |
| G10 / P1 | Validare runtime frontend | frontend/shared/core/api.ts:32 face cast din response.json() as T. | Un răspuns incompatibil poate ajunge la render fără validare runtime. |
| G11 / P1 | Metrici multimodale | /analyze declară layers unknown; worker-ul grafic rulează numai walk. | Bike, transit, destinații, siguranță și metrici accesibile nu sunt end-to-end. |
| G12 / P1 | Accesibilitate universală | Graful pietonal nu conține pante, trotuare, borduri sau crossings; worker fără features. | Eticheta de acces pietonal poate fi interpretată mai larg decât metoda. |
| G13 / P1 | Livrabile profesionale | UI-ul arată rezultate în sesiune, SQLite păstrează înregistrări. | Fără export cu hartă, metodă, input, scenariu și surse. |
| G14 / P1 | Link reproductibil | Secțiunile sunt state React local, necodate în URL. | Fără deep-link sau restaurare după refresh. |
| G15 / P1 | Fezabilitate candidat | Validatorul SIM aplică reguli/heuristici; UI spune cost și fezabilitate necunoscute. | Nu substituie verificarea juridică, accesului, siguranței, utilităților sau construcției. |
| G16 / P1 | Catalog geografic pe hartă | Lista e completă, harta desenează numai selecția. origin/main frontend TODO P0-02/P0-04 cere catalog și rezultate. | Context spațial limitat, comparația vizuală lipsește. |
| G17 / P1 | Proveniență unitară | Spatial afișează revizie/warnings; semafor are avertismente sintetice, dar nu folosește aceeași identitate geografică. | Dosarul scenariului nu este unitar între fluxuri. |
| G18 / P2 | Operare multi-user | SQLite local, semaphore per proces, timeout; /health este liveness. | Lipsesc readiness completă, coadă distribuită, rate limit, tenant, backup și observabilitate demonstrată. |
| G19 / P2 | SUMO calibrat | Runner local în sim/sumo_engine.py; sumo și netconvert nu au fost găsite în PATH în audit. | Fără traffic model integrat/calibrat pe Iași. |
| G20 / P2 | AI generativ | Catalog/validator deterministe; provider extern neintegrat. | Nu se poate promova AI-generated; integrarea ar necesita evaluare separată. |

## Contradicții de documentație

| Document | Contradicție | Observație |
|---|---|---|
| docs/API_CONTRACT.md:11,19 | Declară doar /health și că /analyze, /propose, /evaluate lipsesc. | Codul curent conține rutele. |
| docs/ARCHITECTURE.md | Descrie foundation-ul ca shell + health și API-uri viitoare. | Document anterior integrării. |
| sim/AGENTS.md:8 | Spune că backend-ul expune numai /health. | Stare depășită; regulile de proveniență și ownership SIM rămân utile. |
| frontend/STATUS.md | Prezintă unele integrări/geografie ca „in progress”. | Nu se aliniază complet la codul din acest checkout. |
| origin/main PR #4 TODO | Cere map-first, catalog integral și straturi cu rezultate. | Se confirmă ca lipsuri în implementarea inspectată. |

## Criterii recomandate înaintea utilizării profesionale

1. Sursa, statusul și metoda sunt consecvente în UI; niciun fixture nu este etichetat OSM/observat.
2. Selectarea, geometria analizată și reprezentarea rezultatului folosesc aceeași identitate/proveniență.
3. Fiecare indicator declară unitate, metodă, date, acoperire, incertitudine și verificare cu reper.
4. UI distinge calcul nou, comparație stocată, simulare și observație.
5. Specialiștii țintă confirmă sarcinile și prezentarea rezultatului.

Nu au fost schimbate codul, specificațiile sau statusurile.
