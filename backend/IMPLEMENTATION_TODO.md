# ARTERIA Backend Implementation Handoff

## Purpose and implementation order

Provide a trustworthy backend workflow for the map-first frontend: resolve one canonical SIM neighborhood, create and retain an evidence-backed pedestrian study, validate and evaluate exact SIM candidates, and return provenance the UI can explain. Keep HTTP orchestration in `backend/`; SIM owns geography acquisition, graph analysis, candidate semantics and SUMO capabilities. Do not make the backend imply that unsupported AI or traffic simulation ran.

Recommended order:

1. **P0-01:** stabilize the canonical spatial study, candidate and evaluation lifecycle.
2. **P0-02:** add an optional provider-neutral recommendation layer grounded only in SIM evidence and validated candidates.
3. **P0-03:** preserve execution metadata and unknowns across storage and API contracts.
4. **P0-04:** expose bounded OSM feature acquisition only after adding the needed SIM-owned selector.
5. **P0-05:** integrate real-area SUMO only after SIM can compare supported driving scenarios.
6. **P1-01:** harden resource limits, errors, CORS and storage for a controlled demo.
7. **P2-01:** add identity, isolation and production deployment controls before public multi-user use.

Priority totals: **P0: 5 tasks; P1: 1 task; P2: 1 task.**

## Verified current baseline

The audited source commit is `60fe2eed4230ddeffe56bcedf44c49d66861b206`. The local audit reported 138 Python tests passing and 8/8 backend API checks passing. The backend is a local demo service; it has no cloud LLM provider, no authentication or per-user isolation, and no working SUMO execution adapter. Treat the audit as a snapshot, then rerun focused tests when implementing.

Relevant implementation:

- `backend/main.py` defines the signal demo endpoints and spatial router. `GET /api/v1/areas` returns five demo bookmarks, not the SIM OSM catalog. Errors use `{"error":{"code":"...","message":"...","details":...,"request_id":"..."}}`.
- `backend/spatial_models.py`, `spatial_routes.py`, `spatial_worker.py`, and `spatial_adapter.py` define the study lifecycle. The worker imports SIM from `ARTERIA_SIM_ROOT` and verifies the configured checkout. The adapter serializes spatial work through one slot and applies a 90-second subprocess timeout.
- `backend/storage.py` persists immutable ID-addressed JSON records in SQLite at `backend/.data/arteria.sqlite3`, or `ARTERIA_DB_PATH`. It caps each record category at 1000 but has no user ownership or public delete operation.
- `backend/simulation_adapter.py` is a deterministic synthetic signal-delay demo. `require_sumo()` always reports unavailable because SIM does not expose a network/demand/intervention API for that route. The signal `/analyze`, `/propose` and `/evaluate` endpoints are not neighborhood analysis.
- `backend/engine_contract.py` validates raw SIM result shapes, permits additional SIM fields, and rejects non-finite values. Candidate actions use EPSG:4326 endpoints. Evaluation route rows currently contain outcomes and distance deltas, not route-line GeoJSON.
- `sim/AGENTS.md` documents SIM ownership and API conventions. Never implement SIM-owned changes in `sim/` as part of a backend task; make a precise request to the SIM owner instead.

## Shared frontend/backend flow

Keep the same identity and lifecycle as the frontend handoff:

**Selected OSM polygon → canonical SIM `neighborhood_id` → spatial study → SIM candidate validation → stored-baseline evaluation → map layers and comparison.**

The frontend sends the canonical ID only. The backend resolves it from SIM again. It must not accept a client-provided boundary as the authoritative analysis area. Points, malformed geometry, and polygons requiring controlled analysis are rejected by the standard study path. Keep the demo bookmark API separate; do not add a duplicate neighborhood catalog endpoint while the frontend can load its checked static GeoJSON.

Current study API:

```http
POST /api/v1/spatial/studies
Content-Type: application/json
```

```json
{
  "source": "osm",
  "neighborhood_id": "<canonical SIM catalog ID>",
  "sample_count": 16,
  "max_candidates": 3,
  "seed": "arteria-spatial-v1"
}
```

The implemented request also supports `source: "fixture"`; OSM requires a 1–200 character `neighborhood_id`. `sample_count` is a strict integer from 1 through 64, `max_candidates` from 1 through 3, and `seed` is 1–100 characters. The frontend currently sends only `source` and `neighborhood_id`, so the server applies defaults.

The 201 response is a stored `Study`: `study_id`, `baseline_id`, `created_at`, `source`, `engine_revision`, `calculation: "pedestrian_graph"`, `analysis`, `alternatives`, `proposal_options`, `proposal_validation`, `evidence_packet` and `warnings`. `analysis` carries SIM `area`, `indicators`, `issues`, `issue_geojson`, `heatmaps`, `layer_availability`, `layers`, `networks`, `network_metrics`, `provenance`, `uncertainty` and `warnings`. SIM GeoJSON uses WGS84 / EPSG:4326 coordinates in `[longitude, latitude]` order.

