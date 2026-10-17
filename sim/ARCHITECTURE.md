# SIM Architecture

**Scope:** the version-controlled Python simulation component in this directory. See [README.md](README.md) for usage, [APPLICATION_INTEGRATION.md](APPLICATION_INTEGRATION.md) for the cross-component handoff, [STATUS.md](STATUS.md) for recorded verification and outstanding work, and [AGENTS.md](AGENTS.md) for contributor instructions.

## Component overview

SIM is a Python library for bounded analysis of mapped geographic data. It validates an area, acquires and caches OpenStreetMap (OSM) networks/features, normalizes graphs into metric lengths, calculates connectivity and node-based walking/cycling access, derives deterministic screening issues, and serializes JSON-ready results with GeoJSON layers. The v2 engine loads sourced neighborhood geometry, discovers hypothetical pedestrian links, and evaluates independent alternatives over a shared deterministic route sample. Proposal context/validation APIs prepare evidence-backed graph options. An optional SUMO utility converts a bounded existing driving graph into plain XML and synthetic routes, and executes only when local binaries are available.

| Responsibility | Existing behavior |
|---|---|
| Geographic acquisition | Bounded OSMnx network and feature requests for walk, bike, and drive; local GraphML/GeoJSON and HTTP caches; per-mode availability and warnings. |
| Graph construction | OSMnx street graphs retain disconnected components and boundary connectors. Normalization exposes metre edge lengths and WGS84 node coordinates. |
| Connectivity/access | NetworkX components and shortest paths; walk/bike access to mapped features; graph-node counts, not resident counts. |
| Issue screening | Deterministic disconnected-component, poor-access, and detour candidates with evidence, units, coverage, and uncertainty. |
| Virtual interventions | Add or toggle a hypothetical pedestrian connection on an isolated graph copy; compare one route or a bounded multi-route sample. |
| Neighborhood geometry | Load a partial sourced OSM place catalog, distinguish polygons from point-only records, validate selected boundaries, and enforce the existing 5 km² / 5 km default limits. |
| Candidate discovery | Search bounded metric spatial neighbors for disconnected components, directed reachability gaps, and excessive detours; screen mapped obstacles and return only supported pedestrian-link edits. |
| Alternative evaluation | Evaluate independent candidates over one shared deterministic graph-node pair sample and rank them with an explicit lexicographic rule. |
| Geographic output | JSON-ready dictionaries, EPSG:4326 GeoJSON layers, source metadata, availability, and warnings. |
| SUMO support | Portable binary discovery, bounded OSM drive-graph conversion inputs, deterministic synthetic routes, and optional headless execution; separate from pedestrian graph analysis. |

SIM does not render the frontend map, expose backend HTTP routes, invoke cloud AI, observe real traffic, estimate congestion, or verify intervention safety, ownership, legal approval, accessibility compliance, or construction feasibility. The backend currently implements only its liveness route and does not import SIM. Its draft contract is [../docs/API_CONTRACT.md](../docs/API_CONTRACT.md). An optional browser preview may exist under ignored `sim/.cache/local_demo/`; it is not tracked or a production engine feature.

## Tracked directory tree

There are no tracked source subdirectories under `sim/`. The tree includes the SIM source and the small separately licensed neighborhood catalog. `.cache/` and `__pycache__/` are generated and ignored.

~~~text
sim/
├── .gitignore
├── AGENTS.md
├── ARCHITECTURE.md
├── NEIGHBORHOODS_LICENSE.md
├── README.md
├── STATUS.md
├── __init__.py
├── analysis.py
├── candidates.py
├── demo.py
├── geo.py
├── impact.py
├── iasi-neighborhoods.geojson
├── neighborhoods.py
├── scenario.py
├── proposal_catalog.py
├── proposal_context.py
├── proposal_validation.py
├── proposals.py
├── proposal_demo.py
├── smoke_test.py
├── sumo_engine.py
├── sumo_support.py
└── test_engine.py
~~~

## Module relationships

Solid arrows are imports present in source. The backend is only a potential in-process consumer. The SUMO engine consumes a caller-supplied OSM driving graph and does not modify pedestrian analysis or scenario graphs.

