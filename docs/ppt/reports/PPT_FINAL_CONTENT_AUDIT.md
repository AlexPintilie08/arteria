# ARTERIA — final factual and editorial audit

> This report records the content audit. The current 10-slide master and motion validation supersede its original delivery filenames and are documented in `PREMIUM_MOTION_QA.md`. The audited 13-slide working deck is archived at `../archive/premium-motion-20261018/ARTERIA-Audited-13-slides.pptx`.

Date: 18 October 2026, Europe/Bucharest. Source checkout: `00cf80c` with preexisting presentation edits preserved. Application code was not modified.

## 1. Executive audit summary

The presentation now distinguishes the actual prototype from its product ambition: a connected **synthetic signal-timing demo** and a separate **pedestrian graph-study workflow**, with persisted comparisons, candidate validation and source/uncertainty evidence. The strongest defensible technical contribution is the integrated comparison/validation pipeline, not a demonstrated learned model or calibrated traffic improvement.

The original V2 was already cautious about synthetic data, missing LLM and unvalidated price. Most problems were omissions, vague positioning, stale verification/narration and emphasis, rather than wholesale fabricated functionality. No unsupported claim is called false merely because evidence is absent.

**Original content-audit delivery:** `ARTERIA-Audited.pptx` (13 slides: 10 main + 3 Q&A appendices) and `ARTERIA-Submission.pptx`/`.pdf` (10 slides/pages). The later motion consolidation promoted the corrected ten-slide content to `ARTERIA.pptx`, now the only active editable master. The 13-slide working copy and pre-motion files are archived; current hashes and validation are in `PREMIUM_MOTION_QA.md` and `canonical-publication.json`.

## 2. Evidence and audit sequence

1. Inspected source independently: root configuration, web/mobile/shared clients, real API bodies/models/storage, worker/adapter contract, acquisition/analysis/scenario/candidate/impact/proposal/SUMO modules, tests and CI/history. Read relevant component instructions and technical documentation, noting stale descriptions.
2. Created `PROJECT_REALITY_AUDIT.md` before reading current PPTX/pitch research.
3. Froze the current user deck, scripts and research in `archive/v2-before-content-audit-20261018/`. Backup deck SHA-256: `69dc4f6e03c33e8eb5050953d7c73ef7c68cfcd22cc45927ffb62eefa32484e5`. The older original-template backup was also preserved.
4. Extracted every slide text node, diagram/table text and note paragraph into `PPT_ORIGINAL_EXTRACTION.json`; inspected bitmap text and numerical output separately. Recorded the claim matrix in `PPT_FACT_CHECK.md`.
5. Verified organizer requirements online and the actual supplied template. Built the detailed keep/replace/content plan in `PPT_CONTENT_RESTRUCTURE_PLAN.md` before publishing corrections.
6. Applied corrections through `scripts/audited_content.py`, integrated after V2 shape generation, and validated both direct preservation and a fresh generation/animation rebuild.

Source references in reports are evidence locations, not blanket certification of all behaviors. Fresh offline/browser results are separated from code presence, historical logs and untested online acquisition.

## 3. Slide-by-slide findings and evidence-backed corrections

