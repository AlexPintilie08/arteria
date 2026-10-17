# ARTERIA — raport final de livrare și QA

Finalizat la 18 octombrie 2026, Europe/Bucharest. Audit început la 17 octombrie. Sarcina a inclus cercetarea repository-ului, verificarea afirmațiilor, narațiunea de pitch și reconstrucția prezentării. Nu s-a modificat funcționalitatea aplicației.

## Livrabile

| Fișier | Rezultat |
|---|---|
| `docs/ppt/Template-Pitch-Hackathon.pptx` | Prezentare finală, 10 slide-uri de pitch + 3 anexe |
| `docs/ppt/PROJECT_RESEARCH_FULL.md` | Cercetare detaliată, inventar de funcții, contradicții, registre de dovezi și limite |
| `docs/ppt/PITCH_CONTENT.md` | Conținut pe slide, explicații verbale, surse, tranziții și timpi propuși |
| `docs/ppt/PRESENTATION_DESIGN_PLAN.md` | Inspecția celor două surse, sistem vizual și specificații pe slide |
| `docs/ppt/PRESENTATION_QA_REPORT.md` | Acest raport |
| `docs/ppt/build_deck.py` | Generator nou, cu python-pptx, pornind din pachetul prezentării existente |
| `docs/ppt/render_deck.ps1` | Export PowerPoint în PNG/PDF și măsurarea casetelor text |
| `docs/ppt/qa_deck.py` | Verificarea artefactului, editabilității structurale și a previzualizărilor |
| `docs/ppt/preview/Slide1.PNG` … `Slide13.PNG` | Randări finale 1920×1080; contact sheets în același director |
| `docs/ppt/preview/presentation.pdf` | Export auxiliar pentru previzualizare, 13 pagini |
| `docs/ppt/assets/` | Capturi noi autentice ale aplicației locale; două sunt incluse în deck |
| `docs/ppt/qa-results.json`, `validation.log`, `deck-manifest.json` | Inventar și rezultate automate |
| `docs/ppt/backend-audit-probes.json` | Cinci probe directe de handler, fără a pretinde transport HTTP |
| `docs/ppt/*.inspection.json` | Extrase slide cu slide ale celor două prezentări inițiale |

Surse păstrate: `Template-Pitch-Hackathon.backup.pptx` nu a fost suprascris; `Template-Pitch-Hackathon.pre-audit.pptx` păstrează versiunea populată anterioară; `build_deck.pre-audit.py` păstrează generatorul anterior. `preview-pre-audit/` păstrează imaginile găsite inițial, iar `preview-template/` exportul efectuat asupra ghidului original. Dependența `defusedxml` necesară validatorului a fost instalată numai în `docs/ppt/.qa/deps`, fără modificarea manifestelor aplicației sau a instalării globale.

## Original versus reconstruit

Ambele surse aveau 16 pagini. Backup-ul era un ghid care cere explicit zece slide-uri de pitch și anexe; versiunea populată păstra pagini de instrucțiuni și dubla introducerea. Deck-ul final are **13 slide-uri**, păstrează dimensiunile **13⅓ × 7½ inch**, româna și ordinea celor zece secțiuni. Paginile de ghidaj nu apar în prezentarea juriului. Cele trei anexe urmează după închidere, pentru întrebări.

Reconstrucția păstrează masterele/layout-urile în pachet, pornește din copia prezentării populate și reutilizează paginile pitch/support. Conținutul vizual a fost redesenat, conform cererii. Nu s-a identificat un logo de organizator/sponsor obligatoriu. Autorul ghidului este atribuit în notele slide-urilor; nu este prezentat drept membru al echipei. Nu există în repository un regulament oficial care să impună cele 16 pagini sau designul ghidajului.

Îmbunătățiri vizuale: un singur titlu de produs; titluri mari, corp în general 20–28 pt; paletă derivată din aplicație; alternanță controlată navy/alb; margini și coloane consistente; diagrame native în locul listelor lungi; tabele native pentru alternative/metodă; capturi reale în locul unui pseudo-ecran textual; note pentru detalii. Nu există slide-uri rasterizate integral sau grafice decorative cu date inventate. Font: Calibri, cu diacritice verificate în randări. Tranziții: avans manual, fără animații automate.

