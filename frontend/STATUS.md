# Frontend status

## Working

- Modern GIS & Urban Mobility Ergonomics:
  - **Explore (`/app?section=analysis`)**: Left Control Dock (320px) for areas and layers + Expansive Center Map Canvas + Full-width Horizontal Telemetry Deck under the map. Eliminates cramped right sidebar.
  - **Scenarios (`/app?section=scenarios`)**: Split-screen Scenario Studio (50/50) with corridor spatial preview, alternative level switcher, and interactive parameter tuning console (green wave slider, CTP bus priority toggle, lane width) with real-time recalculated impact.
  - **Compare (`/app?section=comparison`)**: Full-width panoramic decision matrix with traffic regime filters (morning peak, evening peak, midday), congestion load factor slider, dual visual progress bars (Baseline vs Scenario), and instant report export (Markdown & JSON).
  - **Simulation Model Integration**: Parameter tuning console in Scenarios (`greenPhaseSec`, `ctpPriority`, `laneWidthM`) is now seamlessly connected to the Comparison matrix, dynamically evaluating Webster delay and hydraulic flow capacity adjustments in real time.
- WCAG 2.2 AA Accessibility & Micro-Interactions:
  - Custom MapLibre markers in `MapViewport.tsx` converted to interactive `<button>` elements with `tabindex="0"`, `role="button"`, `aria-label`, `aria-pressed`, and keyboard handlers (`Enter` / `Space`).
  - High-visibility focus indicators (`outline: 3px solid var(--accent)`) and `@media (prefers-reduced-motion)` overrides for pulsing pins.
  - Accessible range sliders equipped with explicit `<label>` IDs, `aria-labelledby`, `aria-valuenow`, and descriptive `aria-valuetext`.
  - Accessible clipboard feedback (`aria-live="polite"`) and slider reset button.
  - 100% Romanian localization of presentation components (`ImpactMatrix.tsx`).
- Robust State & API Connectivity:
  - Fixed analyze button gate in `Workspace.tsx` to allow seamless live API connections without forcing demo mode.
  - 7 comprehensive API contract documents authored in `api-specs/` (`auth`, `areas`, `analysis`, `proposals`, `evaluation`, `simulation-engine`, `scenario-persistence`).
- Pure React & TypeScript styling using system tokens (`@arteria/shared/tokens`) without external ad-hoc CSS modules.
- MapLibre GL JS integration with interactive vector corridors and animated pulsing markers for Iași junctions.
- Real-time telemetry display for Iași corridors (Podu Roș 2180 veh/h, queue 340m, delay 74.2s, LOS E/F).
- Native-stack Android mobile scaffold with deep links (`arteria://`).
- Verified HTTP API client communicating with `backend/server.py` on port 8000.

## Verification

- `npm run check` (TypeScript typecheck across all 3 workspaces + 5 transport/fixture tests + Next.js production build): **100% PASS (0 errors)**.
- Endpoints verified with HTTP 200 OK:
  - Frontend `/` and `/app` (Port 3000)
  - Backend `/health`, `/analyze`, `/propose`, `/evaluate` (Port 8000)
- Zero horizontal layout overflow across all tested breakpoints (375px, 768px, 812px, 1440px).

## Next Integration Steps

- Connect native MapLibre adapter in the Expo Android workspace.
- Expand custom user-drawn polygon upload support.

## Blockers

- None for the core desktop/web evaluation workflow.
