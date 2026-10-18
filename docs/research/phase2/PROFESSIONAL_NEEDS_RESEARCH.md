# Cercetarea nevoilor profesionale

**Cercetare documentară:** 18 octombrie 2026. Nu au fost realizate interviuri, observații de lucru sau teste cu specialiști. Prin urmare, responsabilitățile descriu rolurile din documente profesionale și administrative; problemele specifice ARTERIA sunt inferențe din discrepanța dintre aceste sarcini și aplicația inspectată.

## Constatări pe scurt

1. Cererea profesională cu cea mai directă potrivire cu ARTERIA este analiza unei probleme spațiale și compararea unor alternative pietonale pe același graf. Analistul GIS poate verifica datele, dar interfața curentă nu le oferă geometria rezultatelor sau export GIS.
2. Planificarea transportului este multimodală, teritorială, participativă și bazată pe monitorizare; nu se reduce la reglarea unui singur semafor sau la conectivitatea unui graf. Ghidul PMUD românesc din 2025 cere diagnostic, model de transport pentru municipalități/ZUF peste 100.000 locuitori, colectarea cererii, calibrare/validare, prognoze și scenarii cu impact pe eficiență, mediu, accesibilitate și siguranță [Ghidul PMUD, 22 octombrie 2025](https://legislatie.just.ro/Public/FormaPrintabila/00000G013NPGKH2Q66M0MUBJZTGP02MX). Acestea sunt cerințe ale documentului strategic, nu criterii pe care o singură aplicație trebuie să le implementeze integral.
 3. În ingineria semaforizării, datele de intrare includ volume, viraje, cozi, timing-ul existent, viteze și fluxuri pietonale/biciclete. FHWA descrie aceste date și indicatorii de control delay, travel time și percentile de coadă; legislația românească este jurisdicția care trebuie urmată în implementare [FHWA data applications](https://www.fhwa.dot.gov/policyinformation/pubs/traffic-data-applications-highlights/traffic-data-for-operations.cfm), [FHWA Signal Timing Manual, capitolele 2–3](https://ops.fhwa.dot.gov/publications/fhwahop08024/chapter2.htm), [Legea 155/2023](https://legislatie.just.ro/Public/DetaliiDocument/270923).
 4. Accesibilitatea universală cere atribute de infrastructură și audit în teren pe care OSM-ul uzual nu le garantează. Legea românească trimite explicit la NP 051 pentru configurația circulațiilor pietonale; EN 17210:2021 acoperă și zonele pietonale exterioare, iar revizuirea standardului este în curs în 2026 [Ordinul de aprobare NP 051-2012](https://legislatie.just.ro/Public/DetaliiDocument/145914), [NP 051 menționat în reglementări](https://legislatie.just.ro/public/DetaliiDocument/264751), [CEN-CENELEC, 26 februarie 2026](https://www.cencenelec.eu/news-events/news/2026/en-in-the-spotlight/2026-02-26-en-17210-2021/).
 5. În Iași există resurse publice concrete de investigat: PMUD Iași pentru 2021–2035, portal local de date deschise și date de transport public în GTFS, inclusiv date actualizate la 20 de secunde conform CTP. Disponibilitatea publică nu dovedește automat dreptul de reutilizare comercială, acoperirea sau completitudinea datelor [HCL 403/31.10.2023](https://www.primaria-iasi.ro/dm_iasi/hotarari.nsf/352F4896F69AD4A9C2258A6D00440C3B/%24FILE/HCL_403_2023.pdf?Open=), [CTP Iași Open Data](https://www.sctpiasi.ro/servicii/opendata), [Portal Open Data Iași](https://iasi.oras.digital/).

## Profiluri, sarcini și utilitate posibilă

### 1. Analist GIS / analist de rețele pietonale — prioritate de descoperire ridicată

- **Responsabilități și activități:** verifică referința geografică, geometria, topologia, acoperirea și atributele; pregătește rețele; rulează rutare, arii de serviciu și analize comparative; documentează sursa, metoda și exportul. QGIS documentează shortest-path și service-area cu ieșiri vectoriale salvabile în GeoPackage, fișier sau bază de date [QGIS Network Analysis, versiunea 3.44](https://docs.qgis.org/3.44/en/docs/user_manual/processing_algs/qgis/networkanalysis.html).
- **Date:** graf rutabil pentru modul corect, crossings/permisiuni, delimitare de studiu, puncte OD sau destinații, snapshot și CRS; pentru accesibilitate, sidewalks, pante, suprafețe și bariere, dacă sunt analizate.
- **Fricțiune documentată:** snap incorect al punctelor îndepărtate poate genera trasee fără sens; QGIS a adăugat prag de distanță opțional în 3.38–3.40 [issue QGIS #9029](https://github.com/qgis/QGIS-Documentation/issues/9029). O problemă deschisă documentează intersecții false între linii suprapuse în plan dar separate vertical (#63045); este un raport singular, nu o rată generală de defecte [issue QGIS #63045](https://github.com/qgis/QGIS/issues/63045).
- **Instrumente și livrabile:** QGIS/ArcGIS, OSMnx/NetworkX, shapefile, GeoPackage, GeoJSON, hărți și tabel de metodă. Cerința românească PMUD din 2025 indică GeoPackage pentru seturile spațiale asociate.
- **Precizie și nevoie ARTERIA:** trebuie să vadă geometria analizată, nodurile OD, traseele/candidații, elementele ne-rutabile și proveniența. ARTERIA oferă analiză de graf pe fixture/OSM și comparații pe eșantion, dar nu randare a rezultatelor spațiale și export GIS în UI. Reutilizarea candidată: hartă cu sursă/legendă și raport de validitate; ar necesita confirmare cu utilizatori.

### 2. Planificator transport / specialist mobilitate — prioritate de descoperire ridicată

- **Responsabilități și activități:** leagă dezvoltarea urbană și nevoile de transport persoane/mărfuri, evaluează alternative pe scara cartier–oraș–zonă funcțională, lucrează cu instituții și public, monitorizează rezultate. Legea 155/2023 și Ghidul PMUD 2025 descriu aceste domenii; Comisia Europeană recomandă acoperirea zonei urbane funcționale și utilizarea fluxurilor reale [Legea 155/2023](https://legislatie.just.ro/Public/DetaliiDocument/270923), [Ghid PMUD](https://legislatie.just.ro/Public/FormaPrintabila/00000G013NPGKH2Q66M0MUBJZTGP02MX), [Comisia Europeană, SUMP monitoring](https://transport.ec.europa.eu/transport-themes/urban-transport/sustainable-urban-mobility-planning-and-monitoring_en).
- **Date:** rețele și cerere pe moduri, GTFS și performanța serviciului, sondaje/OD, populație și activități, proiecte aprobate, costuri, accidente, emisii și date ex-post. Datele necesare depind de decizia examinată.
- **Fricțiune susținută:** fragmentarea nu este demonstrată de interviuri. Sursele oficiale descriu integrarea și coordonarea ca cerințe de proces, iar GTFS furnizează un format standardizat pentru serviciu. A presupune că orice planificator are aceeași problemă de integrare ar depăși dovezile.
- **Instrumente și livrabile:** GIS, software de model de transport, foi de calcul, documentație PMUD/GIS și scenarii cu indicatori, surse, ipoteze și calendar.
- **Nevoie ARTERIA:** un dosar comparabil între scenarii, în aceeași arie și perioadă, cu indicatori multimodali și incertitudine. Azi oferă un demo de timing sintetic și un flux pietonal separat, fără modelare integrată/cerere reală.

### 3. Inginer de trafic / specialist semaforizare — prioritate medie, limitată de metoda actuală

- **Responsabilități și activități:** numără volume pe mișcări și moduri, verifică geometria, fazele, timing-ul, detectoarele și cererea; estimează delay/cozi și siguranță, propune planuri apoi urmărește operarea.
- **Date:** turning-movement counts pe intervale, volume orare/15-minute peak, faze și ciclu, lost time, saturation flow, benzi, pietoni și biciclete, profil temporal, cozi și observații de teren. FHWA enumeră aceste tipuri de date și cere echilibrarea siguranței și serviciului multimodal; ghidul FHWA pentru intersecții semaforizate arată că modelele au limite la suprasaturație [FHWA Traffic Data for Operations](https://www.fhwa.dot.gov/policyinformation/pubs/traffic-data-applications-highlights/traffic-data-for-operations.cfm), [Signalized Intersections Informational Guide](https://safety.fhwa.dot.gov/intersection/signal/fhwasa13027.pdf).
- **Precizie:** de stabilit conform metodei și normelor acceptate în România, inputului și scopului. HCM/FHWA oferă referințe tehnice, dar HCM este un manual american și nu devine automat normă românească [TRB HCM 6](https://trb.org/publications/hcm6e.aspx). Măsurile de calmare a traficului trebuie fundamentate ex ante și monitorizate ex post potrivit Legii 155, art. 36.
- **Nevoie ARTERIA:** semnalizează transparent că modifică un singur verde într-un model ilustrativ. Pentru utilizare inginerească ar necesita scheme de faze, date numărate, metodă identificată/versionată și verificare cu program de calcul/teren; runnerul SUMO din SIM nu este integrat API/UI.

### 4. Urbanist / specialist dezvoltare urbană — prioritate medie

- **Responsabilități:** corelează mobilitatea cu PUG/planuri urbanistice, funcțiuni, spațiu public și densitate, examinează scenarii de cartier și efecte asupra comunităților.
- **Date:** limite și reglementări, parcele, funcțiuni, planuri de investiții, spațiu public, rețele/moduri, populație și acces la servicii. Ghidul PMUD include context urbanistic și socioeconomic, accesibilitate, mediu, siguranță și scenarii operaționale.
- **Livrabil/precizie:** hartă și fișiere spațiale editabile, scenarii lizibile, motivare, consultare și conformitate; un model conceptual nu substituie documentația de urbanism ori proiectul tehnic.
- **Nevoie ARTERIA:** comparație geografică și narativă între opțiuni; scena 3D curentă este conceptuală, fără relație cu o locație. Nu există editare geometrie de proiect, PUG/parcelar sau evaluare de reglementare.

### 5. Consultant de mobilitate / proiectare — prioritate medie, ipoteză de cumpărare

- **Responsabilități:** livrează diagnostic și scenarii contractate, justifică ipoteze și date, revizuiește cu clientul și reproduce rezultatele.
- **Date/ieșiri:** intrări și fișiere ale clientului, audit trail, versiune de scenariu, hărți, memorandum, metrici/unități și limitări. Sursele PMUD și procedurile locale confirmă nevoia documentației strategice, dar nu demonstrează preferințe software ale firmelor.
- **Instrumente:** QGIS/ArcGIS, Visum/Aimsun/Vissim/SUMO sau foi de calcul, în funcție de contract și întrebare. Nu am găsit dovezi independente despre cota de utilizare în firmele din România.
- **Nevoie ARTERIA:** proiecte, permisiuni, import/export GeoPackage/CSV, raport PDF cu metodă și proveniență, comparații reproductibile. Nu există dovadă de cerere comercială sau disponibilitate de plată.

### 6. Administrație publică / autoritate locală sau metropolitană — prioritate mare ca stakeholder, utilizator necunoscut

- **Responsabilități:** adoptă/implementează PMUD, gestionează rețeaua administrată, prioritizează investiții, contractează studii și colaborează cu operatori și public. PMUD Iași aprobat prin HCL 403/2023 acoperă municipiul și 27 de comune metropolitane pentru perioada 2021–2035 [HCL și raportul PMUD](https://www.primaria-iasi.ro/dm_iasi/hotarari.nsf/352F4896F69AD4A9C2258A6D00440C3B/%24FILE/HCL_403_2023.pdf?Open=).
- **Date/ieșiri:** data oficială de infrastructură și serviciu, evaluări ex-ante/ex-post, hărți, seturi vectoriale și justificare de investiții. Ghidul 2025 impune GPKG pentru datele spațiale PMUD; legea cere model de transport actualizat pentru municipii peste 100.000 de locuitori.
- **Resurse locale identificate:** portalul Open Data Iași; CTP publică GTFS și afirmă date procesate la 20 secunde și harta live. Accesarea efectivă, documentația schemei, licența și continuitatea trebuie verificate înainte de integrare.
- **Nevoie ARTERIA:** proiecte și acces cu roluri, audit, surse oficiale, pachet exportabil pentru analiză/consultare, stări ex-ante/ex-post. Lipsesc securitate multi-user, date oficiale integrate și livrabil instituțional.

### 7. Specialist accesibilitate pietonală / mobilitate activă — prioritate medie pentru validare

- **Responsabilități:** inspectează trasee și intersecții pentru continuitate, pante, lățimi libere, crossings, suprafețe, obstacole și orientare pentru diverse nevoi.
- **Date:** ridicare în teren, geometrie trotuar/crossing, rampe, pante, suprafețe, trepte, curb ramps, semnale acustice/tactile, obstacole și destinații. OSM nu garantează completitudinea atributelor. Un studiu de routing arată că rețelele și atributele pedestrian sunt variabile; concluziile studiilor locale nu se pot transfera direct la Iași [studii OSM quality, selectate în DATA_AND_STANDARDS.md].
- **Standarde:** NP 051-2012 (reconfirmat în reglementare națională), EN 17210:2021; standardul european este în revizuire, proiect final prevăzut pentru 2027 conform CEN-CENELEC (stadiul consultat 18.10.2026).
- **Nevoie ARTERIA:** nu trebuie să numească un simplu graf walk „traseu accesibil”. Are nevoie de atribute măsurate, filtre pe profil, logică explicabilă și validare cu persoane cu dizabilități/specialiști.

### 8. Auditor de siguranță rutieră / proiectant sau administrator de infrastructură — profil conex susținut legal

- **Responsabilități:** auditul/inspecția de siguranță este proces profesional separat, cu inspectare la fața locului, independență și rapoarte reglementate; Legea 265/2008 reglementează auditorii și limitele inspecției. Legea 155 definește pietoni și bicicliști drept utilizatori vulnerabili și cere măsuri/examinări pentru siguranță în domeniile indicate [Legea 265/2008, republicată](https://legislatie.just.ro/Public/DetaliiDocument/140786), [Legea 155/2023](https://legislatie.just.ro/Public/DetaliiDocument/270923).
- **Utilitate posibilă:** hărți de constatări, accidente și măsuri candidate pot organiza investigația. Un score calculat automat nu înlocuiește auditul certificat sau inspecția de teren.
- **Prioritate produs:** consultare de expert pentru delimitarea corectă a afirmațiilor; integrarea ca instrument formal necesită cercetare juridică și metodologică dedicată.

## Dovezi de probleme și limitele lor

- Problemele documentate în issues publice sunt exemple de defecte/risc, nu sondaj de satisfacție. QGIS a introdus un prag de snapping deoarece proiectarea la cel mai apropiat punct poate fi greșită. Un issue separat arată conectivitate plană falsă la pod/underpass. În OSRM apar cazuri de rutare pe trotuar duplicat și dispute despre interpretarea tag-urilor foot/sidewalk [QGIS #9029](https://github.com/qgis/QGIS-Documentation/issues/9029), [QGIS #63045](https://github.com/qgis/QGIS/issues/63045), [OSRM #4790](https://github.com/Project-OSRM/osrm-backend/issues/4790), [OSRM #6008](https://github.com/project-osrm/osrm-backend/issues/6008).
- SUMO recomandă input reproductibil pentru issues și menționează că rutele aleatorii pot fi nerealiste; documentația listează sursele/fișierele necesare pentru debugging. Aceasta indică complexitatea configurării, nu opinia generală a utilizatorilor [SUMO FAQ](https://github.com/eclipse-sumo/sumo/blob/main/docs/web/docs/FAQ.md).
- Sursele profesionale și software descriu instrumente specializate și inputuri; nu există în această etapă eșantion de recenzii sau interviuri independente care să măsoare cât de frecvente sunt frustrările.

## Întrebări de validat cu persoane reale

1. Ce decizie lucrează ultima dată, ce fișiere și software a folosit, ce a verificat manual și cine a semnat?
2. În ce caz ar porni de la hartă/graf, iar în ce caz de la modelul de transport? Care e unitatea de proiect: intersecție, coridor, cartier sau zonă funcțională?
3. Ce prag de precizie acceptă pentru screening și ce nu poate intra într-un raport?
4. Ce date locale poate furniza și redistribui? Ce date sunt sensibile sau contractuale?
5. Ce export predă unui client/primărie și cum reproduce analiza peste 6 luni?
6. Pentru accesibilitate: cine auditează traseul și ce măsurători cer organizațiile persoanelor cu dizabilități?

## Legături către celelalte documente

- [Inventarul și auditul din Etapa 1](../PROJECT_AUDIT_V2.md)
- [Compararea soluțiilor software](COMPETITOR_ANALYSIS.md)
- [Date, metode, licențe și standarde](DATA_AND_STANDARDS.md)
- [Scenarii de lucru complete](PROFESSIONAL_WORKFLOWS.md)
- [Matrice de priorități și decalaje](FEATURE_GAP_MATRIX.md)
- [Registrul surselor și al nivelului de dovadă](SOURCES_AND_EVIDENCE.md)
