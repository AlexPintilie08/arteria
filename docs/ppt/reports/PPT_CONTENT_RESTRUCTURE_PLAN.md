# PPT content restructure plan

Prepared after the independent implementation inventory and original-claim audit, before publishing corrections. Apply through `scripts/audited_content.py`, after existing V2 shape/refinement creation. The following is exact proposed **visible** content (including retained headings/footers and editable table cells), followed by suggested Romanian speaker notes. Line breaks follow existing text boxes. The content pass preserves geometry, typography, colors and slide order; the later dedicated animation pass updates motion as documented in `MOTION_AUDIT.md` and `PREMIUM_MOTION_QA.md`.

## Overall narrative and structural decision

Keep the template sequence: user/problem → alternatives → simple workflow → one demo → architecture/AI boundary → business → market validation → team → concrete ask. The original first two slides named the user but lacked a concrete decision; the revised problem links directly to route comparisons. The architecture remains a three-component explanation rather than a technical specification. Same-sample graph comparison and candidate checks are worth main-slide space; detailed methodology, test scope and future AI flow remain Q&A. No missing slide justifies increasing the count. The market content is replaced in place; appendices remain only in the full working copy.

Official submission format and schedule conflict: see `HACKATHON_REQUIREMENTS_VERIFICATION.md`. A 13-slide working copy is not certified as a compliant ten-slide submission. The derivative contains slides 1–10 only.

| Current slide | Decision | Reason |
|---|---|---|
| 1 | KEEP WITH EDITS | The jury learns scope immediately without more cover text or a new slide. |
| 2 | KEEP WITH EDITS | A new hypothetical connection gives the user a concrete task linked to the implemented pedestrian study. Branches remain planning perspectives, explained in notes. |
| 3 | RESTRUCTURE | Keep the alternatives section and table; use its third row to explain the workflow without inventing competitor weaknesses. |
| 4 | KEEP WITH EDITS | One concise present-tense capability is stronger than a generic future promise. Notes explain eligible OSM polygons and stored evaluation. |
| 5 | KEEP WITH EDITS | One demo path remains understandable in 50 seconds. Replace only the cropped bitmap with a verified current capture in the same image geometry; no visual redesign. |
| 6 | KEEP WITH EDITS | AI status must be in the main presentation, given official evaluation criteria; no nonexistent model is added to improve the score. |
| 7 | KEEP WITH EDITS | The template asks who pays and an explicitly hypothetical price. Retention is defensible with visible qualification; it is not market validation. |
| 8 | REPLACE | Replace speculative commercial arithmetic within the existing slide geometry. Preserve its position to respect the ten-section template; no new market statistic is invented. |
| 9 | KEEP WITH EDITS | Translate without adding experience, ownership of handlers, full-time commitment or field expertise. |
| 10 | KEEP WITH EDITS | Use genuine implementation and validation gaps. No invented pilot, deadline or traffic reduction target. |
| 11 | KEEP WITH EDITS | Keep technical detail in appendix; report the meaning of tests instead of inventing coverage percentages. |
| 12 | KEEP WITH EDITS | This appendix explains existing engineering preparation for AI without relabeling it as an integrated LLM. |
| 13 | KEEP WITH EDITS | A methodology slide is useful when it tells the jury what actually makes comparisons controlled, and what that control cannot establish. |

## Important missing or underrepresented information

