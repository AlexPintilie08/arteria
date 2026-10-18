# ARTERIA — independent implementation inventory

Audit date: 2026-10-18 (Europe/Bucharest). Established from current working source **before reading the PPTX or previous pitch research**. HEAD: `00cf80c`; existing uncommitted presentation work is preserved. Evidence priority: implementation/runtime, tests, configuration, history, technical documentation, research, pitch. A source inspection proves code presence and wiring, not successful live acquisition or field validity.

## Product, problem and users

**Claim:** ARTERIA is a local mobility-planning prototype for examining hypothetical interventions before implementation, with two distinct connected workflows: synthetic signal timing and pedestrian graph studies.

**Status:** IMPLEMENTED AND INTEGRATED (signal workflow is DEMONSTRATIVE / MOCK / SYNTHETIC).

**Evidence:** `frontend/web/src/app/app/page.tsx:ProductPage`; `features/workspace/Workspace.tsx:App`; `ConnectedWorkspace.tsx:analyze/propose/evaluate`; `SpatialPanel.tsx`; `backend/main.py:analyze/propose/evaluate`; `backend/spatial_routes.py:create_study/evaluate`.

**Verification:** Traced page → mode switch → shared HTTP client → actual routes → computation/storage → returned UI fields.

**Limitations:** No demonstrated city deployment, observed traffic reduction or customer adoption. It supports an exploration/decision problem, not automated municipal approval. Municipal planners, mobility engineers and consultants are intended users inferred from the workflow and API proposals, not verified customers. Quantified pain, willingness to pay and procurement fit need user research.

## Feature and integration register

### 1. Browser modes and primary experience

**Claim:** `/` is a marketing page; `/app` selects the fixture preview only when `NEXT_PUBLIC_DEMO_MODE === 'true'`, otherwise it opens the connected workspace. Connected signal flow selects a bookmark, analyzes, requests server alternatives, optionally adjusts north–south green time, evaluates the exact selected action and displays baseline/scenario/deltas.

**Status:** IMPLEMENTED AND INTEGRATED; preview is DEMONSTRATIVE / MOCK / SYNTHETIC.

**Evidence:** `frontend/web/src/lib/api.ts:demoMode`; `Workspace.tsx:App`; `ConnectedWorkspace.tsx:request/reset/analyze/propose/evaluate`; `frontend/shared/core/api.ts:createApiClient`; `backend/main.py:check_area`.

**Verification:** Inspected mode routing, cancellation, error display, state reset, payload identity and no silent failure-to-fixture fallback. `frontend/shared/tests/backend-flow.cjs` contains real-browser coverage, separate from npm unit tests.

**Limitations:** Build-time mode matters; a screenshot alone cannot prove which backend is running. Client response types are compile-time casts, without runtime schema validation (`api.ts:post`).

### 2. Mapping and sourced neighborhood catalog

**Claim:** MapLibre renders OSM raster tiles and selectable source geometries; a bundled partial Iași catalog contains 24 Polygon/MultiPolygon and 7 point-only records. Points do not become study polygons.

**Status:** IMPLEMENTED AND INTEGRATED.

**Evidence:** `frontend/web/src/features/map/MapViewport.tsx`; `features/neighborhoods/NeighborhoodExplorer.tsx`, `sim-geography.ts`; `sim/iasi-neighborhoods.geojson`; `sim/neighborhoods.py:validate_neighborhood_boundary/neighborhood_area_input`; `frontend/web/tests/sim-geography.test.ts`.

**Verification:** Inspected tile URL, geometry handling, catalog tests, canonical server ID lookup and point/oversize rejection in `backend/spatial_worker.py:calculate`.

**Limitations:** OSM place extents are not certified municipal/legal boundaries. The map uses raster data and a pitched view; this does not establish a complete 3D urban digital twin. Five demo bookmarks and 31 sourced catalog records serve different purposes. No live sensors or population inventory.

### 3. Backend contract and safeguards

**Claim:** FastAPI and Pydantic implement health, synthetic analyze/propose/evaluate, record retrieval, area bookmarks and spatial study/candidate/evaluation routes, structured errors, CORS, parameter/geometry/identity validation.

**Status:** IMPLEMENTED AND INTEGRATED.

