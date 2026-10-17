# ARTERIA frontend

This npm workspace contains the Next.js web application, Android app, shared API
client and contracts, design tokens, and frontend tests. The web app serves the
presentation at `/` and the connected workspace at `/app`.

## Web application

Requires Node.js 24.x. Install dependencies from this directory:

```bash
npm ci
```

Start Next.js with `npm run dev`; it serves `http://localhost:3000`. Start the
FastAPI backend separately from the repository root:

```bash
uv run --locked uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The frontend defaults to `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` and
`NEXT_PUBLIC_DEMO_MODE=false`. These defaults work with the backend's local CORS
settings. Optional local configuration belongs in the ignored
`frontend/web/.env.local`; a blank `NEXT_PUBLIC_MAP_STYLE_URL` uses the neutral
canvas, while the bundled Iași catalog remains visible.

The workspace keeps five demo bookmarks and synthetic signal-timing flows
separate from the SIM v3 pedestrian graph panel. The OSM catalog is bundled, but
live graph acquisition requires internet access and a fresh clone has no OSM
cache. OSM place extents are not official administrative boundaries. Graph
comparisons do not run SUMO or establish physical feasibility. Cloud AI is not
connected. See the [spatial API contract](../backend/SPATIAL_API.md) and the
[MacBook handoff](../docs/MACBOOK_HANDOFF.md).

Run frontend checks from this directory:

```bash
npm run typecheck
npm test
npm run build
```

The root project checks run these alongside Python tests and the backend health
smoke test: `bash scripts/check.sh` from the repository root.

## Android application

The `mobile/` workspace contains the Expo/React Native Android application. To
start Expo, run `npm run mobile` from this directory; an Android SDK and emulator
or device are required to launch it. Shared API contracts and tests live in
`shared/`.

Design and implementation references: [design brief](../docs/frontend/DESIGN_BRIEF.md),
[implementation plan](../docs/frontend/IMPLEMENTATION.md), and
[API contract](../docs/API_CONTRACT.md).
