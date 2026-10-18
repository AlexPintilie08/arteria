# ARTERIA — conținutul prezentării

Sursa de adevăr: `PROJECT_RESEARCH_FULL.md`, încheiat înaintea acestui document. Română, conform template-ului. Zece slide-uri de pitch în ordinea originală, apoi trei anexe. Numerele de rezultate sunt limitate la verificări tehnice; nu se revendică efecte de trafic. Plan principal: cinci minute. Timpii sunt ținte de repetiție, nu o regulă oficială de concurs.

## 1. Titlu — ARTERIA

**Scop:** identificarea produsului și a utilizatorului. **Mesaj:** comparație de intervenții urbane pentru specialiști.

**Text exact:**

> ARTERIA
> Planificare urbană pentru echipele de mobilitate
> Compararea intervențiilor, înainte de implementare
> ARION · Hackathon AI Iași 2026
> Prototip demonstrativ

**Dovezi:** C01, C02. **Vizual:** compoziție tipografică dominantă; captură autentică a hărții din workspace în jumătatea dreaptă, cu atribuirea OSM păstrată. Nu se desenează o hartă cadastrală fictivă.

**Verbal:** „Un specialist în mobilitate trebuie să explice ce se schimbă într-un cartier înainte de lucrări. ARTERIA este prototipul nostru pentru această comparație.” Titlul poate sta pe ecran înainte de cronometru; se bugetează totuși 5 s în repetiția de cinci minute.

**Tranziție:** specialistul și decizia sa → problema.

## 2. Omul și durerea — O intervenție. Mai multe efecte.

**Scop:** focalizarea pe decizia specialistului. **Mesaj:** o schimbare cere explicarea compromisurilor.

**Text exact:**

> O intervenție. Mai multe efecte.
> Utilizator vizat: specialistul în mobilitate
> Reconfigurarea unei străzi cere o comparație explicabilă.
> Transport public / Pietoni / Biciclete / Trafic auto
> Ce se schimbă? Pe ce date ne bazăm?
> Nevoie propusă; interviurile cu utilizatori urmează.

**Dovezi:** C01; documentația arhitecturală. Aceasta este o situație de utilizare propusă, fără citat inventat și fără cost numeric. **Vizual:** diagramă nativă de decizie: o intervenție centrală conectată la cele patru perspective, fără săgeți care implică beneficii deja măsurate.

**Verbal (40 s):** descrierea unei discuții de planificare la nivel de cartier. Explicarea motivului pentru care un indicator auto nu este suficient. Nu se atribuie cuiva o experiență reală neintervievată. „Vom verifica această nevoie cu un specialist înainte de a extinde produsul.”

**Tranziție:** ce instrumente există pentru această muncă.

## 3. Dovezi și alternative — Instrumentele există. Integrarea rămâne de construit.

**Scop:** recunoașterea alternativelor și a contextului. **Mesaj:** diferențierea propusă este parcursul de decizie.

**Text exact:**

> Instrumentele există
> QGIS — date și analiză geografică
> SUMO — simulare microscopică de trafic
> PMUD Iași — context de planificare locală
> ARTERIA propune un parcurs comun: zonă → alternative → comparație
> Avantajul de utilizare trebuie validat cu specialiști.
> Surse: qgis.org · sumo.dlr.de · Primăria Iași; consultate 2026

**Dovezi:** sursele externe primare din cercetare §4–5. Nu se fac afirmații despre costurile concurenților sau incapacitatea lor de a compara. **Vizual:** tabel nativ cu trei rânduri și o propoziție distinctă despre integrare. Fără logo-uri copiate sau chart de cote de piață.

**Verbal (40 s):** „Nu pornim de la lipsa instrumentelor. Propunem să legăm selecția unei zone și alternativele într-o experiență inspectabilă. PMUD arată contextul instituțional; nu este validare comercială a produsului nostru.” Se recunoaște lipsa a trei dovezi independente de nevoie cerute de ghid.

**Tranziție:** forma concretă a soluției propuse.

## 4. Soluția — Parcursul unei comparații

