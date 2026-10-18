# SIM v4 Integration Contract

**Contract status:** SIM v4 was implemented on feat/sim-v4-mvp and merged into main by PR #5 at 6760ded19a9985e4d61101b1432b3815e016d51e. This is a Python integration contract; it does not add HTTP endpoints or persistence. The AI planning addendum below is implemented on feat/sim-ai-planning-mvp and is not available on main until that feature PR merges.

## Evidence and execution boundaries

SIM produces four different kinds of information. Keep their labels separate:

1. **OSM snapshot evidence:** mapped/tagged network and feature data with retrieval, area, cache, attribution, and uncertainty metadata.
2. **Calculated graph analysis:** NetworkX indicators and weighted routes from one source snapshot. Sampled graph-node pairs are not observed journeys, a representative population sample, or traffic counts.
3. **Candidate diagnostics:** candidate-independent shared pairs are the only candidate ranking evidence. Candidate-specific targeted routes are diagnostics and never affect the shared ranking.
4. **SUMO simulation:** simulated trips on an OSM-derived road network using deterministic synthetic demand. TripInfo is a SUMO output, not measured urban traffic, a calibrated forecast, or live telemetry. Route GeoJSON uses SUMO-reported edge sequences mapped to source OSM edge geometry; it is not timestep GPS.

The SIM package does not call a cloud LLM. Proposal packets are evidence for a backend-owned model call, and `validate_proposal` / `validate_proposal_set` only check supplied output against the supplied SIM evidence. Physical feasibility, safety, ownership, legal authorization, cost, and construction readiness remain unknown unless an independent source supports them.

## Public signatures

The signatures below are from the v4 implementation. Defaults and keyword-only boundaries are intentional.

```python
def acquire_osm_data(
    area: Any,
    *,
    modes: Iterable[str] = SUPPORTED_MODES,
    cache_dir: str | Path | None = None,
    use_cache: bool = True,
    force_refresh: bool = False,
    overpass_url: str | None = None,
    include_features: bool = True,
    feature_categories: Sequence[str] | None = None,
    max_area_km2: float = DEFAULT_MAX_AREA_KM2,
    max_extent_km: float = DEFAULT_MAX_EXTENT_KM,
) -> OSMData: ...

def get_driving_intervention_catalog(data: OSMData | None = None) -> dict[str, Any]: ...

def prepare_sumo_network(
    data: OSMData,
    output_dir: str | Path,
    *,
    vehicle_count: int = 20,
    seed: int = 4092,
    duration_seconds: float = 180.0,
    default_lanes: int = DEFAULT_LANES_PER_DIRECTION,
    default_speed_mps: float = DEFAULT_SPEED_MPS,
    max_nodes: int = DEFAULT_MAX_NODES,
    max_edges: int = DEFAULT_MAX_EDGES,
    demand_plan: Mapping[str, Any] | None = None,
    installation: SumoInstallation | None = None,
) -> dict[str, Any]: ...

def run_real_area_simulation(
    data: OSMData,
    output_dir: str | Path,
    *,
    vehicle_count: int = 20,
    seed: int = 4092,
    duration_seconds: float = 180.0,
    execution_timeout_seconds: float = 60.0,
    installation: SumoInstallation | None = None,
) -> dict[str, Any]: ...

def evaluate_driving_scenario(
    data: OSMData,
    intervention: Mapping[str, Any],
    output_dir: str | Path,
    *,
    vehicle_count: int = 20,
    seed: int = 4092,
    duration_seconds: float = 180.0,
    execution_timeout_seconds: float = 60.0,
    installation: SumoInstallation | None = None,
) -> dict[str, Any]: ...

def evaluate_candidates(
    data: OSMData,
    *,
    analysis: Mapping[str, Any] | None = None,
    max_candidates: int = 3,
    candidate_pool_limit: int = 100,
    max_evaluated_candidates: int = 12,
    sample_count: int = DEFAULT_ROUTE_SAMPLE_COUNT,
    seed: str | int = "arteria-v1",
    route_geometry_limit: int = DEFAULT_ROUTE_GEOMETRY_LIMIT,
    max_connection_length_m: float = 1_000.0,
    detour_ratio_threshold: float = 2.0,
) -> dict[str, Any]: ...

def build_proposal_context(
    data: OSMData,
    analysis: Mapping[str, Any],
    candidate_evaluation: Mapping[str, Any],
    *,
    max_packet_bytes: int = DEFAULT_MAX_PACKET_BYTES,
    max_issues: int = _DEFAULT_LIMITS["issues"],
    max_indicators: int = _DEFAULT_LIMITS["indicators"],
    max_candidates: int = _DEFAULT_LIMITS["candidates"],
    max_rejected_candidates: int = _DEFAULT_LIMITS["rejected_candidates"],
    max_route_samples: int = _DEFAULT_LIMITS["route_samples"],
    max_evidence_items: int = _DEFAULT_LIMITS["evidence_items"],
) -> dict[str, Any]: ...

def validate_proposal(
    proposal: Any,
    *,
    data: OSMData,
    candidate_evaluation: Any,
    verified_simulation_run_ids: Iterable[str] = (),
) -> dict[str, Any]: ...

def validate_proposal_set(
    proposals: Any,
    *,
    data: OSMData,
    candidate_evaluation: Any,
    verified_simulation_run_ids: Iterable[str] = (),
) -> dict[str, Any]: ...
```

