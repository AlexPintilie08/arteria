# Predare backend ARTERIA

Branch: `feat/backend-api`. Stare la 18 octombrie 2026.

## Ce am implementat

- FastAPI: `/health`, `/analyze`, `/propose`, `/evaluate`, recuperare rezultate,
  catalog `/api/v1/areas` și documentație interactivă `/docs`.
- Modele Pydantic, validare, erori JSON uniforme și CORS pentru frontend.
- Flux complet analiză → recomandări deterministe → evaluarea intervenției selectate,
  cu același baseline, parametri exacți, unități, proveniență și impact negativ/pozitiv.
- DEMO sintetic explicit; cererile SUMO nesuportate primesc indisponibilitate,
  fără înlocuire ascunsă cu rezultate sintetice. Nu există integrare LLM.
- Persistență SQLite, identificatori stabili pentru fluxul demo, rezultate imutabile,
  limite de capacitate și erori de stocare controlate.
- Adaptor separat pentru motorul pietonal al colegului: snapshot Git exportat local,
  subprocess cu timeout, validarea răspunsului înainte de salvare, comparații păstrate
  pe același baseline. `sim/` nu a fost modificat pentru această integrare.
- Client web conectat separat, exemple HTTP și documentație pentru frontend.
- Corectarea scripturilor dev pentru Next.js, workspace explicit și portul 3000.

## Harta și interfața

Ecranul original cu hartă, Explorează / Scenarii / Compară există în continuare.
Este activat local prin `frontend/web/.env.local`:

```dotenv
NEXT_PUBLIC_DEMO_MODE=true
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Fișierul local este ignorat de Git; colegii trebuie să creeze configurația de mai sus
pentru același ecran. Deschideți `http://localhost:3000/app`.
Cu `NEXT_PUBLIC_DEMO_MODE=false` apare ecranul separat conectat la backend.
**Harta originală nu este încă integrată complet cu backend-ul.** Valorile și
intervențiile conceptuale din previzualizare nu reprezintă simulări reale.

## Pornire macOS

Din rădăcina proiectului, cu Python/uv și Node.js 24 instalate:

```bash
python3 -m uv sync --locked
cd frontend
npm ci
cd ..
python3 -m uv run --locked uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

În alt terminal, din rădăcina proiectului:

```bash
cd frontend
npm exec --workspace @arteria/web -- next dev --hostname 127.0.0.1 --port 3000
```

Alternativ: `bash scripts/dev.sh`, dacă `uv` este disponibil în PATH.
Nu porniți încă un Next dev în același checkout dacă există deja unul activ.

Motorul pietonal este opțional și nu este inclus în snapshot-ul versionat al backend-ului.
Revizia verificată este `752c92da9184effc9b87704e0868320f569454ea`.
Pregătire explicită a acelei versiuni, fără modificarea directorului `sim/`:

```bash
git fetch origin feat/sim-engine
python3 -m uv run --locked python -c 'from backend.prepare_sim import prepare; print(prepare("752c92da9184effc9b87704e0868320f569454ea"))'
```

Comanda simplă `python -m backend.prepare_sim` folosește vârful local al
`origin/feat/sim-engine`, care poate fi mai nou decât versiunea testată.
Fără snapshot, API-ul pietonal raportează indisponibilitate; demo-ul principal funcționează.

## Verificări executate

```bash
python3 -m uv run --locked pytest -q
bash -n scripts/dev.sh
```

60 de teste trecute, cu un avertisment upstream Starlette/httpx. Acoperă fluxul complet,
intervenții trimise direct din propose în evaluate, parametri diferiți, validare,
ID-uri necunoscute, proveniență, persistență, indisponibilitate SUMO, răspunsuri motor
invalide, erori filesystem/SQLite și integrarea offline cu snapshot-ul disponibil.
Testul motorului opțional poate fi omis automat dacă snapshot-ul lipsește.

Fluxuri HTTP verificate pe Uvicorn separat cu DB temporară; `/docs` și OpenAPI: 200.
Harta și modul de previzualizare verificate în Chrome automatizat.
Comanda Next corectată acceptă argumentele, dar o a doua instanță este blocată de
serverul deja activ. Pornirea integrată completă și Windows nu au fost reverificate.
Nu s-au verificat achiziția OSM online sau simulări SUMO reale.

Exemple HTTP reproductibile, cu serviciul pornit:

```bash
python3 -m uv run --locked python -m backend.demo_client
python3 -m uv run --locked python -m backend.spatial_demo_client
```

## Ce mai trebuie lucrat, în ordine

1. Conectarea backend-ului în ecranul original cu hartă, păstrând designul și navigarea.
2. Distribuirea reproductibilă a motorului fixat și test obligatoriu de integrare în CI.
3. Alinierea contractelor `/api/v1/*` cu rutele existente și documentarea capabilităților.
4. O zonă OSM verificată și legată de selecția reală; fără a confunda geometria cu măsurători de trafic.
5. Salvare/listare scenarii și export JSON/GeoJSON; apoi autentificare și autorizare.
6. Readiness separat de health, diagnostic intern mai bun și verificare Windows.
7. Integrare SUMO reală numai după existența datelor și operațiilor suportate; AI opțional.

Vezi `FRONTEND_HANDOFF.md`, `SPATIAL_API.md`, `../docs/DEMO_API.md` și
`../docs/BACKEND_AUDIT.md` pentru contracte, exemple și lista detaliată de lipsuri.

## Context Git

Commitul de predare închide merge-ul anterior, deja rezolvat, din master la
`66b6d19b1002fde705e54b46fa8844f0bb93bed6`. Include și fișierele frontend/API-specs
aduse de acel merge, păstrând munca colegilor. Master a avansat între timp;
acest push nu include automat ultimele sale modificări și nu publică pe master.
Bazele locale, snapshot-urile motorului, dependențele, build-urile și configurația
`.env.local` nu sunt incluse în Git.
