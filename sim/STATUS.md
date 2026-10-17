# Spatial analysis and simulation status

Updated: 2026-10-17

## Working

- Bounded Polygon, MultiPolygon, GeoJSON, GeoDataFrame, and bbox validation; 5 km² / 5 km defaults; metric UTM working CRS and WGS84 GeoJSON output.
- Independent cached OSMnx acquisition for requested walking, cycling, and driving modes. Successful modes survive partial network or POI-query failures; failed modes have explicit availability and warnings; complete requested-network failure raises `OSMDataError`.
- Graph normalization, connected components, weighted routes, route detour ratios, mode-appropriate walking/cycling access estimates, stable evidence-backed connectivity/access/detour issues, and heatmap-ready GeoJSON.
- Isolated pedestrian-connection scenarios with endpoint snapping, finite-parameter and length validation, Before/After route calculations, reachability changes, baseline immutability, and consistent walking-speed assumptions.
- Offline simulation regression suite: 31 passed. The standard project check now explicitly runs `tests` and `sim/test_engine.py`; the combined suite contains 36 tests (5 existing project tests and 31 simulation tests).

## Verification and CI coverage

- Local verification used `.venv/Scripts/python.exe` (Python 3.12) with no dependency installation. `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=sim/.cache/pytest-stabilization tests sim/test_engine.py`: 36 passed. The current Windows environment does not have `uv`; the standard `check.ps1` and `check.sh` scripts were syntax-checked, and the backend HTTP health smoke passed.
- `.venv/Scripts/python.exe -m sim.smoke_test`: passed with NetworkX 3.7, OSMnx 2.1.1, GeoPandas 1.2.0, Shapely 2.2.0; deterministic route distance 200.0 m. `.venv/Scripts/python.exe scripts/health_smoke.py`: backend HTTP health passed.
- Local `.venv/Scripts/python.exe -m sim.sumo_support --smoke` skipped because SUMO and `netconvert` are not installed locally; `traci` and `sumolib` 1.28.0 are present. GitHub Actions installed SUMO 1.28.0 on both supported runners and the synthetic TraCI smoke advanced to 1 s successfully. This validates the small synthetic smoke only, not real-area network conversion or calibrated traffic simulation.
- GitHub Actions run [39044641288](https://github.com/AlexPintilie08/arteria/actions/runs/39044641288), for CI commit `55b26a0a17245a77ee8f95c429083b2c9300f801`, passed on `windows-latest` and `macos-15`. Logs reported Windows `RUNNER_ARCH=X64` and macOS `RUNNER_ARCH=ARM64`, `uname -m=arm64`; both jobs passed all 36 tests, backend health, frontend TypeScript checking and production build, and SUMO smoke. The macOS result is ARM64 runner coverage and does not establish direct Apple M5 hardware validation.
- CI now targets Windows x64 and macOS Apple Silicon only. The workflow asserts each runner's architecture, and both standard check scripts explicitly run `uv run --locked pytest -q tests sim/test_engine.py`; the existing five project tests and all 31 simulation regression tests are included. `pyproject.toml` remains unchanged.
- GitHub annotated possible longer queue times for macOS ARM64 runners due to capacity. Both frontend production builds also emitted a non-blocking Vite code-splitting/chunk-size advisory; the builds passed. No blocking integration warnings remained in the verified run.

## Verified real Iași snapshot

Area: `[27.5755, 47.1610, 27.5825, 47.1655]` (central Iași, about 0.26 km²); working CRS EPSG:32635. The previously retrieved snapshot remains cached locally under the ignored `sim/.cache/osm/` directory. This stabilization reused the recorded results and performed no new live OSM download.

- Walking graph: 136 nodes, 354 directed edges, 3 weak components, 131 nodes in the largest component; 107 graph nodes lie inside the study polygon.
- Driving graph: 40 nodes, 78 directed edges, 1 weak component; 24 graph nodes lie inside the study polygon.
- Returned tagged features: 151 roads, 88 walking-infrastructure features, 17 crossings, 275 buildings, 4 schools, 3 healthcare features, 9 supported services, 3 public-transport features, 8 parking features, and 5 green-space features. No explicit cycling-infrastructure features were returned; that does not establish absence.
- At the configured 15-minute / 1.3 m/s walking assumption, 105 of 107 in-area graph nodes are within threshold for each analyzed target group. Median route detour ratios: schools 1.04, healthcare 1.31, services 1.32, public transport 1.64, green space 1.41. Metrics refer to mapped graph nodes, not residents.
- The earlier graph-only intervention between OSM nodes `641092475` and `12079937967` reduced the calculated route from 648.7 m to 34.4 m (delta −614.3 m). No construction feasibility was assessed.
- A live cycling graph was not verified; the previous bounded request was slow and was stopped. The default Overpass endpoint previously returned a capacity-related 502 for some requests; an alternate endpoint supplied the earlier feature snapshot.

## Backend readiness

The library boundary is ready for backend integration: its acquisition, analysis, and scenario functions remain independent from FastAPI and LLM implementations. The backend should assign and persist stable baseline IDs and serialized snapshots, then retain provenance, coverage, warnings, uncertainty, and scenario identifiers with each evaluation. API adaptation and persistence are outside `sim/`.

## Limitations

- OSM geometry, tags, and coverage are incomplete and change over time. Empty layers remain unknown rather than proof of nonexistence.
- Walking/cycling travel times use constant speed assumptions. Population, congestion, observed traffic volumes, and real-time conditions are not inferred.
- Interventions are hypothetical graph links; physical safety, grade, legal status, ownership, and buildability are outside the model.
- SUMO discovery and optional TraCI smoke support are preserved. Real-area network conversion and calibrated traffic simulation are not implemented.
- The `uv` executable is not available in this Windows environment. The existing compatible `.venv` was used without installing dependencies.
