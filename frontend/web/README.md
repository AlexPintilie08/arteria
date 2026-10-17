# Site ARTERIA — React + Next.js

Aplicație web cu Next.js App Router și TypeScript. Next.js este frameworkul site-ului React.

- `src/app/layout.tsx`: document, metadate, fonturi și stiluri globale.
- `src/app/page.tsx`: prezentarea ARTERIA la `/`.
- `src/app/app/page.tsx`: produsul web la `/app`.
- `src/features/workspace/Workspace.tsx`: spațiul de lucru interactiv React.
- `src/features/`: hartă MapLibre, analiză, scenarii și comparație.

Din directorul `frontend`: `npm run dev` → `http://localhost:3000`.
Build: `npm run build`. După build: `npm run preview --workspace @arteria/web`.

Configurarea publică este documentată în `.env.example`. Aplicația Android este în `../mobile`, nu în acest director.