**Evidence:** `backend/main.py`; `models.py:Model/Polygon/Inputs/EvaluateRequest`; `spatial_models.py:SpatialRequest/Selection`; `engine_contract.py:EngineResult`; `tests/test_backend_flow.py`, `test_frontend_contract.py`, `test_backend_regressions.py`, `test_spatial_api.py`.

**Verification:** Read actual route bodies and downstream calls. Unsupported modes reject explicitly. Engine response validation checks consumed fields, not merely HTTP existence.

**Limitations:** API-spec examples of login, report export, scenario sharing, SSE/jobs and broader urban metrics are not implemented routes. `api-specs/auth-endpoints.md` and `scenario-persistence-endpoints.md` are proposals, not proof. No auth or tenant isolation found.

### 4. Durable records

**Claim:** SQLite stores JSON records with namespace/ID keys, immutable retry results, retrieval and capacity limits; spatial study selection reuses stored comparisons.

**Status:** IMPLEMENTED AND INTEGRATED.

**Evidence:** `backend/storage.py:Store.connection/get/put`; `main.py:identity/save`; `spatial_routes.py:studies/load/evaluate`; `test_frontend_contract.py:test_storage_survives_new_process/test_concurrent_retries_return_one_immutable_record`.

**Verification:** Inspected SQL transactions, schema, duplicate key retrieval, record limit and storage error envelope.

**Limitations:** Not a complete project collaboration/export system. Spatial `evaluate` does not run the engine afresh; `execution=stored_graph_comparison`, `evaluated_at=study.created_at`.

### 5. Synthetic traffic estimates

**Claim:** Signal delay uses red-time squared divided by twice cycle time plus a synthetic excess-capacity penalty; directions are demand-weighted for mean delay. Alternatives change green allocation under a fixed cycle/lost-time assumption.

**Status:** DEMONSTRATIVE / MOCK / SYNTHETIC, integrated.

**Evidence:** `backend/simulation_adapter.py:SimulationAdapter.indicators/require_sumo`; `models.py:Inputs/Provenance/Uncertainty/RecommendationModel`; `main.py:propose/evaluate`.

**Verification:** Read calculation and synthetic saturation flow (1800 vehicles/hour), fixed lost time (10 seconds), minimum greens and adverse-effect handling. The same synthetic inputs can appear under different geographic bookmark contexts.

**Limitations:** Neither measured Iași traffic nor microscopic SUMO simulation. The issue is predefined signal balance, not discovered congestion. Requested walking/cycling/layer fields do not make those metrics available through `/analyze`; layer availability remains unknown.

### 6. Spatial acquisition and analysis library

**Claim:** SIM validates bounded study geometries, acquires/cache-reuses walk/bike/drive OSM graphs independently, projects to metric coordinates, computes connectivity, weighted paths and constant-speed access to mapped facilities, and exports GeoJSON/provenance/uncertainty.

**Status:** IMPLEMENTED AND INTEGRATED for pedestrian graph study; broader library analysis IMPLEMENTED BUT NOT INTEGRATED into the complete web workflow.

**Evidence:** `sim/geo.py:normalize_area/acquire_osm_data/feature_collection`; `analysis.py:project_graph/analyze_snapshot/analyze_area`; `sim/test_engine.py` acquisition, unknown-layer, CRS and accessibility tests; `backend/spatial_worker.py:calculate`.

**Verification:** Inspected graph-only backend call: `modes=('walk',)`, `include_features=False`, 5 km²/5 km limits. General library supports more than the connected endpoint exposes.

**Limitations:** Integrated OSM path deliberately skips feature acquisition, so building/POI screening evidence is unavailable there. Empty/failed layers do not establish absence. Population access remains null; times use assumed speeds, not measured journeys. External Overpass acquisition success has not yet been reproduced in this audit.

### 7. Candidate discovery and scenario evaluation

**Claim:** SIM detects candidate links across components or detours, screens a bounded pool, evaluates hypothetical graph edits independently from an unchanged baseline and ranks candidates using one shared seeded sample; targeted local diagnostics are separate.

**Status:** IMPLEMENTED AND INTEGRATED for adding pedestrian links. Connection toggle is IMPLEMENTED BUT NOT INTEGRATED in the UI/API selection workflow.

**Evidence:** `sim/candidates.py:discover_intervention_candidates`; `scenario.py:_prepare_scenario_graph/evaluate_scenario`; `impact.py:sample_route_pairs/evaluate_candidates/_targeted_diagnostic_pairs`; `proposal_catalog.py:get_intervention_catalog`; `spatial_worker.py:calculate`; `SpatialPanel.tsx`.