`DEFAULT_MAX_AREA_KM2` and `DEFAULT_MAX_EXTENT_KM` are both `5.0`. SUMO hard limits are 15,000 source nodes, 50,000 directed edges, 200 requested vehicles, 600 simulated seconds, and 180 seconds wall-clock timeout per execution. Public calls may choose lower bounds. `prepare_sumo_network` and `evaluate_driving_scenario` require already acquired `OSMData`; they never download OSM or silently substitute `DEFAULT_AREA`.

## OSM feature-category selector

`feature_categories=None` preserves the original behavior: when `include_features=True`, it makes the legacy broad feature query. `include_features=False` continues to disable new feature requests and is compatible with `feature_categories=None` or `[]`; a nonempty explicit selection with `include_features=False` raises `ValueError`. An explicit `[]` never makes a broad feature request. The selector accepts only these IDs and at most four at a time:

| Category ID | OSM tag filter |
| --- | --- |
| `buildings` | `building=*` |
| `schools` | `amenity=kindergarten,school,university` |
| `healthcare` | `amenity=clinic,doctors,hospital,pharmacy` OR `healthcare=*` |
| `services` | `amenity=clinic,community_centre,doctors,fire_station,hospital,kindergarten,library,marketplace,pharmacy,police,school,university` |
| `public_transport` | `amenity=bus_station` OR `highway=bus_stop` OR `public_transport=*` OR `railway=halt,station,subway_entrance,tram_stop` |
| `parking` | `amenity=parking` OR `parking=*` |
| `green_space` | supported `landuse`, `leisure`, and `natural` values |
| `crossings` | `crossing=*` OR `highway=crossing` |

Queries are bounded to the existing validated area, four categories, 60-second selected-feature timeout, 5,000 raw features, and 4 MiB serialized GeoJSON. OSMnx rate limiting remains enabled. Category cache identity binds the normalized source-polygon hash, selector schema version, selected categories, and exact tag union. Broad legacy feature cache filenames remain compatible, but a legacy cache-key fallback is permitted only for the broad query. A selected-category cache requires a matching area geometry hash and category/query sidecar. `force_refresh=True` bypasses normalized-cache reads and makes the selected query again.

`metadata.feature_category_availability[category_id]` contains `category_id`, `status`, `feature_count`, `source_query`, `source`, `retrieved_at`, `cache_status`, `area_verification`, and `warnings`. Status values are `not_requested`, `available`, `available_but_empty`, `request_failed`, and `source_unverified`. Unsupported or duplicate IDs, invalid input types, and selectors over four IDs raise `ValueError` before network acquisition. Legacy `layer_availability` keeps `available`, `no_features_returned`, and `unknown`; failed/unrequested categories remain `unknown`, not zero. A failed optional category does not discard a successfully acquired graph.