| Element | Why it matters to the jury | Verification | Placement / replacement | Pitch benefit |
|---|---|---|---|---|
| Shared seeded route sample; independent unchanged baseline | Makes alternatives comparable | impact.py:evaluate_candidates and regression tests; fixture API exercised | Slide 4 replaces generic present/future line; slide 13 gives method | Concrete defensible engineering result |
| Candidate-backed validation and bounded evidence packet | Shows preparation for constrained AI rather than invented AI | proposal_context/proposals/proposal_validation through worker and UI | Slide 6 future-provider text becomes current evidence/rules plus missing LLM; slide 12 details | Honest account of AI-related achievement and gap |
| Catalog source and eligibility | Demonstrates reuse across sourced areas | 24 polygons + 7 points, tests, canonical ID validation | Slide 4 notes and questions; do not crowd main workflow | Geographic credibility without claiming full city coverage |
| Stored comparison / SQLite | Explains traceability and avoids false new-run claims | spatial_routes.evaluate returns stored impact | Slide 6 disclosure and slide 13 notes | Reproducible decision trail |
| Adverse mean-delay tradeoff | Shows the system does not always display improvement | Formula and browser value at green 70 | Slide 5 headline/notes instead of place-based success framing | Defensible demo under questioning |
| Measured technical checks vs unmeasured city impact | Prevents tests being mistaken for product validation | Fresh check logs | Slide 11 notes, main slide 6 scope | Evidence proportional to claim |
| Missing runtime AI | Largest official criterion remains a gap | No provider call; deterministic metadata | Main slide 6 and roadmap 10 | Avoids hiding a material limitation in appendix |

Do not add full library capability lists, SUMO vehicle counts, old cached-route gains, authentication/export specs, mobile parity, or speculative global TAM. Those would increase text or imply integration/validation not demonstrated.

## Three-minute rehearsal allocation

Proposed allocation across slides 1–10: 1: 0s, 2: 25s, 3: 20s, 4: 10s, 5: 50s, 6: 30s, 7: 10s, 8: 10s, 9: 10s, 10: 15s. Total: 180s; cover is pre-roll. This is an allocation, not a verified successful rehearsal. The template also permits omitting market discussion at three minutes; the ten-slide submission retains that section. Reserve live demo for the existing synthetic path; open pedestrian details during questions if time does not allow both.

## Slide 1

**Current title:** ARTERIA

**Current purpose:** Identify product and user

**Problems identified:** Broad urban-planning positioning can imply more modules than the integrated workflows support. The cover image is the preview, not the connected API workspace.

**What should remain:** Product, team, event and prototype label; the authentic historical image with OSM credit.

**What should be removed:** Unqualified impression of complete urban-planning coverage; claim that image is current connected output.

**What should be added:** Name the two actual workflows; label the historical preview.

**Improved headline:** ARTERIA

**Exact proposed slide text:**

> ARTERIA / TITLU
> 01
> ARION · Hackathon AI Iași 2026
> Prototip demonstrativ
> Previzualizare istorică · © contributori OpenStreetMap
> ARTERIA
> Comparații de mobilitate
> pentru specialiști
> Semaforizare demonstrativă
> și acces pietonal pe graf

**Verified evidence supporting that text:** README.md; frontend/web/src/features/workspace/Workspace.tsx:App; ConnectedWorkspace.tsx; SpatialPanel.tsx.

**Suggested speaker notes:**

Ajutăm specialiștii în mobilitate să compare intervenții într-un prototip inspectabil. Astăzi există două fluxuri distincte: semaforizare sintetică și studiu pietonal pe graf. Captura este o previzualizare istorică, nu dovada unui geamăn digital complet. Nu revendicăm utilizatori, economii de timp sau efecte urbane măsurate.

**Reasoning behind the changes:** The jury learns scope immediately without more cover text or a new slide.

## Slide 2

**Current title:** O intervenție. Mai multe efecte.

**Current purpose:** State the user problem

**Problems identified:** The specialist is named, but the original problem is generic. Four transport branches can be mistaken for four implemented evaluation modules. No interviews, user quote or quantified loss is evidenced.

**What should remain:** Specialist as target; proposed-need disclosure; multimodal planning context.

**What should be removed:** Any implied empirical pain validation or multi-mode implementation.

**What should be added:** A concrete route comparison question and explicit unknowns.

**Improved headline:** Ce schimbă o legătură nouă?

**Exact proposed slide text:**

> ARTERIA / P / PROBLEMA
> 02
> Ce schimbă o legătură nouă?
> Caz de utilizare propus · fără interviuri validate · 18.10.2026
> Utilizator vizat: specialistul în mobilitate
> Specialistul trebuie să compare rutele înainte și după.
> Legătură nouă
> Transport public
> Pietoni
> Biciclete
> Trafic auto
> Ce rute se schimbă? Ce rămâne necunoscut?
> Nevoie propusă; interviurile cu utilizatori urmează.

