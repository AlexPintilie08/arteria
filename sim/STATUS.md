# Spatial analysis and simulation status

## Working

- Deterministic NetworkX graph smoke and OSMnx, GeoPandas, and Shapely import checks pass on Windows.
- SUMO 1.28.0, TraCI, and sumolib are pinned where binary wheels are published.
- Windows SUMO 1.28.0 passed a real synthetic network and TraCI simulation-step smoke test.

## In Progress

- macOS Apple Silicon and Intel dependency/CI verification is pending.

## Next

- Select and record a small Iași study area and source-data snapshot.
- Build a reproducible network preparation and one network indicator without SUMO.
- Add SUMO only after a defensible baseline demand scenario is available.

## Blockers

- No OSM acquisition or urban analysis exists. SUMO remains optional; unsupported macOS targets need the official installer fallback.