~~~mermaid
flowchart TD
    API["sim package API (__init__.py)"] --> GEO["geo.py"]
    API --> ANALYSIS["analysis.py"]
    API --> NEIGHBORHOODS["neighborhoods.py + iasi-neighborhoods.geojson"]
    API --> CANDIDATES["candidates.py"]
    API --> IMPACT["impact.py"]
    API --> SCENARIO["scenario.py"]
    ANALYSIS --> GEO
    CANDIDATES --> ANALYSIS
    CANDIDATES --> SCENARIO
    IMPACT --> ANALYSIS
    IMPACT --> SCENARIO
    SCENARIO --> ANALYSIS
    SCENARIO --> GEO
    DEMO["demo.py"] --> ANALYSIS
    DEMO --> IMPACT
    TESTS["test_engine.py"] --> GEO
    TESTS --> ANALYSIS
    TESTS --> SCENARIO
    SMOKE["smoke_test.py"] --> STACK["GeoPandas · NetworkX · OSMnx · Shapely"]
    GEO --> STACK
    ANALYSIS --> STACK
    SCENARIO --> STACK
    SUMO_ENGINE["sumo_engine.py"] --> SUMO_SUPPORT["sumo_support.py discovery"]
    SUMO_SUPPORT --> SUMO_BIN["SUMO · netconvert"]
    SUMO_ENGINE --> DRIVE["OSM driving graph + synthetic demand"]
~~~

- `sim.__init__` re-exports the package API.
- `geo` owns area validation, acquisition, caching, feature classification, and geographic serialization.
- `analysis` consumes `OSMData` and `StudyArea` from `geo`; it owns graph preparation, metrics, access analysis, and issue output.
- `neighborhoods` owns GeoJSON catalog ingestion, provenance-preserving search, boundary validation, and conversion to `normalize_area` input.
- `candidates` consumes the existing walking graph, area, mapped building layer, and analysis issues; it uses a bounded metric STRtree search and emits only `add_pedestrian_connection`.
- `impact` samples graph-node pairs deterministically, reuses the scenario graph-edit helper, calculates Before/After route outcomes, and independently evaluates/ranks alternatives.
- `scenario` consumes the geo types/serializer and imports graph/route helpers from `analysis`, including private `_nearest_nodes`.
- `demo` reads a local cache without network access or uses a synthetic offline fixture; generated results are written under ignored `sim/.cache/`.
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

### Neighborhood catalog

`load_neighborhood_catalog()` reads the tracked `iasi-neighborhoods.geojson` by default and returns normalized JSON-compatible records. The catalog contains 24 mapped OSM place polygons and 7 named place points from a partial bounded query. A point-only record cannot become an analysis boundary. `validate_neighborhood_boundary` uses the existing `normalize_area` safeguards and reports `requires_controlled_analysis` when configured area or extent caps are exceeded. It does not simplify or alter source geometry. A caller can explicitly pass larger limits for a controlled analysis. The catalog and its reuse terms are documented in [NEIGHBORHOODS_LICENSE.md](NEIGHBORHOODS_LICENSE.md); its polygons are not claimed as official municipal boundaries.

### Candidate discovery and multi-route impact

`discover_intervention_candidates` projects the walking graph, selects nodes covered by the study polygon, and uses an STRtree radius lookup. It bounds source nodes, neighbors per source, examined pairs, link length, and a separately configurable opportunity pool (100 by default, hard limit 500). It screens separate weak components first, then directed reachability gaps and directed route detours. Existing direct edges, out-of-area straight lines, over-limit links, invalid weights, and functionally equivalent links are excluded. Issue-geometry proximity is reported as context and does not affect candidate ordering.

Mapped obstacle layers are projected and indexed once per discovery call, before final shortlist selection. Building classifications include material interior crossing (at least 0.5 m overlap), endpoint inside, boundary-only contact, short interior overlap, ambiguous/invalid feature, and no observed mapped conflict. Material crossings, endpoint-inside, and intersecting ambiguous features are excluded from the eligible pool; boundary contacts and short overlaps remain conditional for review. Duplicate OSM feature identities are deduplicated by element type and ID; conflicting geometry for one identity is treated as ambiguous. A no-hit result becomes unknown if legacy cache metadata cannot verify source-area equivalence. Other unavailable evidence—including water/barriers, slope, ownership, access rights, legal review, safety, and construction—remains unknown. No candidate is labeled buildable.

`sample_route_pairs` accepts explicit in-area graph-node pairs or deterministic seeded pairs selected with bounded SHA-256 hash ranking. Explicit samples preserve both route directions. The sample is not observed travel demand. The integrated `evaluate_candidates` pipeline screens the opportunity pool first, excludes evaluated discovery endpoint pairs, and constructs one shared comparison sample for every alternative. Each alternative starts from an immutable copy of the same baseline and applies graph edits through the existing scenario helper. Up to 12 eligible candidates are evaluated by default, then up to 3 are returned.

