# Spatial analysis and simulation status

## Working

- Deterministic NetworkX graph smoke and OSMnx, GeoPandas, and Shapely import checks pass on Windows and macOS 15 ARM64/Intel CI.
- SUMO 1.28.0, TraCI, and sumolib are pinned where binary wheels are published.
- Windows and macOS 15 ARM64 SUMO 1.28.0 passed a real synthetic network and TraCI simulation-step smoke test.
- macOS 15 Intel CI correctly reported no installed SUMO binary; setup and core checks still passed.

## In Progress

- No active changes.

## Next

- Select and record a small Iași study area and source-data snapshot.
- Build a reproducible network preparation and one network indicator without SUMO.
- Add SUMO only after a defensible baseline demand scenario is available.

## Blockers

- No bootstrap blockers. OSM acquisition and urban analysis remain future work. Intel and older macOS SUMO users need the official installer fallback.