Current follow-up routes:

- `GET /api/v1/spatial/studies/{study_id}` returns the stored study.
- `GET /api/v1/spatial/studies/{study_id}/candidates` returns candidates and warnings.
- `POST /api/v1/spatial/studies/{study_id}/evaluate` accepts the matching `baseline_id`, exact returned `candidate_id`, and exact server-returned `intervention`. It rejects mismatched baselines, unknown or edited interventions, and candidates not marked `candidate_backed_evaluated`.

Spatial evaluation currently reports `execution: "stored_graph_comparison"` and `sumo_executed: false`. This means a deterministic comparison on stored pedestrian-graph data; it is not an observed journey, a traffic model or a SUMO run.

## P0 — Mandatory for the hackathon MVP

### P0-01 — Preserve canonical study identity and validate the workflow end to end

**Current behavior:** `POST /api/v1/spatial/studies` runs the SIM worker and stores a baseline. Study and candidate retrieval routes already exist. Evaluation verifies the immutable baseline and exact SIM candidate/intervention. `GET /api/v1/areas` is a separate five-bookmark demo endpoint.

**Desired behavior:** every study/evaluation is tied to the same SIM catalog ID, source and stored baseline; invalid areas and candidate edits fail with stable structured errors. Retrieval gives the frontend the same evidence used for evaluation. Do not duplicate static catalog delivery in the backend.

**Reuse and likely files:** `spatial_models.py`, `spatial_routes.py`, `spatial_worker.py`, `spatial_adapter.py`, `storage.py`, `engine_contract.py`, `tests/test_spatial_api.py`.

**Implementation steps:**

1. Keep OSM lookup server-side through `get_neighborhood` / `get_neighborhoods` and `validate_neighborhood_boundary`; verify the canonical ID against the current configured SIM snapshot. Preserve the current default limits (`max_area_km2=5`, `max_extent_km=5`) unless the SIM owner changes the documented contract.
2. Keep Points, invalid geometry and `requires_controlled_analysis` out of the standard study path. Return the current error envelope and useful `unknown_neighborhood` (404) or `study_area_rejected` (422) codes without substituting fixture data.
3. Keep stored study, candidate and evaluation records linked by their server-generated IDs. Continue requiring the returned `baseline_id`, candidate ID and exact intervention on evaluation; never trust a frontend-supplied metric or geometry.
4. Ensure retrieval returns the stored original baseline and candidate evidence without recomputing against a newer OSM/SIM snapshot. Return 404 for unknown IDs and preserve the source and engine revision.
5. Add an explicit GET method to the shared frontend client only if the frontend team needs the existing study/candidate retrieval routes; do not create redundant backend endpoints.

**Acceptance:** standard OSM study accepts only a currently resolvable, eligible canonical SIM polygon; evaluation is bound to the original baseline and exact validated candidate; retrieval is stable; all failures are structured and never fall back to fixture.

**Tests:** valid OSM study 201 and retrieval; unknown ID 404; Point, malformed and over-limit areas 422; edited/unknown candidate and wrong baseline rejected; retrieval of unknown study 404; acquisition error, busy slot and timeout produce 502/503/504 as documented; assert the SIM worker is not called for invalid request bodies and no synthetic fixture result appears after OSM failure.

**Risks:** client-side bundled validation can be stale. The server-side SIM lookup and validation must remain authoritative. SQLite records are local and not per-user; that limitation is addressed under P1/P2, not disguised as shared cloud state.

**Definition of done:** the API preserves canonical identity and immutable baseline semantics for the full frontend flow, with contract tests for each rejection and retrieval case.

**Effort:** 2–3 hours.

### P0-02 — Add grounded, provider-neutral AI recommendations (optional capability)

**Current behavior:** no cloud LLM is configured. SIM deterministically creates candidate options and exposes `build_proposal_context`; the context is bounded and contains evidence, metrics, issues, candidates and shared sample data, not the full graph. `validate_proposal_set` checks supported actions, units, coordinates, citations, run IDs, metrics, feasibility claims and candidate matching. The signal `/propose` route is deterministic synthetic demo behavior, not AI.

**Desired behavior:** an explicitly configured provider may explain and order the exact SIM-validated candidates for one stored study. The model must not create candidate geometry, metrics, evidence, costs, observed claims, or interventions. No credentials/provider means an explicit unavailable response; deterministic SIM options remain available and are never labeled AI output.

**New route — PROPOSED, NOT CURRENTLY IMPLEMENTED:**

```http
POST /api/v1/spatial/studies/{study_id}/recommendations
Content-Type: application/json
```

```json
{
  "candidate_ids": ["<IDs already present in this study>"],
  "locale": "ro"
}
```

