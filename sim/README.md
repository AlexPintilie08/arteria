# Geospatial analysis and simulation

This package acquires bounded OpenStreetMap snapshots, builds walking/cycling/driving networks, calculates reproducible network indicators, detects evidence-backed access/connectivity issues, exports GeoJSON, and evaluates hypothetical pedestrian-network changes. The backend can import the Python functions directly; no FastAPI or LLM dependency is required.

See [ARCHITECTURE.md](ARCHITECTURE.md) for module relationships and result contracts, [APPLICATION_INTEGRATION.md](APPLICATION_INTEGRATION.md) for the frontend/backend handoff, [STATUS.md](STATUS.md) for verification and limitations, and [AGENTS.md](AGENTS.md) for component-specific agent instructions.

## Public Python API

```python
from sim import (
    analyze_area,
    acquire_osm_data,
    build_proposal_context,
    evaluate_candidates,
    evaluate_multi_route_impact,
    evaluate_pedestrian_connection,
    get_intervention_catalog,
    neighborhood_area_input,
    prepare_candidate_options,
    search_neighborhoods,
    validate_proposal,
    validate_proposal_set,
    validate_neighborhood_boundary,
)

area = {
    "city_id": "iasi-ro",
    "area_id": "iasi-example-area",
    "bbox": [27.5755, 47.1610, 27.5825, 47.1655],  # west, south, east, north
    "crs": "EPSG:4326",
    "boundary_source": "user_selected",
}

# Full acquisition and analysis. Each requested mode is fetched serially.
result = analyze_area(area, modes=("walk", "bike", "drive"))
print(result["network_metrics"]["walk"])
print(result["layer_availability"]["schools"])

# Reuse the same immutable baseline snapshot for scenario evaluations.
snapshot = acquire_osm_data(area, modes=("walk",))
# Choose points inside the area and within the snap limit of mapped walking nodes.
scenario = evaluate_pedestrian_connection(
    snapshot,
    start=[27.5800, 47.1620],
    end=[27.5810, 47.1630],
)
print(scenario["baseline"]["network_distance_m"])
print(scenario["scenario"]["network_distance_m"])
print(scenario["comparison"]["distance_delta_m"])

# Select and validate a sourced polygon boundary, then run ranked alternatives.
record = next(item for item in search_neighborhoods("Tătărași") if item["geometry_type"] == "Polygon")
print(validate_neighborhood_boundary(record))
neighborhood_area = neighborhood_area_input(record)
neighborhood_snapshot = acquire_osm_data(neighborhood_area, modes=("walk",))
ranking = evaluate_candidates(neighborhood_snapshot, sample_count=32, seed="iasi-demo-v1")
print(ranking["ranked_candidates"])
```

`analyze_area` returns the API-friendly JSON-ready result. For a preloaded or synthetic snapshot, call `analyze_snapshot`. `evaluate_scenario` accepts a sequence of `add_pedestrian_connection` and `set_connection_enabled` interventions plus a route origin and destination. `route_between` calculates a weighted graph route and returns network distance, straight-line reference, and detour ratio when node coordinates and CRS are available.

## Neighborhood catalog

`load_neighborhood_catalog()` reads the tracked `iasi-neighborhoods.geojson` dataset by default. It contains 24 OSM-mapped polygons and 7 point-only named places from a partial bounded query. Use `get_neighborhoods`, `get_neighborhood`, `search_neighborhoods`, and `neighborhoods_geojson` to enumerate, select, search, or export records. Search includes identifiers, names, and alternative names and ignores diacritics when matching.

`validate_neighborhood_boundary` distinguishes a valid polygon from a point-only location and applies the same 5 km² area and 5 km extent safeguards as `normalize_area`. An oversized polygon returns `requires_controlled_analysis`; pass explicit larger `max_area_km2` and `max_extent_km` values only for a controlled analysis. `neighborhood_area_input` returns a normal acquisition input only after validation. Geometry is not simplified, replaced, shrunk, or inferred from point locations.