Example backend call:

```python
snapshot = acquire_osm_data(
    area_input,
    modes=("walk",),
    include_features=True,
    feature_categories=("schools", "healthcare"),
)
schools = snapshot.layers["schools"]  # GeoDataFrame in EPSG:4326
availability = snapshot.metadata["feature_category_availability"]["schools"]
```

Example availability fragment (counts and timestamps depend on the requested snapshot):

```json
{
  "category_id": "schools",
  "status": "available_but_empty",
  "feature_count": 0,
  "source_query": {"amenity": ["kindergarten", "school", "university"]},
  "source": "OpenStreetMap",
  "retrieved_at": "<snapshot retrieval timestamp>",
  "cache_status": "miss",
  "area_verification": "verified_by_requested_geometry",
  "warnings": []
}
```

`available_but_empty` means only that the bounded OSM query returned no mapped/tagged matching records. It is not evidence that the real-world category is absent. Population and traffic volumes remain unavailable from this selector.

## Driving intervention catalog

The driving catalog is separate from the pedestrian catalog. It exposes only `set_drive_edge_speed_limit`; signal timing, new lanes, road expansion, roundabouts, underpasses, and construction operations are unsupported.

```python
catalog = get_driving_intervention_catalog(snapshot)
target = next(item for item in catalog["targets"] if item["sumo_edge_id"] == requested_edge_id)
intervention = {
    "schema_version": "arteria.driving-intervention.v1",
    "action": "set_drive_edge_speed_limit",
    "target": {
        "sumo_edge_id": target["sumo_edge_id"],
        "network_revision": target["network_revision"],
        "source_osm_way_ids": target["source_osm_way_ids"],
    },
    "parameters": {"speed_limit_mps": 5.0},
}
```

The action edits one directed edge's modeled `maxspeed` in a deep-copied scenario graph. It does not claim that the change is legal, safe, physically implementable, or recommended. Catalog IDs bind to the current source edge and a deterministic network revision. The accepted speed is finite and between 1 and 55 metres/second inclusive. Missing edge IDs, stale revisions, mismatched source OSM way IDs, and unsupported actions are rejected with `ValueError`.

## Paired SUMO execution

`evaluate_driving_scenario` builds and executes independent baseline and scenario networks from one copied source snapshot. It creates the deterministic OSM shortest-path synthetic demand plan once and passes that exact plan—including IDs, OD node IDs, route edge IDs, and departure times—to both preparations. It reuses the seed and simulation horizon in both SUMO processes. No hidden acquisition or fallback occurs. The parent output directory must be new or empty; an existing nonempty directory is refused.

Result schema: `arteria.sumo-comparison.v1`. Top-level `status` is one of `unavailable`, `preparation_failed`, `timeout`, `failed`, or `completed`. `comparison` is `null` unless both runs complete successfully. Each run reports requested/generated/departed/finished/unfinished/not-departed/unreported counts, horizon, whether TripInfo and vehroute files exist, actual TripInfo measurements (or `null`), preparation details, status, warnings, and output paths. A completed pair compares only vehicle IDs finished in both runs whose actual SUMO-reported route edge sequences are both valid and identical. Changed, invalid, or unreported routes are listed or excluded explicitly. If no comparable vehicles exist, `comparison.metrics` is `null`.

Example invocation:

```python
from sim import evaluate_driving_scenario, get_driving_intervention_catalog

catalog = get_driving_intervention_catalog(snapshot)
edge = catalog["targets"][0]
result = evaluate_driving_scenario(
    snapshot,
    {
        "schema_version": "arteria.driving-intervention.v1",
        "action": "set_drive_edge_speed_limit",
        "target": {
            "sumo_edge_id": edge["sumo_edge_id"],
            "network_revision": edge["network_revision"],
            "source_osm_way_ids": edge["source_osm_way_ids"],
        },
        "parameters": {"speed_limit_mps": 5.0},
    },
    "sim/.cache/my-paired-run",
    vehicle_count=20,
    seed=4092,
    duration_seconds=180,
    execution_timeout_seconds=60,
)
```

