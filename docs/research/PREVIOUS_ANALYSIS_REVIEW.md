# Revizuirea analizelor anterioare

**Data verificării:** 18 octombrie 2026 (Europe/Bucharest)  
**Snapshot analizat:** branch de lucru codex/ppt-diacritics, HEAD ed69c2d08940f6fc516acbf87ca7ece54426f4ca; origin/codex/ppt-finalized pointează la același commit. origin/main este e785649308923c0c91de40ebb1b0b85b5962962e. Working tree curat înaintea Etapei 1.

Acest document evaluează rapoartele fără să le modifice. Analizele și arhivele originale rămân în locațiile lor.

## Proveniență și versiuni

| Sursă | Proveniență disponibilă | Versiune și acoperire | Evaluare |
|---|---|---|---|
| docs/BACKEND_AUDIT.md | Commit 6f59b22, autor Git Făgăteanu Dumitru-Eusebiu; audit datat 17.10.2026 și actualizat în același document. | Checkout feat/backend-api; backend, contracte, clienți, SIM, setup, teste și CI. | Reproduceri concrete, dar concluziile inițiale descriu o ramură mai veche. Addendumul raportează remedieri; codul curent și testele au fost reverificate. |
| docs/ppt/archive/v1/PROJECT_RESEARCH_FULL.md și docs/ppt/archive/v2-before-sync/PROJECT_RESEARCH_FULL.md | Arhive istorice păstrate de repository. | V1 și V2 înaintea sincronizării Git. | Utile istoric; afirmațiile despre backend doar /health, UI doar fixtures și SIM doar smoke sunt depășite. |
| docs/ppt/research/PROJECT_RESEARCH_FULL.md | Commit 793cd12, autor Git Iustin Făgăteanu; actualizat 18.10.2026. | Revizie V2 după integrarea origin/main la 60fe2ee în commitul 00cf80c; produs, utilizatori, arhitectură, capabilități, teste și piață. | Index bun al cercetării și limitărilor; material de produs/pitch, nu validare independentă cu profesioniști. |
| docs/ppt/reports/PROJECT_REALITY_AUDIT.md | Commit 793cd12, autor Git Iustin Făgăteanu; inventar din 18.10.2026 cu addendum de verificare. | Inventar al implementării înaintea lecturii deck-ului, apoi teste și flux browser/API adăugate. | Dovezile de cod și test sunt utile. Mediul QA nu a fost sincronizat exact cu uv.lock; nu validează OSM live, efecte de teren, fezabilitate sau adopție. |
| docs/ppt/reports/PPT_FACT_CHECK.md, PPT_FINAL_CONTENT_AUDIT.md, HACKATHON_REQUIREMENTS_VERIFICATION.md | Rapoarte din auditul prezentării, commituri din 18.10.2026. | Afirmații ale deck-ului, capturi, cifre sintetice și cerințe de prezentare. | Utile pentru urmărirea afirmațiilor istorice; nu substituie auditul aplicației. |
| Handoff-uri și statusuri în backend/, frontend/, sim/ și docs/ | Autori și date diferite. | Intenții de implementare, limite și sarcini de predare. | Tratează-le ca raportări/backlog, nu dovadă de implementare. |
| origin/main:frontend/IMPLEMENTATION_TODO.md și origin/main:backend/IMPLEMENTATION_TODO.md | Adăugate de 541598d, PR #4 merge-uit în e785649 la 18.10.2026. | Handoff-uri și priorități MVP, robustete și operare. | Confirmă lipsuri care se văd în cod: prima vedere fără hartă, catalogul nedesenat integral, rezultatele SIM fără suprapuneri cartografice. Sunt backlog, nu audit nou. |

Istoricul identifică și PR #2/#3 ca merge-uri de integrare full-stack. gh CLI nu este disponibil, iar paginile Pull Requests/Issues nu au putut fi citite în această sesiune. Commiturile de merge nu dezvăluie discuția sau review-ul. Nu afirmăm că repository-ul nu are Issues.

## Concluzii reutilizabile și reevaluate

