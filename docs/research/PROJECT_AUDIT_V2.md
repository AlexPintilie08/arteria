# ARTERIA — audit integral V2

**Data:** 18 octombrie 2026 (Europe/Bucharest)  
**Ref inspectat:** codex/ppt-diacritics / origin/codex/ppt-finalized, HEAD ed69c2d08940f6fc516acbf87ca7ece54426f4ca. origin/main este e785649308923c0c91de40ebb1b0b85b5962962e; baza comună înaintea handoff-ului #4: 00cf80c103459b5a6b8b5ecbcb28c4947d066686.  
**Domeniu:** repository întreg pentru context; produsul este evaluat în principal în frontend/web și backend-ul folosit de acesta. Mobilul a fost inspectat documentar, fără modificări și fără testare nativă.

## Rezumat

Aplicația web are două fluxuri conectate, cu scopuri distincte:

1. **Semaforizare demonstrativă:** analiză, propuneri deterministe și comparație înainte/după pe model aritmetic cu cerere sintetică.
2. **Acces pietonal:** catalog OSM parțial sau fixture sintetic, analiză de graf, candidați de legături ipotetice, validare SIM și comparație pe eșantion de noduri.

Acestea nu sunt încă un instrument integrat de planificare urbană: timing-ul nu folosește geometria aleasă; studiul pietonal nu calculează cerere reală, impact populațional sau trafic auto; rezultatele de graf nu apar ca straturi de trasee pe hartă. Niciun efect de mobilitate nu a fost validat prin măsurători de teren sau feedback profesional în repository.

## Metodă și niveluri de dovadă

- Inspectate: frontend/web, frontend/shared, backend, sim, tests, configurație și documentație.
- Teste fără instalări: Node.js v24.12.0; Python 3.12.14; pachetele Python din runtime-ul QA existent la docs/ppt/reports/.qa/runtime. Runtime-ul nu este sincronizare exactă cu uv.lock.
- Rezultate: npm test — 9/9; typecheck @arteria/web — trecut; build web — trecut la rerulare în afara sandbox-ului; backend + SIM — 138 teste trecute, un warning Starlette/httpx.
- Browser/API real: build Next local pe 127.0.0.1:3001, backend pe 127.0.0.1:8000, CORS explicit și bază SQLite nouă în TEMP. Portul 3000 era deja ocupat și nu a fost atins. API: 200 la /analyze, /propose, /evaluate; 201 la studiul fixture și 200 la evaluarea lui.
- Nu s-a făcut cerere OSM live, nu s-a rulat SUMO și nu s-au contactat profesioniști.

„Implementat” înseamnă cod prezent; „demonstrat în test” înseamnă că testul/fluxul a executat funcția; „simulat” descrie date sau model sintetic; „validat în condiții reale” ar necesita observații de teren, date validate ori feedback profesional. Nicio măsurătoare de efect urban nu intră în ultima categorie.

## Inventarul web

| Suprafață | Comportament actual | Rezultatul și limita |
|---|---|---|
| / | Pagina de prezentare cu conținut editorial și scenă conceptuală Three.js. | Ilustrație, nu GIS, proiect tehnic sau dovadă a unei configurații din Iași. |
| /app implicit | Workspace conectat cu secțiunile Explorează, Scenarii, Compară și Acces pietonal. Preview-ul se activează explicit prin NEXT_PUBLIC_DEMO_MODE=true. | Prima secțiune nu afișează harta; începe cu selectarea unui bookmark. |
| Preview explicit | Interfața fixture cu MapLibre, indicatori necunoscuți și fixtures. | Bună pentru a demonstra UI; nu este analiză live. |
| Selector zonă timing | Cinci contexte bookmark (Copou, Centru, Podu Roș, Tătărași, Alexandru cel Bun), trimise ca preview-* fără boundary real. | Context pentru model sintetic; backend-ul întoarce layer availability unknown. |
| Analiză semafor | Întârzieri nord–sud, est–vest și medie; status, sursă, unități și warnings. | Calcul determinist sintetic: R²/(2C) + 60 × max(0, cerere/capacitate − 1), cu capacitate 1800 × verde/ciclu (backend/simulation_adapter.py:18–29). Nu e trafic local. |
| Scenarii timing | Trepte minimal/moderat/transformativ, slider pentru verde N-S, efecte direcționale și validare backend. | Schimbă un singur parametru la cerere/ciclu fixe; „transformativă” nu înseamnă infrastructură. |
| Comparație timing | Tabel înainte/după/delta, explicația semnului și surse/ipoteze. | Ieșiri sintetice; nu oferă LOS, cozi calibrate, siguranță, tranzit ori efect în teren. |
| Catalog geografic | Încarcă la cerere catalog static cu 24 poligoane și 7 puncte OSM; căutare fără diacritice, metadate de sursă, dată și licență când sunt disponibile. Punctele rămân puncte. | Snapshot parțial, nu limite legale; alegerea din listă nu este selecție cartografică completă. |
| Hartă zonă | MapLibre raster OSM; centrează și desenează conturul obiectului selectat. | Nu primește studiul/alternativele SIM și nu desenează candidați, rute sau efecte. Worker-ul nu achiziționează features: include_features=False. |
| Studiu pietonal | Fixture sau catalog OSM; OSM solicită walk și SIM calculează graf și candidați. | Fixture sintetic; OSM depinde de rețea/calitatea snapshot-ului. Eșantionul de noduri nu este cerere sau călătorie observată. |
| Comparare legături | UI arată perechi evaluate, accesibilitate, distanță și tabel de ID-uri/noduri. API verifică baseline-ul, candidatul și intervenția exactă. | Impactul se calculează la crearea studiului și se returnează ulterior; nu se rerulează după editare. Nu probează construcția. |

