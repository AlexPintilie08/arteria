# Scenarii de lucru profesionale

**Cercetare documentară la 18 octombrie 2026.** Scenariile sunt reconstruite din ghiduri, legi și documentația software; nu sunt relatări din interviuri. „Demo acum” indică doar că există o cale demonstrată tehnic, nu că rezultatul e potrivit unei decizii profesionale.

## Analist GIS / rețele pietonale

### G1. Verifică conectivitatea pietonală între două destinații
- **Problemă/date:** traseu sau acces în rețea; arie, origine/destinație, graf walk, CRS, permisiuni și crossing-uri.
- **Flux și rezultat curent uzual:** QA geometrie/topologie, snapping limitat, rutare, inspectare și vector export; QGIS oferă shortest path/service area și ieșiri salvabile în GPKG/file/database.
- **ARTERIA acum:** OSM/fixture study, analiză de graf și candidate checks; browserul a observat caption fixture greșit ca OSM. Rezultatul nu este desenat pe hartă; tabelul folosește ID-uri.
- **Lipsă/verificare:** snap tolerance, disconnected edges, poduri/niveluri, rută, export; verifică independent în QGIS și cu field walk/sursă oficială. Demo fixture posibilă acum; rezultat pentru rețea reală cere verificare.

### G2. Testează o legătură ipotetică
- **Problemă/date:** identifică dacă un link ipotetic reduce distanța pentru perechi OD și ce perechi nu sunt comparabile.
- **Flux profesional:** fixează baseline, candidate geometry și OD sample, verifică eligibilitatea, aplică graful duplicat, compară aceleași perechi și revizuiește geografia.
- **ARTERIA acum:** acesta este cel mai apropiat flux: candidate generation/validation și pair sample comparison pe aceeași rețea.
- **Lipsă/verificare:** graficarea candidaților, eșantionul vizibil/exportabil, ponderare populațională, cerere, fezabilitate și cost lipsesc. Verificare cu calcul GIS independent și audit al punctelor de conexiune. Fixture demonstrată; OSM live netestat.

### G3. Predă layer pentru PMUD
- **Date/workflow:** baseline, candidate, CRSs, source metadata, validare și metodă; export vectorial editabil și explicație.
- **ARTERIA acum:** SIM și catalogul produc date interne/geografice, fără export profesional complet în UI.
- **Lipsă/verificare:** GPKG cu scheme, hash/snapshot, manifest și PDF/HTML; deschidere în QGIS și rerun independent. Nu e realizabil acum; schema trebuie confirmată cu autoritatea și ghidul PMUD.

## Planificator transport / mobilitate

### P1. Compară accesul la servicii prin 2 alternative
- **Date:** rețea walk/transit, destinații, GTFS, origine/cerere populație și praguri de timp.
- **Flux așteptat din SUMP/PMUD:** diagnostic, scenarii multimodale, impact pe accesibilitate/equity, consultare și evaluare.
- **ARTERIA acum:** numai comparație pietonală topologică pe sample; flow timing separat și sintetic.
- **Lipsă/verificare:** populație, GTFS, destinații, distribuții, export și metodă; validate cu QGIS/OTP și date oficiale. Partea graf e demonstrabilă; analiza multi-modală nu.

### P2. Prioritizează coridor de transport public
- **Date/workflow:** GTFS și timetable, AVL/delay, stop access, passenger counts, traffic/signals, amenajare; mapare catchment, performance și alternative.
- **ARTERIA acum:** nicio integrare GTFS; CTP publică un feed potrivit pentru verificare, dar Etapa 1 nu l-a descărcat.
- **Lipsă/verificare:** transit network, headways/reliability, ridership, multimodal assignment și costuri; validați feedul cu CTP și AVL/field. Cere integrare și metodă nouă.

### P3. Evaluează un pachet PMUD metropolitan
- **Date/workflow:** rețele/moduri, cerere, GIS, costuri, proiecte, indicatori; model transport, opțiuni teritoriale, consultare, monitorizare.
- **ARTERIA acum:** flux sintetic la intersecție și graf pietonal separat; fără identitate metropolitană unică, demand model sau buget.
- **Lipsă/verificare:** model calibrat, scenarii multimodale, GPKG, colaborare și ex-post. Verificați contra HCL PMUD și măsurători. În afara capacității actuale.