**Verified evidence supporting that text:** sim/scenario.py:evaluate_scenario; sim/impact.py:evaluate_candidates. Nevoia utilizatorului este ipoteză, fără interviuri în repository.

**Suggested speaker notes:**

Cazul de utilizare propus: înainte de a discuta o legătură pietonală nouă, specialistul verifică ce rute devin mai scurte sau accesibile și pe ce date se bazează comparația. Diagrama arată perspective de planificare, nu patru module validate. Nu avem interviuri sau un cost al problemei măsurat. Nu inventăm o mărturie de utilizator.

**Reasoning behind the changes:** A new hypothetical connection gives the user a concrete task linked to the implemented pedestrian study. Branches remain planning perspectives, explained in notes.

## Slide 3

**Current title:** Instrumentele există

**Current purpose:** Acknowledge alternatives and proposed differentiation

**Problems identified:** QGIS/SUMO descriptions are fair, but PMUD is a planning document rather than a competing product. The original source list is not three independent proofs of ARTERIA demand.

**What should remain:** QGIS and SUMO; advantage still to be tested.

**What should be removed:** PMUD as an alternative product and any suggestion that competitors cannot compare scenarios.

**What should be added:** Data preparation/scenario comparison as a proposed work process, with qualified integration value.

**Improved headline:** Instrumentele există

**Exact proposed slide text:**

> ARTERIA / R / ALTERNATIVE
> 03
> Instrumentele există
> Surse: qgis.org · sumo.dlr.de · cod ARTERIA · consultate 18.10.2026
> QGIS
> Date și analiză geografică
> SUMO
> Simulare microscopică de trafic
> Procesul de lucru
> Pregătirea datelor și compararea variantelor
> ARTERIA leagă pașii într-un prototip:
> zonă → alternative → comparație
> Avantajul de utilizare trebuie validat cu specialiști.

**Verified evidence supporting that text:** https://qgis.org/project/overview/ ; https://sumo.dlr.de/docs/ ; backend/spatial_worker.py:calculate. Surse consultate 18.10.2026.

**Suggested speaker notes:**

QGIS oferă analiză geografică, iar SUMO simulare microscopică. Nu afirmăm că aceste instrumente nu pot compara scenarii sau că ARTERIA le depășește. Diferențierea propusă este un parcurs comun cu dovezi și limite vizibile. Rândul despre procesul de lucru descrie un caz propus, nu o observație din interviuri. PMUD este context instituțional, nu produs concurent sau dovadă de adopție.

**Reasoning behind the changes:** Keep the alternatives section and table; use its third row to explain the workflow without inventing competitor weaknesses.

## Slide 4

**Current title:** Parcursul unei comparații

**Current purpose:** Explain the user workflow

**Problems identified:** The three stages exist, but synthetic signals and spatial graph studies need separate interpretation. Valuable same-sample comparisons are missing.

**What should remain:** Select area → inspect alternatives → compare.

**What should be removed:** Generic future line duplicating roadmap.

**What should be added:** Same sampled routes for pedestrian alternatives; separate synthetic signal workflow.

**Improved headline:** Parcursul unei comparații

**Exact proposed slide text:**

> ARTERIA / B / SOLUȚIA
> 04
> Parcursul unei comparații
> 01
> Alege zona
> 02
> Examinează
> alternativele
> 03
> Compară
> scenariul
> Graf pietonal: alternative pe același eșantion de rute
> Separat: semaforizare sintetică; impact real nevalidat

**Verified evidence supporting that text:** frontend/shared/core/api.ts:createApiClient; frontend/web/src/features/workspace/SpatialPanel.tsx; backend/spatial_worker.py:calculate; sim/impact.py:evaluate_candidates; frontend/web/tests/sim-geography.test.ts.

**Suggested speaker notes:**

