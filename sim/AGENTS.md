# SIM Agent Instructions

These instructions apply to work owned by `sim/`. Repository-level instructions take precedence. Read [ARCHITECTURE.md](ARCHITECTURE.md) for implementation details, [README.md](README.md) for usage, and [STATUS.md](STATUS.md) for verified capability and limitations.

## Ownership and boundaries

- SIM owns the version-controlled Python/geospatial component under `sim/`.
- Do not modify frontend or backend code without authorization. Backend may import SIM, but currently exposes only `GET /health`; HTTP orchestration and persistence belong to backend owners.
- Coordinate before changing shared dependencies or root CI/configuration.
- Keep changes within requested scope. Do not treat ignored cache data, browser previews, bytecode, or virtual environments as source to publish.

## Runtime and platform

- Use Python `>=3.12,<3.13`, as declared in root `pyproject.toml`.
- Runtime stack: OSMnx, GeoPandas, NetworkX, Shapely, and pyproj. SUMO is optional; analysis does not require its binaries.
- Current CI verifies Windows x64 and macOS Apple Silicon ARM64. Do not claim macOS Intel verification from this workflow.

## Public entry points

Import supported APIs from `sim`: existing acquisition/analysis/scenario functions plus `load_neighborhood_catalog`, `get_neighborhoods`, `get_neighborhood`, `search_neighborhoods`, `neighborhoods_geojson`, `validate_neighborhood_boundary`, `neighborhood_area_input`, `discover_intervention_candidates`, `sample_route_pairs`, `evaluate_multi_route_impact`, and `evaluate_candidates`. Package-root types include `StudyArea`, `OSMData`, `AreaValidationError`, `OSMDataError`, `InterventionError`, and `NeighborhoodCatalogError`. `RouteError` is available from `sim.analysis`, not the package root. Exact signatures and output fields are in [ARCHITECTURE.md](ARCHITECTURE.md) and [README.md](README.md).

## Geographic and evidence conventions
New package-root APIs include `get_intervention_catalog`, `build_proposal_context`, `prepare_candidate_options`, `validate_proposal`, `validate_proposal_set`, `load_cached_driving_snapshot`, `prepare_sumo_network`, `run_real_area_simulation`, `get_driving_intervention_catalog`, and `evaluate_driving_scenario`; `SumoPreparationError` is a package-root type. `acquire_osm_data` has a bounded `feature_categories` selector. See [INTEGRATION_CONTRACT_V4.md](INTEGRATION_CONTRACT_V4.md) for exact signatures and result fields. Proposal validation is not physical feasibility validation. SUMO demand is synthetic; real-area baseline/paired runners require local `netconvert` and `sumo` binaries and never download OSM.


- Bbox values are `[west, south, east, north]`; GeoJSON uses `[longitude, latitude]` in EPSG:4326. Keep calculations in `StudyArea.working_crs` and serialize output back to WGS84.
- Preserve OSM IDs, retrieval metadata, coverage, uncertainty, warnings, and units.
- Do not fabricate geographic observations. An empty or failed OSM layer does not establish real-world absence; preserve `unknown` and `no_features_returned` semantics.
- Network-node counts are not population counts. Weighted graph routes and constant-speed times are calculations, not observed journeys.
- Do not confuse graph access/connectivity with observed traffic or traffic simulation.
- A virtual pedestrian link is a hypothetical graph edge. Do not describe it as physically feasible or approved infrastructure.
- The tracked Iași neighborhood catalog is partial OpenStreetMap place data under ODbL-1.0. Its place polygons are not verified municipal/legal boundaries; point-only records never imply polygons.
- Automatic candidate scores and sampled graph-node route counts describe the network snapshot only. They are not observed trips, resident impact, construction cost, or feasibility evidence.

## Cache and tests

- Default snapshots and OSMnx HTTP responses are local under ignored `sim/.cache/osm/`; the optional preview is under ignored `sim/.cache/local_demo/`. Respect OSM/Overpass usage policies and source provenance.
- Acquisition temporarily changes OSMnx process settings under a lock and restores them; preserve this protection.
- Regression suite: `uv run --locked pytest -q tests sim/test_engine.py` in the standard project environment. Tests use offline fixtures and mocks. Since `uv run` may create/sync an environment when none exists, if installation is not authorized, invoke pytest with an already provisioned interpreter (Windows: `.venv/Scripts/python.exe -m pytest -q tests sim/test_engine.py`).
- Lightweight smoke: `python -m sim.smoke_test`. Optional tool check: `python -m sim.sumo_support --smoke`; missing SUMO is reported as a skip. It tests a synthetic network, not Iași.

## Change and Git rules

- Inspect status and diffs before editing; preserve the working tree. Never use destructive commands such as reset, clean, checkout/restore of user work, or force push.
- Do not modify production algorithms during documentation-only work. Do not switch to or modify `main`, merge a PR, or publish without explicit authorization.
- Do not change shared dependencies without coordination.
- When source behavior changes, update relevant architecture and status documentation. Keep README focused on setup/use, ARCHITECTURE on internals/contracts, STATUS on verified capability/limitations, and these instructions on agent workflow.
- Validate documented signatures, examples, paths, and relative links. Separate implemented, experimental/local-only, and planned capabilities.