An abbreviated result structure (numeric fields are generated by execution, not defaults):

```json
{
  "schema_version": "arteria.sumo-comparison.v1",
  "status": "completed",
  "study_area": {"city_id": "<source city>", "area_id": "<source area>", "boundary_source": "<source>"},
  "source_area_verification": {"status": "verified", "method": "source_geometry_sha256"},
  "network_revision": "<sha256>",
  "baseline_run_id": "sumo_run_<deterministic id>",
  "scenario_run_id": "sumo_run_<deterministic id>",
  "intervention_validation": {"status": "validated_for_graph_edit", "physical_feasibility": "unknown"},
  "seed": 4092,
  "demand": {"synthetic": true, "requested_vehicle_count": 20, "generated_vehicle_count": "<SUMO preparation result>", "sha256": "<demand sha256>"},
  "route_selection_policy": "<deterministic OSM shortest-path demand reused in both runs>",
  "simulation_configuration": {"duration_seconds": 180.0, "step_length_seconds": 1.0},
  "simulator": {"name": "Eclipse SUMO", "version": "<installed version>"},
  "baseline": {"status": "completed", "finished_vehicle_count": "<TripInfo count>", "measurements": "<TripInfo-derived values>"},
  "scenario": {"status": "completed", "finished_vehicle_count": "<TripInfo count>", "measurements": "<TripInfo-derived values>"},
  "comparison": {"status": "comparable_pairs_available", "paired_vehicle_count": "<actual paired count>", "metrics": "<paired differences>"},
  "warnings": [],
  "limitations": ["Synthetic demand; uncalibrated SUMO output; feasibility unknown."],
  "outputs": {"baseline_network_geojson": "baseline/iasi.network.geojson", "scenario_network_geojson": "scenario/iasi.network.geojson", "changed_edge_geojson": "scenario/iasi.changed-edge.geojson"}
}
```

For `completed`, fetch paths relative to the supplied `output_dir`:

- `outputs.baseline_network_geojson`: converted OSM directed road edges.
- `outputs.scenario_network_geojson`: converted scenario network edges.
- `outputs.changed_edge_geojson`: target edge only, when available.
- `outputs.baseline_simulation_geojson` / `outputs.scenario_simulation_geojson`: finished vehicles with SUMO-reported edge-sequence geometry when valid.
- Each run's `outputs.tripinfo` and `outputs.vehroute`: raw SUMO evidence for audit.

`run_real_area_simulation` remains a baseline-only API and now exports route geometry from `vehroute-output`. Its `iasi.simulation.geojson` layer is the actual SUMO-reported edge route mapped to source OSM geometry, never the planned route list and never GPS. `prepare_sumo_network` alone is preparation, not a completed simulation.

## Pedestrian impact, proposals, and stale evidence

`evaluate_candidates` preserves the existing deterministic shared sample and lexicographic ranking. It adds `shared_sample_outcome_status`, `impact_evidence_status`, and `geographic_evidence_status`. `candidate_no_shared_sample_benefit` and `candidate_local_diagnostic_improvement_only` are distinct; targeted-only improvement never becomes shared ranking benefit. Existing numeric fields keep their original sample meaning.

Candidate evaluation includes `study_area_geometry_sha256`. `validate_proposal` rejects a candidate evaluation whose area ID or canonical source polygon does not match the supplied `OSMData`, or whose source identity/retrieval timestamp conflicts. Existing candidate identity, exact intervention, unit, citation, run ID, finite-number, observed-metric, cost, and feasibility checks remain in force.

`build_proposal_context` remains size-bounded (default 65,536 serialized bytes) and now includes `sim_engine_version`, method-version identifiers, the OSM category schema, optional paired SUMO capability, shared-sample outcome codes, separate targeted diagnostic evidence, and explicit limits. It does not call an LLM or turn candidate options into recommendations.

