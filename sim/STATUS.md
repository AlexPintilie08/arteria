# Spatial analysis and simulation status

## Working

- Deterministic NetworkX graph smoke and OSMnx, GeoPandas, and Shapely import checks pass on Windows and macOS 15 ARM64/Intel CI.
- SUMO 1.28.0, TraCI, and sumolib are pinned where binary wheels are published.
- Windows and macOS 15 ARM64 SUMO 1.28.0 passed a real synthetic network and TraCI simulation-step smoke test via `sim/sumo_support.py`.
- macOS 15 Intel CI correctly reported no installed SUMO binary; setup and core checks still passed.
- Deterministic traffic capacity and delay models operational for Iași study corridors:
  - Webster signal delay model on unsynchronized signal phases (e.g. Podu Roș multi-leg junction).
  - Hydraulic flow capacity model for roundabout and turbo-roundabout configurations.
  - Topological route continuity and conflict-point density calculation for walking/cycling networks.
  - Epistemic tracking: observed sensor baselines (inductive loops, ANPR) strictly distinguished from calculated network values.
- Podu Roș multi-leg corridor dataset integrated with flow rates, queue lengths, and LOS classifications.
- Frontend Dynamic Coupling: Real-time recalculation of delay, queue length, and flow rate in the web comparison matrix driven by user parameter tuning (`greenPhaseSec`, `ctpPriority`, `laneWidthM`).
- Simulation Contract Authored: `api-specs/simulation-engine-contract.md` specifying SUMO TraCI micro-simulation runner, Server-Sent Events (SSE) telemetry stream, and analytical fallbacks.

## In Progress

- OSMnx automated graph preparation script for dynamic boundary imports.
- Synthetic demand profile generation for morning and evening peak hours.

## Next

- Optional SUMO TraCI micro-simulation runner for specific junction geometry reconfigurations.
- Export of evaluated network graphs to standard GeoJSON format.

## Blockers

- Microscopic SUMO runs require calibrated OD matrices; deterministic analytical models serve as the reliable primary path. Intel and older macOS SUMO users need the official installer fallback.
