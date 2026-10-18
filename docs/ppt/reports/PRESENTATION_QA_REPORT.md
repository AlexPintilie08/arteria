# ARTERIA V2 — raport de livrare și QA

> **Historical QA record for the 13-slide working deck.** The current submission master is `ARTERIA.pptx` (10 slides) with `ARTERIA-Submission.pdf`; the prior 13-slide deck and pre-motion variants are archived in `archive/premium-motion-20261018/`. Current motion details and playback scope: `MOTION_AUDIT.md` and `PREMIUM_MOTION_QA.md`.

Snapshot la 18 octombrie 2026, înaintea consolidării de motion: deckul complet avea 13 slide-uri (10 pitch + 3 anexe). Versiunea completă este păstrată în `archive/premium-motion-20261018/`; masterul de depunere are acum 10 slide-uri. Comenzile sunt în `docs/ppt/README.md`.

## Sincronizare și audit

La cererea utilizatorului s-au descărcat referințele remote și s-a integrat origin/main (60fe2ee) în master prin merge 00cf80c, fără conflicte. Nu s-a făcut push. Noul cod înlocuiește concluziile V1 despre serverul fixture separat: FastAPI este API-ul unic, cu Pydantic și SQLite. Clientul web conectat și workerul SIM pentru studii pietonale sunt implementate. Semaforizarea folosește date sintetice; SUMO local este opțional, fără integrare în API/UI; cloud LLM rămâne viitor. Nu există impact urban măsurat sau pilot comercial confirmat.

Slide-ul 9 conține exact trei profiluri egale, nume 25 pt și roluri 22 pt:

- Iustin Fagateanu — Frontend and web experience
- Alex Pintilie — Bootstrap and simulation foundation
- Fagateanu Eusebiu — Backend

Rolurile provin din confirmarea utilizatorului. Nu s-au dedus contribuții individuale pe endpoint-uri din istoria Git. Slide-urile 4–6, 10–12 și notele au fost actualizate pentru codul sincronizat. Diagramele, textele, tabelele și grupurile de animație rămân editabile. Capturile sunt imagini autentice ale aplicației; cea de titlu reprezintă preview-ul de hartă, iar cea de demo arată modul conectat. Viewport-ul îngust al capturii demo nu include ultima coloană completă a tabelului; captura ilustrează interfața, iar rezultatele complete au fost verificate în arborele accesibilității.

## Organizare

Finalul este singurul PPTX curent din rădăcina docs/ppt. research/ conține cele trei documente active, scripts/ pipeline-ul, assets/ capturile, preview/ randările actuale, reports/ verificările. archive/ păstrează original-backup, pre-audit, old-previews, v1 și v2-before-sync. Raportul workspace-moves.json documentează mutările inițiale. Proba backend-audit-probes.json din vechiul audit a fost mutată suplimentar în archive/v1; nu descrie backendul curent. Scripturile istorice din arhive nu reprezintă pipeline-ul curent. Artefactele temporare și runtime-urile QA sunt în reports/.qa, ignorat de Git.

Originalul are SHA-256 `56133b4d2fe6946ff4c5a246e4d0f8be0baa0ac2f6638a6e25f969994695d170`, neschimbat. Nu au fost șterse orbește fișiere sau închise prezentări ale utilizatorului.

## Verificări ale prezentării

- Pipeline complet executat din rădăcina repository-ului: python-pptx → PowerPoint COM motion → PNG/PDF → QA → copiere în final.
- 13 slide-uri randate la 1920×1080; compozițiile inspectate, inclusiv slide-urile modificate la rezoluție completă. Conectorul care intersecta avertizarea de pe slide-ul 6 a fost eliminat.
- 153 casete/celule text măsurate de PowerPoint: zero depășiri; zero obiecte în afara canvas-ului.
- Inventar recursiv: 153 texte, 4 tabele native, 2 imagini, 21 conectori, 43 grupuri native, note pe 13/13 slide-uri.
- Validatorul standard PPTX, cu --original backup: All validations PASSED.
- ZIP/XML, ținte de timing și corespondență plan–COM verificate pentru toate slide-urile.

## Mișcare reală

43 efecte native MainSequence: Fade 0,35–0,45 s și Wipe 0,3 s pentru conectorii procesului. Schimbarea direcției Wipe reseta inițial durata la 0,5 s; scriptul a fost corectat să seteze durata după direcție și QA a confirmat corespondența.

13 tranziții Fade Smoothly de 0,55 s; avans numai la click, fără audio și fără Morph. Click-uri suplimentare pe slide: 0, 2, 4, 3, 3, 4, 3, 3, 1, 4, 0, 0, 0. Avertizările rămân vizibile înaintea animațiilor.

Redare vizuală verificată în PowerPoint desktop 16.0, în Slide Show, pe eșantion: titlul/captura de pe slide-ul 1, tranziția și prima etapă Fade + conector Wipe de pe slide-ul 4, slide-ul 9 înainte de click și cele trei profiluri după un singur click. Nu se pretinde vizionarea fiecărei animații pe toate cele 13 slide-uri; verificarea completă a definițiilor este XML + COM. PNG/PDF sunt statice și nu constituie dovadă de playback. Repetiția completă de cinci minute rămâne de făcut de prezentator.

## Verificări ale aplicației după Git sync

- npm test: 9/9 trecute; typecheck web/mobile/shared și build Next: trecute.
- pytest -q tests sim/test_engine.py: 138 passed, 1 warning în 15,75 s. Avertismentul FastAPI/Starlette privește deprecierea transportului TestClient httpx. Niciun test omis în această rulare. Runtime QA izolat, versiuni din intervalele pyproject, fără pretenție de reproducere exactă uv.lock. tests/conftest.py folosește bază SQLite temporară.
- UI local conectat la API: Podu Roș → analiză → verde NS 70 s → propunere → comparație. Rezultat sintetic verificat: nord–sud 13,89→2,22 s/vehicul, est–vest 13,89→125,56, medie 13,89→53,61. Aceste numere nu sunt măsurători din Iași și nu au fost prezentate drept beneficii validate.
- SUMO/netconvert nu au fost rulate; testele Python nu echivalează cu execuția binarelor SUMO sau validarea live OSM. Fără code coverage cuantificat.

Rezultatele structurale și hash-ul final sunt în qa-results.json; planul și inventarul PowerPoint în motion-plan.json și motion-com.json; textul recursiv în deck-manifest.json. Cercetarea detaliată și sursele sunt în research/PROJECT_RESEARCH_FULL.md. Afirmațiile business rămân ipoteze, explicit etichetate.
# Current audit notice — 18.10.2026

This earlier QA record is retained for history. The current deliverables are the 10-slide `ARTERIA.pptx` and its synchronized `ARTERIA-Submission.pdf`. The 13-slide version is archived. Current motion and playback results are in `MOTION_AUDIT.md` and `PREMIUM_MOTION_QA.md`; historical claims below describe the earlier working deck.