Pair outcomes are `improved`, `unchanged`, `regressed`, `newly_reachable`, `newly_unreachable`, and `unreachable_in_both`. Distance/time savings are aggregated only when both routes are reachable; reachability changes are reported separately. Improvement percent is null. The shared sample alone drives ranking: newly reachable pairs, improved pairs, distance savings among comparable pairs, mapped-obstacle intersections, unknown obstacle layers, shorter hypothetical links, then stable candidate ID. A separate candidate-specific diagnostic sample draws nearby nodes from each endpoint's component, preserves each direction, excludes overlap with the shared sample, and is not used to rank or describe representative trips. Returned candidates remain conditional and the pipeline does not make construction recommendations.

### Proposal evidence, capability, and validation

proposal_catalog exposes a copied JSON catalog with only the two graph edits that scenario.evaluate_scenario can execute. proposal_context.build_proposal_context combines one matching OSMData, analyze_snapshot result, and evaluate_candidates result. It uses a stable geometry digest rather than embedding the full network, retains source provenance and uncertainty, includes bounded issue/candidate evidence and route samples, and serializes with non-finite values rejected. Deterministic truncation keeps the packet under the configured byte ceiling or raises if irreducible metadata itself exceeds that ceiling.

proposals.prepare_candidate_options selects only returned ranked candidates that have a supported intervention and a completed graph impact. Presentation categories remain unclassified; link length is not a cost or engineering-complexity proxy. proposal_validation treats incoming mappings as untrusted, checks candidate identity and exact intervention equivalence, geographic containment and supported units, then classifies schema, graph support, graph evaluation, and physical feasibility separately. It rejects unsupported cost, citation, run-ID, observed-metric, feasibility, and duplicate claims. These functions make no cloud calls and do not turn model prose into SIM evidence.

proposal_demo runs this complete path with a synthetic fixture or existing local cache and never requests OSM data.

### Reproducible demonstration

Run `python -m sim.demo` from the repository root. It loads an existing local cached walking snapshot when available and otherwise uses a tiny synthetic offline graph. It never requests OSM data. Use `--source cache` to require local cached OSM or `--source fixture` for the deterministic synthetic example. Outputs go to ignored `sim/.cache/sim-engine-demo/results.json` and `results.geojson` by default. New graph and feature sidecars record normalized source-area GeoJSON and SHA-256, area identifiers, CRS, and query parameters. Historical sidecars remain untouched; a key mismatch without a matching geometry hash is reported as unverified.

### SUMO position

`sim.sumo_engine` consumes an existing directed drive graph and projects its coordinates into the validated metric working CRS. `prepare_sumo_network` writes bounded SUMO plain-XML node/edge inputs, a deterministic seeded synthetic origin-destination route set, an ID map, and WGS84 network GeoJSON. It uses explicit fallback speed/lane assumptions and records missing/ambiguous counts. `run_real_area_simulation` invokes `netconvert` and headless `sumo` only when discovered, caps graph size, vehicle count, duration, and wall-clock time, and reports trip completion, waiting, movement checks, provenance, and route GeoJSON only after actual execution. Missing binaries produce an explicit unavailable result and no traffic metrics.

The local Iași cache path reads only existing files and reports area equivalence. The currently available legacy driving sidecar has no matching source-geometry hash, so it is unsuitable as verified area evidence. Generated demand is synthetic, uncalibrated, and not an observed traffic count; turn restrictions, lane allocation when ambiguous, signals, and physical feasibility remain unverified. `sim.sumo_support` retains the separate one-step synthetic TraCI smoke test.

## Data and result formats

### Inputs and coordinate systems

- Bboxes use `[west, south, east, north]`; GeoJSON positions use `[longitude, latitude]`. GeoJSON and bbox coordinates are EPSG:4326.
- A GeoDataFrame must declare a CRS and is transformed to EPSG:4326. GeoJSON/bbox declaring another CRS is rejected. Shapely geometry inputs are treated as WGS84.
- An area dict may set `city_id`, `area_id`, `boundary_source`, `crs`, and `bbox`, `boundary`, or GeoJSON geometry/Feature. Defaults are `iasi-ro`, `user-selected-area`, and `user_selected`; bbox input is marked `bounded_bbox`.
- `StudyArea.working_crs` is selected using local UTM estimation. Distances and area are metric; travel speeds are m/s, thresholds minutes, and ratios unitless. Exported geometry is WGS84.
- Geometry must be non-empty, valid Polygon/MultiPolygon within coordinate bounds. Limits can be explicitly overridden for controlled analyses.

