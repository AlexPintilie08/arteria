# Geospatial analysis and simulation

This package acquires bounded OpenStreetMap snapshots, builds walking/cycling/driving networks, calculates reproducible network indicators, detects evidence-backed access/connectivity issues, exports GeoJSON, and evaluates hypothetical pedestrian-network changes. The backend can import the Python functions directly; no FastAPI or LLM dependency is required.

## Public Python API

```python
from sim import analyze_area, acquire_osm_data, evaluate_pedestrian_connection

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
scenario = evaluate_pedestrian_connection(
    snapshot,
    start=[27.5800, 47.1620],
    end=[27.5810, 47.1630],
)
print(scenario["baseline"]["network_distance_m"])
print(scenario["scenario"]["network_distance_m"])
print(scenario["comparison"]["distance_delta_m"])
```

`analyze_area` returns the API-friendly JSON-ready result. For a preloaded or synthetic snapshot, call `analyze_snapshot`. `evaluate_scenario` accepts a sequence of `add_pedestrian_connection` and `set_connection_enabled` interventions plus a route origin and destination. `route_between` calculates a weighted graph route and returns network distance, straight-line reference, and detour ratio when node coordinates and CRS are available.

## Geographic inputs and limits

- Inputs may be a valid Polygon/MultiPolygon, GeoJSON geometry/Feature, CRS-declared GeoDataFrame, or `[west, south, east, north]` bounding box. GeoJSON and bbox coordinates use longitude/latitude in EPSG:4326.
- The default limit is 5 km² and 5 km in either dimension. Both bounds can be lowered or raised explicitly for a controlled local analysis.
- Invalid, empty, self-intersecting, out-of-range, or oversized geometries are rejected. Distances and areas use a locally estimated metric UTM CRS; exported geometry uses EPSG:4326.
- `graph_from_polygon` retains disconnected components and one-edge boundary connectors for routing. Area accessibility counts and issue geometry use nodes inside the selected polygon; component totals describe the retrieved graph and may include boundary connectors.

## Acquisition, cache, and provenance

`acquire_osm_data` retrieves OSMnx network graphs for `walk`, `bike`, and/or `drive`, then requests supported infrastructure and POI tags. OSMnx's normal Overpass rate limiting remains enabled, requests are sequential, and the request identifies ARTERIA in its user-agent.

Network modes are independent: a drive-only or bike-only request does not require a walking graph. The iterable must contain at least one supported mode (`walk`, `bike`, or `drive`); duplicate modes are removed while preserving request order. A graph is available only when it contains nodes and routable edges. For partial success, the returned `OSMData.graphs` contains only successful modes, `layer_availability["<mode>_network"]` reports `available` or `request_failed`, and `warnings` includes each failed network request. If every requested mode fails, acquisition raises `OSMDataError` with the per-mode errors and skips the POI query. A POI-query failure does not discard successfully acquired networks; its layers remain `unknown`.

```python
from sim import analyze_snapshot

drive_snapshot = acquire_osm_data(area, modes=("drive",))
drive_result = analyze_snapshot(drive_snapshot)
assert set(drive_result["network_metrics"]) == {"drive"}

mixed_snapshot = acquire_osm_data(area, modes=("walk", "bike", "drive"))
for mode in mixed_snapshot.metadata["requested_network_modes"]:
    print(mode, mixed_snapshot.layer_availability[f"{mode}_network"]["status"])
```

Analysis only emits network metrics for graphs present in the snapshot. Walking/cycling access indicators are calculated only for their corresponding available modes; a driving-only snapshot does not produce pedestrian-access claims. Missing networks, POI layers, or snap-eligible POIs are unknown rather than zero.

The default cache is `sim/.cache/osm/` and contains local GraphML/GeoJSON snapshots plus OSMnx's HTTP response cache. `sim/.gitignore` excludes those generated files. Use `force_refresh=True` to reacquire a snapshot or `cache_dir=...` to provide a different local cache directory. `overpass_url` can select an Overpass-compatible endpoint when the default endpoint is unavailable. The selected endpoint's usage policy still applies.

Metadata records the source, retrieval time, area extent, working CRS, query tags, cached modes, and limitations. An empty OSM layer is `no_features_returned`; a failed or unproven query is `unknown`. Neither status means the real-world feature is absent. OSM tags and network coverage are incomplete and may change after the snapshot was retrieved.

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

## Tests and verified Iași snapshot

Offline engine tests use small in-memory fixtures and mocks; they do not require Overpass access. The explicit local verification command is:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=sim/.cache/pytest-stabilization tests sim/test_engine.py
```

Verified locally after stabilization: 36 passed (5 repository tests and 31 simulation-engine tests). The default `pytest -q` collected only the 5 repository tests, confirming the CI coverage gap below.

CI coverage gap: `pyproject.toml` sets `testpaths = ["tests"]`, and the shared Windows/macOS check scripts run `pytest -q` without naming `sim/test_engine.py`. The regular CI therefore does not collect the simulation-engine regression tests. The smallest proposed shared change is to pass `tests sim/test_engine.py` explicitly in both `scripts/check.ps1` and `scripts/check.sh`; those files were left untouched because this component owns only `sim/`.

Scenario parameter validation rejects non-finite travel speeds and thresholds so results cannot silently contain NaN or Infinity. The baseline and scenario use the same configured walking speed, including the estimate attached to a hypothetical connection. Scenario outputs include deterministic route comparisons, WGS84 GeoJSON, source provenance, and explicit warnings that the intervention is hypothetical.

Backend integration is ready at the Python-library boundary: the backend can call `acquire_osm_data`, `analyze_snapshot`/`analyze_area`, and `evaluate_scenario` without a FastAPI or LLM dependency. For persistent evaluations, the backend should store the source snapshot and its retrieval metadata under a stable `baseline_id`; persist the serialized analysis and scenario identifiers; and retain each response's `layer_availability`, warnings, provenance, and uncertainty. Persistence, request validation, and API response adaptation belong in the backend and are not implemented here.

The real bounded study run used `[27.5755, 47.1610, 27.5825, 47.1655]` in central Iași (EPSG:32635 working CRS). The retrieved snapshot produced 136 walking-graph nodes and 354 directed edges; 107 nodes were inside the study polygon. It returned 151 road features, 88 walking-infrastructure features, 17 crossing features, 275 buildings, 4 schools, 3 healthcare features, 9 other supported services, 3 public-transport features, 8 parking features, and 5 green-space features. No explicit cycling-infrastructure features were returned; that is not proof that none exist.

The same snapshot produced 105 of 107 in-area walking nodes within 15 estimated minutes of each of the supported school, healthcare, service, public-transport, and green-space feature groups. Median route detour ratios were 1.04 for schools, 1.31 for healthcare, 1.32 for services, 1.64 for public transport, and 1.41 for green space. Two graph components each contained one in-area node outside the largest component. These counts refer to mapped network nodes, not people.

A real-graph hypothetical connection between OSM nodes `641092475` and `12079937967` changed their calculated walking route from 648.7 m to 34.4 m (delta −614.3 m). This is a graph-only comparison; the connecting segment has not been checked for physical feasibility.

## SUMO

The existing portable discovery and TraCI smoke support in `sumo_support.py` is preserved. The engine exports a driving graph suitable for later conversion, but does not yet convert a real OSM graph into a SUMO network or claim calibrated traffic simulation. Any future synthetic vehicle demand must be labeled as synthetic and kept separate from graph-only accessibility results.
