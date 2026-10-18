# Roadmap de cercetare — Etapa 2 propusă

Etapa 2 nu a început. Nu s-au căutat în Etapa 1 standarde profesionale, legislație, piață, produse concurente sau date municipale.

## Priorități

### R1 — Validarea profilului și sarcinilor

- **Întrebări:** cine selectează intervenția, cine o analizează și cine aprobă? Ce rol folosește GIS pietonal, timing sau comparații înainte/după? Cum lucrează planificatori, ingineri, consultanți și administrații?
- **Metodă:** interviuri ghidate cu profilurile prioritare din PROFESSIONAL_USER_PROFILES.md; observarea cazului recent și a artefactelor de lucru, cu acord.
- **Rezultat:** hartă de sarcini, actori, frecvență, date de intrare și criterii de acceptare.
- **Limită actuală:** repository-ul descrie intenții, nu practică profesională.

### R2 — Date și metodologii pentru Iași

- **Întrebări:** ce surse actuale există pentru limite, trotuare, crossings, trafic, semafoare, transport public, accesibilitate și accidente? Cine le deține și cu ce licență?
- **Metodă:** cercetare în surse oficiale și documente primare (Primărie, PMUD, CTP/autoritate și seturi open-data dacă există); înregistrarea provenienței, datei, acoperirii și drepturilor.
- **Rezultat:** matrice sursă–indicator–acoperire–licență–responsabil–actualizare.
- **Limită actuală:** disponibilitatea acestor seturi nu a fost confirmată în Etapa 1.

### R3 — Metode și standarde profesionale

- **Trafic:** metode acceptate pentru capacitate, întârziere, LOS, fazare și calibrare; versiune și jurisdicție.
- **Pietonal/accesibilitate:** criterii aplicabile pentru pante, traversări, continuitatea trotuarului, bariere și acces universal.
- **Rezultat:** pentru fiecare indicator: definiție, intrări, metodă, unități, calibrare. Nu comparați output-ul ARTERIA la standard înainte de stabilirea metodei.

### R4 — Validarea geografică SIM/OSM

- **Întrebări:** cât diferă graful/limitele OSM de observația în teren, hărți oficiale și trasee accesibile? Cât de stabile sunt rezultatele între snapshot-uri?
- **Metodă:** studiu bounded, revizie de specialist GIS, field walk și comparație pe link-uri/crossings; salvați snapshot și geometrie.
- **Rezultat:** protocol QA geografic și tipuri de eroare; nu generalizați dintr-o zonă la oraș.

### R5 — Workflow și alternative

- **Întrebări:** cum combină profesioniștii QGIS/ArcGIS, SUMO, spreadsheets și procese PMUD? Ce cost manual se măsoară? Ce e complementar?
- **Metodă:** documentație oficială a uneltelor și comparație de sarcini demonstrabile; fără superioritate nebenchmark-uită.
- **Rezultat:** matrice capabilitate–workflow–limită–dovadă.

### R6 — Procurement, securitate și deployment

- **Întrebări:** cine poate contracta un pilot și ce hosting, SSO, retention, accessibility/security review și date sunt necesare?
- **Metodă:** surse oficiale de achiziții/politici IT și discuții cu responsabili instituționali.
- **Rezultat:** condiții de pilot și cerințe operaționale înaintea conturilor, stocării extinse sau AI cloud.

### R7 — Business și impact

- **Întrebări:** ce cost măsurabil există la pregătirea analizei, ce buget și frecvență au cumpărătorii?
- **Metodă:** interviuri de descoperire; test de preț doar după validarea problemei; caz cu baseline și rezultat observat.
- **Rezultat:** separarea dovezilor pentru utilizare, cumpărător, buget și impact. Prețul din pitch nu este fapt.

## Ordine sugerată

1. R1: interviuri și observarea sarcinilor; alegeți profil și caz bounded.
2. R2 + R3: surse de date și metodele pe care participantul le folosește.
3. R4: verificare de teren/snapshot dacă drepturile și accesul sunt clare.
4. R5 + R6: workflow, alternative, procurement și operare.
5. R7: valoare economică după confirmarea problemei.

## Reguli de cercetare

- Prioritizați documente primare, date oficiale și metode cu versiune/jurisdicție; salvați linkul exact, autorul, datele publicării/consultării și limitele.
- Separați afirmația sursei de interpretare și marcați inferențele.
- Feedback-ul unui singur specialist nu este validare de piață.
- Nu trimiteți informații private către servicii externe fără scop și acord.
- Modificările aplicației rămân în afara roadmap-ului; utilizatorul va analiza și aproba Etapa 1 înainte de Etapa 2 sau implementare.