## Reproducible local CLI

```powershell
python -m sim.mvp_demo --source fixture
python -m sim.mvp_demo --source cache --cache-dir sim/.cache/osm --sumo-baseline
python -m sim.mvp_demo --source area --area-json area.json
python -m sim.mvp_demo --source area --area-json area.json --acquire --feature-categories buildings,schools
```

The CLI defaults to a timestamped ignored directory under `sim/.cache/mvp-demo/` and writes `report.json`, `candidate-evidence.geojson`, and `summary.md`. `fixture` is synthetic and makes no request. `cache` requires an explicit cache directory and never downloads on a miss; area verification is reported. `area` requires an explicit bounded input file; without `--acquire`, it validates the area and produces an unavailable-data report. Only `--acquire` makes an OSM request. Optional SUMO flags require an existing drive graph and do not fetch one.

## Errors and integration guidance

- Invalid selectors, intervention documents, speed values, bounds, and bad run limits raise `ValueError`.
- Invalid study-area geometry raises `AreaValidationError`; total graph acquisition failure raises `OSMDataError`.
- Unsupported/missing driving graphs raise `SumoPreparationError` from direct conversion/evaluation calls.
- SUMO binary absence is a returned `unavailable` status with preparation metadata retained. netconvert/SUMO process timeout, startup failure, nonzero exit, or unreadable TripInfo are returned as explicit paired statuses; no one-sided comparison is generated.
- Output overwrite attempts raise `FileExistsError`.

Backend should expose these typed functions through its own authorization, request validation, persistence, run IDs, and HTTP error mapping; it must not treat local file paths as public URLs. Frontend should render only returned GeoJSON and actual status fields. Preserve OSM attribution/ODbL, the exact source area, nullable metrics, and all unknown/failure statuses. Do not forward SIM candidate line geometry as evidence of buildability.

## SIM AI Planning Contract v1 — implemented on feature branch

This contract is in feat/sim-ai-planning-mvp. It adds Python result generation and validation only; it does not add a provider integration, credentials, backend persistence, HTTP endpoint, or frontend rendering. The backend handoff is appended to ../backend/IMPLEMENTATION_TODO.md; the frontend display handoff is appended to ../frontend/IMPLEMENTATION_TODO.md.

### Problem detection

~~~python
def detect_urban_problems(
    data: OSMData,
    *,
    analysis: Mapping[str, Any] | None = None,
    candidate_evaluation: Any = None,
    paired_sumo_result: Any = None,
    max_problems: int = 12,
    route_pair_sample_count: int = 96,
    detour_ratio_threshold: float = 2.0,
    min_direct_distance_m: float = 75.0,
    min_network_distance_m: float = 150.0,
) -> dict[str, Any]: ...

def problem_locations_geojson(urban_issues: Mapping[str, Any]) -> dict[str, Any]: ...
~~~

The result schema is arteria.urban-issues.v1. Supported localized types are pedestrian_disconnection, excessive_pedestrian_detour, excessive_detour_to_mapped_destination, and weak_access_to_mapped_destination. Feature-layer and crossing coverage uncertainty is reported in coverage_gaps, separately from detected infrastructure problems. Clipping and OSM incompleteness remain explicit limitations. IDs and ordering are stable; the output is bounded to 24 problems. Severity is an explained ordinal rule, not a safety or social-impact score. Route-pair calculations use a deterministic candidate-independent sample. Route geometry is included only when it can be assembled from valid mapped graph edge geometry; component gap geometry is a straight-line location cue and never a proposed road.

Completed paired SUMO evidence, when supplied, appears in simulation_observations only after verification of both completed runs, matching area ID and source geometry hash, finite metrics, and run IDs. Generated demand remains synthetic, and these observations are not pedestrian findings or measured city traffic.

### Solution plan

~~~python
def build_solution_plan(
    data: OSMData,
    analysis: Mapping[str, Any],
    urban_issues: Mapping[str, Any],
    candidate_evaluation: Mapping[str, Any],
    *,
    max_solutions: int = 32,
) -> dict[str, Any]: ...
~~~