This proposal intentionally omits model selection, credentials, geometry, arbitrary prompt text and user-supplied evidence. The server chooses the configured provider/model and builds context from the stored study. A proposed response should identify provider/model/revision, `status`, ordered candidate IDs, short evidence-linked explanations, warnings and an explicit `ai_generated`/execution status. Final field names and response schema remain a backend design decision and must be shared with the frontend before implementation; do not treat this example as an existing contract.

**Reuse and likely files:** `spatial_routes.py`, `spatial_models.py`, `spatial_worker.py`, `storage.py`, `sim` public APIs `build_proposal_context`, `prepare_candidate_options`, `validate_proposal_set`, `get_intervention_catalog`, and `tests/test_spatial_api.py`.

**Implementation steps:**

1. Load the immutable stored study, call or reuse its bounded deterministic proposal context, and obtain candidate options plus validation results from that study’s SIM snapshot. Use the intervention catalog to explain supported action types and `sumo_evaluation_available: false` accurately.
2. Define a small provider interface and a structured output schema. The provider receives only bounded `arteria.proposal-context.v1` evidence and cannot access arbitrary network/filesystem tools. Before coding a concrete vendor adapter, consult that provider’s current official schema/API documentation and keep provider-specific code behind the interface.
3. Have the model return candidate IDs and grounded rationale only. Rejoin every ID to the stored server-owned candidate, attach its exact intervention and SIM-produced validation/impact fields on the server, and run `validate_proposal_set` on any returned proposal structure. Reject unknown, duplicate, unsupported or altered candidate/action references.
4. Store or return the provider/model identity, schema revision, context hash, study/baseline IDs, evidence references, warnings, and success/unavailable/error status for reproducibility. Do not store secrets or raw credentials.
5. When provider configuration is absent or a provider fails, return a clear unavailable/error state; keep deterministic candidates visible under their correct label. Do not silently call a different provider or claim a successful AI run.

**Acceptance:** every recommendation belongs to one stored study and consists only of its SIM-validated candidate IDs; every factual metric and intervention is server-attached; all explanatory claims cite bounded context evidence; disabled/provider-failure cases are explicit and deterministic SIM options remain usable.

**Tests:** provider-free unavailable case; mock provider valid ordering/explanations; unknown or duplicate ID; unsupported action; metric/geometry injection; context-size bound; provider timeout/error; absent credentials; study mismatch; verify no secret enters response/logs and no result is labeled AI unless a provider call completed.

**Risks:** provider output can confidently overstate graph evidence or feasibility. Treat model text as untrusted, validate every reference, keep physical feasibility/cost unknown, and display source/model/warnings to users.

**Definition of done:** provider-neutral, bounded recommendation interface is documented and tested, with a deterministic no-provider path and no model authority over SIM data.

**Effort:** 4–6 hours plus provider configuration and official-schema review.

### P0-03 — Preserve provenance, uncertainty and execution semantics

**Current behavior:** `Study` stores source, SIM engine revision, calculation, analysis, candidates, validation, evidence and warnings. It does not retain the request’s `sample_count`, `max_candidates` or `seed` as top-level study metadata. `SpatialEvaluation` distinguishes `stored_graph_comparison` and `sumo_executed: false`. The route currently sets `evaluated_at` to `study.created_at`, and a test asserts this behavior even though evaluation occurs later. SIM has unknown indicators/layers when evidence is unavailable; they must not be turned into zero.

**Desired behavior:** stored results explain which input and engine snapshot produced them, retain unknown/missing data as unknown, and timestamp the actual evaluation. The API makes graph analysis, synthetic signal estimates, AI and SUMO execution separate capabilities.

**Reuse and likely files:** `spatial_models.py`, `spatial_routes.py`, `spatial_worker.py`, `engine_contract.py`, `simulation_adapter.py`, `tests/test_spatial_api.py`.

**Implementation steps:**

1. Add the validated study request parameters (`sample_count`, `max_candidates`, `seed`) to the persisted `Study` contract and populate them from the actual request. Consider a request/engine contract version if persisted records may outlive a deploy.
2. Set `SpatialEvaluation.evaluated_at` at evaluation time in UTC rather than copying `study.created_at`; update the test that currently enshrines the old timestamp. Keep baseline `created_at` and evaluation time separate.
3. Preserve SIM `provenance`, `uncertainty`, `layer_availability`, `warnings` and null indicator values in storage and API serialization. Do not replace missing values or unavailable feature layers with zero/empty-success language.
4. Return method/execution facts: pedestrian graph calculation, stored graph comparison, synthetic signal estimate, provider call status and SUMO status are distinct. `sumo_executed` remains false unless a real completed SIM run is wired and returned.
5. Keep `engine_revision` tied to the exact configured SIM checkout; preserve the `-sim-dirty` marker and avoid presenting a dirty revision as a release build.