## Inginer trafic / semaforizare

### T1. Revizuire timing intersecție
- **Date/workflow:** turning counts, geometry/lane groups, phases/current plan, queues, pedestrian requirements; field observation, model/control-delay analysis, safety review.
- **ARTERIA acum:** analyze→propose→evaluate schimbă un singur verde cu cerere/capacitate sintetice.
- **Lipsă/verificare:** intrări măsurate, scheme multiphase, lost times, saturation flow, queues, local standard și field comparison. Doar demo sintetic acum; method review cu inginer român necesar.

### T2. Diagnostic de spillback/coordonare
- **Date/workflow:** mai multe intersecții, offsets/cycles, queue distributions, travel-time, tram/bus; model corridor și coordonare.
- **ARTERIA acum:** nicio geometrie/coridor/queue/offset, API/UI nu execută SUMO.
- **Lipsă/verificare:** rețea pe benzi, control plan, demand profile, simulator calibration, multi-seed output; verificați cu controller logs și teren. Necesită date și model nou.

### T3. Măsoară efect după implementare
- **Date/workflow:** observații înainte/după, control/periods, implementation date, flows, queue, crossing/safety; comparație cu confounders și raport.
- **ARTERIA acum:** comparație de model sintetic, fără date observate ex post.
- **Lipsă/verificare:** timeseries, matched period, control area și safety inputs; verificați prin protocol de teren. Legea 155 art. 36 face subiectul relevant; suport curent absent.

## Urbanist / specialist dezvoltare urbană

### U1. Evaluează continuitatea cartierului
- **Date/workflow:** PUG, parcel/use, public space, street/sidewalk, services; overlay, plan options și review urbanistic.
- **ARTERIA acum:** catalog parțial și scenă 3D conceptuală, fără PUG/parcels ori intervenții urbanistice desenate.
- **Lipsă/verificare:** reglementări, funcțiuni și geometry; reconciliere cu documente oficiale și urbanist. Vizualul curent e doar conceptual.

### U2. Compară crossing/link/spațiu public
- **Date/workflow:** right-of-way, crossings, walk network, universal-access data, costs; alternatives and site review.
- **ARTERIA acum:** link ipotetic în graph; fără cost, access features sau construction feasibility.
- **Lipsă/verificare:** design geometry, utilizatori afectați, survey/cadastru/avize; GIS + walk audit + proiectant. Graph fixture only.

### U3. Explică alternativa unei comisii
- **Date/workflow:** options, map, assumptions, costs, effects and consultation records; report and annexes.
- **ARTERIA acum:** tabel înainte/după și warnings, fără export/shareable project.
- **Lipsă/verificare:** print map, accessible Romanian report, URLs and repeatable files; peer review and traceability. Internal screen share possible, formal handoff absent.

## Consultant de mobilitate

### C1. Pregătește un studiu comparativ contractat
- **Date/workflow:** client boundary, datasets, baseline, alternatives, methods; QA → calculation/model → review → report.
- **ARTERIA acum:** comparație synthetic timing și graph fixture/OSM workflow separat.
- **Lipsă/verificare:** project workspace, imports, data rights, method record, report export; client reviewer rerun. Demo only.

### C2. Refolosește workflow între clienți
- **Date/workflow:** template, local source, permission, version and user access across multiple studies.
- **ARTERIA acum:** fără projects/accounts/tenant; catalog static/bookmarks.
- **Lipsă/verificare:** multi-project, role permissions, isolate data/delete/export; security/access tests. Cere validare de workflow și infrastructură.

### C3. Răspunde la review comments
- **Date/workflow:** reviewer asks for geometry or input revision; version diff, rerun, reason and signed export.
- **ARTERIA acum:** validează intervenția exactă și baseline la API; nu are review/comments/history/exports.
- **Lipsă/verificare:** immutable versions, annotated diff, audit log; replay independently. Integrity primitive exists, work management absent.

## Administrație publică / autoritate