În modul conectat, utilizatorul poate analiza semaforizarea sintetică, cere o alternativă și compara valorile returnate de API. Separat, Acces pietonal creează un studiu dintr-un exemplu sintetic sau dintr-un poligon eligibil din catalogul OSM. SIM compară legături ipotetice pe același graf inițial și eșantion. Evaluarea aleasă returnează comparația deja calculată la crearea studiului. Catalogul conține 24 de poligoane și 7 puncte; punctele nu devin poligoane, iar extinderile OSM nu sunt limite municipale oficiale. Achiziția OSM online rămâne dependentă de serviciul extern.

**Reasoning behind the changes:** One concise present-tense capability is stronger than a generic future promise. Notes explain eligible OSM polygons and stored evaluation.

## Slide 5

**Current title:** Podu Roș, în prototip

**Current purpose:** Show an actual product path and result

**Problems identified:** The screenshot is authentic historical connected output, but the port is not a universal current address. The screenshot shows mean delay worsening; it must not be narrated as optimization. Its right edge crops part of the table.

**What should remain:** Three interaction steps, synthetic-data disclosure, screenshot and no-SUMO statement.

**What should be removed:** Local port presented as a stable verified destination; geographic wording implying Podu Roș measurements.

**What should be added:** Tradeoff-focused headline, exact model inputs and adverse mean outcome in notes; optional spatial walkthrough for questions.

**Improved headline:** Semaforizare: un compromis

**Exact proposed slide text:**

> ARTERIA / A / DEMO
> 05
> Semaforizare: un compromis
> DEMO: API conectat
> date sintetice
> Semaforizare estimată
> Fără SUMO din interfață
> Captură verificată la 18.10.2026 · valori sintetice, nu trafic din Iași
> 01
> Selectează reperul
> 02
> Alege o alternativă
> 03
> Deschide comparația

**Verified evidence supporting that text:** backend/models.py:Inputs; backend/simulation_adapter.py:SimulationAdapter.indicators; ConnectedWorkspace.tsx; assets/connected-comparison.png. Numerele descriu exclusiv modelul sintetic.

**Suggested speaker notes:**

Demo principal: analiză → propunere → reglaj verde nord–sud → comparație. Captura refăcută în browser la 18.10.2026 arată 13,89 secunde/vehicul inițial pe ambele direcții, apoi 2,22 nord–sud, 125,56 est–vest și media 53,61, la verde nord–sud 70 s. Aceste valori sunt compatibile cu modelul actual la ciclu 90 s, pierderi 10 s și cerere sintetică 700/500 vehicule/oră. Media inițială este 13,89; media crește, deci exemplul demonstrează un compromis nefavorabil în ansamblu, nu o optimizare reușită. Formula folosește întârziere uniformă și penalizare sintetică de capacitate, nu SUMO. Reperul Podu Roș nu furnizează trafic local. Portul se ia din pornirea curentă, implicit 3000; captura de rezervă nu este o aplicație publicată. Pentru întrebări, demonstrați separat exemplul pietonal: creați studiul, selectați o opțiune validată și afișați perechile de rute îmbunătățite/devenite accesibile. Nu numiți aceste perechi locuitori.

**Reasoning behind the changes:** One demo path remains understandable in 50 seconds. Replace only the cropped bitmap with a verified current capture in the same image geometry; no visual redesign.

## Slide 6

**Current title:** Frontend · Backend · Sim

**Current purpose:** Give technical credibility and accurate AI status

**Problems identified:** Stack and wiring are mostly accurate. Local SUMO scope, stored spatial comparison and candidate validation are underspecified. The old footer mentions a dashed AI link absent from this main diagram.

**What should remain:** Three components, solid connected graph flow, Next.js/MapLibre, FastAPI/Pydantic/SQLite, optional local SUMO.

**What should be removed:** Claim that main diagram has an actual dashed AI dependency; implication that all evaluation passes through SUMO or LLM.

**What should be added:** Stored graph comparison, candidate validation, existing evidence/catalog/rules, explicit LLM absence.

**Improved headline:** Interfață · Backend · SIM

**Exact proposed slide text:**