### Graphs and source metadata

`OSMData` contains `area: StudyArea`; successful `walk`/`bike`/`drive` graphs; GeoDataFrames for roads, walking and cycling infrastructure, crossings, buildings, schools, healthcare, services, public transport, parking, and green space; `layer_availability`; source/cache `metadata`; and `warnings`.

Acquired graphs carry OSM source, mode, retrieval time, and area key. Metadata records requested modes, source label, exact normalized WGS84 source geometry and SHA-256, city/area IDs, boundary source, working CRS, tags, per-mode/feature timestamps, cache hits, and limitations. New graph and feature sidecars retain this source-area provenance and bounded query parameters; old sidecars are not rewritten. Feature IDs/tags are retained. Retrieved timestamps describe the query snapshot, not per-feature edit times.

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

Neighborhood records expose `id`, `name`, `alternative_names`, `geometry`, `geometry_type`, `source`, `source_object_id`, `boundary_status`, `review_status`, `provenance`, `retrieved_at`, `updated_at`, and `uncertainty_notes`. GeoJSON coordinates are interpreted as `[longitude, latitude]` in EPSG:4326. Catalog search includes IDs, names, and aliases with accent-insensitive matching. Polygon selection returns an `analysis_area` input only after validation against the configured limits; point-only records provide localization only.

Candidate discovery returns a schema and method version, bounded pool and screening counts, eligible conditional candidates, bounded material-conflict rejections, and warnings. Each candidate contains the supported intervention payload, endpoints, WGS84 LineString, metric length, graph discovery evidence (including endpoint component sizes and small-component caution), related issue IDs and association methods, obstacle taxonomy and feature-quality detail, missing evidence, provenance, assumptions, and generation method version.

`evaluate_multi_route_impact` returns per-pair Before/After status, distance, estimated time, route paths, and capped GeoJSON. Aggregates separate comparable reachable pairs from reachability transitions. `evaluate_candidates` returns the baseline issue/metric summary, one shared ranking sample, independent candidate impacts, candidate-specific targeted diagnostic routes, bounded rejected candidates, evaluation counts, an explicit empty recommendation list, and the ranking rule. Shared and targeted evidence have distinct roles in the payload. These outputs are Python-library results, not backend HTTP contracts.

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

This inventory covers the tracked files in `sim/`. There are no tracked nested source directories. Test file references outside this directory are linked where useful.

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
- **Public exports:** existing geo, analysis, and scenario types/functions plus `NeighborhoodCatalogError`, catalog load/get/search/GeoJSON/validation helpers, `discover_intervention_candidates`, `sample_route_pairs`, `evaluate_multi_route_impact`, and `evaluate_candidates`. The `__all__` list is the explicit export list. `RouteError` remains available from `sim.analysis`, not package root.
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

### `neighborhoods.py`

- **Purpose:** load and normalize GeoJSON catalog records; search IDs, names, and aliases; validate selected Polygon/MultiPolygon boundaries through `normalize_area`; and create acquisition-ready area inputs.
- **Public API:** `NeighborhoodCatalogError`, `load_neighborhood_catalog`, `get_neighborhoods`, `get_neighborhood`, `search_neighborhoods`, `neighborhoods_geojson`, `validate_neighborhood_boundary`, and `neighborhood_area_input`.
- **Limits:** EPSG:4326 GeoJSON is interpreted in longitude/latitude order. Point-only records are not analysis areas. Default area and extent limits remain 5 km² and 5 km. Oversized polygons require caller-supplied controlled limits; geometry is not simplified. Data provenance and license are retained.
- **Tests:** polygon/MultiPolygon, invalid geometry/CRS, points, missing provenance, configured limits, and stable GeoJSON are covered in `test_engine.py`.

### `iasi-neighborhoods.geojson` and `NEIGHBORHOODS_LICENSE.md`

