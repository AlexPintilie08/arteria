# Audit backend ARTERIA — 17 octombrie 2026

Audit al checkout-ului local `feat/backend-api`: backend, contracte din backend/docs/api-specs,
client web și mobil, motorul sim local și snapshot-ul integrat, teste, setup/dev/check și CI.
Nu au fost modificate implementările în timpul auditului. Nu s-a rulat achiziție OSM
online, simulare SUMO de oraș sau verificare Windows. Singurul fișier creat este acest raport.

## Concluzie

Demo-ul local are un flux funcțional și 43 de teste trecute, dar nu implementează
întreaga specificație de analiză urbană. Există defecte reproductibile în pornirea
integrată și în tratarea răspunsurilor/erorilor motorului și stocării. Nu am identificat
un blocaj al fluxului web standard deja configurat pe această mașină.

## P1 — de rezolvat înainte de predarea către colegi

### 1. Comanda din scripturile de pornire nu este compatibilă cu frontend-ul Next.js

Fișiere: `scripts/dev.sh:27`, `scripts/dev.ps1:26`.
Am executat din frontend exact `npm run dev -- --host 127.0.0.1`.
Comanda devine `next dev --hostname 0.0.0.0 --port 3000 127.0.0.1` și eșuează:
`Invalid project directory .../frontend/web/127.0.0.1` (exit 1).
Ambele scripturi mai afișează portul 5173, deși Next.js ascultă pe 3000.
Pe macOS, scriptul oprește și backend-ul când procesul frontend eșuează.

Remediere: invocare corectă a workspace-ului Next, adrese actualizate, verificarea
pornirii celor două servicii. Windows trebuie verificat separat, nu declarat testat.

### 2. Un răspuns incomplet al motorului poate fi salvat ca studiu valid și apoi produce 500

Fișiere: `backend/spatial_adapter.py:57`, `backend/spatial_models.py`,
`backend/spatial_routes.py:53`.

Reproducere izolată, fără modificarea bazei utilizatorului: am înlocuit răspunsul
subprocesului cu `{"analysis":{},"alternatives":{"ranked_candidates":[{}]}}`.
Adaptorul l-a acceptat, POST studies a returnat **201**, apoi evaluate a returnat
**500 Internal Server Error**, pentru că lipsește `candidate_id`.

Remediere: modele explicite pentru candidate/intervention/impact și validare completă
înainte de stocare; răspuns incompatibil -> 502 structurat. Test de regresie pentru
chei lipsă, tipuri greșite și impact invalid. Clientul TypeScript face doar cast,
deci nu oferă o a doua validare runtime.

### 3. Unele erori de stocare ies din contractul public de erori

Fișiere: `backend/storage.py:23`, `backend/main.py` (handler sqlite3.OperationalError).

Cu ARTERIA_DB_PATH îndreptat, într-un director temporar, către un fișier al cărui
părinte este deja un fișier, POST analyze întoarce **500 text/plain**, fără
`error.code/details/request_id`. Eroarea filesystem apare înainte de sqlite3 și
nu este prinsă de handlerul existent.

Remediere: clasificarea erorilor de filesystem/bază de date, răspuns public sigur
și uniform, diagnostic intern și teste de regresie. `/health` a răspuns 200 în
acest caz: este corect pentru liveness, dar ar trebui adăugat separat un `/ready`
care verifică stocarea și raportează capabilitățile opționale.

### 4. Integrarea sim nu este reproductibilă automat într-un checkout curat / CI

Fișiere: `backend/prepare_sim.py:11`, `backend/spatial_adapter.py:32`,
`tests/test_spatial_api.py:100`, `.github/workflows/ci.yml`.

Pe această mașină funcționează un export ignorat din commitul
`752c92da9184effc9b87704e0868320f569454ea`. Prepararea depinde de existența locală
a ref-ului `origin/feat/sim-engine`. Workflow-ul nu face fetch/preparare pentru acel
ref și nu configurează snapshot-ul. În absența lui, testul de integrare reală dă skip,
iar API-ul pietonal returnează 503. Un CI verde nu garantează funcționarea integrării.

Remediere: distribuirea unei versiuni sim fixate și pregătirea ei explicită în setup/CI;
un job de integrare în care lipsa motorului este eroare, nu skip. Actualul workflow
vizează main/feat și PR către main, nu master. Nu este necesară modificarea algoritmilor sim.

