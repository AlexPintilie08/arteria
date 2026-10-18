# Profiluri profesionale relevante pentru ARTERIA

**Data evaluării:** 18 octombrie 2026  
Relevanța funcțională este justificată prin sarcini și capabilități din repository. Relevanța comercială, frecvența problemei și disponibilitatea de plată rămân neconfirmate până la cercetare și interviuri.

## Prioritizare provizorie

| Prioritate | Profil | Potrivire tehnică actuală | Certitudine de utilizator real |
|---|---|---|---|
| 1 | Analist GIS / analist de rețele pietonale | Ridicată pentru graf și conectivitate; UI-ul nu expune complet geometria rezultatelor. | Medie ca potrivire tehnică; niciun interviu documentat. |
| 2 | Planificator transport / specialist mobilitate urbană | Ridicată pentru comparații și dovezi; workflow-ul este fragmentat. | Ipoteză de produs, nevalidată. |
| 3 | Inginer trafic / specialist semaforizare | Limitată la un verde și un model sintetic; fără calibrare sau rețea. | Relevanță de domeniu, dar aplicația nu este instrument de inginerie validat. |
| 4 | Urbanist / planificator urban | Context de stradă/cartier; lipsesc indicatori și constrângeri urbanistice. | Ipoteză de produs. |
| 5 | Consultant de mobilitate / proiectare | O comparație simplă ar putea ajuta; lipsesc proiecte, export și audit trail. | Ipoteză comercială, fără clienți sau preț validat. |
| 6 | Administrație publică / autoritate de transport | Posibilă utilizare pentru prioritizare/revizuire; lipsesc date oficiale, aprobări și costuri. | Posibil cumpărător/gatekeeper, nu client confirmat. |
| 7 | Specialist accesibilitate pietonală / mobilitate activă | Tema grafului e relevantă; lipsesc bariere, pante, crossings și standarde. | Profil adiacent, potrivire parțială. |
| 8 | Inginer proiectant infrastructură / administrator stradal | Trebuie să verifice siguranță, drepturi și construcție; produsul declară aceste aspecte neevaluate. | Interlocutor de validare viitoare, nu beneficiar direct dovedit. |

Nu sunt considerați utilizatori confirmați șoferii, locuitorii, operatorii de transport public ori furnizorii de senzori: repository-ul nu are un flux real pentru ei. Pot fi participanți la cercetare, fără să-i numim utilizatori actuali.

## Analiza profilurilor

### 1. Analist GIS / analist de rețele pietonale

- **Sarcini:** verifică surse și limite, selectează rețeaua, găsește discontinuități, compară conectivitatea și justifică metoda.
- **Există:** catalog OSM și metadate; validare geometrie; achiziție walk; analiză graf, screening candidați, eșantion comun și packet de dovezi (NeighborhoodExplorer.tsx, sim-geography.ts, backend/spatial_worker.py, sim/analysis.py, sim/candidates.py, sim/impact.py).
- **Testat:** testele test_spatial_api.py rulează fixture-ul SIM offline; browserul a creat și evaluat un studiu fixture.
- **Lipsuri:** selectare cartografică integrală, desenarea rutelor/candidaților, export GIS din UI, compararea snapshot-urilor și QA de tagging.
- **UX:** tabel cu ID-uri tehnice; fixture etichetat greșit ca OSM; harta și rezultatul nu sunt legate vizual.
- **De cercetat:** criteriile GIS pentru acceptarea unei rețele pietonale, sursele locale și formatele necesare.

### 2. Planificator de transport / specialist în mobilitate urbană

- **Sarcini:** definește problema, compară moduri/opțiuni, analizează compromisuri pe zonă și justifică alternative.
- **Există:** context bookmark și timing sintetic; separat, studiu pietonal SIM cu baseline și efecte pentru perechi de noduri.
- **Lipsuri:** legătură între fluxuri; transport public, bike, cerere, acces la servicii pe populație, siguranță, cost și evaluare multicriterială.
- **UX:** analiza zonei pare geografică, dar aria este doar context pentru timing.
- **De cercetat:** workflow-ul real PMUD/studii de trafic, criteriile de comparare și datele disponibile în Iași.

### 3. Inginer de trafic / specialist semaforizare