The catalog preserves source object IDs, source URLs, query/retrieval dates, review status, and uncertainty notes. Its OSM place polygons are not verified municipal or legal neighborhood boundaries, and point-only records remain points. The source query was partial, so the catalog is not a complete Iași neighborhood inventory. The derived dataset is distributed under ODbL-1.0 with attribution; see [NEIGHBORHOODS_LICENSE.md](NEIGHBORHOODS_LICENSE.md).

## Geographic inputs and limits

- Inputs may be a valid Polygon/MultiPolygon, GeoJSON geometry/Feature, CRS-declared GeoDataFrame, or `[west, south, east, north]` bounding box. GeoJSON and bbox coordinates use longitude/latitude in EPSG:4326.
- The default limit is 5 km² and 5 km in either dimension. Both bounds can be lowered or raised explicitly for a controlled local analysis.
- Invalid, empty, self-intersecting, out-of-range, or oversized geometries are rejected. Distances and areas use a locally estimated metric UTM CRS; exported geometry uses EPSG:4326.
- `graph_from_polygon` retains disconnected components and one-edge boundary connectors for routing. Area accessibility counts and issue geometry use nodes inside the selected polygon; component totals describe the retrieved graph and may include boundary connectors.

## Acquisition, cache, and provenance

`acquire_osm_data` retrieves OSMnx network graphs for `walk`, `bike`, and/or `drive`, then requests supported infrastructure and POI tags by default. Graph-only consumers can pass `include_features=False`; feature layers remain `unknown` unless a cached snapshot is available. OSMnx's normal Overpass rate limiting remains enabled, requests are sequential, and the request identifies ARTERIA in its user-agent.

Network modes are independent: a drive-only or bike-only request does not require a walking graph. The iterable must contain at least one supported mode (`walk`, `bike`, or `drive`); duplicate modes are removed while preserving request order. A graph is available only when it contains nodes and routable edges. For partial success, the returned `OSMData.graphs` contains only successful modes, `layer_availability["<mode>_network"]` reports `available` or `request_failed`, and `warnings` includes each failed network request. If every requested mode fails, acquisition raises `OSMDataError` with the per-mode errors and skips the POI query. A POI-query failure does not discard successfully acquired networks; its layers remain `unknown`.

```python
from sim import acquire_osm_data, analyze_snapshot

drive_snapshot = acquire_osm_data(area, modes=("drive",))
drive_result = analyze_snapshot(drive_snapshot)
assert set(drive_result["network_metrics"]) == {"drive"}

mixed_snapshot = acquire_osm_data(area, modes=("walk", "bike", "drive"))
for mode in mixed_snapshot.metadata["requested_network_modes"]:
    print(mode, mixed_snapshot.layer_availability[f"{mode}_network"]["status"])
```

Analysis only emits network metrics for graphs present in the snapshot. Walking/cycling access indicators are calculated only for their corresponding available modes; a driving-only snapshot does not produce pedestrian-access claims. Missing networks, POI layers, or snap-eligible POIs are unknown rather than zero.

The default cache is `sim/.cache/osm/` and contains local GraphML/GeoJSON snapshots plus OSMnx's HTTP response cache. `sim/.gitignore` excludes those generated files. Use `force_refresh=True` to reacquire a snapshot or `cache_dir=...` to provide a different local cache directory. `overpass_url` can select an Overpass-compatible endpoint when the default endpoint is unavailable. The selected endpoint's usage policy still applies.

Metadata records the source, retrieval time, area extent, working CRS, query tags, cached modes, and limitations. New cache sidecars also store the exact normalized WGS84 source polygon and its SHA-256 hash, area identifiers, CRS, and request parameters. Existing sidecars are not rewritten. A legacy cache-key mismatch without a matching source-geometry hash leaves area equivalence unverified. An empty OSM layer is `no_features_returned`; a failed or unproven query is `unknown`. Neither status means the real-world feature is absent. OSM tags and network coverage are incomplete and may change after the snapshot was retrieved.

