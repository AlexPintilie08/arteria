# ARTERIA — prezentarea de depunere

`ARTERIA.pptx` este singurul fișier PowerPoint activ și autoritar. Are exact 10 slide-uri și un buget de prezentare de 180 de secunde; coperta este pre-roll. `ARTERIA-Submission.pdf` este exportul static sincronizat. Versiunile editabile istorice, inclusiv deckul auditat de 13 slide-uri cu anexele Q&A, sunt în `archive/`.

Conținutul factual folosește verificarea independentă din `reports/PROJECT_REALITY_AUDIT.md`, matricea din `reports/PPT_FACT_CHECK.md` și planul din `reports/PPT_CONTENT_RESTRUCTURE_PLAN.md`. Auditul de animație și rezultatele PowerPoint sunt în `reports/MOTION_AUDIT.md` și `reports/PREMIUM_MOTION_QA.md`.

## Rebuild, animații și validare

Din rădăcina repository-ului, pe Windows cu PowerPoint desktop și runtime-ul Python folosit la verificare:

```powershell
& docs/ppt/scripts/rebuild.ps1 -Python 'C:\Users\fagat\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
```

Pipeline-ul reconstruiește deckul auditat, extrage exact primele 10 slide-uri corectate, aplică efecte PowerPoint native din `reports/motion-plan.json`, verifică timpul și țintele animațiilor, exportă PNG și PDF prin PowerPoint, rulează QA-ul vizual de limite și validatorul de pachet, apoi publică PowerPoint-ul și PDF-ul. `scripts/refine_v2.py` definește grupurile semantice; `scripts/apply_motion.ps1` aplică efectele native editabile și tranzițiile.

Pentru verificarea redării native după rebuild:

```powershell
& docs/ppt/scripts/smoke_slideshow.ps1 -Deck docs/ppt/ARTERIA.pptx
```

Pentru redare, deschideți `ARTERIA.pptx` în Microsoft PowerPoint și apăsați F5. Textele rămân pe loc și apar automat prin Fade, în secvențe cu întârzieri scurte. Nu este nevoie de click pentru dezvăluirea conținutului; clickul avansează manual la slide-ul următor. Nu există avans automat.

Pașii individuali de diagnostic:

```powershell
python docs/ppt/scripts/build_deck.py
python -X utf8 docs/ppt/scripts/audited_content.py docs/ppt/reports/.qa/build/static.pptx --submission docs/ppt/reports/.qa/build/submission-static.pptx
& docs/ppt/scripts/apply_motion.ps1 -InputDeck docs/ppt/reports/.qa/build/submission-static.pptx -OutputDeck docs/ppt/reports/.qa/build/animated-10-slide.pptx
& docs/ppt/scripts/render_deck.ps1 -InputDeck docs/ppt/reports/.qa/build/animated-10-slide.pptx -OutputDir docs/ppt/reports/.qa/preview-build -Pdf
python -X utf8 docs/ppt/scripts/qa_deck.py --deck docs/ppt/reports/.qa/build/animated-10-slide.pptx --preview docs/ppt/reports/.qa/preview-build
python -X utf8 docs/ppt/scripts/validate_package.py docs/ppt/reports/.qa/build/animated-10-slide.pptx
```

## Arhiv

`archive/premium-motion-20261018/` păstrează versiunile active anterioare consolidării și previzualizările lor. `archive/v2-before-content-audit-20261018/` păstrează deckul și sursele înghețate înaintea auditului factual. `archive/original-backup/`, `archive/v1/`, `archive/v2-before-sync/` și `archive/pre-audit/` păstrează istoricul anterior.

PowerPoint este necesar pentru animații native, capturi și PDF. `validate_package.py` folosește validatorul skill-ului local cu template-ul original ca bază. Capturile PNG și PDF sunt randări statice; verificarea cronologiei nu înlocuiește vizionarea unei redări F5 pe ecran.