> ARTERIA / B / CONSTRUCȚIE
> 06
> Interfață · Backend · SIM
> Cod: backend/main.py · spatial_worker.py · sim/ · LLM și SUMO neconectate la UI
> Interfață
> Next.js / MapLibre
> Client API conectat
> Backend
> FastAPI / Pydantic
> SQLite · API evaluare
> Studii spațiale
> SIM
> Graf pietonal / OSM
> Rute · candidați validați
> SUMO separat, local
> Graf: comparație salvată în SQLite. Semaforizare: estimări sintetice.
> LLM neintegrat
> Există: dovezi, catalog și validare. Generarea LLM urmează.

**Verified evidence supporting that text:** frontend/web/package.json; backend/main.py; storage.py:Store; spatial_adapter.py:SpatialAdapter.run; spatial_worker.py:calculate; sim/sumo_engine.py; sim/proposal_context.py; sim/proposal_validation.py.

**Suggested speaker notes:**

Interfața Next.js folosește clientul HTTP comun. FastAPI validează cu Pydantic și persistă analize, propuneri, evaluări și studii în SQLite. Fluxul de semaforizare se calculează în backend/simulation_adapter.py. Studiul pietonal rulează SIM într-un subproces limitat la 90 s, cu verificarea structurii rezultatului; sursa, revizia motorului și comparațiile sunt păstrate. În calea OSM integrată se cere numai graful pietonal, fără achiziția straturilor de clădiri/POI. SIM are separat conversie de graf auto și executare SUMO locală cu cerere sintetică, fără integrare în UI sau calibrare. Nu există apel LLM conectat. Există deja catalog, pachet de dovezi cu hash al geometriei și validare a candidaților calculați. Procentul de cod sau fișierele generate cu asistență AI nu sunt confirmate; echipa trebuie să declare instrumentele folosite fără a inventa atribuții.

**Reasoning behind the changes:** AI status must be in the main presentation, given official evaluation criteria; no nonexistent model is added to improve the score.

## Slide 7

**Current title:** Model economic de testat

**Current purpose:** Identify buyer and business hypothesis

**Problems identified:** €1,500/month is inherited from previous pitch material. It has no interview, price test, accepted offer, measured delivery cost or paying-customer evidence. Existing qualification is honest but can be clearer.

**What should remain:** Buyer, proposed subscription, visibly unvalidated price, costs to measure.

**What should be removed:** Any interpretation as actual tariff, traction or verified zero customers beyond available evidence.

**What should be added:** Evidence-limited customer wording; retain price only as the template-requested hypothesis.

**Improved headline:** Model economic de testat

**Exact proposed slide text:**

> ARTERIA / MODEL ECONOMIC
> 07
> Model economic de testat
> Ipoteză din pitch-ul anterior, 2026 · preț nevalidat prin interviuri
> Abonament propus,
> preț nevalidat
> Nu avem dovezi de clienți plătitori
> Cumpărător vizat
> Administrație locală /
> consultanță de mobilitate
> 1.500 €
> / lună
> Valoare de verificat: timpul
> pregătirii unei comparații
> Costuri de măsurat:
> date, calcul și suport

**Verified evidence supporting that text:** Ipoteză preexistentă în archive/v2-before-content-audit-20261018/Template-Pitch-Hackathon.v2.pptx; nicio validare comercială găsită.

**Suggested speaker notes:**

Model propus: abonament pentru administrații locale sau consultanțe de mobilitate. 1.500 €/lună este exclusiv ipoteza din pitch-ul anterior, nu preț testat, ofertă acceptată sau disponibilitate de plată. Ar echivala aritmetic cu 18.000 €/an, fără a demonstra cerere. Nu avem dovezi în materialele auditate de clienți plătitori. Validăm timpul necesar unei comparații, utilitatea și costurile de date, calcul și suport înainte de a susține marjă sau economii.

**Reasoning behind the changes:** The template asks who pays and an explicitly hypothetical price. Retention is defensible with visible qualification; it is not market validation.

## Slide 8

**Current title:** Primii utilizatori, înainte de extindere

**Current purpose:** Explain market entry

**Problems identified:** Ten organizations are a proposed list, not a verified segment. €180,000/year is correct multiplication but contributes no evidence of market size, conversion or revenue.