**Acceptance:** study can be reproduced from persisted input metadata and engine revision; evaluation time reflects the evaluation; unknown and unavailable states survive serialization; no endpoint conflates graph calculation, synthetic estimate, AI request or SUMO execution.

**Tests:** round-trip nullable indicators, missing and unknown layers, provenance and uncertainty; assert request parameters are persisted; assert evaluation timestamp is later than/equal to request time and independent of study timestamp; test method/status labels and no-SUMO false state for graph comparisons.

**Risks:** schema additions affect stored SQLite JSON and frontend contracts. Make new fields backward-compatible for existing records and coordinate matching frontend types before requiring them.

**Definition of done:** every persisted result carries enough truthful provenance and run configuration to identify what happened and what remains unknown.

**Effort:** 2–3 hours.

### P0-04 — Add bounded OSM feature availability through a SIM-owned contract

**Current behavior:** `spatial_worker.py` calls `acquire_osm_data(..., modes=("walk",), include_features=False, ...)`. This intentionally avoids optional POI layers, so their availability is unknown. The current SIM API has a single boolean `include_features`; it has no `feature_categories` selector. There is no population dataset in the current flow, so population remains unknown even if OSM feature data is acquired.

**Desired behavior:** after a SIM-owned API change, backend may request a small, explicit set of supported feature categories within documented area/time/resource limits. Each returned layer retains per-layer availability and source provenance. Unsupported or unavailable categories stay unknown; OSM feature counts do not become population estimates.

**SIM API request — SIM OWNER ACTION REQUIRED; not available today:**

1. Add a bounded category selector to `acquire_osm_data`, for example `feature_categories: Sequence[SupportedFeatureCategory] | None`, while retaining the existing `include_features` compatibility path. The SIM owner must define the enum/category names from supported OSM tags, not the backend.
2. Define and test the exact output contract per requested category: either returned feature data with CRS/geometry validity and OSM source IDs, or an explicit availability state such as available, unavailable, unsupported, not requested, or failed, with retrieval timestamp, query/source attribution and warnings.
3. Apply category count, feature-count, area, extent, cache and request-time bounds inside SIM. Reject an unsupported category and report partial availability rather than dropping a whole successful neighborhood study.
4. Keep population, demographics, pedestrian counts and incident truth as unknown unless a separately sourced dataset and methodology are introduced.

**Backend implementation after that SIM change:**

1. Add an optional validated feature-category setting to `SpatialRequest` with an empty/default setting that preserves current behavior. Intersect requests with the SIM-supported category enum; never pass raw Overpass/tag query text from the browser.
2. Pass the category list and existing `max_area_km2=5`, `max_extent_km=5`, cache and timeout controls through the worker. Keep `include_features=False` behavior for requests that select no categories.
3. Preserve each layer’s feature collection, availability, retrieval provenance and warnings through `engine_contract.py`, `Study` storage and GET retrieval. Bound serialized response size and fail/omit an oversized optional layer with an explicit state, not a fabricated empty result.
4. Expose per-layer status to the frontend so the map legend can distinguish not requested, unavailable, failed and available-empty.

**Likely backend files:** `spatial_models.py`, `spatial_routes.py`, `spatial_worker.py`, `engine_contract.py`, `tests/test_spatial_api.py`; SIM files are owned by the SIM maintainer and are not to be edited in this backend task.

**Acceptance:** default requests preserve current offline/cache behavior; requested supported layers are bounded and carry provenance/status; optional feature failure does not corrupt core walking-network results; no POI count is represented as residents or population.

**Tests:** default feature-off; each supported category; unsupported category validation; available-empty vs unavailable vs failed; partial layer failure; oversized response behavior; cache reuse; area/time/count limit enforcement; unknown population remains null/unknown.

**Risks:** external OSM query latency, ODbL obligations, response growth and stale cache. Keep refresh explicit, preserve OSM attribution/ODbL, and use bounded cached retrieval. This task cannot be completed until the SIM owner publishes the selector and output schema.

**Definition of done:** backend and SIM agree on a versioned category/availability contract and optional features never make core analysis claim unsupported evidence.

**Effort:** 3–5 backend hours after the SIM contract is available; separate SIM estimate required.

### P0-05 — Integrate SUMO only after SIM supports a real scenario comparison

**Current behavior:** `SimulationAdapter.require_sumo()` always raises `SimulationUnavailable`. SIM exposes `load_cached_driving_snapshot()` for the newest existing local driving graph for `DEFAULT_AREA` (not necessarily the selected neighborhood), `prepare_sumo_network(...)`, and `run_real_area_simulation(...)`. The runner is a bounded headless baseline using synthetic OD demand, requires a non-empty `data.graphs["drive"]`, downloads no OSM data, and accepts no intervention/scenario comparison. It cannot convert the pedestrian graph or current pedestrian candidate into a driving network intervention. SUMO/netconvert binaries may be absent. SIM caps include 15,000 nodes, 50,000 edges, at most 200 vehicles, at most 600 seconds of simulated duration, and at most 180 seconds of execution timeout.