**Scop:** explicarea produsului într-un flux. **Mesaj:** o singură cale ușor de urmărit.

**Text exact:**

> Parcursul unei comparații
> 01 Alege zona
> 02 Examinează alternativele
> 03 Compară scenariul
> Astăzi: API conectat și studii pe graf pietonal
> Urmează: calibrare și validare cu un specialist

**Dovezi:** C02–C05. **Vizual:** flux editabil cu trei noduri; sub el delimitarea prezent/viitor, pe două rânduri deschise, fără panouri repetitive.

**Verbal (15 s):** „Am conectat interfața la API. Semaforizarea folosește date sintetice; separat, studiile pietonale evaluează alternative pe graf.”

**Tranziție:** demonstrație pe Podu Roș.

## 5. Demo — Podu Roș, în prototip

**Scop:** arătarea parcursului real din UI. **Mesaj:** navigarea și reglajele funcționează, datele nu validează impactul.

**Text exact:**

> Podu Roș, în prototip
> Selectează reperul → Alege o alternativă → Deschide comparația
> DEMO: API conectat, date sintetice
> Semaforizare estimată; fără SUMO din interfață
> Demo local verificat: localhost:3001/app
> Captură din aplicația existentă · OpenStreetMap © contributori

**Dovezi:** C02–C05; browser local și capturi în `assets/`. **Vizual:** captură autentică a comparației, dominantă (circa 65% din slide). Textul de avertizare trebuie să fie lizibil, independent de etichetele posibil excesive din UI. Captura nu este o reconstrucție inventată.

**Verbal / demo (75 s):** alege Podu Roș, analizează prin API, deschide propunerile, setează verde nord–sud la 70 s și compară. Verificarea conectată arată compromisul: nord–sud scade, est–vest crește. Modelul este sintetic. „Aceste valori ilustrează interacțiunea. Nu sunt rezultate măsurate la Podu Roș.” Dacă live-ul nu este disponibil, se folosește captura; nu se declară că există înregistrare video. Site-ul public anterior nu se promovează fără verificare.

**Tranziție:** ce componente susțin prototipul și ce lipsește.

## 6. Cum e construit — Frontend · Backend · Sim

**Scop:** credibilitate tehnică fără confuzie între plan și cod. **Mesaj:** separarea componentelor și a rolului AI.

**Text exact:**

> Frontend · Backend · Sim
> Frontend — Next.js / MapLibre; client API conectat
> Backend — FastAPI / Pydantic / SQLite; analiză, propuneri, evaluare
> Sim — graf pietonal / candidați / dovezi; SUMO opțional local
> AI planificat — alternative structurate, validate înainte de evaluare
> Linii continue: implementat · întrerupte: AI viitor
> Stack și stare: surse repository, audit 2026

**Dovezi:** C06–C11, C15. **Vizual:** diagramă editabilă cu exact trei componente principale, provider AI separat ca dependență viitoare. Legături frontend→backend→sim continue pentru fluxurile implementate. LLM separat, întrerupt. Semaforizarea rămâne sintetică; studiile spațiale folosesc graf și candidați validați.

**Verbal (30 s):** „Web-ul este conectat la FastAPI, cu validare Pydantic și persistență SQLite. SIM evaluează grafuri pietonale și candidați. Semaforizarea este sintetică. SUMO local este opțional, fără legătură la UI; providerul LLM rămâne viitor.” Autorii decid arhitectura; ponderea codului generat de AI nu este stabilită.

**Tranziție:** cine ar cumpăra această experiență dacă nevoia se confirmă.

## 7. Cine plătește — Model economic de testat

**Scop:** cumpărător și sustenabilitate explicite. **Mesaj:** model comercial ipotetic, fără venituri pretinse.

**Text exact:**

> Model economic de testat
> Cumpărător vizat: administrație locală / consultanță de mobilitate
> 1.500 € / lună
> Ipoteză de abonament, nevalidată
> Valoare de verificat: timpul pregătirii unei comparații
> Costuri de măsurat: date, calcul și suport
> Niciun client plătitor confirmat
> Sursă preț: ipoteza din pitch-ul anterior, 2026

