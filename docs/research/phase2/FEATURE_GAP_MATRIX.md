# Matricea nevoilor și decalajelor

**Snapshot cod:** ed69c2d / origin/codex/ppt-finalized. Recomandările sunt ipoteze de prioritizare, nu solicitări colectate de la clienți. Vezi [auditul Etapei 1](../PROJECT_AUDIT_V2.md), [nevoile profesionale](PROFESSIONAL_NEEDS_RESEARCH.md), [date și standarde](DATA_AND_STANDARDS.md) și [scenarii](PROFESSIONAL_WORKFLOWS.md).

## Clasificări

- **Obligatoriu pentru utilizare profesională:** status/proveniență/metodă/unități corecte, inputuri validate, warnings și rezultat reproductibil.
- **Important pentru eficiență:** hartă conectată la rezultate, export standard, versionare/scenarii și link reproductibil.
- **Opțional:** dashboard, comentarii avansate sau colaborare publică, până când workflow-ul o cere.
- **Experimental:** AI/LLM sau ranking nou; măsurători nu pot fi generate de LLM.
- **Necesită validare suplimentară:** predicție, siguranță, acces universal, impact asupra populației, cost sau feasibility.

Prioritatea ordinală cântărește impactul asupra corectitudinii și siguranței, frecvența susținută de ghiduri, dovezi, complexitate și risc. Nu este un scor statistic.

## Matrice profesională

| Profil | Problemă profesională | Instrumente existente | Ce oferă ARTERIA | Lipsuri | Dovezi | Prioritate |
|---|---|---|---|---|---|---|
| Analist GIS/rețele | QA topologie/snap, rutare și layer export | QGIS, ArcGIS, OSMnx | Graf OSM/fixture, candidate checks, comparație OD eșantion | QA complet, geometry overlays, snapping report, GPKG export | QGIS docs + issues 9029/63045; cod spatial | **Important**, după corectitudinea etichetei |
| Planificator transport | Scenarii multimodale pe aria funcțională cu fluxuri reale | Visum/OpenPaths, GIS, spreadsheets | Timing sintetic și graf pietonal, separate | Demand model, GTFS, population, strategic KPIs, integrated layers/ex-post | Ghid PMUD 2025, EC SUMP, Legea 155 | **Obligatoriu** doar după selectarea unui task bounded |
| Inginer semaforizare | Timpi/faze sigure și performante pe counts și geometrie reală | Vissim/Aimsun/SUMO și metode capacity | Green-split synthetic demo | counts, phase/lane data, pedestrians, queue/corridor, calibration | FHWA manuals/guides, Legea 155, backend formula | **Experimental**, utilizare profesională necesită validare |
| Urbanist | Leagă mobilitatea de planuri, parcele, servicii, spațiu public | GIS, urban plans, modele transport | Catalog parțial și visual concept | PUG, uses, editing, site constraints, report | PMUD Guide și HCL Iași 403 | **Important** dacă interviurile confirmă cazul |
| Consultant mobilitate | Studiu repetabil și predare către client | GIS, documente, model tools | Comparație într-o sesiune; persistence API | projects, ownership, import/export, audit/review | GPKG PMUD requirement; workflow local not interviewed | **Important** după customer discovery |
| Administrație/autoritate | Prioritizează, justifică, administrează și monitorizează măsuri | PMUD/GIS/open data/procurement | demonstrații synthetic și graph | official sources, GPKG report, access roles, approval/ex-post | Legea 155, Ghid 2025, PMUD Iași | **Important** pentru discovery; cerințe de hosting ridicate |
| Accesibilitate pietonală | Traseu continuu fără bariere pentru un profil dat | GIS + field audit + normative | Topologie walk numai | sidewalks, widths, slope, ramps, surfaces, crossings, user profile | NP051, EN17210, OSM studies | **Necesită validare suplimentară** înaintea unei afirmații de acces |
| Operator/planificator CTP | Legături stop, orare, fiabilitate și călători | GTFS/RT, AVL, operations tools | Nimic de transit end-to-end | feed import, temporal routing, ridership/performance | CTP Open Data page and EC urban transport | **Important** numai dacă utilizatorii și drepturile se confirmă |
| Auditor rutier/proiectant | Siguranță, legal și feasibility pentru infrastructură | planșe, field audit, crash/exposure data | candidate graph and mapped building screening | safety method, roads/traffic input, surveyed constraints, statutory review | Legea 265/2008 și 155/2023 | **Necesită validare suplimentară**; tool-ul nu substituie auditorul |