**Desired behavior:** report unavailable honestly until the selected driving network and supported intervention can be simulated as a comparable baseline/scenario pair. A baseline-only synthetic-demand run can be useful diagnostics, but it must never appear as the effect of a pedestrian candidate or a real travel-demand forecast.

**SIM API request — SIM OWNER ACTION REQUIRED; not available today:**

1. Define a versioned supported driving intervention catalog with validated IDs, parameters, units, network applicability and explicit support/unsupported status. Do not reuse `add_pedestrian_connection` or `set_connection_enabled` as SUMO interventions; both currently have `sumo_evaluation_available: false`.
2. Add a bounded API that accepts an already acquired/cached driving snapshot for the requested study area, one supported intervention, deterministic seed, bounded demand inputs and run limits. It must not silently load `DEFAULT_AREA` when the user selected another neighborhood and must not download data as a side effect.
3. Return a versioned result containing baseline and scenario run IDs, snapshot/network revision and area ID, intervention ID/parameters, seed/demand provenance, execution status, tool versions, warnings, and separately reported finished, unfinished and not-departed trip counts. Include only actual generated GeoJSON routes/edges and returned SUMO metrics; expose unavailable/timeout/failed states as first-class outcomes.
4. Add deterministic offline tests for unsupported interventions, missing binaries, timeout, partial trip completion/accounting, network bounds and baseline/scenario alignment.

**Proposed backend API — PROPOSED, NOT CURRENTLY IMPLEMENTED:**

```http
POST /api/v1/sumo/runs
GET  /api/v1/sumo/runs/{run_id}
```

The POST request should reference a stored study or explicit validated area/network snapshot, a SIM catalog intervention ID and bounded parameters, seed and bounded synthetic-demand settings. It must not accept arbitrary command lines, file paths, raw network geometry or claimed metric values. Exact request/response fields must follow the SIM versioned result contract above; do not ship these routes until that contract exists. A truthful response can be `unavailable`, `timeout`, `failed` or `completed`; only `completed` may expose actual produced metrics/GeoJSON. If doing a demonstration before scenario support, a bounded precomputed artifact is acceptable only if it is verifiable, labeled as baseline-only and tied to its actual area, network revision, demand, seed and run provenance.

**Reuse and likely files:** `backend/simulation_adapter.py`, `backend/main.py` or a separate SUMO router, `backend/spatial_models.py`, `backend/storage.py`, tests; SIM public funcs `load_cached_driving_snapshot`, `prepare_sumo_network`, `run_real_area_simulation`.

**Acceptance:** no standard OSM pedestrian study is presented as a traffic simulation; selected area/network and intervention are matched; unavailable tooling returns explicit status with no synthetic fallback; trip accounting distinguishes finished, unfinished and not-departed vehicles.

**Tests:** adapter unavailable today; missing binaries; mismatched area; unsupported/pedestrian intervention; seed and limits; timeout; completed result schema; no route geometry when absent; trip counts and returned GeoJSON correspond only to completed actual runs; frontend-visible status never says SUMO executed for a graph comparison.

**Risks:** SUMO represents simulated network/demand assumptions, not observed traffic. Network preparation, demand generation and scenario applicability require a SIM contract and may exceed local resource budgets. Do not enable a route until SIM proves a paired comparison.

**Definition of done:** SIM supplies and tests a bounded paired-scenario contract; backend validates and stores the run/result; unavailability remains explicit; no fabricated route or impact is returned.

**Effort:** SIM design/implementation first, then 4–8 backend hours depending on run lifecycle and result size.

## P1 — Controlled-demo robustness

### P1-01 — Make resource, error, CORS and storage limits explicit

**Current behavior:** one in-process spatial slot and a 90-second worker timeout protect the local demo. `spatial_adapter.py` maps busy/unavailable, timeout and generic failures to 503, 504 and 502. CORS defaults allow ports 3000 and 5173; `ARTERIA_CORS_ORIGINS` overrides them, so do not assume a frontend on port 3001 is allowed. SQLite is local, immutable-ID keyed, capped at 1000 records/category, persists through restarts and has no authentication, ownership or cleanup endpoint.

**Desired behavior:** the controlled demo has documented limits and observable, actionable failures without exposing stack traces/secrets or claiming durable multi-user jobs.

**Reuse and likely files:** `backend/main.py`, `spatial_adapter.py`, `spatial_routes.py`, `storage.py`, `backend/README.md`, `tests/test_spatial_api.py`.

**Implementation steps:**