### A1. Triază o discontinuitate raportată
- **Date/workflow:** report/location, asset owner, street/sidewalk inventory; site check, prioritization and repair referral.
- **ARTERIA acum:** graph screen only; no citizen intake or official ownership layer.
- **Lipsă/verificare:** issue workflow, authority layers and inspection evidence; field inspection is decisive. No institutional flow current.

### A2. Pregătește dosar de scenarii PMUD/investiție
- **Date/workflow:** official layers, PMUD project list, traffic/transport, cost, constraints; compare departments/stakeholders and export spatial evidence.
- **ARTERIA acum:** demo functions, no official source import, GPKG report, approval workflow or users/permissions.
- **Lipsă/verificare:** data rights, institutional security, GPKG, audit and collaboration; reconcile with approved HCL/PMUD. Not fit as formal package today.

### A3. Monitorizează ex ante/ex post
- **Date/workflow:** baseline/post, implementation date, counts, periods, safety and control site; monitor and document outcome.
- **ARTERIA acum:** persisted simulated evaluation only.
- **Lipsă/verificare:** actual measurements, time-series, measurement protocol and results; authority attests source. No current support.

## Specialist accesibilitate / mobilitate activă

### X1. Verifică ruta fără bariere
- **Date/workflow:** sidewalk geometry/width, slope, curb ramps, surface, steps, crossings, signals, obstacles; route tool + field audit.
- **ARTERIA acum:** walk graph does not receive features, accessibility attributes, or user profile.
- **Lipsă/verificare:** surveyed facts, standard and user-group validation; field audit plus NP 051/EN 17210 review. No accessibility verdict possible today.

### X2. Evaluează traseu accesibil către transit/services
- **Date/workflow:** accessibility graph, GTFS, stop access, lifts/outages and destinations; multimodal routing by profile.
- **ARTERIA acum:** no GTFS integration; walking graph groundwork only.
- **Lipsă/verificare:** temporal accessible transit graph and field check. New data/method required.

### X3. Prioritizează sectoare de reabilitare trotuar
- **Date/workflow:** measured barrier/condition, population exposure, schools/health services, costs/ownership; transparent weighted ranking.
- **ARTERIA acum:** hypothetical link check; no evidence-backed ranking, population or costs.
- **Lipsă/verificare:** audit, criteria/weight sensitivity, community input; independent field validation. Not ready for priority order.

## Operator transport public (profil conex susținut de sursa CTP)

### O1. Verifică schimbare de traseu/orar
- GTFS/AVL, timetable, stops and passenger data; compare running times and connections.
- ARTERIA has no transit import. Verify CTP feed terms and schema; new flow.
### O2. Găsește goluri first/last mile
- Stops + accessible walking graph + destinations + demand. ARTERIA graph only; needs crossing/sidewalk, timetable and user check.
### O3. Măsoară efectul unei prioritizări de transport public
- Before/after AVL, signal plan, ridership and traffic. ARTERIA synthetic signal not linked to bus/AVL; needs field evaluation.

## Auditor de siguranță rutieră (profil conex susținut de Legea 265/2008)

### S1. Pre-screen al unei treceri
- Planuri, speed/volume, crossings, sight lines, vulnerable-user flows and site photos. ARTERIA gives graph geometry only; it cannot issue an audit finding. Qualified auditor/site check required.
### S2. Inspectează un segment
- Inspection on site, accidents/exposure and road inventory. ARTERIA has no safety workflow/data. Legal statutory procedure verifies.
### S3. Compare alternatives for safety
- Design geometry and risk method. ARTERIA has synthetic signal only; needs local method, qualified independent review, separate safety evidence.

## Verdictul implementabilității

- **Demonstrabil azi:** synthetic signal tradeoff; fixture graph and candidate comparison; OSM catalog/source flow in code (live fetch not tested).
- **Disponibil extern, dar neverificat în aplicație:** CTP GTFS/realtime, Iași open-data catalog and PMUD spatial attachments.
- **Necesită date/algoritmi noi:** transit access, population impacts, accessibility, safety, cost/feasibility and calibrated traffic.
- **Validare obligatorie:** site observations, qualified local technical review, licensing, user interviews and official standards. Sursele sunt indexate în SOURCES_AND_EVIDENCE.md.
