# Strategie de dezvoltare a produsului web

Aceasta este o propunere de cercetare și produs, nu aprobarea implementării. În Etapa 2 codul nu a fost schimbat.

## Poziționare validată de implementare

ARTERIA este azi un prototip conectat cu două capabilități separate: comparație semaforică pe input sintetic și screening pietonal pe graf/fixture. Niciuna nu este validată în teren. Nu este model multimodal local, proiect tehnic, audit de siguranță sau instrument de aprobare a investițiilor.

Slice-ul cu distanța cea mai mică față de cod este analiza bounded GIS: selectează o zonă/snapshot, verifică graf walk, examinează o întrerupere, adaugă link ipotetic, compară aceleași OD pairs și exportă mapă + GPKG + metodă. GIS analyst e utilizator de descoperire propus, nu client confirmat.

Traffic engineering are risc și date necesare semnificativ mai mari. Mențineți demo-ul synthetic până când un inginer local stabilește input, metodă și reper de calibrare. Nu integrați SUMO/AI doar pentru paritate cu concurenții.

## Gate 0: înțelegerea utilizatorului și a cazului

- Intervievați GIS analyst, planner/consultant, inginer trafic, specialist accesibilitate, CTP și autoritate.
- Cereți un task recent și artefactul livrat: date, software, verificare manuală, aprobare și export.
- Selectați user, area, task, decision boundary and acceptance criteria. Nu extrapolați de la un interviu la piață.
- Inventariați drepturile și schema pentru PMUD Iași, portal local și feed CTP; nu trimiteți date către API public fără terms review.

## Faza 1: corectitudine și reproducibilitate

- Etichete pentru observed/calculated/synthetic/simulated/replay/unknown, unit, method, date, provenance and coverage.
- Aliniați eticheta sursei fixture/OSM și identitatea geografică a timing/spatial flows.
- Salvați source snapshot/hash, network parameters, source timestamps, CRS, method/version, baseline/scenario, OD sample, warnings and run ID.
- Adăugați QA pentru bad snapping, disconnected links, overpass/bridges, permissions, missing tags și unknown coverage.
- Validați o zonă Iași în paralel cu GIS/field walk. Recalculați aceeași metrică pe snapshot versioned.

## Faza 2: livrabil GIS bounded

Numai dacă Gate 0 confirmă cazul:

1. Map-first area selection plus baseline/candidate/result overlays.
2. GPKG import/export for spatial layers, plus JSON manifest and CSV comparison.
3. Accessible HTML/PDF report: purpose, inputs, map, methods, units, snapshot, findings, assumptions, unknowns, sample denominator and review status.
4. Deep link or project save to reproduce the same result.

Acceptance: independent GIS user opens exported files, traces each result to source/method, and reproduces comparison on same snapshot. Numeric target for acceptable discrepancies must be agreed with reviewers before pilot.

## Faza 3: date și metode de transport

- Start with CTP GTFS feed validation offline: terms, schema/calendar/coverage. Build no live route planner until specific task and data rights are known.
- Traffic lane: specify a locally accepted method, turning counts, phase/geometry inputs, pedestrian service, queues and field measurements; validate independently before labeling professional.
- SUMO: run only on suitable network and demand; outputs include version, config, seeds/replications, input hashes, real status and calibration/field fit. Synthetic demand yields synthetic scenario evidence only.
- Aimsun/PTV/Visum comparison: interview existing model users and test whether the job should export/import their model. No need to clone their full suites.

## Faza 4: instituții și operare

If the pilot requires team use: user/tenant ownership, roles, project/history, retention and deletion, audit, backup, job queue, readiness checks, rate limits, monitoring, hosting and incident support. Design data separation before uploading client data. For public use, audit contrast, keyboard/screen reader, map alternative and accessible exports.

## Faza 5: AI după un beneficiu măsurat

AI may organize evidence or draft bounded candidate descriptions only if a user task is slower today and validation can catch unsupported output. Candidate geometry must pass independent catalog/schema, evidence and spatial checks. LLM must not invent measurements, cost, population impact, compliance or simulation results. Test hallucinations, bias, prompt injection, abstention and reproducibility with professionals. If deterministic rules solve the task, keep them.

## Raportare și comparații

Report must distinguish input measurement from calculated output, simulation from replay, and unknown from zero. Include coverage, uncertainty/sensitivity, date, method and responsible reviewer. Compare ARTERIA to QGIS/ArcGIS/SUMO/Aimsun on one task and identical input; measure time, errors, rerun and export acceptance. No superiority claim without a comparative study.

## Indicatori pentru un pilot

Set targets with participants before pilot: task completion/export validity; time-to-result versus current method; discrepancy versus independent reference; independent rerun success; user comprehension of synthetic/observed/unknown; coverage/error rate; output accepted into workflow; privacy/access review passed. Completion is not an adoption contract; satisfaction is not model validation.

## Riscuri și dependențe

| Risc | Consequence | Need before wider use |
|---|---|---|
| Synthetic output mistaken for local prediction | wrong decision or loss of trust | distinct labels, UI tests and user comprehension |
| OSM omission/staleness/topology issue | false route/absence | local snapshot QA, ground truth and licensed official data |
| Public API rate/availability limits | unstable service or policy violation | cache/hosted extracts and terms review |
| No demand/turns | unjustified traffic/access numbers | unknowns or measured input, not invented values |
| Incorrect accessibility/safety claim | harmful or non-compliant result | local qualified specialists and field audit |
| Missing project authorization/security | data leakage or unowned files | authentication, retention and tenant review |
| Data licenses conflict with redistribution | unlawful export | dataset-specific rights review |
| Miscalibrated stochastic simulation | false precision | calibration, replication/seed and measured validation |
| Competitor feature sprawl | cost and complexity without demand | build only after observed workflow |

## Propunere pentru Etapa 3

După aprobarea rezultatelor Etapei 2, propun o etapă de validare cu persoane reale, fără implementare:

1. Alegeți o zonă Iași bounded și dataset cu permisiuni confirmate.
2. Faceți 6–8 discovery sessions cu GIS, planner, consultant, inginer, accessibility user/specialist, CTP și autoritate. Acesta este eșantion exploratoriu, nu reprezentativ statistic.
3. Observați un task recent și validați un low-fidelity flow/report draft.
4. Validați feedul/datele locale, OSM comparison, standard/metodă și reviewer-ul.
5. Stabiliți acceptance criteria, product scope, risks and go/no-go pentru pilot.
6. Raportați ce au spus participanții separat de concluziile documentare; cereți aprobare explicită înainte de etapa de implementare.

Nicio persoană nu a fost contactată în Etapa 2.
