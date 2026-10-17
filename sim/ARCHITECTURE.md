# SIM Architecture

**Scope:** the version-controlled Python simulation component in this directory. See [README.md](README.md) for usage, [STATUS.md](STATUS.md) for recorded verification and outstanding work, and [AGENTS.md](AGENTS.md) for contributor instructions.

## Component overview

SIM is a Python library for bounded analysis of mapped geographic data. It validates an area, acquires and caches OpenStreetMap (OSM) networks/features, normalizes graphs into metric lengths, calculates connectivity and node-based walking/cycling access, derives deterministic screening issues, and serializes JSON-ready results with GeoJSON layers. It can evaluate a hypothetical pedestrian-network edit against a copied baseline graph. A separate optional utility discovers SUMO and can run a tiny synthetic TraCI smoke scenario.

| Responsibility | Existing behavior |
|---|---|
| Geographic acquisition | Bounded OSMnx network and feature requests for walk, bike, and drive; local GraphML/GeoJSON and HTTP caches; per-mode availability and warnings. |
| Graph construction | OSMnx street graphs retain disconnected components and boundary connectors. Normalization exposes metre edge lengths and WGS84 node coordinates. |
| Connectivity/access | NetworkX components and shortest paths; walk/bike access to mapped features; graph-node counts, not resident counts. |
| Issue screening | Deterministic disconnected-component, poor-access, and detour candidates with evidence, units, coverage, and uncertainty. |
| Virtual interventions | Add or toggle a hypothetical pedestrian connection on an isolated graph copy; recalculate a route Before/After. |
| Geographic output | JSON-ready dictionaries, EPSG:4326 GeoJSON layers, source metadata, availability, and warnings. |
| SUMO support | Portable binary discovery and optional one-step synthetic SUMO/TraCI smoke check, separate from analysis. |

SIM does not render the frontend map, expose backend HTTP routes, invoke cloud AI, observe real traffic, estimate congestion, or verify intervention safety, ownership, legal approval, accessibility compliance, or construction feasibility. The backend currently implements only its liveness route and does not import SIM. Its draft contract is [../docs/API_CONTRACT.md](../docs/API_CONTRACT.md). An optional browser preview may exist under ignored `sim/.cache/local_demo/`; it is not tracked or a production engine feature.

## Tracked directory tree

There are no tracked source subdirectories under `sim/`. This tree includes all tracked files after this documentation milestone. `.cache/` and `__pycache__/` are generated and ignored.

~~~text
sim/
├── .gitignore
├── AGENTS.md
├── ARCHITECTURE.md
├── README.md
├── STATUS.md
├── __init__.py
├── analysis.py
├── geo.py
├── scenario.py
├── smoke_test.py
├── sumo_support.py
└── test_engine.py
~~~

## Module relationships

Solid arrows are imports present in source. The backend is only a potential in-process consumer. SUMO helpers are independent of analysis and scenario modules.

~~~mermaid
flowchart TD
    API["sim package API (__init__.py)"] --> GEO["geo.py"]
    API --> ANALYSIS["analysis.py"]
    API --> SCENARIO["scenario.py"]
    ANALYSIS --> GEO
    SCENARIO --> ANALYSIS
    SCENARIO --> GEO
    TESTS["test_engine.py"] --> GEO
    TESTS --> ANALYSIS
    TESTS --> SCENARIO
    SMOKE["smoke_test.py"] --> STACK["GeoPandas · NetworkX · OSMnx · Shapely"]
    GEO --> STACK
    ANALYSIS --> STACK
    SCENARIO --> STACK
    SUMO["sumo_support.py CLI"] --> SUMO_BIN["SUMO · netconvert · TraCI"]
~~~

- `sim.__init__` re-exports the package API.
- `geo` owns area validation, acquisition, caching, feature classification, and geographic serialization.
- `analysis` consumes `OSMData` and `StudyArea` from `geo`; it owns graph preparation, metrics, access analysis, and issue output.
- `scenario` consumes the geo types/serializer and imports graph/route helpers from `analysis`, including private `_nearest_nodes`.
- `test_engine.py` uses in-memory fixtures, temporary caches, and OSMnx mocks. SUMO support has a separate optional tool path.

## Data flow

### Geographic analysis

