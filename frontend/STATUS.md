# Frontend status

## Working

- React, TypeScript, Vite, Tailwind CSS, and MapLibre development shell is in place.
- The Iași map preview uses the OpenFreeMap public dark style and displays a fallback if the style cannot load.
- Backend health status is polled through the Vite API proxy and exposes an unavailable state.
- Windows Node.js 24.22.0 TypeScript check and production build pass locally.
- Windows, macOS 15 ARM64, and macOS 15 Intel CI setup, TypeScript, and production build checks pass.

## In Progress

- No active changes.

## Next

- Add typed API clients and geographic area selection for one end-to-end scenario.
- Choose a small Iași area with usable public data and wire selection to analysis.

## Blockers

- No bootstrap blockers. Area selection, urban layers, and analysis remain future work.
