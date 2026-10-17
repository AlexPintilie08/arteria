# Frontend

## Responsibilities

Present the map-focused urban planning experience: neighborhood selection, spatial indicators and heatmaps, AI proposal review, intervention controls, Before/After comparison, and SUMO simulation visualization or replay.

## Planned technology

React, TypeScript, Vite, MapLibre GL JS, and WebGL. Tailwind CSS is optional and should be used only if it supports the visual system. The intended direction is premium, dark, elegant, fluid, and map-focused rather than a generic AI dashboard.

## Inputs and outputs

- **Inputs:** geographic area identifiers, analysis responses, provenance and uncertainty metadata, validated intervention proposals, and evaluation results from the backend API.
- **Outputs:** user-selected areas, analysis parameters, proposal requests, intervention selections, and evaluation requests. The frontend must label data as observed, calculated, estimated, or unknown and must not imply that a replay is a live simulation.

## Integration interfaces

Use the JSON interfaces in `docs/API_CONTRACT.md`: `POST /analyze`, `POST /propose`, and `POST /evaluate`. Keep backend communication behind typed client functions so UI state is not coupled to transport details.

## Implementation objectives

Build one coherent end-to-end scenario on a reusable map and geographic selection model. Show the source and status of each indicator, make assumptions inspectable, and support baseline-versus-scenario comparison. Preserve usable behavior when an optional data layer is unavailable.

## Technical risks

Large vector layers and 3D rendering can hurt performance; use bounded areas and progressive layer loading. Map projections and geometry validity can cause selection and display errors. Data gaps must not be presented as zero values. API uncertainty and provenance need consistent visual treatment. Simulation replay must be distinguished from newly computed simulation results.