1. Input a Shapely Polygon/MultiPolygon, GeoJSON geometry/Feature, CRS-declared GeoDataFrame, or `[west, south, east, north]` bbox.
2. `normalize_area` checks type, topology, WGS84 coordinate bounds, and default maximums (5 km² and 5 km in either extent dimension). It chooses a local UTM working CRS and returns `StudyArea`.
3. `acquire_osm_data` requests each distinct requested mode serially. A usable graph has nodes and edges. Successful modes survive other mode failures; feature-query failures remain warnings and unknown availability. If every requested graph fails, it raises `OSMDataError`.
4. OSM feature frames are normalized to EPSG:4326. Graph analysis creates projected copies with metric `length_m`.
5. Available modes receive connectivity metrics. Walking and cycling additionally receive access and detour analysis for mapped schools, healthcare, services, public transport, and green space. Driving does not produce pedestrian-access claims.
6. Deterministic rules turn disconnections, access-threshold misses, and detour exceedances into issue candidates.
7. `analyze_snapshot` returns indicators, issue objects and GeoJSON, heatmaps, availability, clipped feature/network layers, metrics, provenance, uncertainty, and warnings.

The default cache is `sim/.cache/osm/`, including an `http/` subdirectory. Application snapshots are keyed by normalized area geometry, configured feature tags, and OSMnx version. There is no application cache expiry; `force_refresh=True` requests fresh source data. OSMnx settings changed during acquisition are locked and restored. Cache problems become warnings if analysis can continue. OSMnx graphs are NetworkX graph objects (the polygon acquisition path normally yields a directed multigraph) with the source CRS in graph metadata and metre routing weights normalized as `length_m`.

### Intervention evaluation

1. Reuse an acquired `OSMData` snapshot as baseline.
2. Validate intervention coordinates/type. Coordinates are EPSG:4326 longitude/latitude; endpoints and the straight link must lie inside the area and snap to walking nodes (50 m default, at most 250 m).
3. Add/remove the modeled edge on a projected graph copy. A new connection must be over 0 m and at most 1,000 m.
4. Snap route origin/destination to the baseline graph, calculate weighted routes before and after, and serialize route geometries as WGS84 GeoJSON.
5. Return route statuses/distances, constant-speed estimates, comparison outcome, intervention details, snap distances, provenance, and feasibility warnings. The source walk graph is not mutated.

### SUMO position

`sim.sumo_support` does not consume OSM graphs. The optional smoke path writes temporary synthetic node/edge/route XML, calls `netconvert`, starts SUMO via TraCI, advances one step, then removes temporary files. It checks a small artificial network only. Real-area OSM-to-SUMO conversion, demand modeling, calibration, and traffic-impact evaluation are not implemented.

## Data and result formats

### Inputs and coordinate systems

- Bboxes use `[west, south, east, north]`; GeoJSON positions use `[longitude, latitude]`. GeoJSON and bbox coordinates are EPSG:4326.
- A GeoDataFrame must declare a CRS and is transformed to EPSG:4326. GeoJSON/bbox declaring another CRS is rejected. Shapely geometry inputs are treated as WGS84.
- An area dict may set `city_id`, `area_id`, `boundary_source`, `crs`, and `bbox`, `boundary`, or GeoJSON geometry/Feature. Defaults are `iasi-ro`, `user-selected-area`, and `user_selected`; bbox input is marked `bounded_bbox`.
- `StudyArea.working_crs` is selected using local UTM estimation. Distances and area are metric; travel speeds are m/s, thresholds minutes, and ratios unitless. Exported geometry is WGS84.
- Geometry must be non-empty, valid Polygon/MultiPolygon within coordinate bounds. Limits can be explicitly overridden for controlled analyses.

### Graphs and source metadata

`OSMData` contains `area: StudyArea`; successful `walk`/`bike`/`drive` graphs; GeoDataFrames for roads, walking and cycling infrastructure, crossings, buildings, schools, healthcare, services, public transport, parking, and green space; `layer_availability`; source/cache `metadata`; and `warnings`.

Acquired graphs carry OSM source, mode, retrieval time, and area key. Metadata records requested modes, source label, WGS84 extent, working CRS, tags, per-mode/feature timestamps, cache hits, and limitations. Feature IDs/tags are retained. Retrieved timestamps describe the query snapshot, not per-feature edit times.