**What should remain:** Iași as first geography; mentor/community introductions as proposed channel.

**What should be removed:** Dominant €180,000 scenario and arbitrary ten-organization target from the slide.

**What should be added:** First case/interviews and utility/willingness-to-pay exit criterion; preserve arithmetic only in notes.

**Improved headline:** Validarea pieței începe în Iași

**Exact proposed slide text:**

> ARTERIA / R / PIAȚA
> 08
> Validarea pieței începe în Iași
> Plan propus · 18.10.2026 · nu reprezintă tracțiune comercială
> Fără listă validată de clienți sau dimensiune de piață măsurată
> Iași: propunem un prim caz cu un specialist
> Apoi: identificăm organizații de intervievat
> Canal propus: introduceri prin mentori și comunități de mobilitate
> Criteriul propus pentru continuare
> Utilitate și plată validate

**Verified evidence supporting that text:** Absența listei și a contractelor în dovezile disponibile; plan propus. Aritmetică istorică, nu cercetare de piață.

**Suggested speaker notes:**

Plan propus de acces la piață: un caz de lucru în Iași, interviuri cu specialiști și identificarea organizațiilor relevante prin mentori/comunități. Nu există o listă verificată de zece organizații. Calculul istoric 10 × 12 × 1.500 € = 180.000 €/an este aritmetic corect, dar presupune zece cumpărători, preț acceptat și un an întreg; nu este dimensiune de piață sau venit realizat. De aceea nu mai domină slide-ul. Continuarea comercială presupune utilitate, disponibilitate de plată și cost de livrare validate. Instituțiile locale sunt potențiali interlocutori, nu parteneri confirmați.

**Reasoning behind the changes:** Replace speculative commercial arithmetic within the existing slide geometry. Preserve its position to respect the ten-section template; no new market statistic is invented.

## Slide 9

**Current title:** ARION

**Current purpose:** Identify the team

**Problems identified:** Names and broad responsibilities are supplied by the team; the English role descriptions break Romanian consistency.

**What should remain:** All three names, equal profiles and only supplied roles.

**What should be removed:** English role descriptions and any invented granular authorship.

**What should be added:** Romanian equivalents of the same responsibilities.

**Improved headline:** ARION

**Exact proposed slide text:**

> ARTERIA / O / ECHIPA
> 09
> ARION
> Nume și responsabilități furnizate de echipă · 18.10.2026
> Iustin Fagateanu
> Interfață și
> experiență web
> Alex Pintilie
> Inițializare proiect
> și baza de simulare
> Fagateanu Eusebiu
> Dezvoltare backend
> Următoarea nevoie: validare cu un specialist în mobilitate

**Verified evidence supporting that text:** Nume și responsabilități furnizate explicit în cererea de audit a echipei, 18.10.2026; nu se deduce autorie individuală din Git.

**Suggested speaker notes:**

Echipa a furnizat numele și responsabilitățile: Iustin Fagateanu — interfață/frontend; Alex Pintilie — inițializarea proiectului și baza de simulare; Fagateanu Eusebiu — backend. Traducerea păstrează aceste roluri, fără atribuirea unor endpoint-uri, algoritmi sau rezultate individuale pe care dovezile nu le stabilesc. Continuitatea după eveniment, rolurile de scenă și experiența profesională nu sunt confirmate.

**Reasoning behind the changes:** Translate without adding experience, ownership of handlers, full-time commitment or field expertise.

## Slide 10

**Current title:** Prima comparație pe date verificate

**Current purpose:** Close with next step and ask

**Problems identified:** Data validation and specialist feedback are appropriate; missing LLM integration deserves explicit roadmap placement. Existing first-comparison wording can understate graph capabilities already built.

**What should remain:** Concrete introduction/data ask, specialist test and measurable workflow goal.

**What should be removed:** Any impression that all data handling/graph comparisons remain to be built.

**What should be added:** LLM with validation; proposal correctness as an intended metric; calibration/field checks in notes.

**Improved headline:** Următorul pas: un caz validat