- **Purpose:** a compact OSM-derived Iași place catalog plus source, attribution, coverage, and reuse terms.
- **Contents:** 24 source-mapped polygons and 7 point-only records from a partial bounded Overpass query retrieved 2026-10-17. OSM IDs, URLs, retrieval timestamps, uncertainty notes, and ODbL-1.0 markings are included.
- **Limits:** place extents are not verified legal or municipal boundaries; coverage is partial. The raw Overpass/geocoder responses remain ignored in the local demo cache and are not tracked.

### `candidates.py`

- **Purpose:** deterministic spatial-index discovery and obstacle screening for hypothetical pedestrian connections.
- **Public API:** `discover_intervention_candidates(data, *, issues=(), max_candidates=3, candidate_pool_limit=100, max_connection_length_m=1000, detour_ratio_threshold=2, max_screened_pairs=10000, max_source_nodes=500, max_neighbors_per_source=20)`.
- **Methods/limits:** only separate weak components, directed reachability gaps, and excessive directed route detours are screened. Node lookup and the 100-item default obstacle-screening pool (500 maximum) are bounded; all shortlist links must remain inside the study polygon and within the scenario engine's 1,000 m maximum. Existing direct edges and equivalent links are removed. Material building conflicts are blocked; boundary/short overlaps and incomplete source evidence remain conditional.
- **Tests:** graph components, detours, direct-edge exclusion, duplicate links and OSM identities, length and polygon limits, building-intersection taxonomy, source-area uncertainty, pool screening, stable IDs, and unsupported types are covered in `test_engine.py`.

### `impact.py`

- **Purpose:** deterministic route-node sampling, independent multi-route Before/After calculations, and candidate ranking.
- **Public API:** `sample_route_pairs`, `evaluate_multi_route_impact`, and `evaluate_candidates`.
- **Methods/limits:** explicit OD pairs preserve direction; seeded SHA-256 hash sampling remains bounded with no all-pairs allocation or undocumented randomness. Discovery pairs are excluded from the common comparison sample. Separate targeted endpoint-component diagnostics preserve both directions and never drive ranking. Route graph edits reuse the existing scenario helper; distance/time are compared only when reachable both before and after; reachability transitions remain separate. Ranking is shared-sample-only and does not claim project feasibility.
- **Tests:** improved/unchanged/newly reachable outcomes, explicit reverse directions, invalid pairs, determinism, targeted diagnostics, independent alternatives, immutability, aggregate math, geometry cap, and stable ranking are covered in `test_engine.py`.

### `demo.py`

- **Purpose:** run analysis, candidate discovery, multi-route evaluation, ranking, and JSON/GeoJSON export from one command.
- **Use:** `python -m sim.demo`; optional `--source cache|fixture` selects cached OSM or the tiny offline graph. The `auto` default uses the cache if present and otherwise uses the fixture. The CLI never downloads data and writes only to ignored `sim/.cache/` by default.
- **Limitations:** a legacy cache-key mismatch without a matching stored source-geometry hash is preserved as unknown. Synthetic results are labeled as synthetic and are not evidence about Iași.

### `smoke_test.py`

- **Purpose:** dependency/import and deterministic graph smoke check for a tiny in-memory NetworkX graph.
- **Public functions:** `run() -> dict[str, str | int | float]` imports/reports GeoPandas, NetworkX, OSMnx, and Shapely versions and asserts shortest path `a -> b -> c` is 200 m. `main() -> None` prints the result.
- **Errors/dependencies/callers/side effects:** assertion failure raises `AssertionError`; missing dependencies fail import. Called directly with `python -m sim.smoke_test` and by `tests/test_spatial_smoke.py`. No network, file, OSM cache, or SUMO side effects.
- **Assumptions/limits:** checks imports and basic NetworkX path behavior only; it does not validate OSM acquisition or the full analysis engine.

### SUMO engine

`sumo_engine.py` converts caller-provided directed OSM drive graphs into projected node/edge XML and reproducible synthetic route inputs, retains an ID map and EPSG:4326 GeoJSON, and optionally runs a bounded headless simulation. Its cache loader is read-only. It does not download OSM, calibrate demand, create physical interventions, or claim measured traffic.

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

V2 neighborhood, discovery, impact, and ranking entry points are also available at package root:

~~~python
from sim import (
    evaluate_candidates,
    get_neighborhoods,
    neighborhood_area_input,
    search_neighborhoods,
)

record = next(item for item in search_neighborhoods("Tătărași") if item["geometry_type"] == "Polygon")
area_input = neighborhood_area_input(record)  # raises for point-only/invalid/over-limit areas
snapshot = acquire_osm_data(area_input, modes=("walk",))
ranked = evaluate_candidates(snapshot, sample_count=32, seed="iasi-demo-v1")
~~~