## Layers and analysis

The feature query classifies roads, walking infrastructure, cycling infrastructure, crossings, buildings, schools, healthcare, supported services, public-transport stops/stations, parking, and mapped green space. Each layer reports an availability status and tagged-feature count. The output includes clipped feature GeoJSON, clipped network-edge GeoJSON, heatmap-ready GeoJSON, and analysis issues.

Network indicators cover node/edge counts, weakly connected components, largest-component share, and isolated nodes. Walking and cycling access use weighted NetworkX shortest paths to the nearest snap-eligible mapped service. Default constant speeds are 1.3 m/s walking and 4.5 m/s cycling; the default threshold is 15 minutes. These are explicit estimates, not measured travel times. The engine does not infer population access, traffic counts, congestion, or real-time conditions.

Detour ratios compare a calculated network route with straight-line distance to the nearest mapped target geometry. The default issue threshold is a ratio greater than 2.0 and can be changed with `detour_ratio_threshold`. It is a screening assumption, not a feasibility judgment.

Issue IDs are stable for an area/type/component. Every issue includes its geometry, calculated metrics and units, OSM evidence references, method provenance, severity, coverage, and uncertainty. Severity rules are deterministic:

- A disconnected component is high when it contains one in-area node and medium when it contains more.
- Poor access is high when at least 25% of in-area graph nodes are unreachable, medium when any are unreachable or at least 25% are outside the time threshold, and low for other threshold exceedances.
- A detour issue is high when at least 25% of in-area graph nodes exceed the configured ratio, medium at 10% or more, and low below 10%.

Issue/heatmap point samples are capped for response size, but indicator counts use all in-area nodes. No issue is a claim that a physical project is safe, legal, funded, or automatically feasible.

## Virtual interventions

`evaluate_pedestrian_connection` adds a straight-line hypothetical link between two EPSG:4326 locations snapped to existing walking nodes. `evaluate_scenario` also supports enabling/disabling an identified modeled ARTERIA connection. It validates the area, node snap distance, and maximum 1,000 m link length; copies the projected baseline graph; and recalculates the same weighted route before and after. The response includes both route geometries, distances, estimated walking times, delta, and any reachability change. Baseline inputs are not mutated. No impact percentage is fabricated.

The hypothetical link does not evaluate street crossing safety, grade, accessibility standards, land ownership, utilities, legal approval, or construction feasibility.

## Candidate discovery and multi-route impact

`discover_intervention_candidates(snapshot, issues=analysis["issues"])` searches the metric walking graph with bounded spatial indexing. It considers nearby nodes in separate weak components, directed reachability gaps, and connected pairs with route detours above the configured ratio. It rejects direct existing links, invalid/out-of-area lines, links above the scenario engine's 1,000 m maximum, and functionally equivalent links. The default opportunity pool is 100 (hard limit 500); mapped layers are indexed once and every pool entry is screened before the final shortlist is selected. The only generated intervention is `add_pedestrian_connection`.

Building findings distinguish material interior crossings, endpoints inside a building, boundary-only contact, short interior overlaps, ambiguous/invalid features, and no observed mapped conflict. Interior overlaps of at least 0.5 m, endpoint-inside cases, and intersecting ambiguous features are excluded from the eligible pool. Boundary contact and shorter overlaps remain conditional for review. A no-hit result is marked unknown when the cached source area is unverified. Duplicate OSM identities are deduplicated by element type and ID, with conflicting duplicate geometry treated as ambiguous. Candidate output includes feature-quality counts and bounded intersection details. Water/barrier, elevation, slope, ownership, legal, safety, and access-rights evidence can still be missing; no candidate is labeled buildable.