**Verification:** Inspected common sample creation excluding discovery pairs, independent scenario copies, lexicographic ranking, negative/reachability outcomes, and no-candidate paths. Tests: `test_candidate_pipeline_uses_one_shared_non_discovery_sample_and_stable_ranking`, `test_independent_alternatives_start_from_the_same_baseline`, `test_scenario_is_deterministic_and_never_mutates_baseline_graph`.

**Limitations:** Sampled node pairs are not trips/residents. Candidate validity does not establish ownership, slope, accessibility, construction safety or engineering feasibility. Default HTTP study uses 16 sampled pairs, returns at most 3 candidates and evaluates at most 6 from a pool of 30; library defaults differ. OSM building checks are conditional on available trustworthy features.

### 8. Proposal evidence and validation; current AI status

**Claim:** A versioned intervention catalog, bounded evidence packet with geometry SHA-256, deterministic candidate options and strict proposal checks exist. Validation matches candidates/actions, geometry, units and evidence and rejects unsupported claims/duplicates.

**Status:** IMPLEMENTED AND INTEGRATED. External LLM generation: PLANNED / NOT FOUND in current runtime.

**Evidence:** `sim/proposal_catalog.py`; `proposal_context.py:build_proposal_context`; `proposals.py:prepare_candidate_options`; `proposal_validation.py:validate_proposal/validate_proposal_set`; `spatial_worker.py:calculate`; `SpatialPanel.tsx:acceptedIds/proposalOptions`; `sim/test_engine.py` proposal tests.

**Verification:** Traced evidence/options/validation through study response and accepted-option filtering to exact candidate selection. Searched backend, SIM and clients for provider SDKs/calls. Signal provider is literally `deterministic`, `model_id=signal-catalog-1`.

**Limitations:** This is deterministic decision-support infrastructure, not a working learned/LLM system. Graph options deliberately have no minimal/moderate/transformative engineering classification. Validation includes finite rules/heuristics, not proof of universal hallucination prevention. `proposal_context.py` still labels real-area SUMO conversion unsupported although `sumo_engine.py` implements it locally: stale capability metadata should be reconciled in future application work.

### 9. SUMO capability and boundaries

**Claim:** A local optional runner converts an existing directed driving snapshot to SUMO inputs and can execute bounded headless simulation with seeded synthetic OD demand, source mapping and trip accounting when binaries exist.

**Status:** IMPLEMENTED BUT NOT INTEGRATED; runtime execution UNVERIFIED at inventory stage.

**Evidence:** `sim/sumo_engine.py:load_cached_driving_snapshot/prepare_sumo_network/run_real_area_simulation`; `sumo_support.py:discover_sumo/run_sumo_smoke`; `sim/test_engine.py:test_sumo_plain_xml_conversion_preserves_directed_osm_edges_metric_coords_and_reproducible_demand` and runner/accounting cases.

**Verification:** Read actual subprocess invocations, timeout paths, fixed-seed demand, fallback speed/lane disclosure, completed/unfinished trip accounting. `/evaluate` instead calls `require_sumo`, which always rejects; spatial responses declare `sumo_executed=False`.

**Limitations:** Does not download its driving snapshot, calibrate demand, or compare an integrated pedestrian intervention in vehicle dynamics. Presence of Python TraCI bindings does not prove installed binaries. No verified real-world traffic prediction.

### 10. Mobile client

**Claim:** Expo/React Native navigation and placeholder analysis/scenario/comparison screens exist with shared contracts/tokens.

**Status:** PARTIALLY IMPLEMENTED; UI scaffold, not connected product parity.

**Evidence:** `frontend/mobile/src/app/App.tsx`; `features/map/MapPlaceholder.tsx`; `features/analysis/AnalysisScreen.tsx`; `features/comparison/ComparisonScreen.tsx`.

**Verification:** Read renderer and screen bodies; no connected analysis or evaluated data display.

**Limitations:** No native device run in this audit. Do not pitch Android parity.

## Testing and reproducible evidence

Fresh frontend `npm.cmd run check` passed typechecking (web/mobile/shared), **9/9 Node tests**, and Next.js production build; transcript: `docs/ppt/reports/audit-frontend-check.log`. These tests cover HTTP transport via mocked fetch and catalog parsing, not browser end-to-end behavior or traffic accuracy.