### Analysis output

`analyze_snapshot` and `analyze_area` return a dictionary serializable with `json.dumps(..., allow_nan=False)`. Stable top-level keys:

- `analysis_id`, `area` (boundary, source, CRS), `created_at`
- `indicators`: `id`, `label`, `value`, `unit`, `status`, `provenance`, `uncertainty`
- `issues`: `id`, `type`, `severity`, `description`, WGS84 `geometry`, `metrics`, `evidence`, `data_coverage`, `provenance`, `uncertainty`
- `issue_geojson`, `heatmaps`, `layers`, and `networks` as GeoJSON FeatureCollections (heatmaps keyed by mode/category)
- `layer_availability`, `network_metrics`, `provenance`, `uncertainty`, `warnings`

`value: null` with `status: "unknown"` means evidence is unavailable. `no_features_returned` means the query returned no matching tagged features, not real-world absence. Unknown/failed queries remain `unknown`. Access counts refer to mapped graph nodes, never residents. Heatmaps are capped at 500 points per mode/category and issue geometries at 250 points; indicator counts use all relevant nodes.

The `population_accessibility` indicator is always emitted with a null value and unknown status because this snapshot has no population/address demand dataset.

`route_between` returns `status`, `path`, `distance_m`, `direct_distance_m`, and `detour_ratio`. An unreachable pair returns `status: "unreachable"` and null distances where not computable; unknown node IDs raise `RouteError`.

Scenario output has `scenario_id`, `area_id`, `mode`, `baseline`, `scenario`, `comparison`, `interventions`, `snap`, `provenance`, and `warnings`. Route payloads contain status, network/direct distances, detour ratio, estimated seconds, path node IDs, and a GeoJSON geometry or null. Comparison outcomes are improved, regressed, unchanged, became_reachable, became_unreachable, or unreachable_in_both. `improvement_percent` is intentionally null.

### Errors and unavailable data

| Condition | Behavior |
|---|---|
| Invalid or over-limit area | `AreaValidationError`, a `ValueError`. |
| Empty/string/unsupported modes | `ValueError`. |
| All requested networks fail or are unusable | `OSMDataError`; feature acquisition is skipped. |
| One mode fails while others succeed | Successful graphs remain; failed mode has `request_failed` availability and warning. |
| OSM feature request fails | Networks remain; feature layers stay unknown and a warning is added. |
| Missing features or no feature-to-network snaps | Access/detour outputs are null/unknown, never zero. |
| Invalid analysis thresholds/speeds | `ValueError` from `analyze_snapshot`. |
| Unknown route node or unusable edge lengths | `RouteError`; no path is reported as unreachable only when valid nodes exist but no path connects them. |
| Invalid scenario, no walking baseline, far/out-of-area endpoints, or too-long link | `InterventionError`, a `ValueError`. |
| Cache read/write problem | Warning when remaining acquisition can proceed. |

## File-by-file inventory

This inventory covers all 12 tracked files in `sim/` after this documentation update. There are no tracked nested source directories. Test file references outside this directory are linked where useful.

### `.gitignore`

- **Purpose:** keeps generated OSM cache, Python bytecode, and compiled Python files out of Git using `.cache/`, `__pycache__/`, and `*.py[cod]` patterns.
- **Interfaces/parameters/results:** Git ignore rules only; no Python API or return value.
- **Dependencies/callers/side effects:** Git reads it during status/add operations; it has no runtime effects.
- **Coverage/assumptions/limits:** no dedicated test. It does not ignore all possible temporary files; add patterns only for generated artifacts owned by this component.

### `AGENTS.md`

- **Purpose:** operational instructions for future SIM contributors and coding agents.
- **Interfaces/parameters/results:** documentation only; no callable API.
- **Dependencies/callers/side effects:** read by agents before making component changes; links to this architecture, README, and STATUS.
- **Coverage/assumptions/limits:** no automated tests. It delegates technical signatures and result details to source-linked docs and must be kept aligned with repository-level instructions.

### `ARCHITECTURE.md`

