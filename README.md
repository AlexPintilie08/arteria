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

- **Frontend:** web with React, TypeScript, Next.js, MapLibre GL JS and WebGL; Android with Expo/React Native. Shared API contracts and visual tokens live inside `frontend/`.
- **Backend:** Python, FastAPI, Pydantic, and a cloud LLM API. Local Qwen may be an optional fallback.
- **Simulation and spatial analysis:** Python, OSMnx, NetworkX, GeoPandas, Shapely, Eclipse SUMO, and TraCI/libsumo.

The repository includes a runnable development foundation across frontend, backend, and simulation with cross-platform bootstrap scripts and comprehensive UI/UX capabilities.

## System architecture

The product has exactly three application components: `frontend/`, `backend/`, and `sim/`. The frontend presents the map and scenarios. The backend exposes the HTTP/JSON contract, prepares spatial context, coordinates recommendations and evaluations, and validates requests and responses. The `sim` component acquires and prepares geographic data, computes network indicators, applies virtual changes, and runs traffic simulation when appropriate. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/API_CONTRACT.md](docs/API_CONTRACT.md), and [api-specs/](api-specs/).

## Current status

The repository has a runnable development foundation: a Next.js/React/MapLibre shell with an OpenFreeMap public style and resilient offline fallback, a FastAPI `GET /health` endpoint, an operational standard library backend server (`backend/server.py`), and deterministic NetworkX/geospatial import checks. Local Windows setup and Windows, macOS 15 ARM64, and macOS 15 Intel CI jobs passed. SUMO 1.28.0 passed a real smoke test on Windows and macOS ARM64; no SUMO binary is installed on Intel macOS, where the optional fallback is reported. SUMO is optional and not required to start either service. See each component's `STATUS.md` and the [roadmap](docs/ROADMAP.md).

## Quick start

Prerequisites: Node.js 24 LTS and `uv`. Setup acquires a project-local, uv-managed Python 3.12 runtime, installs locked dependencies, and runs validation. No AI key or SUMO installation is needed for basic app startup.

| Platform | Setup once | Start both services | Checks |
| --- | --- | --- | --- |
| Windows 10/11 x64, PowerShell | `./scripts/setup.ps1` | `./scripts/dev.ps1` | `./scripts/check.ps1` |
| macOS, Terminal | `bash scripts/setup.sh` | `bash scripts/dev.sh` | `bash scripts/check.sh` |

Web interface is available at <http://localhost:3000> (presentation at `/`, workspace at `/app`). The API health response is at <http://127.0.0.1:8000/health>. The npm and Python lockfiles are committed; installed dependencies, `.venv`, and the uv-managed Python runtime stay local and ignored.

### Frontend direct commands

From `frontend/`:
```bash
npm ci
npm run dev        # Launches Next.js web app on http://localhost:3000
npm run check      # Full typecheck across workspaces + tests + build
npm run mobile     # Starts Expo React Native for Android
```

### Optional SUMO

The project pins the `eclipse-sumo` 1.28.0 package on Windows x64, Linux x64/ARM64, and macOS 15+ ARM64. That release does not publish a wheel for Intel Macs or older macOS versions. On those configurations, install SUMO using the [official platform instructions](https://sumo.dlr.de/docs/Installing/). SUMO discovery checks `PATH` and an optional `SUMO_HOME` value; it does not assume an installation directory. The check command runs a temporary one-step SUMO/TraCI scenario when a complete installation is found and reports unavailable or failed SUMO separately from the core app checks.

## Developer onboarding and collaboration

Three developers collaborate through one shared GitHub repository. Use feature branches when working concurrently, integrate frequently, communicate in short messages, and update the relevant component `STATUS.md` when meaningful work is completed. There are no permanent component owners or required project-management systems.

For an initial checkout, clone the repository and read this document, the architecture, API contract, roadmap, and the relevant component README and STATUS. Frontend setup and local web/Android commands are documented in [frontend/README.md](frontend/README.md).