- **Sarcini:** volume/viraje, geometrie, faze, timpi, cerere, cozi și siguranța pietonilor.
- **Există:** slider pentru verde N-S, model cu ciclu/pierderi/cerere fixe, indicatori de întârziere; backend-ul validează baseline-ul și intervenția.
- **Dovezi:** browserul a traversat API-ul complet; testele verifică tradeoff și respingerea parametrilor invalizi.
- **Lipsuri:** fluxuri măsurate, benzi/viraje, fazare, cozi, delay calibrat, LOS, pietoni, coordonare, SUMO integrat.
- **UX:** „minimal/moderat/transformativ” poate sugera amploare inginerească; schimbarea este o singură durată de verde.
- **De cercetat:** metodologiile și indicatorii acceptați de inginerii locali și datele minime de calibrare.

### 4. Urbanist / planificator urban

- **Sarcini:** compară amenajări, acces la servicii, spații publice și constrângeri.
- **Există:** hartă/catalog parțial, intervenții pietonale ipotetice, vizual conceptual.
- **Lipsuri:** parcelar, funcțiuni, spațiu public, planuri, acces universal, cost, reglementări și desenarea intervențiilor.
- **UX:** scena 3D este ilustrativă, nu model al unui loc; /app nu începe cu hartă.
- **De cercetat:** dacă urbanistul decide asupra acestor opțiuni, ce date și ce nivel de detaliu îi trebuie.

### 5. Consultant de mobilitate / firmă de proiectare

- **Sarcini:** studii pentru clienți, versionare scenarii, trasabilitate, comparație reproductibilă, livrabile.
- **Există:** comparație unică într-o sesiune, baseline și explicații.
- **Lipsuri:** conturi, proiecte, istoric, partajare, export PDF/GeoJSON, branding de raport, comentarii, audit trail și permisiuni.
- **UX:** SQLite păstrează rezultatul, dar aplicația nu are listă de proiecte sau flux de predare către client.
- **De cercetat:** workflow-ul firmelor, livrabilele, costul manual și disponibilitatea de plată. Tariful istoric din pitch nu e validare.

### 6. Administrație publică / autoritate de transport

- **Sarcini:** planifică investiții, verifică conformitatea, justifică bugete, consultă operatori și păstrează dosar.
- **Există:** câteva rezultate cu proveniență/limite și comparații.
- **Lipsuri:** limite legale, date oficiale, cost/mentenanță, standarde, aprobare, auth, multi-user, export administrativ și operare sigură.
- **UX:** OSM parțial nu echivalează cu datele oficiale municipale; fără proiecte/permisiuni nu e workspace instituțional.
- **De cercetat:** responsabilități, achiziții, PMUD/CTP, date publice și posibilitatea de pilot. Primăria/CTP sunt interlocutori ipotetici, nu parteneri confirmați.

### 7. Specialist accesibilitate pietonală / mobilitate activă

- **Sarcini:** continuitate walk/bike, traversări, pante, bariere și acces fără trepte.
- **Există:** bibliotecă SIM are funcții walk/cycle; UI-ul conectat expune un studiu walk.
- **Lipsuri:** worker-ul nu include features; lipsesc pante, trotuare, borduri, crossing, standarde, destinații și populații afectate.
- **UX:** „Acces pietonal” poate sugera accesibilitate universală, dar produsul calculează proprietăți de graf.
- **De cercetat:** standardele locale/UE și metodele de audit în teren.

### 8. Inginer proiectant infrastructură / administrator stradal

- **Sarcini:** verifică drepturi, utilități, proprietate, siguranță, cost și autorizare.
- **Există:** screening-ul exclude unele conflicte mapate și declară necunoscute costul/fezabilitatea.
- **Lipsuri:** cadastru, utilități, topografie, inspecție teren, coduri de proiectare, cost și avize.
- **Relevanță:** interlocutor de limitare a riscului; nu e utilizator direct demonstrat.
- **De cercetat:** dovezile obligatorii înaintea unei propuneri de graf să devină concept constructibil.

## Ce știm despre utilizatori

Codul dovedește că există sarcini explorabile; nu dovedește cine le face în organizații, cât durează procesul, cine aprobă ori cine plătește. Niciun profil nu este confirmat prin interviu, pilot, analytics sau scrisoare de intenție în repository.