1. Document and expose configuration for worker concurrency, timeout, allowed origins, database path and record cap. Keep defaults conservative; do not add a queue or infrastructure for this task.
2. Configure the actual local frontend origin explicitly through `ARTERIA_CORS_ORIGINS` when needed. Keep origins exact and avoid wildcard credentials.
3. Ensure API responses return stable error codes and request IDs; keep stack traces, environment values, OSM credentials (if any) and filesystem paths in protected server logs only. Add structured duration/status logging without recording provider secrets or full user prompts.
4. Add tests for overlapping work, slot release after exceptions/timeouts, disallowed and allowed CORS origins, database cap, malformed stored records and request IDs.
5. Clearly document SQLite’s local scope, persistence and lack of user isolation; do not present it as a shared cloud project database.

**Acceptance:** limits and allowed local origins are reproducible; error envelope remains stable; slot is released on all exits; CORS and storage behavior are covered; logs and responses do not leak secrets or internal exception details.

**Risks:** persistent local studies may include source-derived data and can outlive code updates. Avoid broad cleanup or migrations without backup and explicit retention rules.

**Definition of done:** documented controlled-demo operation has tested concurrency, timeout, origin and persistence boundaries.

**Effort:** 2–3 hours.

## P2 — Before public multi-user deployment

### P2-01 — Add identity, tenant isolation and production operations

**Current behavior:** backend has no auth, per-user records, deletion, rate limits, abuse controls or production deployment configuration. The local SQLite store is not suitable for shared public deployment. CORS is not authorization. The optional LLM recommendation feature must not be enabled publicly without server-side secret management and spend/rate controls.

**Desired behavior:** public users can only access authorized studies; records have ownership, retention and deletion semantics; external engine/provider work is bounded, auditable and protected.

**Likely files:** `backend/main.py`, route/model/storage layers, `backend/README.md`, deployment-specific configuration and integration tests (only when public deployment is actually scheduled).

**Implementation steps:**

1. Select and configure a supported identity provider; verify authorization server-side on create, retrieval, candidate, evaluation, recommendation and run routes.
2. Move persistence to a supported concurrent database with schema migrations, tenant-scoped queries, retention and deletion policy; do not simply expose the local SQLite file.
3. Add rate/concurrency/size limits, request deadlines, audit records, privacy and ODbL/source-attribution handling, backups, monitoring and incident procedures.
4. Keep LLM and SUMO credentials/configuration server-side; constrain spend and access; add security review and deployment tests before enabling public traffic.

**Acceptance:** cross-user ID guessing cannot read or mutate another user’s records; delete/retention behavior is tested; rate and resource controls are enforced; secrets never reach clients; production security review is complete.

**Tests:** authenticated/unauthenticated routes; cross-tenant access denial for each record type; deletion and retention; rate/concurrency limits; secret redaction; database recovery and migration; public CORS does not grant data access.

**Risks:** identity and hosting choices affect architecture and require product/operations decisions. This is intentionally post-hackathon and should be scoped with the deployment owner.

**Definition of done:** deployable service has verified identity, tenant isolation, secure storage, retention and operational controls.

**Effort:** estimate after deployment architecture and hosting target are selected.

## Backend verification checklist

Run focused tests from the repository’s established Python environment; the documented project convention is `uv run --locked pytest ...`.

- [ ] A valid canonical OSM polygon creates and retrieves a stored study with stable baseline ID and engine revision.
- [ ] Point, invalid, unknown and controlled-analysis neighborhoods fail with the expected structured code/status and never use fixture fallback.
- [ ] Candidate evaluation accepts only the exact stored baseline, candidate ID and intervention returned by SIM.
- [ ] Study request parameters, provenance, uncertainty and layer availability survive storage and GET retrieval; unknown remains unknown.
- [ ] Evaluation timestamp reflects evaluation time, not study creation time.
- [ ] AI recommendation is explicitly unavailable without a provider; mock-provider output can only reference validated stored candidates; provider errors do not relabel deterministic options as AI.
- [ ] OSM feature acquisition stays off by default, and any future category request is bounded and carries per-layer source/availability metadata.
- [ ] Pedestrian graph comparison always reports `sumo_executed: false`; no SUMO route is exposed until SIM supplies a paired-scenario contract.
- [ ] SUMO result (when implemented) ties baseline/scenario to the same area/network revision and accounts for finished, unfinished and not-departed trips separately.
- [ ] Worker busy, timeout, generic failure, CORS and SQLite limits have regression coverage; errors do not leak secrets or stack traces.
- [ ] No backend endpoint represents OSM feature counts as population, synthetic signal delay as observed traffic, or graph distances as measured journeys.

## SIM owner requests required by this handoff

1. **Optional feature layers:** extend `acquire_osm_data` with a bounded supported-category selector, per-category availability/provenance and deterministic offline tests. Current API has only `include_features: bool`; no category selector exists.
2. **SUMO scenario comparison:** define a versioned driving-intervention catalog and a paired baseline/scenario API bound to an explicit selected driving snapshot, with bounded demand, run status, trip accounting and actual GeoJSON outputs. Current `run_real_area_simulation` is baseline-only and has no intervention argument.