| Slide | Decision and final change | Evidence and justification |
|---|---|---|
| 1 | KEEP WITH EDITS: name the two real workflows; mark cover image historical preview | `Workspace.App`, `ConnectedWorkspace`, `SpatialPanel`; the cover is not a full connected digital twin |
| 2 | KEEP WITH EDITS: concrete question about routes before/after a new link | `scenario.evaluate_scenario`, `impact.evaluate_candidates`; proposed user need remains unvalidated. Transport branches describe planning context, not four validated modules |
| 3 | RESTRUCTURE: retain fair QGIS/SUMO descriptions; replace PMUD product-comparison row with work process | Primary QGIS/SUMO documentation supports their capabilities. No benchmark or user study establishes their inferiority; PMUD is institutional context |
| 4 | KEEP WITH EDITS: expose shared-sample graph comparison and separate synthetic signals | `impact.evaluate_candidates`; current browser/API fixture flow; do not imply the same spatial calculation runs in `/analyze` |
| 5 | KEEP WITH EDITS: tradeoff headline, verified current screenshot, synthetic disclosure and exact inputs in notes | `SimulationAdapter.indicators`, real UI/API at NS green 70 s. NS improves while EW and overall mean worsen. The old screenshot's missing difference column is corrected by a real capture in the same image box |
| 6 | KEEP WITH EDITS: retain real stack/data flow; describe stored graph comparison, validated candidates and missing LLM | `main.py`, `storage.Store`, `spatial_worker.calculate`, SIM evidence/validation modules. SUMO local code exists but is separate; no connected provider or SUMO UI path |
| 7 | KEEP WITH EDITS: keep €1,500/month only as visibly unvalidated subscription hypothesis | Traceable to prior pitch, with no price experiment or accepted offer. The template asks for a hypothetical price; no customer absence is asserted beyond available evidence |
| 8 | REPLACE content in place: first case/interviews and a validation criterion replace dominant €180,000 arithmetic | Ten organizations are not a sourced customer segment. The multiplication is correct but is neither market sizing nor traction; exact historic calculation remains qualified in notes |
| 9 | KEEP WITH EDITS: Romanian roles, exact supplied names | Team-supplied responsibility statement. No invented granular contributions, expertise or continuation commitment |
| 10 | KEEP WITH EDITS: local data, evidence-constrained LLM and specialist test; measure time and proposal correctness | Actual absent provider and calibration/field validation gaps, compared with `docs/ROADMAP.md`. Concrete introduction/data ask retained, without a signed pilot claim |
| 11 | KEEP WITH EDITS: dated technical checks and their limited meaning | Fresh 9/9 Node tests, typecheck/build and 138 Python tests. Mock/fixture results do not prove field impact or Android functionality |
| 12 | KEEP WITH EDITS: describe evidence/context and rule checks as today's implementation, LLM as future | `proposal_context`, `proposals`, `proposal_validation`, worker and UI acceptance filtering. No learned generation or universal hallucination prevention claimed |
| 13 | KEEP WITH EDITS: actual baseline/sample controls and limits replace generic methodological promises | `impact`, `scenario`, stored spatial evaluation, SUMO runner. Repeatability is distinguished from physical validity; graph-node samples are not observed trips |

## 4. Unsupported claims removed or qualified

- Removed the displayed 10-organization/€180,000 annual exercise from the market slide; preserved transparent arithmetic in notes as a historical hypothetical scenario.
- Kept €1,500/month only as an inherited, unvalidated price hypothesis, not tested willingness to pay, an accepted contract or verified revenue.
- Qualified customer evidence as what was found in supplied materials; did not invent customers or infer absolute commercial status outside the repository.
- Replaced local port 3001 as an apparently stable demo destination with a dated actual capture. Public demo accessibility is not claimed.
- Replaced every note's claim that previous research is the source of truth. Code and reproducible checks now have priority.
- Removed five-minute rehearsal instructions from the live notes after official three-minute guidance was verified.
- Removed the main architecture footer's assertion about a dashed AI connector that was not actually drawn there. Geometry was preserved; the future LLM remains explicitly labeled.
- Qualified the historical preview image, real OSM data versus synthetic traffic, repeatability versus validity, local SUMO versus connected evaluation, and deterministic options versus LLM generation.

No fake traffic statistics, cost saving, code-coverage percentage, customer traction, market share, AI success rate, construction feasibility or adoption proof was introduced.

## 5. Important information added without a text-heavy deck

Main slides now emphasize alternatives calculated on one shared sample, a stored comparison trace, validated computed candidates and evidence/rule infrastructure already built. These are understandable, defensible achievements. More detailed catalog coverage (24 polygons, 7 points), canonical area validation, exact signal inputs, separate diagnostics and the strict candidate/action comparison appear in notes and Q&A material rather than long main-slide lists.

The negative mean-delay outcome makes the demonstration stronger technically: the product can expose a tradeoff instead of guaranteeing improvement. The AI gap is visible on the architecture slide and roadmap, not hidden solely in an appendix. Given the organizer's AI criterion, this remains a substantive implementation gap that editing cannot cure.

## 6. Structure and official requirements

The ten main sections and their order are preserved. No additional slide was added, no mandatory team/business section was dropped, and the main architecture was not expanded into a technical specification. The supplied template permits Q&A appendices, but the official regulation limits the submitted document to ten slides. A separate ten-slide submission resolves that conflict while retaining the useful full deck.

