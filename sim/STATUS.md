# Spatial analysis and simulation status

Updated: 2026-10-17

See [ARCHITECTURE.md](ARCHITECTURE.md) for SIM internals, [APPLICATION_INTEGRATION.md](APPLICATION_INTEGRATION.md) for the frontend/backend handoff, [README.md](README.md) for usage, and [AGENTS.md](AGENTS.md) for component instructions.

## Working

- Bounded Polygon, MultiPolygon, GeoJSON, GeoDataFrame, and bbox validation; 5 km² / 5 km defaults; metric UTM working CRS and WGS84 GeoJSON output.
- Independent cached OSMnx walking, cycling, and driving acquisition; partial mode success; explicit failures, availability, provenance, timestamps, and cache warnings.
- Graph normalization, connectivity, weighted routes, walking/cycling access estimates, deterministic evidence-backed issues, and GeoJSON analysis output.
- Isolated hypothetical pedestrian-link scenarios with endpoint snap checks, finite parameter validation, length constraints, Before/After route output, reachability changes, and baseline graph immutability.
- Neighborhood catalog API with 24 OSM-mapped polygons and 7 point-only records; area validation reuses the existing 5 km² / 5 km defaults and never infers point boundaries.
- Bounded deterministic pedestrian-link candidate discovery screens a 100-item opportunity pool before selecting the shortlist; material building crossings and endpoint-inside conflicts are excluded, while boundary/short/uncertain findings remain conditional.
- Deterministic common graph-node comparison samples plus separate bounded endpoint-component diagnostics; explicit route direction, independent baseline evaluations, and shared-sample-only ranking.
- A versioned machine-readable intervention catalog, deterministic bounded proposal evidence packet, and candidate-backed options; only supported graph edits are exposed and planning categories remain unclassified.
- Strict untrusted proposal validation checks candidate identity/action equivalence, coordinates, units, provenance claims, costs, observed metrics, simulation run IDs, physical-feasibility claims, and duplicates; JSON parsing never grants a validated status.
- Offline proposal demo can generate and validate candidates from a deterministic fixture or a read-only cached snapshot without network access or cloud API calls.
- Bounded SUMO preparation converts an existing directed driving graph into metric-coordinate plain XML, a source-ID map and WGS84 GeoJSON; deterministic synthetic OD routes have explicit bounds, seed, speed/lane defaults, and no OSM requests.
- New OSM graph/feature cache sidecars preserve the exact normalized source polygon and hash; legacy cache snapshots remain unchanged and unverifiable when their key differs and no hash exists.
- Offline/cached demo command exports JSON and GeoJSON without making an OSM network request.

## Neighborhood source and coverage

- `iasi-neighborhoods.geojson` contains 24 source-mapped polygons and 7 named point-only locations from a partial bounded OpenStreetMap Overpass query retrieved 2026-10-17.
- The source OSM object IDs, source URLs, retrieval/snapshot timestamps, tags, query bounds, uncertainty notes, attribution, and ODbL-1.0 terms are recorded in the catalog and [NEIGHBORHOODS_LICENSE.md](NEIGHBORHOODS_LICENSE.md).
- These place polygons are not verified legal or municipal boundaries. Coverage is partial; missing polygons are not inferred. The ignored raw response is not included in the repository. Reuse `load_neighborhood_catalog(path)` to import the checked-in GeoJSON.

## SIM v3 proposal verification

- Pre-change Windows/Python 3.12 baseline used the provisioned environment without installing dependencies: 65 passed (60 SIM and 5 project tests). The SIM v3 suite now passes 78 total tests (73 SIM and 5 project tests), including proposal validation and bounded SUMO preparation/accounting cases.
- Offline proposal demos generated a 48,022-byte fixture evidence packet and a 64,118-byte cached Iași packet; each produced 3 candidate-backed graph options, all 3 passed proposal validation, remained unclassified, and retained unknown physical feasibility.
- The cached Iași proposal demo used the existing graph without a network request and produced 3 calculated options. Its legacy sidecar has no matching geometry hash, so selected-area equivalence remains unverified and mapped-building no-hit evidence stays unknown.
- Final cached Iași SUMO preparation read a 40-node/78-directed-edge OSM driving graph, generated 20 deterministic routes with departures in the first 70% of the 180-second horizon, and wrote metric plain-XML inputs, source ID mapping, and WGS84 network GeoJSON. It used the 13.9 m/s speed and one-lane-per-direction fallbacks for 70 and 60 edges respectively; 18 edges used straight-line geometry fallbacks. It stopped at network conversion because netconvert is absent; SUMO vehicle execution and traffic measurements were not produced. The cached source-area equivalence is also unverified.

## Verification and CI coverage

- Local Windows/Python 3.12 regression run used the provisioned `.venv` without installing dependencies: `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=sim/.cache/pytest-v21-final tests sim/test_engine.py`: **65 passed** (60 SIM and 5 project tests).
- Final SIM v3 regression run: `.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider --basetemp=sim/.cache/pytest-v3-final-20261017b tests sim/test_engine.py`: **78 passed** (73 SIM and 5 project tests). Spatial smoke passed. SUMO discovery smoke skipped because the `sumo` and `netconvert` executables are absent; Python bindings are installed. Fixture and cached proposal demos passed validation for all 3 options each, and the cached Iași SUMO preparation produced all bounded input artifacts before reporting `unavailable` at network conversion.
- SIM v2.1 implementation commit `c6d9b66` passed [GitHub Actions PR run 39056468183](https://github.com/AlexPintilie08/arteria/actions/runs/39056468183): Windows x64 and macOS ARM64 jobs succeeded.
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
- Plain-XML conversion inputs and synthetic demand generation are implemented and offline-tested, but this Windows environment has neither netconvert nor sumo; no SUMO network was built and no vehicle simulation ran. Real traffic is uncalibrated and the available legacy cached Iași source area is unverified.
- `origin/master` proposal endpoints remain draft/precomputed. The separate `origin/feat/backend-api` adds a pedestrian graph-study API backed by pinned SIM v2.1 snapshot `752c92da9184effc9b87704e0868320f569454ea`; it does not consume these v3 proposal APIs or execute SUMO. SIM itself has no cloud provider, persistence, HTTP endpoint, or adapter to the shared TypeScript Alternative wire shape.
- The current workflow does not include a separate macOS Intel job; this revision was CI-verified on Windows x64 and macOS ARM64.