- **Purpose:** authoritative source map, data-flow description, API contract notes, and module-by-module technical reference for this directory.
- **Interfaces/parameters/results:** documents the APIs; defines no runtime interface.
- **Dependencies/callers/side effects:** links to source, tests, CI scripts, the root draft API contract, and local-only demo notes.
- **Coverage/assumptions/limits:** manually validated against the current branch. Update it when source behavior changes; it is not a substitute for inspecting implementation.

### `README.md`

- **Purpose:** setup/use guide and user-facing Python examples for SIM.
- **Interfaces/parameters/results:** its public API example covers acquisition and scenario use; see the linked architecture for exact API and output contracts.
- **Dependencies/callers/side effects:** read by developers integrating or running SIM; no runtime imports or side effects.
- **Coverage/assumptions/limits:** usage prose is not executable coverage. OSM acquisition examples may make live network requests when no local snapshot is available. Keep tests and platform status synchronized with the actual scripts and workflow.

### `STATUS.md`

- **Purpose:** records implemented capabilities, verification evidence, limitations, and outstanding work.
- **Interfaces/parameters/results:** documentation only.
- **Dependencies/callers/side effects:** read by developers and linked from README, AGENTS, and this document.
- **Coverage/assumptions/limits:** dated verification can become stale; CI run results are historical evidence, not a guarantee for later commits. Update after meaningful source verification.

### `__init__.py`

- **Purpose:** provides the stable package-level import surface and keeps callers from needing module-internal paths.
- **Public exports:** `AreaValidationError`, `OSMDataError`, and `InterventionError`; `StudyArea` and `OSMData`; `normalize_area`, `acquire_osm_data`, `feature_collection`, `geojson_geometry`, `normalize_graph`, `project_graph`, `network_metrics`, `route_between`, `analyze_snapshot`, `analyze_area`, `evaluate_scenario`, and `evaluate_pedestrian_connection`. The `__all__` list is the explicit export list. `RouteError` is defined in `sim.analysis` but is not re-exported at package root.
- **Parameters/results/errors:** no functions are defined here; imported callables retain their module signatures, return values, and exceptions documented below.
- **Dependencies/callers/side effects:** re-exports from `geo`, `analysis`, and `scenario`. README examples and tests import this surface. Importing it imports the geospatial stack; it does not acquire data or write files.
- **Assumptions/limits/tests:** repository root/package must be importable. Package import paths are exercised by `sim/test_engine.py` and `tests/test_spatial_smoke.py`; there is no separate __init__ test.

### `geo.py`

- **Purpose:** validates areas, acquires OSM networks/features, classifies feature layers, manages local caches, and serializes WGS84 geometry.
- **Public types/API:** `AreaValidationError(ValueError)`, `OSMDataError(RuntimeError)`, frozen `StudyArea(polygon, city_id, area_id, boundary_source, working_crs)`, and `OSMData(area, graphs, layers, layer_availability, metadata, warnings)`. Exact callable signatures: `normalize_area(area: Any, *, max_area_km2: float = 5.0, max_extent_km: float = 5.0) -> StudyArea`; `acquire_osm_data(area: Any, *, modes: Iterable[str] = SUPPORTED_MODES, cache_dir: str | Path | None = None, use_cache: bool = True, force_refresh: bool = False, overpass_url: str | None = None, max_area_km2: float = 5.0, max_extent_km: float = 5.0) -> OSMData`; `feature_collection(frame: gpd.GeoDataFrame) -> dict[str, Any]`; `geojson_geometry(geometry: BaseGeometry, crs: str | CRS) -> dict[str, Any]`.
- **Important parameters/results:** supported modes are walk, bike, drive; mode strings are rejected as iterables, empty/unsupported selections raise `ValueError`, and duplicates are removed while preserving order. Cache path defaults to `sim/.cache/osm`. Each successful graph is stored under its mode; layers and their availability are separate mappings. Acquisition may return partial graph success.
- **Errors/dependencies/callers:** invalid areas raise `AreaValidationError`; all-mode failure raises `OSMDataError`; mode argument errors raise `ValueError`. Uses OSMnx, GeoPandas, pyproj, Shapely, JSON/hashlib/pathlib. Called by `analyze_area`; backend consumers can call it through the package API, but there is no current backend import. Serializers are used by analysis and scenario output.
- **Helpers/side effects/assumptions:** `_get_input_geometry` parses geometry/metadata; `_area_key` hashes geometry/tags/library version; `_feature_frame`, `_truthy_tag`, `_tag`, `_tag_in`, and `_layer_masks` normalize/classify OSM records; `_cache_frame`, `_load_cached_frame`, `_network_metadata_path`, and `_is_usable_network` manage/validate cache artifacts; `_json_default` handles provider timestamp/numpy values. Acquisition creates cache directories and reads/writes GraphML, GeoJSON and JSON metadata; it also changes OSMnx global settings under a lock and restores them. Feature and network timestamps are snapshot-level. OSM coverage is incomplete and cached snapshots have no application TTL. Exporting a GeoDataFrame without a declared CRS raises `ValueError`.
- **Tests/limits/integration:** covered by `test_area_validation_accepts_bounded_polygon_and_bbox`, cache reuse, independent/partial/failed mode tests, unusable graph and invalid mode tests, feature failure handling, and GeoJSON serialization tests in `test_engine.py`. No OSM result is evidence of complete coverage; call policy-compliant endpoints and retain warnings/provenance.