`HACKATHON_REQUIREMENTS_VERIFICATION.md` records primary links, presentation duration, criteria and remaining schedule discrepancy. Proposed slide timing totals 180 seconds; this is not a claim that a team rehearsal has been completed. Existing animation effects/click behavior remain intact and require rehearsal within that allocation.

## 7. Validation results

| Check | Actual result | Practical limit |
|---|---|---|
| Frontend check | TypeScript web/mobile/shared passed; 9/9 tests; production build passed | Node tests use mocked fetch/catalog data; native app not run |
| Python backend/SIM | 138 passed, 1 deprecation warning, 15.59 s | Existing isolated Python 3.12 QA runtime; compatible ranges, not verified `uv.lock` sync; offline fixtures/mocks |
| Real browser/API | Signal workflow and SIM fixture candidate/stored-comparison flow passed; no page exceptions; no page-width overflow at 375/768/1440 | Audit-only SQLite and explicit CORS origin; no online OSM acquisition/field validation |
| Proposal demo | Fixture evidence/options/validation output reproduced | No LLM call; synthetic fixture |
| SUMO | Python bindings found; executables missing; smoke skipped | No vehicle simulation executed and no calibrated result |
| PPTX validation | Standard package validator passed for full and submission decks | Not a certification of all external claims |
| PowerPoint | Both files opened and exported successfully using local PowerPoint COM | Static export does not prove a newly observed animation playback session |
| Text fit | 153 native text/table regions checked; zero overflow, zero out-of-canvas objects | Small source footers and screenshot metrics remain small at auditorium distance; live demo is preferable |
| Animation preservation | 43 native effects; every target valid; transitions and animation timing XML identical to frozen V2 | Preserved behavior; no fresh claim of live slideshow playback inspection |
| Design preservation | Full-slide XML identical after blanking only text values; theme/layout/geometry/styles unchanged | One authorized necessary exception: uncropped current comparison bitmap, same 829×720 dimensions and picture geometry |
| Submission | Exactly 10 PPTX slides and 10 PDF pages; main slide XML identical to full deck | Team still needs a functional public demo/repository link and accompanying submission materials |
| Rebuild | Existing generator + V2 refinement + native motion regenerated equal visible content and notes | Binary ZIP/COM metadata is not expected to be byte-reproducible; content/structure is checked |

Supporting logs: `audit-frontend-check.log`, `audit-python-final.log`, `audit-browser.log`, `audit-browser-results.json`, `audit-runtime-versions.json`, `audit-sumo.log`, `audit-package-full.log`, `audit-package-submission.log`, `audit-deck-qa.log`, `content-preservation.json`, `audit-rebuild-verification.json`. `qa-results.json`/`text-bounds.json` describe the delivered full deck. The source PNG/JPEG capture is preserved as `assets/connected-comparison-audited.*`.

## 8. Remaining uncertainties and team confirmations

1. Confirm the submission time with organizers: linked regulation/guide and current organizer webpage disagree. The three-minute pitch and ten-slide document limit are established.
2. Supply/confirm the public demo or repository link and its accessibility. A local screenshot is not a public deployment. No link was invented or published by this audit.
3. Provide the actual AI development tools used and distinguish them from runtime product capabilities; confirm preexisting-code disclosure and human contribution. No AI authorship percentage or file-level attribution is inferred.
4. Confirm who presents each slide and who continues after the event. Supplied member names/roles are preserved.
5. Validate user pain, willingness to pay, organizations to interview and delivery costs. No completed interviews, adoption or pilot agreement was evidenced.
6. Reproduce eligible-area OSM acquisition online and review source completeness and canonical-area equivalence. The passing browser study used the explicit fixture, not downloaded city infrastructure.
7. Connect/evaluate LLM generation and relevant SUMO jobs as future application work; calibrate any traffic claim and check hypothetical links in the field.

## 9. Final content-quality assessment

The revised deck is a defensible prototype pitch with a clearer concrete user question, truthful integration boundaries, stronger engineering evidence, explicit business assumptions and Romanian presenter notes. It is not proof of AI-product maturity, validated demand or traffic impact. No claim of perfection or unconditional submission readiness is made.

The authoritative ten-slide file retains the audited content. The 13-slide working version, pre-motion submission, and pre-audit source remain preserved in their archives. No unrelated application code or user database was altered.