Only `add_pedestrian_connection` is auto-discovered. Keep the analysis issue set, candidate screening, shared route sample, ranking rule, provenance, warnings, and unknown feasibility visible to downstream consumers. Do not translate graph-node route counts into residents or observed trips.

Backend responsibilities include HTTP request/response validation and adaptation, stable `baseline_id` assignment, persistence of source snapshots and metadata, authorization, timeouts, and API error mapping. SIM has no baseline store, HTTP endpoint, LLM proposal API, or traffic simulation evaluation mode. The scenario functions return graph-route comparisons only.

The draft [API contract](../docs/API_CONTRACT.md) describes planned `/analyze`, `/propose`, and `/evaluate` routes; current `backend/main.py` only implements `GET /health`. The draft and SIM result schemas differ: SIM returns an indicators array, issues array, dictionary-valued `layer_availability`, and named `layers`/`networks` FeatureCollections. SIM does not persist `baseline_id`, return the draft availability array, generate AI proposals, or populate a `simulation` response. Backend code must map shapes and preserve unknown values, provenance, warnings, units, and uncertainty.

## Testing and verification

- `sim/test_engine.py` uses in-memory graph/GeoDataFrame fixtures, temporary cache directories, and mocked OSMnx requests. Coverage includes existing acquisition/analysis/scenario behavior plus catalog validation, bounded candidate generation, building-intersection taxonomy and data quality, cache sidecar geometry/hash, source-area uncertainty, deterministic shared and targeted route sampling, directionality, multi-route outcomes/aggregates, baseline immutability, and stable ranking.
- `tests/test_spatial_smoke.py` checks imports and a deterministic 200 m synthetic NetworkX route; no OSM request.
- `tests/test_sumo_support.py` checks portable binary discovery using temporary dummy files; it does not execute SUMO.
- `tests/test_backend.py` checks health, CORS, and that planned routes remain 404; it does not exercise SIM.
- [scripts/check.ps1](../scripts/check.ps1) and [scripts/check.sh](../scripts/check.sh) run `pytest -q tests sim/test_engine.py`, backend health, frontend checks/build, and optional SUMO smoke. Since `pyproject.toml` sets `testpaths = ["tests"]`, bare `pytest -q` omits `sim/test_engine.py`.
- CI is [../.github/workflows/ci.yml](../.github/workflows/ci.yml): Windows x64 (`windows-latest`) and macOS ARM64 (`macos-15`, asserted as `ARM64`/`arm64`). Python is constrained to 3.12. Current workflow does not test macOS Intel.
- [STATUS.md](STATUS.md) records the current local result of 65 pytest cases (60 SIM plus 5 project tests) and separately records the CI result for the published commit. SUMO smoke is a separate synthetic executable check, not real-area traffic simulation.

Run the SIM regression suite in an already provisioned environment. The project check scripts use `uv run --locked`; that command may create/sync an environment when none exists. If dependency installation is not authorized, use an existing interpreter directly (for example, `.venv/Scripts/python.exe -m pytest -q tests sim/test_engine.py` on Windows):

~~~sh
uv run --locked pytest -q tests sim/test_engine.py
~~~

Standalone checks: `python -m sim.smoke_test` and, if SUMO/netconvert are available, `python -m sim.sumo_support --smoke`.

## Current capabilities and future work

**Implemented:** bounded validation; cached OSM network/features; walk/bike/drive graph metrics; walking/cycling node access and detour analysis; deterministic issue candidates; WGS84 serialization; ODbL-attributed neighborhood/place catalog with polygon/point distinction; automatic bounded pedestrian-link candidate discovery; mapped-building obstacle screening; deterministic multi-route evaluation; independent candidate ranking; an offline/cached reproducible JSON/GeoJSON demo; SUMO discovery and synthetic TraCI smoke support.

**Experimental/local-only:** the ignored browser preview and neighborhood mapping/editor under `sim/.cache/local_demo/`, if present. It is absent from clones and is not a production SIM module. Its local-only notes are in `sim/.cache/local_demo/ARCHITECTURE.md`.

**Planned or absent:** real-area OSM-to-SUMO conversion and synthetic vehicle demand; traffic calibration/live/offline simulation; water/elevation/slope/ownership/legal/safety feasibility screening; expanded POI sources; browser preview integration of the new result schema. These are not implemented.
