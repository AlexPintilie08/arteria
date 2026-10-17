# Frontend status

## Working

- React, TypeScript, Vite, Tailwind CSS, and MapLibre development shell is in place.
- The Iași map preview uses the OpenFreeMap public dark style and displays a fallback if the style cannot load.
- Backend health status is polled through the Vite API proxy and exposes an unavailable state.
- Windows Node.js 24.22.0 TypeScript check and production build pass.

## In Progress

- macOS GitHub Actions verification is pending.

## Next

- Add typed API clients and geographic area selection for one end-to-end scenario.
- Choose a small Iași area with usable public data and wire selection to analysis.

## Blockers

- No area selection, urban layers, or analysis endpoints exist yet.
