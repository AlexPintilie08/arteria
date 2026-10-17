# ARTERIA frontend

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
