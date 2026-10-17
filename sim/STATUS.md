# Spatial analysis and simulation status

Updated: 2026-10-17

## Working

- Bounded Polygon, MultiPolygon, GeoJSON, GeoDataFrame, and bbox validation; 5 km² / 5 km defaults; metric UTM working CRS and WGS84 GeoJSON output.
- Independent cached OSMnx acquisition for requested walking, cycling, and driving modes. Successful modes survive partial network or POI-query failures; failed modes have explicit availability and warnings; complete requested-network failure raises `OSMDataError`.
- Graph normalization, connected components, weighted routes, route detour ratios, mode-appropriate walking/cycling access estimates, stable evidence-backed connectivity/access/detour issues, and heatmap-ready GeoJSON.
- Isolated pedestrian-connection scenarios with endpoint snapping, finite-parameter and length validation, Before/After route calculations, reachability changes, baseline immutability, and consistent walking-speed assumptions.
- Offline simulation regression suite: 31 passed. Combined existing repository and simulation tests: 36 passed. Default `pytest -q` collected only 5 tests from `tests/`, confirming that it omits the simulation suite.

## Verification and CI coverage

- Local verification used `.venv/Scripts/python.exe` (Python 3.12) with no dependency installation. `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=sim/.cache/pytest-stabilization tests sim/test_engine.py`: 36 passed; `.venv/Scripts/python.exe -m pytest -q`: 5 passed and did not collect `sim/test_engine.py`.
- `.venv/Scripts/python.exe -m sim.smoke_test`: passed with NetworkX 3.7, OSMnx 2.1.1, GeoPandas 1.2.0, Shapely 2.2.0; deterministic route distance 200.0 m. `.venv/Scripts/python.exe scripts/health_smoke.py`: backend HTTP health passed.
- `.venv/Scripts/python.exe -m sim.sumo_support --smoke`: optional smoke skipped because SUMO and `netconvert` executables are not installed; `traci` and `sumolib` 1.28.0 are present. Command exited successfully with the documented skip.
- The prior PR checks passed on Windows, macOS ARM64, and macOS Intel, but they do not collect `sim/test_engine.py`. `pyproject.toml` selects only `tests/`, while `scripts/check.ps1` and `scripts/check.sh` invoke pytest without explicit paths.
- Proposed smallest shared fix: change both check scripts to run `pytest -q tests sim/test_engine.py`. No shared pytest configuration, scripts, or CI workflow files were modified because this milestone is limited to `sim/`.
- New-commit CI must be checked after publication; green CI does not establish simulation regression coverage until the shared test-selection gap is addressed.

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