**Exact proposed slide text:**

> ARTERIA / A / CE URMEAZĂ
> 10
> Următorul pas: un caz validat
> Măsurăm timpul de lucru și corectitudinea propunerilor.
> Un caz verificabil. Apoi extindere.
> Date locale
> verificate
> LLM cu
> validare
> Test cu
> un specialist
> Cererea noastră
> O introducere către un specialist
> și acces la un set de date local.

**Verified evidence supporting that text:** docs/ROADMAP.md comparat cu backend/main.py și sim/proposals.py/proposal_validation.py; goluri curente din PROJECT_REALITY_AUDIT.md.

**Suggested speaker notes:**

Priorități propuse: un caz pe date locale verificabile; conectarea unui LLM constrâns de dovezi și evaluarea corectitudinii propunerilor; test cu un specialist. Măsurăm timpul de lucru și trasabilitatea, nu promitem o reducere de trafic. Calibrarea cererii, integrarea SUMO în fluxul potrivit și verificarea fezabilității în teren rămân necesare înainte de rezultate urbane. Cerem o introducere către un specialist și acces la date. Nu există un acord de pilot în dovezi.

**Reasoning behind the changes:** Use genuine implementation and validation gaps. No invented pilot, deadline or traffic reduction target.

## Slide 11

**Current title:** Ce este verificat astăzi

**Current purpose:** Support technical questions with evidence

**Problems identified:** 9/9, typecheck and build need a current run. Historical 138 Python tests in notes must be independently rerun. Passing fixture tests do not establish calibrated impact or browser completion.

**What should remain:** 9/9 frontend result; web/mobile/shared typecheck; build routes.

**What should be removed:** Historical-only verification wording and untranslated check labels.

**What should be added:** Audit date, scope distinction and fresh Python result in notes/report.

**Improved headline:** Verificări tehnice, nu impact urban

**Exact proposed slide text:**

> ARTERIA / ANEXA A / DOVEZI
> 11
> Verificări tehnice, nu impact urban
> Verificări reluate la 18.10.2026 · npm run check · detalii în note
> Verificare TypeScript
> web · mobil · comun
> Compilare web
> / și /app
> API și SIM: teste offline; fără validare în teren
> LLM și SUMO în interfață: neintegrate
> 9 / 9
> teste frontend

**Verified evidence supporting that text:** reports/audit-frontend-check.log; reports/audit-python-final.log; tests/; sim/test_engine.py. Se consultă raportul final pentru acoperire și limite.

**Suggested speaker notes:**

Verificare reluată la 18.10.2026: npm run check a trecut verificarea TypeScript pentru web, mobil și cod comun, 9/9 teste Node și compilarea Next.js pentru / și /app. Testele Node folosesc transport simulat și verifică geografia catalogului; nu sunt nouă teste complete de produs. Python: 138 teste trecute, un avertisment de depreciere, în runtime QA izolat, fără sincronizare uv.lock. Rularea curentă și limitele ei sunt în reports/audit-python-final.log și PPT_FINAL_CONTENT_AUDIT.md. Rezultatele istorice nu se confundă cu o rulare nouă. Testele offline verifică API-ul, stocarea, motorul de graf, validarea și conversia SUMO; nu demonstrează trafic real, calibrare, fezabilitate fizică sau execuție SUMO în UI.

**Reasoning behind the changes:** Keep technical detail in appendix; report the meaning of tests instead of inventing coverage percentages.

## Slide 12

**Current title:** Rolul AI în fluxul propus

**Current purpose:** Explain AI boundary and future constrained generation

**Problems identified:** LLM is already marked future, which is honest. The implemented bounded evidence packet and strict candidate-backed validation are underrepresented. Deterministic generation is not a working learned model.

**What should remain:** Evidence → future LLM → rules → independent evaluation; recommendation ≠ measurement.

**What should be removed:** Any ambiguity that the proposed full AI flow executes today.

**What should be added:** Calculated candidates/rule checks today; evidence-bounded generation planned; no physical feasibility guarantee.

**Improved headline:** Dovezi și reguli înainte de LLM