## P2 — funcționalitatea produsului și contractul

### 5. Contractele nu au o singură variantă autoritară

`backend/API_ENDPOINTS.md` și clientul folosesc /analyze, /propose, /evaluate.
`api-specs/` cere /api/v1/analyze, /api/v1/propose, /api/v1/evaluate.
Cele trei rute versionate au fost verificate și returnează **404**.
Există diferențe și în versiunea catalogului, tipurile intervențiilor, constrângerile
buget/coridor tramvai, telemetry și câmpurile de cost/durată. Numai aliasurile de rută
nu ar implementa aceste capabilități.

Remediere: contract v1 explicit, matrice de capabilități, aliasuri compatibile dacă
se păstrează rutele curente, teste pe payload-uri agreate. Exemplele de senzori și
furnizori AI nu trebuie transformate în date/integrări fictive.

### 6. Zona selectată nu produce încă analiză reală a acelei zone

`backend/main.py:analyze`, `backend/catalog.py`, `backend/simulation_adapter.py`:
zonele sunt bookmarks și rulează același model sintetic implicit. Straturile rămân
unknown, iar network_modes/pragurile sunt validate, nu calculate. Catalogul de zone
nu întoarce poligoane; `/api/v1/areas/{area_id}/geometry` returnează **404**.
Clientul pietonal trimite explicit `source:fixture`, indiferent de zona din selector.

Există calea source:osm în API-ul pietonal, dar nu a fost verificată online și nu
este legată de selecția din interfață. Motorul colegului are un catalog OSM parțial,
nu frontiere cadastrale certificate, și poate oferi baza unei integrări reale.

Remediere: catalog/geometrie cu proveniență, un studiu bounded OSM verificat, apoi
legarea acelei zone și a indicatorilor reali în fluxul produsului. Nu promitem date
reale de trafic doar pentru că avem un graf OSM.

### 7. Evaluarea pietonală este selecția unei comparații precompute, nu o rulare nouă

`backend/spatial_routes.py:26` calculează analiza și alternativele împreună;
`evaluate` întoarce impactul deja salvat. Este etichetat corect
`stored_graph_comparison`. Nu se păstrează obiectul graf pentru intervenții arbitrare
ulterioare. Sunt salvate rezultatele, nu o stare suficientă pentru orice reevaluare.

Dacă produsul cere editarea liberă a scenariului: persistarea snapshot-ului și a
parametrilor, aplicarea intervenției pe copie și reevaluarea cu aceeași versiune.
Pentru demo-ul cu selecție dintre alternativele salvate, comportamentul actual este valid.

### 8. Lipsesc scenariile utilizatorului, exportul și autentificarea din specificație

Rutele POST /api/v1/scenarios și GET /api/v1/auth/me au fost verificate: **404**.
Nu există login/logout/refresh, autorizare per utilizator, titlu/note/proprietar pentru
scenarii, listare/paginare, link de partajare sau export JSON/GeoJSON/PDF conform contractului.
SQLite salvează analize/propuneri/evaluări și permite citirea după ID, dar nu înlocuiește
API-ul de proiecte/scenarii. Limita de 1000 înregistrări pe categorie nu are un mecanism
administrativ de arhivare/curățare. Studiile noi primesc ID nou la fiecare cerere,
deci retry-ul poate repeta calcule și consuma din limită.

Prioritate: scenariu salvat și export JSON/GeoJSON pentru demo; autentificare și
izolare înainte de utilizare cu conturi/date private. PDF și partajare după stabilirea
cerințelor. Documentul auth menționează refresh în UX, dar nu îi definește complet contractul.

### 9. Simularea de trafic și AI sunt capabilități neimplementate, nu bug-uri ascunse

Nu există joburi SUMO, streaming SSE, scenarii rutiere calibrate, optimizare tramvai,
lățime de bandă, giratoriu sau pasaj. Endpoint-ul analytical/evaluate cerut separat
în specificație returnează 404. Modelul demo nu este o implementare validată HCM.
LLM-ul nu este integrat; recomandările curente sunt deterministe.

Necesită date și operații suportate de componenta sim, apoi adaptor backend. Un test
SUMO de instalare nu demonstrează evaluarea unei intervenții urbane.

## P3 — operare, testare și documentație