## Matrice funcțională transversală

| ID | Decalaj / stare | Clasificare | Impact, dovezi, complexitate/risc | Recomandare |
|---|---|---|---|---|
| F01 | Fixture caption greșit ca OSM; confirmat în browser, SpatialPanel.tsx:158 | **Obligatoriu** | Risc direct de proveniență falsă; remediere mică | Corectați eticheta și adăugați test de source mode |
| F02 | Bookmark timing fără boundary; backend returns synthetic/layers unknown | **Obligatoriu** | Risc de a înțelege selectorul drept analiză geografică | UI spune clar synthetic; definiți un singur bounded study identity |
| F03 | Rezultatele și candidate geometry nu sunt desenate pe hartă | **Important** | Handoff PR #4 și audit cod confirmă; efect mare pentru GIS review | Overlay baseline/candidate/results, legend and source |
| F04 | OSM snapshot/QA și availability | **Obligatoriu** pentru analiză OSM | Live request Etapa 1 netestată; OSM quality și public API limits | Persist source/date/hash/filters, cache bounded, QA and field check |
| F05 | Provenance, method, units, uncertainty per output | **Obligatoriu** | Legea/PMUD și EU data process; risc interpretare synthetic/unknown | Evidence contract comun pentru fiecare indicator |
| F06 | Export GPKG/report | **Important** | Ghid PMUD cere GPKG layers; GIS task | GPKG + accessible report + manifest, după workflow validation |
| F07 | GTFS/transit | **Experimental**, apoi important dacă validat | Feed local declarat public, dar neinspectat | Validate feed offline and license before app integration |
| F08 | Delay semafor/model traffic | **Necesită validare suplimentară** | Synthetic input vs FHWA counts/queues/phases; safety risk | Keep illustrative; define Romanian method with engineer first |
| F09 | Populație/equity effects | **Experimental** | Sample OD graph is not residents or trips | Keep pair-count metric; acquire demand/denominator and validate |
| F10 | Universal accessibility | **Necesită validare suplimentară** | OSM tags/worker features insufficient; normative/field needed | Do not label route accessible; consult experts and users |
| F11 | Runtime JSON schema validation | **Obligatoriu** reliability | shared api.ts casts success response as T | Add runtime schema validation before new integrations |
| F12 | Projects/auth/sharing | **Important** for organization pilot | Code confirms missing owner/tenant; no user research yet | Define data owner/roles/retention before importing client datasets |
| F13 | Versioning, comments, report review | **Important** for consulting/authority | Candidate baseline exists; workflow not implemented | Add immutable revision/history after user research |
| F14 | SUMO API/UI | **Experimental** | runner code exists, no execution in Etapa1 env or connected UI | only connect with demand/calibration and explicit run/replay/failure state |
| F15 | LLM | **Opțional/experimental** | no user benefit evidence; deterministic paths already exist | defer; never generate measurements or compliance |
| F16 | Production readiness/security | **Obligatoriu before external institutional data** | no auth/readiness/queue demonstrated | threat/data-flow and operational review before external pilot |
| F17 | Accessibility in web UI | **Important/obligatoriu for public use** | partial keyboard/ARIA check only | WCAG review with assistive tech and responsive map alternative |

## First product slice

1. Correct status/provenance wording and tie one bounded area/source to its results.
2. Validate one GIS task: flag a pedestrian network discontinuity and compare a hypothetical link, with a visible map.
3. Provide reproducible GPKG + report: source snapshot, method, units, assumptions, warnings, sample denominator and unknowns.
4. Verify output with independent GIS analysis and a local walk audit.
5. Only then decide whether the next slice is CTP/GTFS, accessibility details, traffic model or collaboration. No source establishes that any single slice is already demanded by buyers.
