# ARTERIA frontend

## Connected backend flow

`/app` now defaults to the FastAPI-connected workspace. It calls analyze → propose
→ evaluate and renders returned evidence, IDs, interventions and comparisons. A
separate pedestrian panel uses the graph API. The original visual fixture preview
is retained only when `NEXT_PUBLIC_DEMO_MODE=true`; it is never a failure fallback.

Run the backend from the repository root:

```sh
python3 -m uv run --locked uvicorn backend.main:app --reload --port 8000
```

Then, in another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open http://localhost:3000/app. Defaults: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
and `NEXT_PUBLIC_DEMO_MODE=false`. Override in `frontend/web/.env.local` and restart
Next.js. If backend CORS is overridden, include `http://localhost:3000`.

Connected traffic data is explicitly synthetic. Area names are bookmarks, not
certified boundaries. The timing slider requests a new validated proposal before
evaluation. CTP priority, lane width and structural projects are not exposed as
supported controls. Changing area/layers/issue/timing invalidates downstream results.

For the optional pedestrian panel, first run `python3 -m uv run --locked python -m
backend.prepare_sim` from the repository root (as a single command). It uses a
synthetic offline graph and displays saved graph comparisons, never a SUMO run.
See [backend integration](../backend/FRONTEND_HANDOFF.md).

Checks: `npm run typecheck`, `npm test`, `npm run build`. Browser test against both
running services: `node shared/tests/backend-flow.cjs` with Playwright installed,
or set `PLAYWRIGHT_MODULE` to an external Playwright module path. It uses Chrome
by default. `browser-smoke.cjs` remains a check for explicit fixture-preview mode.


## Baza implementată

Două aplicații separate: `web` pentru prezentare și produsul în browser, `mobile` pentru Android. `shared` conține doar codul reutilizat de ambele. O singură instalare npm și un singur lockfile în acest director.

```text
frontend/
  web/          React + Next.js: prezentare la /, produs la /app
  mobile/       aplicație Android React Native + Expo
  shared/       contracte API, client HTTP, tokenuri și teste
```

Vezi și instrucțiunile separate pentru [site](web/README.md) și [Android](mobile/README.md).

Din `frontend`, cu Node 22.12+ sau Node 24:

```powershell
npm ci
npm run dev
```

Prezentare: `http://localhost:3000`. Produs web: `http://localhost:3000/app`. Pentru Expo: `npm run mobile`; pentru emulator/dispozitiv Android disponibil: `npm run android`. Comenzile se rulează din `frontend`.

```powershell
npm run check
npm run export:android --workspace @arteria/mobile
```

- [Prompt complet pentru AI](../docs/frontend/AI_INTERFACE_PROMPT.md) — gata de copiat pentru implementarea întregii interfețe.
- [Brief vizual premium](../docs/frontend/DESIGN_BRIEF.md) — direcție, tokenuri, referințe și criterii de calitate.
- [Structură și integrare](../docs/frontend/IMPLEMENTATION.md) — setup, API, hartă, Android și limitări.

Aceasta este o structură inițială cu ecrane de bază. Harta web necesită un stil configurat în `.env`; harta Android este un placeholder explicit. Preview-ul nu inventează rezultate. Propunerile și comparațiile sunt puncte de extindere, fără integrare backend. Vezi [STATUS](STATUS.md).

## Current foundation

The app starts with a React/TypeScript shell, a MapLibre 2.5D map centered on Iași, a backend liveness indicator, and a clear fallback if the public map style cannot load. The style is `https://tiles.openfreemap.org/styles/dark`; OpenFreeMap identifies its project license as MIT, allows commercial use, and requires map attribution, which MapLibre displays automatically. The service is provided as-is without an SLA. Urban layers, neighborhood selection, and analysis are not implemented.

Install with `npm ci` from this directory, then run `npm run dev`. Root `scripts/setup.*` and `scripts/dev.*` commands coordinate the full project.

## Responsibilities

Present the map-focused urban planning experience: neighborhood selection, spatial indicators and heatmaps, AI proposal review, intervention controls, Before/After comparison, and SUMO simulation visualization or replay.

## Technology

Web: React, TypeScript, Next.js, MapLibre GL JS, WebGL and CSS tokens. Android: Expo and React Native with native-stack navigation. The direction is premium, dark, restrained and map-focused. See the design brief for concrete decisions.

## Inputs and outputs

- **Inputs:** geographic area identifiers, analysis responses, provenance and uncertainty metadata, validated intervention proposals, and evaluation results from the backend API.
- **Outputs:** user-selected areas, analysis parameters, proposal requests, intervention selections, and evaluation requests. The frontend must label data as observed, calculated, estimated, or unknown and must not imply that a replay is a live simulation.

## Integration interfaces

Use the JSON interfaces in `docs/API_CONTRACT.md`: `POST /analyze`, `POST /propose`, and `POST /evaluate`. Keep backend communication behind typed client functions so UI state is not coupled to transport details.

## Implementation objectives

Build one coherent end-to-end scenario on a reusable map and geographic selection model. Show the source and status of each indicator, make assumptions inspectable, and support baseline-versus-scenario comparison. Preserve usable behavior when an optional data layer is unavailable.

## Technical risks

Large vector layers and 3D rendering can hurt performance; use bounded areas and progressive layer loading. Map projections and geometry validity can cause selection and display errors. Data gaps must not be presented as zero values. API uncertainty and provenance need consistent visual treatment. Simulation replay must be distinguished from newly computed simulation results.