These are requests to the SIM owner, not backend capabilities that may be assumed during implementation. Keep `sim/` unchanged until its owner accepts and delivers the API contract.

## SIM v4 contract addendum (branch pending merge)

The SIM owner has implemented both requested Python contracts on `feat/sim-v4-mvp`; they are not in `main` yet. Review [sim/INTEGRATION_CONTRACT_V4.md](../sim/INTEGRATION_CONTRACT_V4.md) after that branch's PR merges. This addendum supersedes the two “not available today” statements above only once that merge is complete.

- `acquire_osm_data(..., feature_categories=...)` accepts a bounded set of eight fixed OSM category IDs, preserves default broad-query and `include_features=False` compatibility, and returns `metadata.feature_category_availability` per category. Keep category failure/unknown distinct from available-empty and pass OSM attribution/ODbL through storage and responses.
- `get_driving_intervention_catalog(data)` and `evaluate_driving_scenario(data, intervention, output_dir, ...)` are separate from pedestrian graph edits. The only current driving operation is version-bound `set_drive_edge_speed_limit` (1–55 m/s). Paired runs share one deterministic synthetic OD plan and return `arteria.sumo-comparison.v1`; the SIM evaluator makes no OSM request and has no persistent job store or HTTP endpoint.
- Backend should accept only a selected stored snapshot's drive graph, resolve catalog targets against its exact network revision, invoke SIM in a bounded worker, persist both run outputs/provenance, and map explicit `unavailable`, `preparation_failed`, `timeout`, `failed`, and `completed` states. `comparison` is `null` unless both runs complete. Stable public run IDs, authorization, concurrency limits, persistence, HTTP schemas, and safe artifact serving remain backend-owned.
- Only actual TripInfo metrics from both runs and actual matching valid SUMO-reported routes can appear in paired deltas. Demand remains synthetic; simulation is uncalibrated; SUMO route GeoJSON is not GPS; feasibility/legal status is unknown. Keep pedestrian graph comparison marked as not SUMO-executed.

Implement the adapter only after the contract branch merges and cross-check backend schemas against that document; this task does not change backend source.

## SIM AI Planning Contract — Integration Required

**Status:** SIM v4 PR #5 was merged normally into `main` as `6760ded19a9985e4d61101b1432b3815e016d51e`. Its Windows x64 and macOS ARM64/Intel checks passed. The new AI planning APIs described here are available only in `feat/sim-ai-planning-mvp` until its PR is merged. Backend AI planning is not implemented, and no cloud LLM has been called by SIM.

**Current storage limitation:** `backend/spatial_worker.py::calculate` acquires or creates an `OSMData`, calculates `analysis`, candidates, proposal validation and the existing `build_proposal_context` packet, then exits its subprocess. `backend/spatial_routes.py::create_study` stores an immutable `Study` with those JSON results. The raw `OSMData` graph is not persisted, and the current worker does not emit urban problems, the solution plan or the new AI planning packet. Build these records while the matching snapshot is still in the worker, then add them to the stored study contract. The recommendation request must use the stored packet unchanged and must not fetch a new snapshot.

**SIM functions to call:**

- `detect_urban_problems(snapshot, analysis=analysis, candidate_evaluation=evaluation, paired_sumo_result=optional_verified_pair)` creates localized problems, coverage gaps and separately labeled verified SUMO observations.
- `build_solution_plan(snapshot, analysis, urban_issues, evaluation)` uses `prepare_candidate_options` and `validate_proposal_set` to connect actual evaluated candidates to problems; conceptual suggestions carry no executable geometry or impact.
- `build_ai_planning_packet(snapshot, analysis, urban_issues, evaluation, solution_plan)` wraps `build_proposal_context`, preserves provenance and bounds the packet to 65,536 bytes by default. Store its `integrity.sha256` with the immutable study record; it is a checksum, not a signature.
- `AI_SYSTEM_PROMPT` and `AI_OUTPUT_SCHEMA` define the provider-neutral model call. `run_ai_planning(packet, call_model, timeout_seconds=20)` invokes an injected callback and `validate_ai_planning_response(response, packet)` returns accepted references with authoritative SIM candidate geometry, intervention and impact attached.
- `problem_locations_geojson(urban_issues)` exports problem markers and actual calculated geometry in EPSG:4326.

**Study creation flow:**

```python
snapshot = acquire_osm_data(
    neighborhood_area_input(get_neighborhood(neighborhood_id)),
    modes=("walk",),
    include_features=True,
    feature_categories=("schools", "healthcare", "public_transport", "crossings"),
)
analysis = analyze_snapshot(snapshot)
evaluation = evaluate_candidates(snapshot, analysis=analysis, sample_count=request.sample_count, seed=request.seed)
urban_issues = detect_urban_problems(snapshot, analysis=analysis, candidate_evaluation=evaluation)
solution_plan = build_solution_plan(snapshot, analysis, urban_issues, evaluation)
ai_packet = build_ai_planning_packet(snapshot, analysis, urban_issues, evaluation, solution_plan)
# Persist analysis, evaluation, solution_plan, and ai_packet in the same immutable Study.
# Keep the packet available after this worker exits; do not persist or re-fetch the graph for LLM calls.
```