**Exact proposed slide text:**

> ARTERIA / ANEXA B / AI
> 12
> Dovezi și reguli înainte de LLM
> Cod: sim/proposal_context.py · proposals.py · proposal_validation.py · 18.10.2026
> Dovezi
> și catalog
> LLM viitor
> Alternative
> Reguli
> și geometrie
> Evaluare
> independentă
> Astăzi: candidați calculați, verificați prin reguli
> Planificat: generare LLM pe dovezi; specialistul decide
> O recomandare nu constituie o măsurătoare.

**Verified evidence supporting that text:** sim/proposal_context.py:build_proposal_context; proposals.py:prepare_candidate_options; proposal_validation.py:validate_proposal_set; backend/models.py:RecommendationModel; backend/spatial_worker.py:calculate.

**Suggested speaker notes:**

Astăzi nu există integrare LLM sau model învățat conectat. Generarea semaforizării și a opțiunilor pietonale este deterministă. Există un pachet limitat de dovezi cu referință SHA-256 la geometrie, catalog de intervenții, candidați evaluați și verificări de identitate/acțiune, coordonate, unități și afirmații nesusținute. Validarea nu certifică fezabilitatea fizică și nu garantează eliminarea oricărei halucinații. Opțiunile pietonale nu primesc etichete inginerești minimal/moderat/transformator. Fluxul cu LLM din diagramă este viitor. AI este central în intenția produsului, dar componenta generativă lipsește din implementarea actuală; regulile deterministe nu se prezintă drept LLM.

**Reasoning behind the changes:** This appendix explains existing engineering preparation for AI without relabeling it as an integrated LLM.

## Slide 13

**Current title:** Condițiile unei evaluări credibile

**Current purpose:** Explain methodology and limits

**Problems identified:** Original content mixes implemented comparison controls and future simulation requirements. Repeating a result does not validate field accuracy.

**What should remain:** Provenance, shared baseline, explicit unknowns and no validated traffic outcomes.

**What should be removed:** Generic reproducibility phrasing suggesting validity; simulation as an unqualified connected workflow.

**What should be added:** Shared graph/sample; sampled routes ≠ observed travel; hypothetical link ≠ feasible construction; local SUMO synthetic demand.

**Improved headline:** Cum comparăm alternativele

**Exact proposed slide text:**

> ARTERIA / ANEXA C / METODĂ
> 13
> Cum comparăm alternativele
> Cod: sim/impact.py · backend/spatial_routes.py · sim/sumo_engine.py · 18.10.2026
> Rute eșantionate ≠ călătorii observate
> Legătură ipotetică ≠ lucrare fezabilă
> Repetabilitate ≠ validare în teren
> Nu avem rezultate validate de trafic real.
> Date
> Sursă, dată, acoperire, licență
> Comparație
> Același graf inițial și eșantion comun de rute
> SUMO local
> Cerere sintetică; execuție separată de interfață

**Verified evidence supporting that text:** sim/impact.py:evaluate_candidates; sim/scenario.py:_prepare_scenario_graph; backend/spatial_routes.py:evaluate; backend/spatial_models.py:SpatialEvaluation; sim/sumo_engine.py:run_real_area_simulation.

**Suggested speaker notes:**

Comparația pietonală folosește același graf inițial și un eșantion comun, cu sămânță fixată. Perechile folosite la descoperirea candidaților sunt excluse din eșantionul de clasare; diagnosticele locale sunt separate. Modificările se aplică pe copii ale grafului inițial. Studiul și comparațiile sunt persistate; selectarea unui candidat nu lansează o nouă simulare. Repetabilitatea presupune aceleași date, versiuni și parametri; marcajele temporale/ID-urile nu sunt identice la fiecare cerere. OSM are acoperire incompletă. Lipsa unui strat rămâne necunoscută. SUMO local are cerere sintetică și setări păstrate, dar nu rezultate de trafic calibrate pentru Iași. Nu confundăm simularea cu validarea în teren.

**Reasoning behind the changes:** A methodology slide is useful when it tells the jury what actually makes comparisons controlled, and what that control cannot establish.
