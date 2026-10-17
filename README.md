# ARTERIA by ARION

**Understand the city. Shape its future.**

ARTERIA is an AI-assisted urban planning and mobility analysis platform. It helps people examine neighborhoods, identify mobility and infrastructure problems, compare intervention options, and evaluate measurable effects before physical implementation. Iași, Romania is the first supported city; the product is intended to work across its neighborhoods rather than remain tied to one demonstration site.

## Product workflow

1. Explore Iași in an interactive 2.5D/3D map.
2. Select a neighborhood or other supported geographic area.
3. Inspect roads, buildings, places, walking and cycling networks, public transport, parking, and green space where data is available.
4. Review detected issues, heatmaps, indicators, and their data provenance.
5. Request structured minimal, moderate, and transformative intervention options for a selected issue.
6. Validate and apply a supported intervention in a virtual scenario.
7. Recalculate geographic indicators and run a traffic simulation when the scenario and data justify it.
8. Compare baseline and intervention conditions with maps, metrics, visualizations, and transparent assumptions.

Observed data, calculated results, estimates, and unknown information must remain distinguishable throughout the product. An AI recommendation is a proposal, not a measurement: it must pass intervention-type and geographic constraint checks. An LLM must never invent simulation output.

## Planned technology

- **Frontend:** React, TypeScript, Vite, MapLibre GL JS, WebGL, and Tailwind CSS if useful.
- **Backend:** Python, FastAPI, Pydantic, and a cloud LLM API. Local Qwen may be an optional fallback.
- **Simulation and spatial analysis:** Python, OSMnx, NetworkX, GeoPandas, Shapely, Eclipse SUMO, and TraCI/libsumo.

These are planned choices. No application functionality has been implemented yet.

## System architecture

The product has exactly three application components: `frontend/`, `backend/`, and `sim/`. The frontend presents the map and scenarios. The backend exposes the HTTP/JSON contract, prepares spatial context, coordinates recommendations and evaluations, and validates requests and responses. The `sim` component acquires and prepares geographic data, computes network indicators, applies virtual changes, and runs traffic simulation when appropriate. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/API_CONTRACT.md](docs/API_CONTRACT.md).

## Current status

**Documentation-only initialization.** The directory and architecture are defined, but there are no application endpoints, UI, data pipelines, or simulations. See each component's `STATUS.md` and the [roadmap](docs/ROADMAP.md) for the proposed sequence.

## Developer onboarding and collaboration

Three developers collaborate through one shared GitHub repository. Use feature branches when working concurrently, integrate frequently, communicate in short messages, and update the relevant component `STATUS.md` when meaningful work is completed. There are no permanent component owners or required project-management systems.

For an initial checkout, clone the repository and read this document, the architecture, API contract, roadmap, and the relevant component README and STATUS. Implementation setup instructions will be added when the first code is introduced. This initialization does not install dependencies or start services.
