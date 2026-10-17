# ARTERIA — plan de design și reconstrucție

Plan încheiat după cercetare și conținut, înaintea generării PPTX. Surse: `PROJECT_RESEARCH_FULL.md`, `PITCH_CONTENT.md`, două prezentări inspectate și previzualizări originale. Utilizatorul cere elemente native editabile și preferă python-pptx; această cerință are prioritate față de autorul implicit recomandat de skill-ul presentations.

## 1. Inspecția originalului

Ambele fișiere au 16 pagini, 16:9, 13⅓ × 7½ inch (12192000 × 6858000 EMU). Backup-ul este ghidul original în română; versiunea populată păstrează două pagini de ghidaj și repetă coperta, deci numărul 16 nu reprezintă 16 slide-uri obligatorii de pitch. Layout-urile/masterele și textul integral sunt inventariate în `Template-Pitch-Hackathon.backup.inspection.json` și `Template-Pitch-Hackathon.inspection.json`.

| Pagina originală | Backup / rol | Versiunea populată / problemă | Tratament final |
|---|---|---|---|
| 1 | Copertă de ghid | Copertă ARTERIA încărcată, afirmații sub 5 s | Eliminată ca pagină de ghid; titlul pitch devine pagina 1 |
| 2 | Instrucțiuni pentru completare | Ghidaj încă prezent | Nu intră în deck-ul juriului |
| 3 | Ordine și timpi | Ghidaj încă prezent | Ordinea păstrată; timpii merg în note/document |
| 4 | Pitch 1: titlu | Repetă coperta și face promisiuni de simulare | Redesenat, minim, fără rezultate |
| 5 | Pitch 2: omul | Citat și cifre fără surse verificabile | Situație propusă, fără testimonial |
| 6 | Pitch 3: alternative | Costuri și comparații neverificate | QGIS, SUMO, PMUD cu surse primare |
| 7 | Pitch 4: soluție | Import/simulare/optimizare declarate complete | Parcurs UI și statut demonstrativ |
| 8 | Pitch 5: demo | Pseudo-ecran textual „simulare activă” | Captură reală, avertizare vizibilă |
| 9 | Pitch 6: construcție | Stack greșit și integrări neimplementate | Arhitectură actuală + legături viitoare marcate |
| 10 | Pitch 7: business | Prag legal, marjă, costuri neprobate | Preț ca ipoteză, costuri de validat |
| 11 | Pitch 8: piață | TAM/SAM și clienți prezumați | Cohortă de interviuri și calcul ipotetic |
| 12 | Pitch 9: echipa | Roluri exclusive/advisory inventate | Două nume păstrate, contribuții Git și limite în note |
| 13 | Pitch 10: cererea | Pilot și reducere trafic presupuse | Introducere la specialist + set de date |
| 14 | Anexe sugerate | Detalii dense și rezultate neprobate | Anexa A: verificări tehnice și limite |
| 15 | Q&A de pregătire | Răspunsuri care repetă afirmațiile neprobate | Anexa B: rolul AI planificat |
| 16 | Checklist de pregătire | Checklist care declară dovezi inexistente | Anexa C: condițiile evaluării; checklist în QA |

Nu există fotografii de produs sau logos instituționale obligatorii de păstrat. Template-ul folosește pictograme raster mici pentru ghidaj; nu sunt branduri de sponsori. Numele autorului ghidului se păstrează în note de atribuire/documentație, fără a-l prezenta ca membru ARION. Masters/layouts rămân în pachetul PPTX. Instrucțiunile originale cer eliminarea ghidajului; redesenarea paginilor pitch respectă această permisiune explicită.

## 2. Backup și trasabilitate

Backup-ul `.backup.pptx` nu se suprascrie. Copia populată anterioară este păstrată separat ca `Template-Pitch-Hackathon.pre-audit.pptx`; generatorul anterior ca `build_deck.pre-audit.py`. Generatorul final încarcă această copie, reține cele zece pagini de pitch (indicii originali 4–13) și trei pagini suport, șterge ghidajul și redesenează conținutul. Nu pornește de la o prezentare goală. Nu se fac modificări funcționale în frontend/backend/sim.

## 3. Sistemul vizual