In the actual worker, retain the current area validation/error mapping and request bounds. Fixture studies must call `fixture_snapshot()` and remain labeled synthetic; never substitute a fixture for a failed OSM request. The selected feature categories are optional and bounded to four. Keep unknown and available-empty states distinct.

**Recommendation request flow:**

```python
study = load_study(study_id)                       # existing study and its stored packet
packet = study.ai_evidence_packet                  # immutable snapshot-bound JSON

def call_model(*, packet, system_prompt, output_schema, timeout_seconds):
    return configured_backend_provider.structured_json(
        system_prompt=system_prompt,
        input_json=packet,
        schema=output_schema,
        timeout_seconds=timeout_seconds,
    )

result = run_ai_planning(packet, call_model, timeout_seconds=20)
# Persist a separate immutable planning result linked to study_id and packet SHA-256.
# Return result.validation; it already contains only accepted model references and attached SIM facts.
```

The `configured_backend_provider.structured_json` call is an adapter placeholder, not a current method or provider dependency. The backend must request schema-constrained output, keep provider credentials server-side, enforce provider-side deadlines, and map SIM statuses without exposing exception details. `provider_unavailable`, `timeout`, `provider_error`, `invalid_response`, `completed_with_rejections`, and `completed` are distinct states. Do not call deterministic demo output an AI result.

**Illustrative model input and output:** IDs below are placeholders and must be copied verbatim from the stored packet; the model cannot create new ones.

```json
{
  "schema_version": "arteria.ai-planning-packet.v1",
  "study_area": {"area_id": "<stored-area-id>"},
  "urban_intelligence": {
    "problems": [{"problem_id": "prob_<packet-id>", "evidence": [{"evidence_id": "ev_<packet-id>"}]}]
  },
  "solution_plan": {
    "solutions": [{"solution_id": "sol_<packet-id>", "candidate_id": "cand_<packet-id>", "status": "supported_evaluated"}]
  },
  "integrity": {"sha256": "<packet-sha256>"}
}
```

```json
{
  "schema_version": "arteria.ai-planning-response.v1",
  "area_id": "<stored-area-id>",
  "evidence_packet_sha256": "<packet-sha256>",
  "summary": "Dovezile mapate justifică verificarea problemei citate.",
  "identified_problems": [{"problem_id": "prob_<packet-id>", "explanation": "Graful indică o posibilă întrerupere care trebuie verificată în teren.", "evidence_ids": ["ev_<packet-id>"]}],
  "recommended_solutions": [{"solution_id": "sol_<packet-id>", "candidate_id": "cand_<packet-id>", "problem_ids": ["prob_<packet-id>"], "title": "Evaluarea conexiunii candidate", "explanation": "Opțiunea este legată de dovezile citate; verificarea fizică este necesară.", "expected_benefit_type": "graph_connectivity_or_sampled_route_access", "evidence_ids": ["ev_<packet-id>"], "field_verification_required": true}],
  "supported_candidate_ids": ["cand_<packet-id>"],
  "evidence_references": ["ev_<packet-id>"],
  "limitations": ["Datele mapate pot fi incomplete."],
  "requires_field_verification": true
}
```

After validation, SIM returns the canonical `solution_id` and attaches the matching `authoritative_sim_solution` from the packet, including candidate geometry, exact intervention, shared-sample impact and separate targeted diagnostics. Persist that validated structure; never merge model-authored metrics or geometry into it. Unknown problem/candidate/evidence IDs, extra action/geometry/metric/cost/citation/SUMO fields, non-finite or oversized JSON, area/hash mismatch, feasibility claims and numeric prose are rejected. Invalid entries can be rejected individually while unrelated valid entries survive; an area/hash mismatch rejects the whole response.

**Proposed API addition (not implemented):** `POST /api/v1/spatial/studies/{study_id}/planning` with an empty or bounded preferences-only request; it must load the study's immutable stored packet, make no acquisition, and return an immutable planning-result ID, study/baseline IDs, packet hash, provider status and validated response. Update `Study` persistence/schema first to include `urban_issues`, `solution_plan` and `ai_evidence_packet`. Store each provider result separately because `Store.put` treats IDs as immutable. The current API has no AI planning route, provider integration, or provider credentials.

Before the product says “AI connected,” the backend owner must run one authenticated cloud-provider smoke test with server-side credentials, validate the returned packet-bound response, and verify that timeout/provider failures remain explicit. SIM's deterministic mock demo and tests do not satisfy this check. This handoff adds no backend implementation or endpoint.
