# Registrul surselor și dovezilor

**Consultate la 18 octombrie 2026.** Linkuri pentru verificare, nu garanție de disponibilitate permanentă. Pagini de vendor descriu afirmațiile vendorului. Probleme GitHub individuale ilustrează cazuri, nu prevalență. Nu au fost intervievați profesioniști și niciun dataset local nu a fost descărcat/validat.

## România, Iași și Uniunea Europeană

| ID | Sursă și dată | Relevanță și limită |
|---|---|---|
| R01 | [Legea 155/2023](https://legislatie.just.ro/Public/DetaliiDocument/270923), publicată 31.05.2023 | Cadrul românesc; art. 34 vulnerabili/calmare, art. 36 ex ante/ex post, art. 37 model PMUD pentru municipii peste 100k. Interpretarea proiectului cere jurist/autoritate. |
| R02 | [Ghid PMUD MDLPA](https://legislatie.just.ro/Public/FormaPrintabila/00000G013NPGKH2Q66M0MUBJZTGP02MX), Ordin 22.10.2025 | Diagnostic, moduri, mediu, safety, accessibility, demand model/calibrare/validare și seturi spațiale GPKG. Ghid pentru documente PMUD, nu specificație universală de produs. |
| R03 | [HCL 403/31.10.2023 și documentația PMUD Iași](https://www.primaria-iasi.ro/dm_iasi/hotarari.nsf/352F4896F69AD4A9C2258A6D00440C3B/%24FILE/HCL_403_2023.pdf?Open=) | Aprobare PMUD pol de creștere; raport municipal descrie aria și perioada 2021–2035. Pentru dataset-uri trebuie consultate anexele complete. |
| R04 | [CTP Iași Open Data](https://www.sctpiasi.ro/servicii/opendata), acces 18.10.2026 | CTP spune că publică GTFS cu date la interval de 20s și hartă live. Nu am verificat feed-ul, licența, schema sau SLA. |
| R05 | [Portal Open Data Iași](https://iasi.oras.digital/), acces 18.10.2026 | Portal local anunță date reutilizabile; fiecare set cere termeni, update și coverage review. |
| R06 | [Eurostat GISCO administrative units](https://ec.europa.eu/eurostat/en/web/gisco/geodata/administrative-units), acces 18.10.2026 | Limite și condiții licență; unele unități nu sunt comercial utilizabile fără acord. Verifică produsul concret; nu e limită juridică locală. |
| R07 | [Ordinul 189/2013: NP 051-2012](https://legislatie.just.ro/Public/DetaliiDocument/145914) | Aprobare oficială normativ accesibilitate mediu construit. Specificațiile tehnice nu sunt reproduse aici. |
| R08 | [Reglementare 01.02.2023](https://legislatie.just.ro/public/DetaliiDocument/264751) | Referă NP 051 pentru circulații pietonale persoane cu handicap; relevanța se stabilește pe proiect. |
| R09 | [Legea 265/2008 republicată](https://legislatie.just.ro/Public/DetaliiDocument/140786) | Cadru pentru audit/inspecție siguranță, independență și inspectare; algoritmul nu îl substituie. |
| R10 | [Ordin 233/2016](https://legislatie.just.ro/Public/DetaliiDocument/267783) | Context de corelare PMUD/urbanism; modificat în timp, ghid 2025 are prioritate unde a înlocuit conținut. |
| R11 | [EC Sustainable Urban Mobility Plans](https://transport.ec.europa.eu/transport-themes/urban-transport/sustainable-urban-mobility-planning-and-monitoring_en), acces 18.10.2026 | Zona funcțională, fluxuri reale, participare, colaborare, TEN-T and indicators; general policy, nu fapt despre fiecare oraș. |
| R12 | [SUMP guidelines third edition](https://urban-mobility-observatory.transport.ec.europa.eu/sustainable-urban-mobility-plans/guidelines-developing-and-implementing-sustainable-urban-mobility-plan-0_en), 08.06.2026 | Ediția europeană curentă și destinatarii. Full guide/annex should be reviewed for details. |
| R13 | [EC urban public transport/shared mobility](https://transport.ec.europa.eu/transport-themes/urban-transport/urban-public-transport-shared-mobility_en) | Policy discusses accessibility and urban/periurban transit. |
| R14 | [European Accessibility Act, Directive 2019/882](https://eur-lex.europa.eu/eli/dir/2019/882/oj), 07.06.2019 | Product/service scope and built environment provisions. ARTERIA applicability requires legal scope analysis. |
| R15 | [CEN-CENELEC EN 17210 update](https://www.cencenelec.eu/news-events/news/2026/en-in-the-spotlight/2026-02-26-en-17210-2021/), 26.02.2026 | Revision underway; forecast publication 2027, not final standard at research time. |
| R16 | [NEN overview EN 17210:2021](https://connect.nen.nl/Standard/Detail/3641676), 2021 edition | Scope includes outdoor pedestrian/urban spaces. Full standard is licensed and overview is not substitute. |

## Metode, date și geospatial

| ID | Sursă | Relevanță și limită |
|---|---|---|
| D01 | [FHWA Signal Timing Manual Ch.2](https://ops.fhwa.dot.gov/publications/fhwahop08024/chapter2.htm) | Timing objectives and performance; US guidance, not Romanian regulation. |
| D02 | [FHWA Signal Timing Manual Ch.3](https://ops.fhwa.dot.gov/publications/fhwahop08024/chapter3.htm) | Delay/queue definitions and field measurement limits. |
| D03 | [FHWA traffic data for operations](https://www.fhwa.dot.gov/policyinformation/pubs/traffic-data-applications-highlights/traffic-data-for-operations.cfm) | Volumes, queues, vehicle classes, signal timing, pedestrian/bicycle counts. |
| D04 | [FHWA Signalized Intersections Guide PDF](https://safety.fhwa.dot.gov/intersection/signal/fhwasa13027.pdf), FHWA-SA-13-027 | Turning-count intervals, pedestrian actuation and model limitations under oversaturation. US source. |
| D05 | [TRB HCM Sixth Edition](https://trb.org/publications/hcm6e.aspx) | US multimodal capacity/quality manual. Licensed; not assumed Romanian standard. Later-edition applicability not independently resolved. |
| D06 | [QGIS 3.44 network analysis](https://docs.qgis.org/3.44/en/docs/user_manual/processing_algs/qgis/networkanalysis.html) | Shortest path, service area, impedance, non-routable output and export. Algorithm docs don't validate input graph. |
| D07 | [OSM copyright/licence](https://www.openstreetmap.org/copyright) | ODbL and attribution/share-alike. Derived database classification needs legal review. |
| D08 | [OSMF attribution guidelines](https://osmfoundation.org/wiki/Attribution_Guidelines), adopted 25.06.2021 | Attribution should make source apparent; full license governs. |
| D09 | [OSMnx stable getting started, v2.1.1 docs](https://osmnx.readthedocs.io/en/stable/getting-started.html) | OSMnx relies on tags/settings and respects Overpass rate limits; high volume use merits own instance. |
| D10 | [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/) | Public service max 1 request/second and bulk-geocoding limitation; only applies to that endpoint. |
| D11 | [Overpass commons docs](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html) | Public instance resource limits and hosting considerations; load-dependent. |
| D12 | [Barrington-Leigh & Millard-Ball, 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6042734/) | Peer-reviewed quality signal study over 28 global cities; intrinsic metrics cannot diagnose all error types alone. No Iași field result. |
| D13 | [Crowdsourcing and Sidewalk Data, 2022 preprint](https://arxiv.org/abs/2210.02350) | Sidewalk data completeness challenge; preliminary US-focused study. |
| D14 | [OSMnx network methods paper](https://arxiv.org/abs/1611.01890), 2017 | Technical capabilities to acquire, construct, analyze and export networks; current docs take precedence. |
| D15 | [EU road infrastructure safety directive 2008/96/EC](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32008L0096), [EC overview](https://road-safety.transport.ec.europa.eu/eu-road-safety-policy/priorities/infrastructure/roads_en) | EU safety-management framework and 2019 update; check Romanian transposition/current scope. |

## Software vendors, projects and issues

| ID | Sursă | Ce susține |
|---|---|---|
| C01 | [QGIS license](https://www.qgis.org/license/) | GPL/open source. No operations/support total cost. |
| C02 | [ArcGIS Network Analyst licenses](https://doc.esri.com/en/arcgis-pro/latest/help/analysis/networks/licensing-and-the-network-analyst-extension.html) | Network capabilities gated by extension. |
| C03 | [ArcGIS Pro license levels](https://doc.esri.com/en/arcgis-pro/latest/get-started/license-levels.html) | Basic/Standard/Advanced tied to user type/capabilities. |
| C04 | [Esri pricing page](https://www.esri.com/en-us/arcgis/products/arcgis-pro/buy) | User-type purchase model; no Romania-specific total price used. |
| C05 | [PTV Vissim packages/pricing](https://www.ptvgroup.com/en-us/products/ptv-vissim/pricing) and [FAQ](https://www.ptvgroup.com/en/products/ptv-vissim/faqs) | Features/packages, quote-based price, vendor statement that calibration/data/geometry matter. |
| C06 | [PTV Visum](https://www.ptvgroup.com/en-us/products/ptv-visum) | Product-listed network, demand/activity-based modelling and scenario tools. Vendor source. |
| C07 | [Aimsun public prices](https://www.aimsun.com/aimsun-next-editions-prices/) and [licensing manual](https://docs.aimsun.io/next/latest/UsersManual/AimsunLicensing.html) | Edition capabilities; accessed prices €2,000/3,500/5,500/7,500 per seat/year. Prices change, vendor source. |
| C08 | [SUMO docs](https://sumo.dlr.de/docs/) and [netconvert](https://sumo.dlr.de/docs/netconvert.html) | Network conversion, demand, simulation, output and TraCI. |
| C09 | [SUMO FAQ](https://github.com/eclipse-sumo/sumo/blob/main/docs/web/docs/FAQ.md) | Random routes can be unrealistic; reproducible bug reports need scenario/config inputs. |
| C10 | [SUMO issue #17399](https://github.com/eclipse-sumo/sumo/issues/17399), Dec. 2025 | One calibrator regression fixed for 1.26; example only. |
| C11 | [MATSim official site/docs](https://www.matsim.org/), [install guide](https://www.matsim.org/install/) | Open agent-based framework; scenario demand/network and technical configuration required. |
| C12 | [Bentley OpenPaths](https://www.bentley.com/products/openpaths) | Multimodal/model features and vendor starting prices $9,951 Advanced / $12,877 Ultimate per 12-month subscription, accessed 18.10.2026. |
| C13 | [OpenTripPlanner docs](https://docs.opentripplanner.org/en/latest/) | Complementary open-source multimodal transit routing, not a traffic simulator. |
| C14 | [QGIS issue #9029](https://github.com/qgis/QGIS-Documentation/issues/9029), Apr. 2024–2025 | Snapping far endpoints caused meaningless results; max-distance option added. |
| C15 | [QGIS issue #63045](https://github.com/qgis/QGIS/issues/63045), opened Sep. 2025, open at access | One report of false graph junction at grade-separated roads; no prevalence estimate. |
| C16 | [OSRM issue #4790](https://github.com/Project-OSRM/osrm-backend/issues/4790), Jan. 2018 | Separate sidewalk tagging/routing behavior discussion; old, specific example. |
| C17 | [OSRM issue #6008](https://github.com/project-osrm/osrm-backend/issues/6008), Apr. 2021 | One foot/bike profile and tagging question. |

## Repository and previous work

| ID | Sursă | Ce susține |
|---|---|---|
| A01 | [Previous analysis review](../PREVIOUS_ANALYSIS_REVIEW.md) | Provenance/status of earlier reports; repetition is not independent verification. |
| A02 | [Etapa 1 project audit](../PROJECT_AUDIT_V2.md) | Inventory at HEAD ed69c2d and test/browser/environment evidence. |
| A03 | [Etapa 1 professional profiles](../PROFESSIONAL_USER_PROFILES.md) | Initial role hypotheses from code, without interviews. |
| A04 | [Etapa 1 gap analysis](../GAP_ANALYSIS.md) and [roadmap](../RESEARCH_ROADMAP.md) | Earlier gaps/questions; Stage2 updates, not overwrites them. |
| A05 | [Historical project research](https://github.com/AlexPintilie08/arteria/blob/ed69c2d08940f6fc516acbf87ca7ece54426f4ca/docs/ppt/research/PROJECT_RESEARCH_FULL.md) and [reality audit](https://github.com/AlexPintilie08/arteria/blob/ed69c2d08940f6fc516acbf87ca7ece54426f4ca/docs/ppt/reports/PROJECT_REALITY_AUDIT.md) | Prior repository analysis; authors/date/caveats listed in previous-analysis review. |
| A06 | HEAD ed69c2d08940f6fc516acbf87ca7ece54426f4ca; origin/main e785649308923c0c91de40ebb1b0b85b5962962e; origin/codex/ppt-finalized equalled HEAD at Stage1 | Branch context. No merge/rebase/reset in Stage2. |
| A07 | frontend/web ConnectedWorkspace.tsx, SpatialPanel.tsx, NeighborhoodExplorer.tsx, MapViewport.tsx; frontend/shared/core/api.ts | Web flows, source label, map/result state and JSON response cast. |
| A08 | backend/main.py, simulation_adapter.py, spatial_routes.py, spatial_worker.py, spatial_adapter.py, storage.py, models.py | Synthetic traffic, API routes, stored graph comparison, OSM worker and persistence. |
| A09 | sim/analysis.py, candidates.py, impact.py, scenario.py, sumo_engine.py, proposal_validation.py, STATUS.md | Graph calculation, candidates, sampled OD impact and conditional SUMO runner. |
| A10 | Etapa1 npm tests 9/9; web typecheck/build passed; pytest 138 passed with one deprecation warning; local browser fixture/API success | Technical evidence under isolated env, not model accuracy/adoption. Full env is in PROJECT_AUDIT_V2. |

## Dovezi, inferențe și necunoscute

- **Triangulated findings:** PMUD remit uses Romanian legal/technical framework plus EC SUMP; traffic inputs use FHWA methods plus PTV calibration caveat; OSM reliability uses peer-reviewed studies and OSMnx/Overpass/OSMF docs.
- **One-source authoritative claims:** CTP feed availability is CTP’s statement; PMUD coverage is the municipal HCL/report; vendor prices are vendor pages. Data/terms or quote need direct validation.
- **Anecdotal only:** GitHub issues are selected reports. No representative user review dataset or defect frequency.
- **Inference:** proposed features and priorities derive from professional documentation plus Stage1 code. No interview quote, adoption, or feature request claim.
- **Unknown:** local OSM quality; CTP schema/license/uptime; municipal data terms; traffic counts access; accepted local traffic method; user adoption; WTP; production security; productivity advantage.

## Limitări

No professional interviews; no systematic review analysis; prices exclude tax/support/compute; no full licensed normative copied; no GTFS/municipal data or live OSM downloaded; no field measurement, safety audit, or software benchmark. Before commitments, inspect PMUD spatial annex/model, validate CTP/local files, run OSM/orthophoto/field audit and interview the roles in [PROFESSIONAL_NEEDS_RESEARCH.md](PROFESSIONAL_NEEDS_RESEARCH.md).