## Deciziile de conținut și sursele

1. Produsul este prezentat ca prototip de planificare urbană, conform `README.md` și `docs/ARCHITECTURE.md`, nu ca optimizator complet de semafoare.
2. Capturile arată interfața actuală. Pe slide-ul demo apare explicit „date predefinite și ajustări locale”, deoarece `frontend/shared/core/fixtures.ts` și `frontend/web/src/features/comparison/ComparisonPanel.tsx` furnizează valorile și aritmetica locală.
3. FastAPI `/health`, serverul demo separat și utilitarele sim sunt delimitate conform `backend/main.py`, `backend/server.py`, `sim/smoke_test.py`, `sim/sumo_support.py`. Liniile întrerupte arată integrările urbane de construit; existența clientului non-demo `/analyze` este explicată în note.
4. AI generativ este **planificat**, nu integrat. Catalogul fix nu este prezentat ca apel LLM. Surse: server și arhitectură.
5. Au fost eliminate rezultatele neverificate de trafic, citatul fără interviu, parteneriatele, marjele, pragurile juridice și URL-urile publice neconfirmate. Nu s-au introdus înlocuitori fictivi.
6. Prețul de 1.500 euro/lună este păstrat din pitch-ul anterior **ca ipoteză nevalidată**. Exercițiul 10×18.000=180.000 euro/an este condițional, fără clienți sau venituri revendicate. Costurile de serving sunt necunoscute.
7. Numele echipei sunt păstrate din deck; descrierile contribuțiilor sunt susținute de istoricul Git. Roster-ul complet rămâne de confirmat, deoarece README menționează trei dezvoltatori.
8. Alternativele QGIS/SUMO și contextul PMUD sunt susținute prin paginile oficiale citate în cercetare și în notele slide-ului 3. Nu există benchmark de superioritate sau cost comparativ verificat.

Registrul complet de afirmații C01–C20 se află în `PROJECT_RESEARCH_FULL.md`. Fiecare slide are note native cu explicație, surse exacte și limite relevante.

## Validare de proiect efectuată

- `npm test`: **5 trecute / 5 definite**, teste de transport/fixtures cu fetch mock. Nu reprezintă code coverage sau validare end-to-end a serverului alternativ.
- `npm run typecheck`: **trecut** pe web, mobile și shared.
- `npm run build`: **trecut**, rute `/` și `/app`; prima încercare a întâlnit EPERM într-un director generat, rerularea autorizată în afara sandboxului a reușit.
- Cinci probe la nivel de handler: confirmă reutilizarea Podu Roș pentru Copou și diferența `alternative_level`/`alternative`. Fișierul brut este inclus; nu se prezintă ca test HTTP, deoarece conexiunea socket a fost restricționată în prima încercare.
- Browser local: selectare Podu Roș, previzualizare, scenarii, aplicare în UI și deschidere comparație, cu capturi noi.
- Testele Python, rularea SUMO, browser-smoke complet, Android pe dispozitiv și auditul WCAG complet **nu au fost rerulate**. Runtime-ul auditului nu conținea dependențele Python ale proiectului și checkout-ul nu avea `.venv`/uv utilizabil.

Pornirea Next a modificat automat `frontend/web/next-env.d.ts`; această modificare generată a fost readusă la conținutul inițial după oprirea serverului. Statusul Git final nu arată modificări funcționale urmărite în aplicație. Elementele `.agents/` și `skills-lock.json` erau deja neversionate la început și nu au fost schimbate de această sarcină.

## Validare PPTX și editabilitate

**PowerPoint instalat a deschis și exportat normal toate cele 13 slide-uri**, prin COM read-only, la PNG 1920×1080 și PDF. Toate imaginile au fost inspectate; slide-urile modificate au fost inspectate din nou după reexport. Nu s-a bazat concluzia doar pe cod sau contact sheets.

Prima rundă a detectat două casete insuficient de înalte: cererea finală de pe slide-ul 10 și regulile de statut de pe slide-ul 13. Casetele au fost mărite/repoziționate, iar slide-urile regenerate. Marginile celor două tabele au fost uniformizate cu restul grilei. Ultima rundă nu raportează depășiri.