The planner reuses prepare_candidate_options and validate_proposal_set. It outputs supported_evaluated, supported_not_yet_evaluated, concept_only_not_evaluated, unsupported, or rejected records. Candidate geometry, exact graph intervention, shared sample impact and screening are copied from SIM; candidate-local diagnostics remain separately labeled and do not affect common-sample ranking. A candidate must link to a detected problem to become a supported proposal. Conceptual field/data reviews cite real evidence and contain no executable geometry, intervention or numerical benefit. Construction, safety, ownership and legal feasibility stay unknown.

### AI packet and response

~~~python
def build_ai_planning_packet(data, analysis, urban_issues, candidate_evaluation, solution_plan, *, max_packet_bytes=65_536) -> dict: ...
def validate_ai_planning_response(response, packet) -> dict: ...
def run_ai_planning(packet, call_model, *, timeout_seconds=20.0) -> dict: ...
~~~

build_ai_planning_packet wraps the existing build_proposal_context, preserves source attribution and ODbL metadata, and uses deterministic bounds. Its integrity.sha256 covers the canonical packet body; the checksum detects stale/changed payloads but is not an authenticity signature. The default canonical packet ceiling is 65,536 UTF-8 bytes; model response JSON is capped at 16,384 bytes.

AI_SYSTEM_PROMPT and AI_OUTPUT_SCHEMA define provider-neutral structured output. The model may reference only the supplied IDs. It cannot return authoritative geometry, numeric metrics, costs, citations, action documents, SUMO run IDs, or feasibility claims. validate_ai_planning_response rejects wrong area or packet hash, non-finite/malformed/oversized JSON, unknown or mismatched IDs, unrelated evidence, contradictions, and extra authoritative fields. Invalid individual recommendations are rejected while unrelated valid entries survive; an invalid packet or area/hash mismatch rejects the entire response. Accepted entries have authoritative_sim_solution attached from the stored SIM packet, including the corresponding candidate geometry, intervention, shared impact and separate targeted diagnostics.

run_ai_planning accepts None or an injected synchronous call_model keyword callback receiving packet, system_prompt, output_schema, and timeout_seconds. It returns explicit provider_unavailable, timeout, provider_error, invalid_response, completed_with_rejections, or completed status. The callback should also configure its own provider-side timeout; Python cannot forcibly stop a provider request that ignores its deadline. SIM makes no cloud call by itself.

### Reproducible planning demo

~~~powershell
python -m sim.mvp_demo --source fixture --planning --output-dir sim/.cache/mvp-demo/ai-planning-fixture
python -m sim.mvp_demo --source area --area-json area.json --acquire --planning --feature-categories schools,healthcare,services,public_transport --output-dir sim/.cache/mvp-demo/ai-planning-area
~~~

The fixture is synthetic and explicitly labeled; it makes no network request and uses a deterministic mock provider only to exercise the response contract. It does not claim OSM observations or live AI. Planning mode writes analysis.json, urban_problems.json, solutions.json, ai_evidence_packet.json, ai_input_example.json, ai_output_schema.json, candidate_evidence.geojson, problem_locations.geojson, summary.md, and validation_report.json under ignored local output. Real area mode requires explicit --acquire; a failure remains a failure and is never replaced with the fixture.

The current backend spatial_worker.py discards OSMData when its worker exits and stores only analysis/candidate/evidence JSON. Backend must add problem/solution/AI packet storage during study creation and use that immutable packet for the later model call. The proposed endpoint and storage steps are documented in the backend handoff; neither is implemented yet.

Useful consumer tests include: all eight category filters and statuses; wrong/missing-hash category caches; unavailable native binaries; stale edge revisions; unchanged source graphs and reused demand; one-side failure/timeout with null comparison; partial/unreported trips; changed or invalid route exclusion; GeoJSON CRS and geometry validation; source-area mismatch; zero shared-sample effect versus local-only diagnostics; non-finite or fabricated proposal fields; and fixture/cache/area demo source-mode behavior.
