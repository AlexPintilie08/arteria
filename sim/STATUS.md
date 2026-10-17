# Spatial analysis and simulation status

Updated: 2026-10-17

See [ARCHITECTURE.md](ARCHITECTURE.md) for implementation and integration details, [README.md](README.md) for usage, and [AGENTS.md](AGENTS.md) for component instructions.

## Working

- Bounded Polygon, MultiPolygon, GeoJSON, GeoDataFrame, and bbox validation; 5 km² / 5 km defaults; metric UTM working CRS and WGS84 GeoJSON output.
- Independent cached OSMnx walking, cycling, and driving acquisition; partial mode success; explicit failures, availability, provenance, timestamps, and cache warnings.
- Graph normalization, connectivity, weighted routes, walking/cycling access estimates, deterministic evidence-backed issues, and GeoJSON analysis output.
- Isolated hypothetical pedestrian-link scenarios with endpoint snap checks, finite parameter validation, length constraints, Before/After route output, reachability changes, and baseline graph immutability.
- Neighborhood catalog API with 24 OSM-mapped polygons and 7 point-only records; area validation reuses the existing 5 km² / 5 km defaults and never infers point boundaries.
- Bounded deterministic pedestrian-link candidate discovery screens a 100-item opportunity pool before selecting the shortlist; material building crossings and endpoint-inside conflicts are excluded, while boundary/short/uncertain findings remain conditional.
- Deterministic common graph-node comparison samples plus separate bounded endpoint-component diagnostics; explicit route direction, independent baseline evaluations, and shared-sample-only ranking.
- New OSM graph/feature cache sidecars preserve the exact normalized source polygon and hash; legacy cache snapshots remain unchanged and unverifiable when their key differs and no hash exists.
- Offline/cached demo command exports JSON and GeoJSON without making an OSM network request.

## Neighborhood source and coverage

- `iasi-neighborhoods.geojson` contains 24 source-mapped polygons and 7 named point-only locations from a partial bounded OpenStreetMap Overpass query retrieved 2026-10-17.
- The source OSM object IDs, source URLs, retrieval/snapshot timestamps, tags, query bounds, uncertainty notes, attribution, and ODbL-1.0 terms are recorded in the catalog and [NEIGHBORHOODS_LICENSE.md](NEIGHBORHOODS_LICENSE.md).
- These place polygons are not verified legal or municipal boundaries. Coverage is partial; missing polygons are not inferred. The ignored raw response is not included in the repository. Reuse `load_neighborhood_catalog(path)` to import the checked-in GeoJSON.

## Verification and CI coverage

- Local Windows/Python 3.12 regression run used the provisioned `.venv` without installing dependencies: `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=sim/.cache/pytest-v21-final tests sim/test_engine.py`: **65 passed** (60 SIM and 5 project tests).
- Coverage includes taxonomy for interior/endpoint/boundary/short overlap, duplicate OSM identity, MultiPolygon and nonpolygon geometry, source-area uncertainty, pool screening before shortlist, honest empty results, sidecar source geometry/hash, oriented route pairs, targeted diagnostics, and baseline-independent shared ranking.
- Cached Iași demo used the existing 136-node walking graph (107 nodes in area) and made no network request. It generated 273 raw opportunities, deduplicated 200, screened the bounded first 100, rejected 84 material mapped-building conflicts, and retained 16 conditional candidates. The final three include 74.1 m and 134.3 m bridges plus a 17.0 m same-component detour link. Both component bridges produce 1 newly reachable pair in the shared 32-pair sample (30 unchanged, 1 unreachable in both, 0 m comparable savings) and 16 newly reachable local diagnostic pairs apiece. The local sample is candidate-specific and does not affect ranking.
- Root cause of the prior weak shortlist: discovery generated 273 opportunities but truncated to three before obstacle checks. Its issue-proximity count (within 100 m of summary geometry) affected ordering. All three old links joined the same 3-node weak component to the 131-node component and each crossed five valid building polygons; the crossings totalled eight unique OSM IDs. The 30 already-reachable pairs in the shared sample were unchanged, so no comparable savings were present; only one sampled pair became reachable. The engine now checks a wider pool first, does not rank on proximity-only issue counts, and leaves the two newly surfaced bridges' no-hit building status unknown because the historical cache sidecar cannot verify its source area.
- Offline fixture demo used 7 synthetic graph nodes and made no network request. It returned 3 conditional candidates with separate local diagnostics; synthetic results do not describe Iași.
- V2 implementation commit `a3075c3` passed [GitHub Actions run 39051501061](https://github.com/AlexPintilie08/arteria/actions/runs/39051501061): Windows x64 and macOS 15 ARM64 each ran all 59 tests, plus the existing backend HTTP and synthetic SUMO smoke checks.
- The `uv` executable is not available in the current Windows environment. Tests use the existing `.venv`; no dependency installation was performed. The SUMO synthetic smoke and earlier platform CI checks do not establish real-area SUMO behavior.

## Backend readiness

Package-root imports now expose catalog loading/selection/validation, candidate discovery, route sampling, multi-route impact evaluation, and candidate ranking. The functions remain independent from FastAPI and cloud AI libraries. The backend still owns HTTP adaptation, authorization, persistence, and stable baseline IDs; numerical SIM results must remain attributable to the snapshot and sample settings.

## Limitations and remaining work

- OSM geometry, tags, and coverage are incomplete and change over time. Empty layers are not proof of real-world absence.
- Candidate lines remain conditional. Mapped material building conflicts are filtered from the eligible shortlist; historical cache uncertainty, water/barrier coverage (not acquired), ownership, access rights, legal status, grade/slope, field safety, accessibility standards, and construction feasibility remain unknown. Small-component links can reflect graph or boundary artifacts and need source-data review.
- Route samples are graph-node pairs, not observed trips or a statistically representative sample. Counts are not extrapolated to residents.
- Walking/cycling times use constant-speed assumptions. Population, congestion, observed traffic volumes, and real-time conditions are not inferred.
- Real-area OSM-to-SUMO conversion and synthetic vehicle demand are not implemented. Only the existing optional synthetic TraCI smoke is supported.
- The current workflow does not include a separate macOS Intel job; this revision was CI-verified on Windows x64 and macOS ARM64.