`sample_route_pairs` accepts explicit graph-node pairs or creates a bounded deterministic sample from in-area graph nodes with a stable seed. It never invents resident trips. `evaluate_multi_route_impact` reports Before/After reachability, network distance, constant-speed walking time, outcome, and deltas for every sampled pair. Distance savings are aggregated only for pairs reachable before and after; newly reachable/unreachable pairs are counted separately. Route geometry has its own cap, independent of the numeric sample count.

`evaluate_candidates` analyzes the baseline, screens the bounded opportunity pool, excludes evaluated discovery pairs from a common deterministic comparison sample, and evaluates each eligible alternative from the same immutable baseline. The shared sample alone drives the lexicographic ranking: newly reachable pairs, improved pairs, comparable route savings, obstacle findings, unknown layers, link length, and stable ID. Up to 12 eligible candidates are evaluated by default and up to 3 are returned. A separate bounded diagnostic sample uses nearby nodes in each candidate's endpoint components to show local reachability or detour effects; both route directions are retained, and these candidate-specific probes never affect shared-sample ranking. Returned candidates remain conditional, and the API makes no construction recommendation. When no candidate passes material-conflict screening, it returns an honest empty result with bounded rejected-candidate diagnostics.

## Proposal evidence and candidate options

The intervention catalog is versioned and machine-readable. Only add_pedestrian_connection and set_connection_enabled are supported graph edits; neither has SUMO evaluation. Traffic signals, lanes, underpasses, roundabouts, construction cost, and physical feasibility remain unsupported.

build_proposal_context(snapshot, analysis, candidate_evaluation) creates a deterministic packet for a future backend-owned model. It includes a SHA-256 reference to the study geometry, source/timestamp metadata, bounded issue and indicator evidence, network metrics, candidate geometry and screening, shared and targeted route samples, before/after graph outcomes, source availability, uncertainty, ranking rules, unsupported capabilities, and explicit limitations. It omits full network graphs and caps serialized JSON at 64 KiB by default. Deterministic truncation and the serialized byte count are returned.

prepare_candidate_options(analysis, candidate_evaluation) returns only evaluated add_pedestrian_connection candidates, in stable rank order. It does not force three options or assign the frontend's Minimală/Moderată/Transformatoare labels because SIM has no engineering-backed mapping for those categories. Graph impact is labeled calculated and sampled, not observed; construction cost remains unsupported.

validate_proposal(proposal, data=snapshot, candidate_evaluation=evaluation) and validate_proposal_set(...) treat model output as untrusted. They check the supported type, finite EPSG:4326 endpoints, study-area containment, known candidate ID, exact match to the evaluated intervention, units, citations, simulation run IDs, observed metric claims, costs, and feasibility claims. Results distinguish schema validity, graph support, graph evaluation, and physical feasibility; JSON validity alone never produces a validated status. Repeated actions are rejected as duplicates.

Run an offline demonstration without an API key or network request:

    .\.venv\Scripts\python.exe -m sim.proposal_demo --source fixture --output sim/.cache/proposal-demo/results.json

The optional cache mode reads existing files only. It carries legacy source-area warnings when its cache key and saved geometry do not verify the selected area. Prefer the deterministic fixture for a source-independent example.

## Reproducible demonstration

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m sim.demo
```

The default `auto` mode loads a local cached walking snapshot if available and otherwise uses a tiny deterministic offline fixture. The demo never downloads OSM. Use `--source cache` to require a cached snapshot, or `--source fixture` for the synthetic example. It writes `results.json` and `results.geojson` under ignored `sim/.cache/sim-engine-demo/`. Output includes source-area verification, pool/screen/rejection counts, the shared comparison sample, targeted diagnostic routes, and screened-out candidates. Cache-key mismatches without a matching original geometry hash remain explicitly unverified.

## Tests and verified Iași snapshot

Offline engine tests use small in-memory fixtures and mocks; they do not require Overpass access. The explicit local verification command is:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=sim/.cache/pytest-stabilization tests sim/test_engine.py
```