The repository `.venv` and `uv` are absent. Initial Python test launch could not execute; historical results in status documents are not current results. An isolated audit environment is being prepared with the bundled Python 3.12; subsequent outcomes will be appended. `tests/conftest.py` isolates the database in a temporary directory.

CI configuration includes Windows x64, macOS ARM64 **and macOS Intel**; `sim/STATUS.md` and part of `sim/AGENTS.md` are stale about Intel and old integration branches. Workflow configuration is not proof of a fresh successful run. No remote CI result is asserted without verification.

## Strongest defensible achievements and innovation

The distinctive contribution is integration and evidence discipline: candidate discovery → independent same-baseline graph comparisons → validation tied to computed candidates → UI disclosure and persisted study evidence. Common-sample ranking, separated local diagnostics, immutable baselines, provenance and explicit unknowns are defensible engineering achievements. They do not establish algorithmic novelty over all competing tools, a world-first feature, or superiority in measured performance.

## Priority gaps and future work

1. Connect and evaluate constrained LLM generation using existing evidence packets; measure proposal validity and explanation faithfulness.
2. Reproduce sourced-area studies online; preserve exact geometry/snapshot and expose calculated links/routes on the map (current spatial map displays selected area, not returned candidate overlays).
3. Collect observed mobility demand and field feedback; validate sampled graph findings and physical feasibility.
4. Integrate bounded SUMO jobs only for supported road interventions; calibrate inputs and distinguish simulation output from observations.
5. Validate user need, procurement, price and pilot success criteria; no customer traction found.
6. Add authentication, export/collaboration and mobile API workflows only as separate product work.

These are possibilities or genuine gaps, not achievements. No application code was changed during this inventory.

## Fresh verification addendum (after independent inventory)

The existing ignored `docs/ppt/reports/.qa/runtime` was subsequently located and reused with bundled Python **3.12.14**. No dependency installation succeeded or was needed; an initial sandboxed pip attempt failed DNS resolution. The audit runtime follows compatible dependency ranges but is **not** a verified synchronization of `uv.lock`. Versions are recorded in `audit-runtime-versions.json`.

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, existing runtime on `PYTHONPATH`, `python -m pytest -q -p no:cacheprovider ... tests sim/test_engine.py`: **138 passed, 1 warning in 15.59 seconds**, fresh run. The warning concerns Starlette/httpx deprecation. `audit-python-final.log` is authoritative for this run. Sandbox TestClient execution stalled; the same isolated tests completed outside the sandbox. Earlier empty/stalled logs are not test failures or successful results.
- Fresh `npm.cmd run check`: web/mobile/shared TypeScript checks, **9/9 Node tests**, production web build all passed (`audit-frontend-check.log`). The native scaffold typechecking is not an Android device test.
- Headless Chrome on the built app at audit port 3002, real API at 8000 and an audit-only SQLite database: signal analysis/proposal/tuned evaluation passed at green 70; mean delay increased; source remained synthetic. Pedestrian fixture study returned **3/3 accepted candidate-backed options**; selecting a link returned `stored_graph_comparison`, retained the baseline and declared `sumo_executed:false`. No page exceptions; no document-width overflow at 375, 768 and 1440 px. `audit-browser-results.json` and `audit-browser.log` preserve this evidence. Audit-port CORS was configured via environment only; the first attempt was blocked by default CORS, then passed with the explicit audit origin.
- `python -m sim.proposal_demo --source fixture`: generated a finite evidence/options/validation packet (`audit-proposal-fixture.json`); deterministic fixture, no cloud AI or OSM network request.
- SUMO discovery: TraCI/sumolib **1.28.0** are importable, but `sumo` and `netconvert` executables were **not found**, so optional synthetic smoke **skipped**, not passed. No vehicle simulation ran (`audit-sumo.log`).

These results upgrade the integrated **fixture** path from source-wired to reproduced browser/API behavior. They do not establish live OSM acquisition success, field validity, physical feasibility, authenticated production operation, calibrated traffic or a connected LLM. The historical browser script in `frontend/shared/tests/backend-flow.cjs` contains older spatial button/heading selectors; it was not falsely reported as passing unchanged. A focused audit script used current selectors and real backend responses.

Official organizer documents were then found online; earlier research uncertainty on duration/criteria is superseded by `HACKATHON_REQUIREMENTS_VERIFICATION.md`. That check does not alter the independent implementation inventory.