Validatorul skill-ului local `scripts/office/validate.py` a fost rulat cu `--original Template-Pitch-Hackathon.backup.pptx`: **All validations PASSED!**. A fost necesar Python UTF-8 și un director temporar local pentru a evita limitările de encoding/temp Windows. Nu s-au modificat scripturile validatorului. ZIP-ul a trecut verificarea de integritate.

Inventarul final din `qa-results.json`: **142 forme cu text_frame (inclusiv noduri goale), două tabele native, două imagini, 14 conectori și 13 seturi de note native**. PowerPoint a măsurat **133 obiecte cu text efectiv**; niciun boundHeight/boundWidth nu depășește caseta cu peste 1 pt. Nicio formă nu depășește canvasul. Nu au rămas paranteze de completat sau ghidaje de template. Textul, tabelele și diagramele pot fi editate ca obiecte PowerPoint; imaginile de produs rămân raster, conform scopului lor. Nu s-a făcut un test de editare manuală în UI, dar obiectele native sunt verificate în pachet și în export.

SHA-256 backup original, neschimbat:
`56133b4d2fe6946ff4c5a246e4d0f8be0baa0ac2f6638a6e25f969994695d170`

SHA-256 PPTX final:
`e9d3cb96e1eedff92a3263a64e4483afa5bd05fb13be2e9c4ebf8f93e5a2f543`

## Inspecție vizuală pe slide

| Slide | Verificare finală |
|---|---|
| 1 | Titlu și public lizibile; captură autentică, proporții păstrate, statut prototip vizibil |
| 2 | Diagramă cu patru perspective, etichete separate și sursă lizibilă |
| 3 | Tabel cu alternative, margini corectate, surse și limită de validare distincte |
| 4 | Flux cu trei pași; prezent/viitor diferențiate clar |
| 5 | Captură și instrucțiuni separate; disclaimer demonstrativ vizibil |
| 6 | Exact trei componente principale; AI viitor și legături întrerupte explicite |
| 7 | Preț și eticheta „ipoteză nevalidată” împreună; fără marjă inventată |
| 8 | Calcul comercial condițional; lipsa validării nu este ascunsă în note |
| 9 | Nume și contribuții lizibile; fără advisory sau fotografii inventate |
| 10 | Caseta cererii corectată; închidere fără suprapunere cu ultimul rând |
| 11 | 5/5 explicat ca teste client, limitările Python/SUMO vizibile |
| 12 | Flux AI etichetat propus; fără apel LLM astăzi |
| 13 | Caseta regulilor corectată, tabel aliniat; lipsa impactului verificat vizibilă |

## Limite rămase și confirmări înainte de concurs

Nu există defecte de încadrare/text cunoscute în deck-ul final. Capturile sunt fragmente autentice ale viewport-ului disponibil în browser, nu capturi integrale de desktop de rezoluție mare. Detaliile fine ale UI-ului se arată mai bine în demo live; textul principal al prezentării rămâne nativ și lizibil. UI-ul capturat conține încă etichete excesive despre surse/metode; avertizarea de pe slide și notele explică faptul că datele nu sunt validate. Nu s-a retușat captura pentru a sugera alt produs.

Deck-ul respectă structura verificabilă a template-ului; lipsesc însă unele dovezi cerute de ghid: interviu real, trei urme independente ale nevoii, preț validat, cost per client și lista concretă de zece organizații. Au fost declarate ca lipsuri/ipoteze, nu completate fictiv. De aceea nu se afirmă că toate cerințele de dovezi ale unui pitch matur sunt îndeplinite.

De confirmat: durata și regulamentul oficial al concursului, eventualele condiții minime AI, roster-ul complet și rolurile de scenă, continuarea după hackathon, contactul și demo URL public, datele reale disponibile și dreptul de utilizare. AI/analiza reală/SUMO din UI rămân neintegrate în checkout; o prezentare nu remediază acest lucru. Nu se poate certifica eligibilitatea sau punctajul fără regulament.

Pentru repetiție: versiunea propusă de cinci minute include cele zece slide-uri; pentru trei minute se sare piața, conform ghidului. Se încheie pe slide-ul 10 și se deschid anexele numai la întrebare. Backup-ul de demo disponibil este captura, fără înregistrare video declarată. Aceste confirmări nu au împiedicat livrarea documentelor și a deck-ului onest.