### `analysis.py`

- **Purpose:** normalizes/project graphs, calculates graph metrics/routes, derives walk/bike access indicators and issue candidates, and assembles the analysis response.
- **Public API/signatures:** `RouteError(ValueError)`; `normalize_graph(graph: nx.Graph) -> nx.Graph`; `project_graph(graph: nx.Graph, working_crs: str | CRS | None = None) -> nx.Graph`; `network_metrics(graph: nx.Graph, mode: str) -> dict[str, Any]`; `route_between(graph: nx.Graph, origin: Any, destination: Any) -> dict[str, Any]`; `analyze_snapshot(data: OSMData, *, access_threshold_minutes: float = 15.0, walking_speed_mps: float = 1.3, cycling_speed_mps: float = 4.5, poi_snap_tolerance_m: float = 150.0, detour_ratio_threshold: float = 2.0) -> dict[str, Any]`; `analyze_area(area: Any, **options: Any) -> dict[str, Any]`.
- **Important parameters/results:** `analyze_area` separates acquisition options (modes/cache/limits/Overpass URL) from analysis options. `analyze_snapshot` only emits metrics for graphs present. The result schema and caps are listed above. `route_between` weights by `length_m`, returns reachable/unreachable status and distance/direct-distance/detour fields, and raises `RouteError` for unknown nodes or unusable lengths.
- **Errors/dependencies/callers:** invalid/non-finite thresholds and speeds raise `ValueError`. Uses GeoPandas, NetworkX, OSMnx, pyproj, Shapely STRtree, and `geo` types/serializers. `analyze_area` calls acquisition; `scenario` reuses `project_graph`, `route_between`, and private `_nearest_nodes`.
- **Helpers/side effects/assumptions:** `_edge_length` and `_node_sort_key` normalize route inputs; `_nearest_nodes`, `_feature_target_nodes`, and `_distances_to_targets` implement metric snapping and multi-source Dijkstra; nearest-node lookup uses Shapely STRtree rather than OSMnx's SciPy-dependent helper; `_timestamp`, `_provenance`, `_uncertainty`, `_indicator`, `_stable_issue_id`, and `_issue` build explainable outputs; `_network_layer` and `_nodes_inside_area` clip/select geometry. Uses fixed default speeds (1.3/4.5 m/s) and 15-minute access threshold; no population weighting or traffic model. Returns results without writing files; it makes no network requests when given an existing snapshot.
- **Tests/limits/integration:** covered by route/connectivity, deterministic accessibility, missing-POI, drive-only, geometry ordering, JSON validity, and finite-parameter tests in `test_engine.py`. Access and detour analysis is limited to mapped features and graph nodes; sample geometries and heatmaps are capped.

### `scenario.py`

