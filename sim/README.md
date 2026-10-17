# Spatial analysis and simulation

## Current foundation

The repository includes a deterministic NetworkX smoke test and verifies OSMnx, GeoPandas, and Shapely imports. It does not download OSM data or implement city analysis yet.

## Responsibilities

Acquire and prepare OpenStreetMap data; construct geographic networks; calculate accessibility and connectivity; detect mobility issues; apply virtual infrastructure modifications; recompute measurable indicators; and run microscopic vehicle simulation for suitable traffic scenarios.

## Planned technology

Python, OSMnx, NetworkX, GeoPandas, Shapely, Eclipse SUMO, and TraCI/libsumo. Network and geographic analysis must work independently of SUMO. SUMO runs on CPU and is used only where traffic questions and available inputs justify it.

## Inputs and outputs

- **Inputs:** bounded geographic areas, versioned source data, analysis parameters, baseline networks, and validated virtual intervention definitions.
- **Outputs:** network-derived indicators, detected issues, modified scenario networks, evaluation measurements, and simulation run metadata. Each result should include units, source/version, method, timestamp, and uncertainty or limitations where known.

## Integration interfaces

The backend coordinates this component for the API operations in `docs/API_CONTRACT.md`. The initial implementation may use an in-process Python interface; a service boundary can be introduced when independent scaling or deployment requires it. Avoid coupling the frontend to simulation file formats.

## Implementation objectives

Make geographic analysis useful without SUMO. Preserve baseline inputs and create scenario variants rather than mutating source networks. Track data acquisition and processing versions for reproducibility. Support small live simulations for responsive demonstrations and reproducible offline simulations for controlled comparisons.

## Simulation modes and honest replay labels

- **Small live simulation:** run a bounded scenario with the CPU simulator during a user-requested evaluation; return the actual run status, configuration, and computed measurements.
- **Reproducible offline simulation:** execute a versioned scenario with fixed inputs, configuration, random seed where applicable, and recorded tool versions; store enough metadata to rerun it.
- **Replay:** display previously recorded output. Label it as a replay and show its run identifier and timestamp. A replay is not a new simulation and must not be described as one.

Geographic measures such as connectivity or network access can be recomputed without claiming a SUMO result. If required inputs or simulator execution are unavailable, report that clearly.

## Portable SUMO installation

`pyproject.toml` pins `eclipse-sumo`, `traci`, and `sumolib` to 1.28.0 where the binary wheel is published: Windows x64, Linux x64/ARM64, and macOS 15+ ARM64. On macOS, the wheel is ARM64-only and requires macOS 15 or newer. Intel Macs and older macOS versions can use the [official SUMO installers](https://sumo.dlr.de/docs/Installing/); SUMO is optional for setup and app startup. Discovery checks executable names on `PATH` and searches an explicitly provided `SUMO_HOME` root for `sumo` and `netconvert`; it does not hardcode an installation path.

Run `uv run --locked python -m sim.sumo_support --smoke` to inspect executable and Python package versions and, when available, build a temporary network and advance a real SUMO simulation through TraCI. SUMO is only marked verified when that smoke test passes. The temporary scenario is removed after the check.

## Technical risks

OSM coverage, tags, and update dates vary by area. Coordinate reference systems, topology repair, and network simplification affect measurements. SUMO requires defensible demand and calibration; uncalibrated traffic output is scenario-specific and uncertain. Data licensing, download size, CPU time, and reproducibility need explicit handling.