| Concluzie veche | Status | Dovezi actuale și tratament |
|---|---|---|
| Pornirea Next, validarea răspunsului SIM și erorile SQLite/filesystem aveau defecte P1. | **REZOLVATĂ** | Addendumul din docs/BACKEND_AUDIT.md raportează fixuri; codul validează răspunsul engine în backend/engine_contract.py și normalizează erorile în backend/storage.py. Suita curentă a trecut 138 teste în mediul Etapei 1. |
| Integrarea SIM nu era reproductibilă în checkout curat/CI. | **PARȚIAL REZOLVATĂ** | Workerul curent pornește SIM din repository-ul configurat și înregistrează revizia; fluxul fixture a trecut local. OSM live nu a fost testat. |
| Contractul era divergent și funcțiile din specificația extinsă lipseau. | **PARȚIAL REZOLVATĂ** | Fluxurile conectate și endpoint-urile /api/v1/spatial/* există. Autentificarea, izolare tenant, scenarii de proiect, export, joburi/SSE și metrici extinse rămân propuneri. |
| Zona selectată nu producea analiză geografică reală. | **PARȚIAL REZOLVATĂ** | Există un flux separat de graf pietonal, cu fixture sau sursă OSM. Semaforizarea rămâne sintetică; workerul OSM cere numai rețea walk și exclude features. Nu s-au verificat date live aici. |
| Evaluarea grafului pietonal selectează comparația precomputată la crearea studiului. | **CONFIRMATĂ** | backend/spatial_routes.py returnează impactul candidatului din studiul salvat; evaluated_at este timpul creării studiului. |
| Lipsesc conturi, izolare multi-tenant, proiecte, export și colaborare. | **CONFIRMATĂ** | SQLite păstrează rezultatele, dar nu există login, ownership, permisiuni, proiecte, ștergere publică sau export de raport. |
| AI cloud și impact de trafic calibrat nu sunt implementate. | **CONFIRMATĂ** | Propunerile sunt deterministe; timing-ul este model sintetic; API/UI nu rulează SUMO. Binarul sumo și netconvert nu au fost găsite în PATH. |
| Backend doar /health, UI doar fixtures, SIM doar smoke. | **DEPĂȘITĂ** | Descrieri din V1, docs/API_CONTRACT.md, docs/ARCHITECTURE.md și unele statusuri nu corespund implementării curente. Rutele și fluxurile conectate au fost probate. |
| Specialistul în mobilitate/urbanism este publicul central; administrația și consultanța pot cumpăra produsul. | **NECESITĂ CERCETARE** | Repository-ul susține relevanța sarcinilor, dar nu conține interviuri, utilizatori, bugete, achiziții sau disponibilitate de plată. |
| Impactul social și avantajul față de unelte GIS/simulare sunt demonstrate. | **NECONFIRMATĂ** | Nu există măsurători în teren sau comparații independente. Nu se preiau ca beneficii realizate. |

## Surse de adevăr pentru audit

- Web curent: frontend/web/src/features/workspace/ConnectedWorkspace.tsx, SpatialPanel.tsx, frontend/web/src/features/neighborhoods/NeighborhoodExplorer.tsx, frontend/web/src/features/map/MapViewport.tsx și frontend/shared/core/api.ts.
- API și persistență: backend/main.py, backend/models.py, backend/spatial_routes.py, backend/spatial_worker.py, backend/spatial_adapter.py, backend/storage.py.
- Metode și limite: backend/simulation_adapter.py, sim/analysis.py, sim/candidates.py, sim/impact.py, sim/proposal_validation.py, sim/sumo_engine.py, sim/STATUS.md.
- Handoff-ul de pe main trebuie citit direct din ref origin/main la e785649; acele fișiere nu sunt în branch-ul local auditat.

Mai multe rapoarte de pitch și inventar au același autor Git și aceeași zi. Apariția aceleiași concluzii în mai multe fișiere nu este confirmare independentă. Etapa 1 a reverificat codul, a rulat testele disponibile și a executat fluxuri fixture. Nici codul, nici aceste teste nu confirmă singure că indicatorul reflectă realitatea locală sau că un specialist îl găsește folositor.