- **Purpose:** validates a narrow set of hypothetical pedestrian-link edits and compares a single route on baseline and scenario graph copies.
- **Public API/signatures:** `evaluate_scenario(data: OSMData, interventions: Iterable[dict[str, Any]], *, origin: Any, destination: Any, max_snap_distance_m: float = 50.0, walking_speed_mps: float = 1.3) -> dict[str, Any]`; `evaluate_pedestrian_connection(data: OSMData, start: Any, end: Any, *, origin: Any | None = None, destination: Any | None = None, max_snap_distance_m: float = 50.0, walking_speed_mps: float = 1.3) -> dict[str, Any]`. `InterventionError(ValueError)` is raised for unsupported/invalid scenario inputs.
- **Important parameters/results:** inputs are Point, GeoJSON Point or [lon, lat]. Supported intervention types are `add_pedestrian_connection` and `set_connection_enabled`. Snap limit must be positive and no greater than 250 m; virtual links are at most 1,000 m. Results include route payloads, comparison, intervention IDs/status, snap distances, provenance, and warnings.
- **Errors/dependencies/callers:** requires `data.graphs["walk"]`, valid in-area points near the walk network, finite positive speed, and supported intervention payloads; otherwise raises `InterventionError`. Uses NetworkX, GeoPandas, OSMnx, Shapely, and `geo` serialization plus helpers from `analysis`. Exposed by package `__init__` and used in the README/demo exporter.
- **Helpers/side effects/assumptions:** `_coordinate_point` and `_snap_to_graph` validate/snap coordinates; `_connection_id`, `_has_connection`, `_remove_connection`, `_add_connection`, and `_apply_interventions` implement stable virtual edges and toggles; `_route_geometry` and `_route_result` create route payloads. It projects/copies the graph before editing and does not mutate source baseline data. Assumes straight-line link length and constant walking speed; does not check crossings, slope, rights, legal approval, safety, or feasibility.
- **Tests/limits/integration:** covered by baseline immutability, improvement/regression/reachability changes, disable/enable, endpoint/snap/length validation, deterministic output, and finite parameter tests in `test_engine.py`. It evaluates one origin/destination pair and does not calculate a network-wide impact or percent improvement.

### `smoke_test.py`

- **Purpose:** dependency/import and deterministic graph smoke check for a tiny in-memory NetworkX graph.
- **Public functions:** `run() -> dict[str, str | int | float]` imports/reports GeoPandas, NetworkX, OSMnx, and Shapely versions and asserts shortest path `a -> b -> c` is 200 m. `main() -> None` prints the result.
- **Errors/dependencies/callers/side effects:** assertion failure raises `AssertionError`; missing dependencies fail import. Called directly with `python -m sim.smoke_test` and by `tests/test_spatial_smoke.py`. No network, file, OSM cache, or SUMO side effects.
- **Assumptions/limits:** checks imports and basic NetworkX path behavior only; it does not validate OSM acquisition or the full analysis engine.

### `sumo_support.py`

- **Purpose:** discovers optional SUMO executables and reports or runs a temporary synthetic TraCI smoke scenario.
- **Public API:** frozen `SumoInstallation(sumo: Path | None, netconvert: Path | None, home: Path | None)`; `discover_sumo(environ: dict[str, str] | None = None, search_path: str | None = None) -> SumoInstallation`; `run_sumo_smoke(installation: SumoInstallation) -> str`; `report_status(run_smoke: bool = False) -> int`; `main() -> int`.
- **Important parameters/results:** discovery prefers explicit `SUMO_HOME` roots, then PATH; Windows checks `.exe` names. `environ` and `search_path` allow deterministic discovery tests. `report_status(run_smoke: bool = False) -> int` prints platform, executables, home, and Python package versions. CLI flag `--smoke` requests execution if binaries/dependencies are present.
- **Errors/dependencies/callers/side effects:** `run_sumo_smoke` raises `RuntimeError` for missing prerequisites; subprocess and TraCI errors propagate to the caller. Its subprocesses have timeouts, and `report_status` catches failures, prints them, and returns 1. Uses stdlib process/platform/tempfile tools and imports `traci` only when running. Writes temporary XML/network files under a temporary directory, which is removed on exit. Called from CI/setup scripts and standalone CLI; analysis/scenario do not call it.
- **Helpers/tests/limits:** `_executable_names` and `_find_under` locate platform binary names; `_python_package_version` checks Python bindings; `_write_synthetic_scenario` creates one synthetic vehicle network. `tests/test_sumo_support.py` covers discovery; CI calls `python -m sim.sumo_support --smoke`. If SUMO is missing, the smoke is skipped with exit code 0. It does not convert real OSM networks or provide traffic indicators.