The SIM v2.1 local regression run completed with 65 cases (5 project tests and 60 SIM cases). The checked-in `scripts/check.ps1` and `scripts/check.sh` explicitly invoke `pytest -q tests sim/test_engine.py`, so CI includes the simulation suite. A bare `pytest -q` follows `pyproject.toml`'s `testpaths = ["tests"]` and omits `sim/test_engine.py`; use the explicit command above.

Scenario parameter validation rejects non-finite travel speeds and thresholds so results cannot silently contain NaN or Infinity. The baseline and scenario use the same configured walking speed, including the estimate attached to a hypothetical connection. Scenario outputs include deterministic route comparisons, WGS84 GeoJSON, source provenance, and explicit warnings that the intervention is hypothetical.

The integrated FastAPI backend uses SIM v3 through `/api/v1/spatial`: it validates a canonical neighborhood catalog ID, acquires the walking graph, analyzes the snapshot, prepares and validates graph candidates, and stores an immutable study with source provenance, uncertainty, and evidence. OSM feature layers are not requested in this flow and remain unknown. Candidate comparison is graph-only; it does not establish physical feasibility and does not run SUMO. See [`backend/SPATIAL_API.md`](../backend/SPATIAL_API.md) for request and response details.

The real bounded study run used `[27.5755, 47.1610, 27.5825, 47.1655]` in central Iași (EPSG:32635 working CRS). The retrieved snapshot produced 136 walking-graph nodes and 354 directed edges; 107 nodes were inside the study polygon. It returned 151 road features, 88 walking-infrastructure features, 17 crossing features, 275 buildings, 4 schools, 3 healthcare features, 9 other supported services, 3 public-transport features, 8 parking features, and 5 green-space features. No explicit cycling-infrastructure features were returned; that is not proof that none exist.

The same snapshot produced 105 of 107 in-area walking nodes within 15 estimated minutes of each of the supported school, healthcare, service, public-transport, and green-space feature groups. Median route detour ratios were 1.04 for schools, 1.31 for healthcare, 1.32 for services, 1.64 for public transport, and 1.41 for green space. Two graph components each contained one in-area node outside the largest component. These counts refer to mapped network nodes, not people.

A real-graph hypothetical connection between OSM nodes `641092475` and `12079937967` changed their calculated walking route from 648.7 m to 34.4 m (delta −614.3 m). This is a graph-only comparison; the connecting segment has not been checked for physical feasibility.

## SUMO

`sim.sumo_engine` can prepare a bounded existing directed drive graph as metric-coordinate SUMO plain XML, generate deterministic synthetic origin-destination routes, preserve source IDs, and export WGS84 network GeoJSON. Missing speeds use the documented 13.9 m/s fallback; generic lane counts on two-way roads use one lane per direction when directional allocation is not established. Conversion and headless simulation are attempted only when local `netconvert` and `sumo` binaries are discovered. The runner is bounded to 15,000 nodes, 50,000 edges, 200 vehicles, 600 simulated seconds, and a 180-second wall-clock timeout. It reports completed/incomplete trips, waiting time, and positive movement only from actual SUMO tripinfo output. Outputs include source attribution, demand seed, a source-ID map, and WGS84 GeoJSON. This is synthetic, uncalibrated traffic demand and does not measure Iași traffic.

Run the cached Iași demonstration without network access:

    .\.venv\Scripts\python.exe -m sim.sumo_engine --output-dir sim/.cache/iasi-sumo-demo

This reads the newest local cached drive graph and writes SUMO input files. If `netconvert` or `sumo` is missing, the result records the unavailable stage and contains no simulated traffic measurements. The current legacy cache cannot verify its source geometry against the selected area, so the demonstration is technical only. The separate portable discovery and one-step synthetic TraCI smoke check remains available with `python -m sim.sumo_support --smoke`.