- Adaptorul capturează stderr al subprocesului, dar îl aruncă la eșec: fără log intern
  corelat cu request_id, diagnosticarea unui 502 este dificilă.
- Limita de o execuție simultană este per worker. Timeout-ul este 90 s; anularea din
  browser nu oprește imediat procesul. De adăugat control global/joburi doar dacă
  intrăm în execuții lungi sau mai mulți utilizatori.
- Validarea backend verifică suprafața poligonului, iar motorul verifică suplimentar
  extinderea de 5 km; erorile acestuia sunt comprimate în 502 generic. Ar trebui
  păstrate distincțiile input invalid / indisponibilitate / timeout.
- Aplicația mobilă nu apelează încă fluxul real; ecranele folosesc placeholders.
  Este integrare frontend mobil, nu dovadă că endpoint-urile backend lipsesc.
- README rădăcină încă spune că backend-ul nu este implementat. Documentația locală
  sim descrie smoke-only, iar adaptorul rulează o altă revizie exportată: trebuie
  explicate clar versiunea activă și setup-ul.
- Scripturile check nu rulează testul browser/backend și nici testele npm shared.
  Nu am rulat pipeline-ul Windows sau întregul setup în acest audit.
- Git este în merge nefinalizat; există fișiere backend importante untracked.
  La finalul lucrului trebuie incluse în commitul aprobat, altfel colegii nu le primesc.
  Auditul nu a făcut commit/push și nu a finalizat merge-ul.

## Verificări executate

- `python3 -m uv run --locked pytest -q`: **43 passed**, un warning upstream
  Starlette/httpx; inclusiv integrarea offline cu snapshot-ul disponibil local.
- Probe TestClient cu DB temporară: rute lipsă, răspuns motor invalid acceptat,
  evaluate 500 și storage-path 500. Baza aplicației nu a fost modificată de probe.
- Comanda frontend exactă din dev scripts: eșec reproducibil de interpretare argument.
- Inspecție statică a scripturilor, CI, contractelor și clienților web/mobile.
- Nu am rulat achiziție OSM, calibrat trafic sau evaluat capabilități AI.

## Ordine recomandată

1. Corectarea pornirii integrate și pregătirea reproductibilă a motorului.
2. Validarea completă a răspunsurilor sim și erori de stocare uniforme, cu regresii.
3. Contract unic și catalog de capabilități; readiness și loguri utile.
4. O zonă OSM verificată, conectată la selecția utilizatorului.
5. Salvare/listare/export scenarii; apoi cerințele de conturi și execuții lungi.

## Actualizare — primul lot de stabilizare

Punctele 1–3 au primit corecții izolate:

- Scripturile dev invocă explicit workspace-ul Next.js, cu `--hostname` și portul
  3000. `bash -n scripts/dev.sh` trece. Comanda Next a fost executată pe portul
  alternativ 3099: argumentele au fost acceptate, dar pornirea unei a doua instanțe
  este blocată de serverul existent pe 3000. Nu am oprit serverul utilizatorului.
  Pornirea integrată completă și Windows rămân de verificat.
- `backend/engine_contract.py` validează câmpurile consumate ale rezultatelor
  motorului înainte de salvare: candidate unice, intervenții/coordonate, impact,
  rute și proveniență. JSON-ul original și extensiile sale sunt păstrate. Rezultatele
  incompatibile produc 502; impacturile negative și lista goală rămân valide.
- Stocarea normalizează erorile filesystem/SQLite în 503 `storage_unavailable`;
  conexiunile sunt închise inclusiv la eșecul inițializării schemei. `/health`
  păstrează contractul de liveness.

Verificare: `python3 -m uv run --locked pytest -q` — 60 teste, inclusiv regresii
și integrarea offline cu motorul configurat. Fluxurile HTTP demo și pietonal au
fost verificate separat pe un Uvicorn temporar, cu bază temporară. `/docs` și
`/openapi.json` răspund 200. Nu au fost modificate frontend/ sau sim/ în acest lot
(verificat prin SHA256 față de backup). Punctele 4–9 rămân deschise.

Backupul anterior corecțiilor, inclusiv copie SQLite consistentă, este în
`../.arteria-backups/backend-stabilization-20261017-233640`. Nu s-a făcut commit,
push sau finalizarea merge-ului existent.