### `test_engine.py`

- **Purpose:** offline regression suite for geo, analysis, serialization, cache behavior, mode failures, and scenarios.
- **Important helpers:** `_fixture_data`, `_network_graph`, `_install_osm_mocks`, `_snapshot_with_graphs`, and `local_cache_dir` build deterministic graph/feature inputs, patch OSMnx, or create temporary ignored cache folders.
- **Behavior covered:** area validation; route metrics; deterministic analysis and absent POI semantics; baseline immutability; GeoJSON properties/timestamps; application cache; independent walk/drive/bike requests, deduplication and partial/all failures; unusable graphs/invalid modes; drive-only analysis; projection/order and finite JSON; scenario determinism, regressions, reachability, snap/length constraints, and non-finite parameters.
- **Dependencies/callers/side effects:** pytest, pandas, GeoPandas, NetworkX, Shapely and SIM modules. Collected by the root check scripts with `tests`. OSM requests are mocked; temporary files are removed by pytest/tempfile. The file does not expose production APIs.
- **Limits/integration:** fixtures are synthetic and narrow; they do not establish current OSM coverage, SUMO behavior, frontend rendering, or backend endpoint integration. The complete collected suite is run by `uv run --locked pytest -q tests sim/test_engine.py`.

### `README.md`

- **Purpose:** installation/use, public API examples, geographic inputs, cache and provenance, layer/issue behavior, scenario use, testing, and current SUMO distinction.
- **Cross-links:** points to this architecture, STATUS and AGENTS.
- **Validation/limits:** Markdown and example signatures were checked against current source. Acquisition examples can contact Overpass if cache misses; no documentation test executes them automatically.

### `STATUS.md`

- **Purpose:** dated evidence of implemented capabilities, CI/local verification, known limitations, and backend readiness.
- **Cross-links:** points to architecture, README, and AGENTS.
- **Validation/limits:** verification claims refer to their recorded commits/runs; they are historical. Update results after new tests/CI, not from inference.

### `AGENTS.md`

- **Purpose:** concise day-to-day rules for component agents: ownership, runtime, platforms, public entry points, geographic evidence, cache, tests, docs, and Git safety.
- **Cross-links:** points to architecture, README and STATUS.
- **Validation/limits:** operational guidance only, no automated test; repository-level instructions remain authoritative.

### `ARCHITECTURE.md`

- **Purpose:** this authoritative component architecture and integration reference.
- **Cross-links:** source modules, tests, README, STATUS, AGENTS, CI/scripts, backend contract, and ignored demo note.
- **Validation/limits:** source behavior and links must be rechecked when APIs or repository structure change; this file is not runtime code.


## Integration Contract for Backend Agents

The supported boundary is the importable Python package, not an HTTP endpoint. The repository root must be on `sys.path` (for example, run from the repository root). No backend module currently imports SIM.

~~~python
from sim import (
    AreaValidationError,
    InterventionError,
    OSMDataError,
    acquire_osm_data,
    analyze_snapshot,
    evaluate_pedestrian_connection,
    normalize_area,
)

area_input = {
    "city_id": "iasi-ro",
    "area_id": "iasi-example-area",
    "bbox": [27.5755, 47.1610, 27.5825, 47.1655],
    "crs": "EPSG:4326",
    "boundary_source": "user_selected",
}

try:
    validated_area = normalize_area(area_input)
    snapshot = acquire_osm_data(validated_area, modes=("walk",))
except (AreaValidationError, OSMDataError, ValueError) as exc:
    # Adapt to the backend error schema; do not return raw provider internals.
    raise RuntimeError(f"SIM could not acquire this area: {exc}") from exc

analysis = analyze_snapshot(snapshot)
school_access = next(
    (item for item in analysis["indicators"]
     if item["id"] == "walk_access_schools_within_15_min"),
    None,
)
issues = analysis["issues"]
school_layer = analysis["layers"]["schools"]  # EPSG:4326 GeoJSON FeatureCollection
schools_status = analysis["layer_availability"]["schools"]["status"]

# Choose points inside the area and near mapped walk nodes.
try:
    comparison = evaluate_pedestrian_connection(
        snapshot,
        start=[27.5800, 47.1620],
        end=[27.5810, 47.1630],
    )