Direcție: atelier cartografic sobru, derivat din identitatea produsului. Dominant navy `101820`, text alb `EDF2F6`, secundar `A8BAC9`, accent `8BC9ED`, avertisment `EFC47C`, verde discret `A4D8BC`. Slide-uri de conținut albe `FFFFFF` cu text navy, alternate intenționat cu pagini navy pentru titlu/demo/închidere/AI. Culorile au rol de ierarhie și statut, nu schimbare decorativă. Nu se folosesc gradienți, neon sau dungi decorative.

Tipografie: Calibri pentru compatibilitate Office și diacritice. Copertă 58–64 pt; titluri 34–38 pt; texte principale 20–24 pt; etichete 14–16 pt; surse min. 11 pt. Cifre comerciale 48–58 pt numai când sunt explicit ipotetice. Nu se micșorează corpul pentru a salva paragrafe; se taie conținutul secundar și se mută în note.

Grilă: margine x=0,65 inch, dreapta=12,68; titlu y=0,9–1,75; conținut y=2,15–6,4; sursă/folio y≈6,95. Gutter de 0,35–0,5 inch. Titluri și text aliniate la stânga. Diagramele folosesc noduri și conectori nativi strict pentru semnificația fluxurilor cerute; fără ilustrații programatice decorative. Un singur folio discret arată numărul și secțiunea P/R/O/B/A/business.

Textul rămâne editabil; tabelele sunt native, diagramele sunt forme/conectori PowerPoint. Nu se creează chart cu valori de trafic demonstrative. Capturile sunt singurele obiecte raster importante și nu acoperă un slide integral. Se păstrează proporțiile și atribuirea OSM. Capturile conțin UI-ul real, inclusiv etichete încă excesive; eticheta externă „date predefinite” este obligatorie.

## 4. Specificații pe slide

### 1 — Titlu

Fundal navy. ARTERIA ocupă aproximativ jumătatea stângă, 64 pt, apoi publicul 24 pt și scopul 20 pt. Captură workspace pe dreapta, până la 42% lățime, contain fără deformare. Dacă captura are un viewport îngust, se păstrează proporția și se alocă suficient loc. „Prototip demonstrativ” în amber, 14 pt, separat de sursă. Note: introducere, C01/C02, atribuirea șablonului. Tranziție: click simplu.

### 2 — Problemă

Fundal alb. Titlu 36 pt, propoziția despre utilizator 24 pt. Diagramă nativă de decizie cu intervenția și patru perspective (nu KPI): transport, pietoni, biciclete, auto. Ocupă 55–60% din zona utilă. Legăturile au rol de dependență, nu cauzalitate măsurată. Subsol 14 pt precizează că interviurile urmează. Note: situație ipotetică, fără citat/cost inventat. Click simplu.

### 3 — Alternative

Fundal alb. Tabel nativ cu trei rânduri, primele coloane nume/rol, fără panouri. Titlu 36 pt, tabel 21 pt; rânduri de circa 0,85 inch. Takeaway 24 pt sub tabel; surse pe rând separat la 11 pt. Note: URL-uri primare, fără benchmark. Click simplu.

### 4 — Soluție

Fundal navy. Titlu 36 pt. Flux pe o singură linie cu trei noduri native, ocupând 70% lățime și circa 1,5 inch înălțime. Numere 01/02/03 la 36 pt; etichete 22 pt, conectori simpli. Delimitarea prezent/viitor pe două rânduri 19 pt sub flux. Note: catalog fix și ajustări locale. Click simplu.

### 5 — Demo

Fundal navy, conținut pe două coloane: explicații 34%, captură comparație 62%, gutter 4%. Titlu 36 pt. Trei acțiuni scurte 21 pt. Disclaimer amber 18–20 pt, poziționat lângă captură, nu ascuns în footnote. Captura contain, pe fundal neutru, cu atribuirea OSM dacă apare harta; interfața nu este redesenată artificial. Adresa localhost este text de lucru, nu QR public. Note: demo de 75 s și plan B captură, fără afirmație de video înregistrat. Click simplu; fără animație automată.

### 6 — Arhitectură