**Dovezi:** C16; cercetare §17. **Vizual:** preț tipografic mare și o coloană de argumente scurte, fără grafic de venituri sau marjă.

**Verbal (30 s):** prețul este punct de plecare pentru interviuri, nu tarif probat. Primul pilot validează utilitatea înainte de vânzare. Nu se promit proceduri juridice, fonduri sau achiziție rapidă.

**Tranziție:** cum se testează cererea de jos în sus.

## 8. Piață și primii clienți — Primii utilizatori, înainte de extindere

**Scop:** plan de acces la piață și calcul transparent. **Mesaj:** prospectarea se construiește, nu este o bază de clienți.

**Text exact:**

> Primii utilizatori, înainte de extindere
> Iași: primul specialist și un caz de lucru
> Apoi: listă de 10 organizații de intervievat
> Canal propus: introduceri prin mentori și comunități de mobilitate
> Exercițiu comercial: 10 × 18.000 € = 180.000 € / an
> Scenariu ipotetic; organizațiile și conversia nu sunt validate
> Ipoteze de lucru, 2026 · Nu reprezintă venit sau piață măsurată

**Dovezi:** C16 și lipsurile declarate în cercetare §17. **Vizual:** progresie geografică textuală Iași→interviuri→replicare; calcul nativ într-un singur rând, fără TAM global inventat.

**Verbal (20 s):** „Primăria și CTP Iași sunt posibile interlocutoare, nu parteneri confirmați. Lista de zece organizații trebuie construită. Calculul arată numai mecanica abonamentului dacă toate cele zece ar cumpăra.” Pentru trei minute se sare acest slide, conform ghidului.

**Tranziție:** cine a construit baza vizibilă.

## 9. Echipa — ARION

**Scop:** prezentarea echipei complete. **Mesaj:** trei responsabilități confirmate direct de utilizator.

**Text exact:**

> ARION
> Iustin Fagateanu
> Frontend and web experience
> Alex Pintilie
> Bootstrap and simulation foundation
> Fagateanu Eusebiu
> Backend
> Responsabilități confirmate de echipă
> Următoarea nevoie: validare cu un specialist în mobilitate

**Dovezi:** C17; componența și responsabilitățile exacte sunt confirmate de utilizator în cerința V2 din 18 octombrie 2026. Codul și Git nu stabilesc autorul fiecărui handler; nu atribuim endpoint-uri sau module individuale lui Eusebiu. **Vizual:** trei profiluri egale, aceleași dimensiuni și aceeași ierarhie; fără ranguri sau fotografii inventate.

**Verbal (20 s):** „Iustin lucrează la frontend și experiența web, Alex la bootstrap și baza de simulare, iar Fagateanu Eusebiu la backend. Pentru următoarea etapă căutăm validare cu un specialist în mobilitate.” Rolurile de scenă și continuarea după eveniment rămân de stabilit; roster-ul tehnic este confirmat. Nu se declară exclusivitate pe fișiere sau disponibilitate full-time.

**Mișcare:** același Fade de 0,4 s pentru fiecare profil, într-un singur grup de click cu succesiune scurtă, fără diferențe de rang.

**Tranziție:** pasul concret și cererea către juriu.

## 10. Ce urmează — Prima comparație pe date verificate

**Scop:** închidere și cerere acționabilă. **Mesaj:** un pas măsurabil înaintea extinderii.

**Text exact:**

> Prima comparație pe date verificate
> Date documentate → Calibrare și verificare → Test cu un specialist
> Măsurăm timpul pregătirii comparației și trasabilitatea rezultatului.
> Cererea noastră: o introducere către un specialist și acces la un set de date local.
> Un caz verificabil. Apoi extindere.

**Dovezi:** roadmap și criterii recomandate, nu un angajament semnat. **Vizual:** roadmap editabil cu criterii de ieșire și o cerere dominantă. Fără deadline arbitrar sau reducere de trafic țintă prezentată ca validată.

