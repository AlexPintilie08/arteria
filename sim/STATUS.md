# Spatial analysis and simulation status

Updated: 2026-10-17

See [ARCHITECTURE.md](ARCHITECTURE.md) for implementation and integration details, [README.md](README.md) for usage, and [AGENTS.md](AGENTS.md) for component instructions.

## Working

- Bounded Polygon, MultiPolygon, GeoJSON, GeoDataFrame, and bbox validation; 5 km² / 5 km defaults; metric UTM working CRS and WGS84 GeoJSON output.
- Independent cached OSMnx walking, cycling, and driving acquisition; partial mode success; explicit failures, availability, provenance, timestamps, and cache warnings.
- Graph normalization, connectivity, weighted routes, walking/cycling access estimates, deterministic evidence-backed issues, and GeoJSON analysis output.
- Isolated hypothetical pedestrian-link scenarios with endpoint snap checks, finite parameter validation, length constraints, Before/After route output, reachability changes, and baseline graph immutability.
- Neighborhood catalog API with 24 OSM-mapped polygons and 7 point-only records; area validation reuses the existing 5 km² / 5 km defaults and never infers point boundaries.
- Bounded deterministic pedestrian-link candidate discovery from component gaps, directed reachability gaps, and high route detours; mapped building intersections are warnings, and physical feasibility remains unknown.
- Deterministic graph-node route sampling; multi-route Before/After outcomes and aggregates; independent candidate evaluation; explicit lexicographic ranking; bounded route geometry.
- Offline/cached demo command exports JSON and GeoJSON without making an OSM network request.

## Neighborhood source and coverage

- `iasi-neighborhoods.geojson` contains 24 source-mapped polygons and 7 named point-only locations from a partial bounded OpenStreetMap Overpass query retrieved 2026-10-17.
- The source OSM object IDs, source URLs, retrieval/snapshot timestamps, tags, query bounds, uncertainty notes, attribution, and ODbL-1.0 terms are recorded in the catalog and [NEIGHBORHOODS_LICENSE.md](NEIGHBORHOODS_LICENSE.md).
- These place polygons are not verified legal or municipal boundaries. Coverage is partial; missing polygons are not inferred. The ignored raw response is not included in the repository. Reuse `load_neighborhood_catalog(path)` to import the checked-in GeoJSON.

## Verification and CI coverage

- Local Windows/Python 3.12 regression run used the provisioned `.venv` without installing dependencies: `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=sim/.cache/pytest-v2-p0 tests sim/test_engine.py`: **59 passed** (54 SIM and 5 project tests).
- The run covers catalog import/validation, point-only and oversized boundaries, bounded candidate discovery and obstacle warnings, deterministic route sampling, multiple outcome classes, aggregate calculations, geometry caps, baseline immutability, independent alternatives, and stable ranking alongside the existing regressions.
- Cached OSM demo: `.venv/Scripts/python.exe -m sim.demo --source cache` used the local 136-node walking graph and made no network request. It returned 3 graph candidates and evaluated 32 sampled graph-node pairs per candidate. Each result had 1 newly reachable, 30 unchanged, 1 unreachable in both, 0 improved/regressed, and 0 m savings among comparable routes. The 3 candidate lines each intersected 5 mapped building geometries; each requires field verification. The cache key did not match the current demo-area key and the sidecar lacks the original polygon, so boundary equivalence is unverified.
- Offline fixture demo: `python -m sim.demo --source fixture` used 7 synthetic graph nodes, returned 3 candidates, and evaluated 18 pairs per candidate without network requests.
- V2 implementation commit `a3075c3` passed [GitHub Actions run 39051501061](https://github.com/AlexPintilie08/arteria/actions/runs/39051501061): Windows x64 and macOS 15 ARM64 each ran all 59 tests, plus the existing backend HTTP and synthetic SUMO smoke checks.
- The `uv` executable is not available in the current Windows environment. Tests use the existing `.venv`; no dependency installation was performed. The SUMO synthetic smoke and earlier platform CI checks do not establish real-area SUMO behavior.

## Backend readiness

Package-root imports now expose catalog loading/selection/validation, candidate discovery, route sampling, multi-route impact evaluation, and candidate ranking. The functions remain independent from FastAPI and cloud AI libraries. The backend still owns HTTP adaptation, authorization, persistence, and stable baseline IDs; numerical SIM results must remain attributable to the snapshot and sample settings.

## Limitations and remaining work

- OSM geometry, tags, and coverage are incomplete and change over time. Empty layers are not proof of real-world absence.
- Candidate lines are hypothetical. Mapped-building intersections are reported; water barriers are not currently acquired. Ownership, access rights, legal status, grade/slope, field safety, accessibility standards, and construction feasibility remain unknown.
- Route samples are graph-node pairs, not observed trips or a statistically representative sample. Counts are not extrapolated to residents.
- Walking/cycling times use constant-speed assumptions. Population, congestion, observed traffic volumes, and real-time conditions are not inferred.
- Real-area OSM-to-SUMO conversion and synthetic vehicle demand are not implemented. Only the existing optional synthetic TraCI smoke is supported.
- The current workflow does not include a separate macOS Intel job; this revision was CI-verified on Windows x64 and macOS ARM64.