Fundal alb. Trei componente principale editabile pe orizontală, nod AI sub backend; descrieri 19–20 pt și titluri 24 pt. Conectorii către analiza urbană și LLM sunt întrerupți, cu legendă 14 pt. Sunt denumite exact limitele FastAPI și serverului demo. Spațiu liber de minimum 0,3 inch între noduri; niciun conector nu trece prin cuvinte. Note: scheme incompatibile, sim smoke, fără provider. Click simplu.

### 7 — Business

Fundal alb. Preț 56 pt în stânga, „ipoteză nevalidată” imediat sub el la 20 pt. Cumpărător/valoare/costuri în dreapta, 21 pt, trei blocuri de text deschise, fără badge-uri. Ultimul rând „niciun client confirmat” la 17 pt. Sursa ipotezei și anul lângă preț. Note: fără marjă, prag legal sau cost de serving inventat. Click simplu.

### 8 — Piață

Fundal alb. Planul de interviuri în jumătatea superioară, etichete 22 pt. Calcul 10×18.000=180.000 într-un rând 34 pt, numai pe fondul ipotezei vizibile la 18 pt. Nu se folosesc cercuri TAM/SAM sau bar chart de venituri. Surse: ipoteze proprii/preț preexistent, 2026. Note: nu există lista celor zece sau conversii. Click simplu; se sare manual la pitch de trei minute.

### 9 — Echipa

Fundal navy. Două coloane simetrice, nume 30–32 pt, contribuții 22 pt. Fără poze sintetice, logos sau titulaturi C-level. Mențiune discretă despre istoricul Git. Un rând 21 pt despre nevoia de specialist de domeniu. Note: roster/roluri finale și disponibilitate de confirmat, fără „full-time”. Click simplu.

### 10 — Închidere

Fundal navy. Titlu 36 pt. Roadmap nativ în trei pași, 21 pt, circa 1,1 inch înălțime. Cererea ocupă 50% din atenție: maximum trei rânduri la 30 pt. Metrica de validare 19 pt între roadmap și cerere. Final 24 pt. Nu se inventează email/site public. Note: stop la încheiere și deschidere anexe numai la întrebări. Click simplu.

### 11 — Anexa A / dovezi

Fundal alb. „5/5” 64 pt, „teste client API” 24 pt. Typecheck/build în două rânduri de 22 pt, apoi limite la 18 pt. Sursă/an vizibile. Fără procent de acoperire. Note: fetch mock, Python și SUMO nereexecutate. Click simplu.

### 12 — Anexa B / AI

Fundal navy. Flux editabil cu patru pași; tip 19–21 pt, minimum 0,3 inch gutter. Legături întrerupte și etichetă „flux propus” la 16 pt. Linia „catalog fix, fără LLM” la 23 pt în amber, vizibilă. Axioma despre recomandare/măsurătoare la 24 pt. Note: validare schema + spațiu + specialist și calcule separate. Click simplu.

### 13 — Anexa C / metodă

Fundal alb. Tabel nativ cu trei rânduri date/comparație/simulare, 19–20 pt. Reguli de statut într-un rând distinct sub tabel. Declarația lipsei impactului verificat la 18 pt. Note: reproductibilitate, surse, calibrare și limite de producție. Click simplu.

## 5. Implementare și QA

Generatorul nou folosește componente Python reutilizabile pentru titlu, text, tabel, nod/legătură și captură contain. Toate coordonatele folosesc inch și sunt verificate față de canvas. Notele sunt native. Nu se aplică scriptul vechi de fade care presupune 16 slide-uri; se folosește avans manual, fără tranziții spectaculoase.

După generare: se verifică deschiderea cu python-pptx și integritatea ZIP/XML, se rulează validatorul skill-ului cu `--original` backup, se deschide prin PowerPoint și se exportă fiecare slide la PNG 1920×1080. Se măsoară boundHeight/boundWidth pentru text, se inspectează fiecare randare și se corectează elementele problematice. Contact sheets ajută consistența, dar nu înlocuiesc inspecția full-size a slide-urilor. Se reexportă după modificări. Nicio afirmație de QA vizual nu se bazează numai pe generator.

Raportul final include diferențele față de original, trasabilitatea afirmațiilor, limitările de date/testare, editabilitatea și aspectele care trebuie confirmate înainte de concurs. Backup-urile rămân intacte, iar codul aplicației nu se repară în această sarcină.