**Verbal (25 s):** „Vom documenta o zonă, verifica indicatorii și calibra ipotezele modelului. Cu un specialist vom măsura cât durează pregătirea comparației și dacă rezultatul se poate verifica. Căutăm introducerea și datele pentru acest prim caz.” După cerere, prezentarea se oprește.

**Tranziție:** numai la întrebări, către anexe.

## 11. Anexa A — Ce este verificat astăzi

**Scop:** răspuns la „ce merge?”. **Mesaj:** teste tehnice, nu impact urban.

**Text exact:**

> Ce este verificat astăzi
> 9 / 9 teste frontend
> Typecheck: web · mobile · shared
> Build web: / și /app
> API și graf pietonal implementate; calibrarea rămâne de făcut
> AI cloud și SUMO din UI — neintegrate
> Sursă: verificări locale ale repository-ului, 2026

**Dovezi:** C12–C14, §14; 138 teste Python/backend/SIM trecute în runtime QA izolat (1 avertisment de depreciere), fără execuție SUMO. **Vizual:** cifra mare 9/9, două rânduri de rezultate și un rând clar de limite. **Verbal:** testele Node acoperă transportul API și geografia; nu probează impactul urban. SUMO necesită binare externe și calibrare. **Tranziție:** rolul AI.

## 12. Anexa B — Rolul AI în fluxul propus

**Scop:** răspuns tehnic și transparență. **Mesaj:** sugestii separate de verificare.

**Text exact:**

> Rolul AI în fluxul propus
> Dovezi și catalog → LLM viitor → Reguli și geometrie → Evaluare
> Astăzi: propuneri deterministe și validare
> Planificat: provider LLM; decizia rămâne la specialist
> O recomandare nu constituie o măsurătoare.
> Sursă: docs/ARCHITECTURE.md; stare verificată în cod, 2026

**Dovezi:** C08, C15. **Vizual:** patru pași nativi cu legăturile către LLM viitor întrerupte și evaluarea implementată continuă. **Verbal:** validarea de schemă este necesară, dar nu suficientă; sunt necesare reguli spațiale și calcule independente. Nu se cuantifică autorie AI a codului. **Tranziție:** metodologia de validare.

## 13. Anexa C — Condițiile unei evaluări credibile

**Scop:** răspuns la întrebările de date/metodă. **Mesaj:** inputuri și rezultate reproductibile înaintea promisiunilor.

**Text exact:**

> Condițiile unei evaluări credibile
> Date: sursă, dată, acoperire, licență
> Comparație: aceeași zonă și aceeași metodă
> Simulare: cerere documentată, versiune, seed și rezultate păstrate
> Lipsă date → necunoscut
> Propunere AI → ipoteză
> Rulare repetată → rezultat verificabil
> Nu există încă efecte de trafic validate în repository.

**Dovezi:** C15, C19; SUMO Calibrator și arhitectură. **Vizual:** tabel nativ „intrare / condiție de acceptare”, cu etichete textuale în loc de procente. **Verbal:** diferența între observed/calculated/estimated/unknown; etichetele singure nu probează proveniența. Auth, jobs și Android complet rămân etape viitoare; persistența SQLite există. **Tranziție:** revenire la cererea de pe slide-ul 10.

## Reguli de folosire și repetiție

Buget de cinci minute: 5+40+40+15+75+30+30+20+20+25 = 300 s. Acestea sunt ținte; se repetă și se scurtează verbal dacă nu încap. Anexele nu intră în pitch. Pentru trei minute se folosește ordinea ghidului cu slide-ul de piață sărit; nu se mută business/echipa înaintea demo-ului.

Fiecare slide include note editabile cu explicația, sursele exacte și limitele. Sursele externe sunt link-uri în note și surse scurte pe slide-ul 3. Fără citate fictive, statistici de trafic, logo-uri instituționale, URL public neverificat, QR inventat sau promisiune de pilot semnat. Aspectele de confirmat din cercetare rămân în QA, fără a bloca livrarea deck-ului demonstrativ.