## Fluxuri probate în browser

- Semafor: baseline demonstrativ de 13,89 s/vehicul pe ambele direcții. Alternativa moderată a dat 12,10 N-S și 15,80 E-V; media 13,64. Este un compromis al acelui input sintetic, nu un câștig real de trafic.
- Graf fixture: studiul a întors 3 alternative validate și 15 perechi. Opțiunea inspectată avea 4 perechi devenite accesibile, 0 îmbunătățite/înrăutățite și 0 m diferență agregată. Mai multe perechi erau necomparabile; caption-ul tabelului a numit fixture-ul „graful OpenStreetMap” (defect confirmat, SpatialPanel.tsx:158).
- Logurile Uvicorn au confirmat cererile POST. Demonstrează conexiunea UI/API, nu validitatea modelului pe teren.

## Backend-ul folosit de web

- FastAPI implementează /health, /analyze, /propose, /evaluate, GET pentru rezultate, /api/v1/areas și /api/v1/spatial/studies. Pydantic validează shape-ul și identitatea scenariului (backend/main.py, models.py, spatial_models.py).
- Semaforizarea este separată de geografie: bookmark-ul oferă context, iar indicatorii provin dintr-o intersecție sintetică; straturile rămân unknown (backend/main.py:83–123).
- SQLite păstrează rezultate imutabile pe namespace/ID și retry idempotent; nu există proprietari/proiecte/management de utilizator (backend/storage.py).
- Adaptorul spațial rulează SIM într-un proces limitat la un slot cu timeout 90 s și revizie din HEAD/configurație (backend/spatial_adapter.py:38–75); nu există coadă distribuită.
- Workerul validează ID-ul OSM canonic, acceptă geometrie eligibilă și cere doar walk fără features (backend/spatial_worker.py:26–50).
- Clientul TS propagă timeout/AbortSignal și erorile HTTP, dar success response folosește response.json() as T fără validare runtime (frontend/shared/core/api.ts:10–45).
- Nu există autentificare, tenant, proiecte, provider LLM, job SUMO/SSE sau API mobil conectat în codul inspectat.

## Dovezi pe funcționalitate

| Funcție | Cod prezent | Test/demo Etapa 1 | Sintetic | Validată în condiții reale |
|---|---:|---:|---:|---:|
| Analyze→propose→evaluate semafor | Da | Da; browser și teste API/frontend | Da | Nu |
| Persistență și verificare baseline/acțiune | Da | Da; retry, retrieval și mismatch în teste | N/A | Nu măsoară efect urban |
| SIM fixture study/evaluate | Da | Da; 138 teste și browser cu worker real | Da | Nu |
| Catalog OSM și validare geometrii | Da | Da pentru parser/static catalog și teste | N/A | Catalog snapshot există; achiziția online nu a fost rerulată |
| Studiu OSM descărcat la cerere | Da în cod | Nu în Etapa 1 | Calcul pe OSM dacă sursa este disponibilă | Nu |
| SUMO | Runner local condiționat | Fără sumo/netconvert găsite în PATH; nu s-a rulat | Cererea poate fi sintetică | Nu |
| AI/LLM | Nu găsit activ | N/A | Propuneri deterministe | Nu |
| Adopție sau efect de politică publică | N/A | Fără teste de utilizatori | N/A | Nu |

## UX și accesibilitate

**Puncte susținute:** skip link, controale native cu label, stări aria-pressed, focus vizibil, role=status/alert pentru cereri și butoane de 46 px în eșantion. La viewport 375 px nu a existat overflow orizontal. Harta este încărcată dinamic.

**Probleme confirmate:**

1. /app începe cu formularul timing, fără hartă. Catalogul și grafurile sunt separate; selectorul bookmark poate părea zonă analizată geografic, deși acea cale este sintetică.
2. Studiul OSM nu desenează link-urile propuse sau rutele pe hartă. Tabelul folosește ID-uri de noduri.
3. Caption-ul spatial spune OSM și în modul fixture (SpatialPanel.tsx:158); a fost observat în browser.
4. Secțiunile sunt state React local, fără URL/deep-link sau restaurare după refresh.
5. Nu s-a făcut audit complet cu cititor de ecran, contrast, keyboard-only pentru fiecare control ori verificare automată WCAG.

**Documentație contradicțională:** docs/API_CONTRACT.md:11,19 spune că există numai /health; docs/ARCHITECTURE.md descrie endpoint-urile ca viitoare; sim/AGENTS.md:8 repetă că backend-ul expune doar health; frontend/STATUS.md păstrează sarcini de geografie ca „in progress”. Acestea nu corespund codului curent. PR #4 de pe origin/main cere map-first, catalog integral și straturi de rezultat, lipsuri confirmate în cod.

## Limite și concluzie

Datele OSM pot fi incomplete sau schimbătoare; lipsa unui feature nu dovedește absența lui. Legăturile candidate și perechile eșantionate nu reprezintă populație, cerere sau fezabilitate. Nu s-a demonstrat deployment, traffic model calibrat, AI cloud, SUMO integrat, auth sau feedback de client.

Produsul este util ca prototip conectat pentru comparații controlate pe date sintetice și studii pietonale pe graf. Nu este încă suport de decizie pentru proiectare, investiții ori aprobare municipală. Nu s-a modificat aplicația.

Vezi PROFESSIONAL_USER_PROFILES.md, GAP_ANALYSIS.md și RESEARCH_ROADMAP.md pentru profiluri, lipsuri și cercetarea propusă.