### SIM v4: selected feature layers and paired driving scenarios

`acquire_osm_data(..., feature_categories=("schools", "healthcare"))` requests only those supported OSM categories. `None` preserves the legacy broad query when `include_features=True`; `[]` makes no feature request. Selection is limited to four categories and reports per-category status, count, tag filter, retrieval time, cache state, area verification, and warnings in `metadata["feature_category_availability"]`. Legacy `layer_availability` statuses remain compatible. The complete tag table and cache rules are in [INTEGRATION_CONTRACT_V4.md](INTEGRATION_CONTRACT_V4.md).

`get_driving_intervention_catalog(data)` exposes only a version-bound directed-edge speed limit edit. `evaluate_driving_scenario(data, intervention, output_dir, ...)` creates baseline and scenario copies, reuses one deterministic synthetic demand plan, executes both locally with SUMO, and returns `arteria.sumo-comparison.v1`. The comparison contains numerical deltas only if both runs complete and actual finished vehicles have matching valid SUMO-reported edge sequences. No OSM download occurs inside this evaluator. Speed limits are modeled graph edits; feasibility and legal status remain unknown. SUMO metrics are not measured or calibrated traffic.

Run the integrated deterministic demo:

```powershell
.\.venv\Scripts\python.exe -m sim.mvp_demo --source fixture
.\.venv\Scripts\python.exe -m sim.mvp_demo --source cache --cache-dir sim/.cache/osm --sumo-baseline
.\.venv\Scripts\python.exe -m sim.mvp_demo --source area --area-json area.json
.\.venv\Scripts\python.exe -m sim.mvp_demo --source area --area-json area.json --acquire --feature-categories buildings,schools
```

The CLI does not silently fall back between sources. `cache` requires an explicit local cache path and remains offline. `area` validates an explicit bounded input without acquiring data unless `--acquire` is supplied. Outputs default to an ignored timestamped directory under `sim/.cache/mvp-demo/` with a JSON report, candidate/issue/route GeoJSON evidence, and short Markdown summary. Optional SUMO flags use only the selected snapshot's existing drive graph.

The successful native verification recorded in [STATUS.md](STATUS.md) uses a newly acquired, geometry-hash-verified bounded Iași OSM driving graph; its old legacy-cache caveat above applies only when that historical cache is selected.

## Urban problem and AI planning demo

Planning mode layers localized issue detection and evidence-linked solutions over the existing analysis and candidate evaluation. Run its deterministic offline contract example:

~~~powershell
.\.venv\Scripts\python.exe -m sim.mvp_demo --source fixture --planning --output-dir sim/.cache/mvp-demo/ai-planning-fixture
~~~

The fixture remains synthetic and is not an Iași observation. Its mock model call only exercises the provider-neutral schema and validator; no cloud inference occurs. To use a real bounded catalog area, prepare a GeoJSON/area input and explicitly permit acquisition:

~~~powershell
.\.venv\Scripts\python.exe -m sim.mvp_demo --source area --area-json area.json --acquire --planning --feature-categories schools,healthcare,services,public_transport --output-dir sim/.cache/mvp-demo/ai-planning-area
~~~

Planning mode writes analysis, urban problems, solutions, the bounded AI evidence packet, a model input/schema example, candidate/problem GeoJSON, a Markdown summary and validation report under the ignored output directory. Acquisition failure remains explicit and never falls back to fixture data.

Package-root APIs are detect_urban_problems, problem_locations_geojson, build_solution_plan, build_ai_planning_packet, validate_ai_planning_response and run_ai_planning. The backend should build and persist the immutable packet while its study worker still holds the matching OSMData graph. Later provider requests consume that packet and do not acquire another snapshot. See INTEGRATION_CONTRACT_V4.md and the backend/frontend implementation handoffs for exact status, schema, evidence and visualization rules. SIM itself has no cloud provider, credentials, or AI HTTP endpoint.