except InterventionError as exc:
    comparison = {"status": "unavailable", "message": str(exc)}

before = comparison.get("baseline")
after = comparison.get("scenario")
delta_m = comparison.get("comparison", {}).get("distance_delta_m")
~~~

The coordinate pairs use the correct format; whether they satisfy the 50 m snap rule depends on the acquired graph. Handle `InterventionError` rather than assuming every selected point has a nearby mapped node. Acquisition may use cache or contact OSM/Overpass if no usable local snapshot exists. Requested modes are fetched serially.

Backend responsibilities include HTTP request/response validation and adaptation, stable `baseline_id` assignment, persistence of source snapshots and metadata, authorization, timeouts, and API error mapping. SIM has no baseline store, HTTP endpoint, LLM proposal API, or traffic simulation evaluation mode. The scenario functions return graph-route comparisons only.

The draft [API contract](../docs/API_CONTRACT.md) describes planned `/analyze`, `/propose`, and `/evaluate` routes; current `backend/main.py` only implements `GET /health`. The draft and SIM result schemas differ: SIM returns an indicators array, issues array, dictionary-valued `layer_availability`, and named `layers`/`networks` FeatureCollections. SIM does not persist `baseline_id`, return the draft availability array, generate AI proposals, or populate a `simulation` response. Backend code must map shapes and preserve unknown values, provenance, warnings, units, and uncertainty.

## Testing and verification

- `sim/test_engine.py` uses in-memory graph/GeoDataFrame fixtures, temporary cache directories, and mocked OSMnx requests. Coverage includes validation, metric routing, deterministic access/issues, missing data, independent/partial network acquisition, cache reuse, GeoJSON order, finite JSON, scenario constraints/reachability, and baseline immutability.
- `tests/test_spatial_smoke.py` checks imports and a deterministic 200 m synthetic NetworkX route; no OSM request.
- `tests/test_sumo_support.py` checks portable binary discovery using temporary dummy files; it does not execute SUMO.
- `tests/test_backend.py` checks health, CORS, and that planned routes remain 404; it does not exercise SIM.
- [scripts/check.ps1](../scripts/check.ps1) and [scripts/check.sh](../scripts/check.sh) run `pytest -q tests sim/test_engine.py`, backend health, frontend checks/build, and optional SUMO smoke. Since `pyproject.toml` sets `testpaths = ["tests"]`, bare `pytest -q` omits `sim/test_engine.py`.
- CI is [../.github/workflows/ci.yml](../.github/workflows/ci.yml): Windows x64 (`windows-latest`) and macOS ARM64 (`macos-15`, asserted as `ARM64`/`arm64`). Python is constrained to 3.12. Current workflow does not test macOS Intel.
- [STATUS.md](STATUS.md) records the historical result of 36 pytest cases (31 simulation plus 5 project tests). Check the current PR/workflow before treating historical results as current. SUMO smoke is a separate synthetic executable check, not real-area traffic simulation.

Run the SIM regression suite in an already provisioned environment. The project check scripts use `uv run --locked`; that command may create/sync an environment when none exists. If dependency installation is not authorized, use an existing interpreter directly (for example, `.venv/Scripts/python.exe -m pytest -q tests sim/test_engine.py` on Windows):

~~~sh
uv run --locked pytest -q tests sim/test_engine.py
~~~

Standalone checks: `python -m sim.smoke_test` and, if SUMO/netconvert are available, `python -m sim.sumo_support --smoke`.

## Current capabilities and future work

**Implemented:** bounded validation; cached OSM network/features; walk/bike/drive graph metrics; walking/cycling node access and detour analysis; deterministic issue candidates; WGS84 serialization; isolated pedestrian-link comparison; SUMO discovery and synthetic TraCI smoke support.

**Experimental/local-only:** the ignored browser preview and neighborhood mapping/editor under `sim/.cache/local_demo/`, if present. It is absent from clones and is not a production SIM module. Its local-only notes are in `sim/.cache/local_demo/ARCHITECTURE.md`.

**Planned or absent:** real-area OSM-to-SUMO conversion; traffic demand and calibrated/live/offline simulation; automatic intervention generation; multi-route impact analysis; expanded POI sources; neighborhood-aware engine analysis. These are not implemented.
