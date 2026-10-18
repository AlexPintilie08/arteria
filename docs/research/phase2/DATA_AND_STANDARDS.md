# Date, metode și standarde

**Situație verificată la:** 18 octombrie 2026. Documentul delimitează ce poate furniza calculul pe date deschise și ce cere măsurători, metodă recunoscută sau calibrare. Nu reprezintă aviz juridic, standard complet ori certificare a rezultatului ARTERIA.

## 1. Cadrul România / Uniunea Europeană

### Legea mobilității urbane durabile și PMUD

Legea 155/2023 stabilește cadrul național pentru mobilitate echitabilă, eficientă și incluzivă. Pentru municipii cu peste 100.000 de locuitori, PMUD include model de transport actualizat permanent (art. 37); măsurile de calmare a traficului se fundamentează ex ante și se monitorizează ex post (art. 36); legea conține obligații relevante pentru municipii reședință de județ (art. 34) [Portal Legislativ, Legea 155/2023](https://legislatie.just.ro/Public/DetaliiDocument/270923). Aplicarea exactă și normele în vigoare trebuie verificate cu jurist/administrația la proiect.

Ghidul MDLPA din 22.10.2025 detaliază context urbanistic și socio-economic, rețea stradală, transport public, mărfuri, mobilitate alternativă și verde, managementul traficului, zgomot, sărăcie în transport, accesibilitate și siguranță. Secțiunea de model cere colectare date, cerere, calibrare/validare, prognoze și testare; scenariile compară impacturi. Datele spațiale asociate trebuie prezentate în GeoPackage [Ghid PMUD, Anexa 1 și 2](https://legislatie.just.ro/Public/FormaPrintabila/00000G013NPGKH2Q66M0MUBJZTGP02MX). Recomandarea este ca orice export profesional ARTERIA să fie GPKG pentru layers și un raport lizibil pentru rezultate/metadate, dacă specialiștii confirmă.

Comisia Europeană descrie SUMP ca proces de planificare pentru zona funcțională urbană cu fluxuri reale, cooperare între nivele, participare și evaluare; nodurile urbane TEN-T au responsabilități SUMP și indicatori de mobilitate [EC SUMP monitoring](https://transport.ec.europa.eu/transport-themes/urban-transport/sustainable-urban-mobility-planning-and-monitoring_en). Ghidul SUMP ediția a treia a fost publicat la 8 iunie 2026 și este resursa actuală pentru procesul european [EU Urban Mobility Observatory](https://urban-mobility-observatory.transport.ec.europa.eu/sustainable-urban-mobility-plans/guidelines-developing-and-implementing-sustainable-urban-mobility-plan-0_en).

### Context documentat Iași

- HCL 403 din 31 octombrie 2023 aprobă PMUD pentru polul de creștere Iași; raportul municipal îl descrie pentru perioada 2021–2035 și arie formată din Iași plus 27 comune metropolitane [hotărâre și documentație](https://www.primaria-iasi.ro/dm_iasi/hotarari.nsf/352F4896F69AD4A9C2258A6D00440C3B/%24FILE/HCL_403_2023.pdf?Open=).
- Portalul de date deschise al Iași permite descărcarea/folosirea unor seturi în aplicații, dar catalogul specific, licențele, actualitatea și schema trebuie inspectate per dataset [iasi.oras.digital](https://iasi.oras.digital/).
- CTP Iași publică acces la date GTFS și spune că feed-ul include date procesate la interval de 20 secunde și o hartă live cu trasee/poziții [pagina CTP Open Data](https://www.sctpiasi.ro/servicii/opendata). Aceasta este afirmația CTP despre serviciul său. Nu am descărcat sau validat feed-ul pentru schema GTFS, istoricul, dreptul de redistribuire, uptime sau precizie în Etapa 2.
- Portalul Eurostat/GISCO oferă limite administrative, dar pagina consultată restricționează utilizarea comercială pentru anumite descărcări (comune/countries/postal codes) și cere atribuire. Verificați licența exactă înainte de utilizarea într-un serviciu comercial [GISCO administrative units](https://ec.europa.eu/eurostat/en/web/gisco/geodata/administrative-units). Nu folosiți limitele de referință drept limită legală certificată fără confirmarea autorității.

## 2. OpenStreetMap: licență, calitate, disponibilitate

OSM este o bază colaborativă, licențiată ODbL, cu obligație de atribuire și condiții de share-alike pentru baze de date derivate. Pagina OSMF precizează formele de atribuire în funcție de utilizare [OSM copyright](https://www.openstreetmap.org/copyright), [OSMF attribution guidelines](https://osmfoundation.org/wiki/Attribution_Guidelines). Pentru un produs comercial, review juridic trebuie să stabilească dacă se distribuie o derived database sau produced work; nu deduceți automat răspunsul numai dintr-o hartă.

Calitatea OSM nu este o singură proprietate globală: completitudinea, poziția, semantica, topologia și actualitatea diferă între locuri/atribute. Un studiu academic pe 28 de orașe arată că măsuri interne de quality pot fi utile, dar nu identifică singure dacă eroarea e completitudine, acuratețe sau consistență; validarea manuală rămâne necesară [Barrington-Leigh & Millard-Ball, 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6042734/). Un studiu despre sidewalk data identifică lacune de completitudine ca problemă pentru analiză și navigare [Sidewalk data, 2022](https://arxiv.org/abs/2210.02350). Acestea nu măsoară Iași.

Pentru ARTERIA, un graf derivat din OSM poate susține screening transparent dacă UI arată snapshot/retrieval, moduri și filtre, aria, atribute, coverage, disconnected elements și warnings. Nu poate singur susține afirmația „acest trotuar există/este accesibil”, „nu există trecere” sau „X locuitori beneficiază”. OSMnx documentează că operațiile depind de tagging și setările utilizate și recomandă o instanță locală când volumul depășește utilizarea modestă [OSMnx 2.1.1 getting started](https://osmnx.readthedocs.io/en/stable/getting-started.html). API-ul public Nominatim are limită maximă 1 request/s și descurajează bulk-geocoding [policy](https://operations.osmfoundation.org/policies/nominatim/); Overpass are concurență/time/space limits [Overpass commons](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html). Datele pot fi deschise, serviciile publice gratuite nu sunt SLA de producție.

### Protocol de validare locală recomandat

1. Păstrați interogarea, timestamp-ul, sursa/API, OSM base timestamp, licența și hash-ul de snapshot.
2. Comparați pe eșantioane cu ortofoto/date municipale licențiate și walk audit cu specialist local.
3. Verificați topologie 2D versus pasaje/poduri, crossings, permissions, access, stairs, separate sidewalks, access restrictions și rute fără puncte snap-uibile.
4. Raportați completeness/attribute coverage și erori pozitive/negative în strat; nu convertiți lipsa tag-ului în „nu există”.
5. Recalculați același indicator pe snapshot-uri succesive și comunicați sensibilitatea la modificări.

Surse independente și primare: evaluarea academică a quality [studiu 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6042734/), cercetare sidewalk [2022](https://arxiv.org/abs/2210.02350), documentația OSMnx/Overpass [OSMnx](https://osmnx.readthedocs.io/en/stable/getting-started.html) și licența oficială [OSMF](https://www.openstreetmap.org/copyright).

## 3. Date: disponibilitate versus ceea ce pot demonstra

| Întrebare/indicator | Date deschise care pot ajuta | Ce nu demonstrează fără alte date |
|---|---|---|
| Conectivitate geografică | OSM walk/bike, pasaje, crossing dacă sunt cartografiate; limite de studiu | Starea actuală la sol, siguranța, accesibilitatea universală sau cererea |
| Acces la destinații | Graful + destinații OSM/locale + prag declarat de timp/distanță | Locuitori deserviți dacă lipsesc populația, intrările clădirilor și distribuția destinațiilor; variație în timp |
| Transport public | GTFS schedule și feed realtime unde furnizat; stops, routes, calendars | Număr de pasageri, fiabilitate istorică, accesibilitatea platformei sau reprezentativitate |
| Trafic semaforizat | Rețea, date timing publice dacă există, numărători agregate și restricții | Delay/calibrare fără turning counts, cerere temporală, geometry, controller phase/offset și field validation |
| Siguranță | accidente geolocalizate cu perioadă, severitate și expunere; date stradale | Risc relativ fără expunere/denominator, reporting bias, confounders |
| Săracie/echitate în transport | venit, vârstă/dizabilitate, servicii esențiale și rețele | Cauzalitate sau acces individual; protecția datelor și geografie statistică contează |
| Mediu | stații/indicatori oficiali de zgomot, aer, emisii și model | efect de intervenție fără perioadă comparable, meteorologie și design evaluare |
| Cost/fezabilitate | costuri standard/date cadastrale/utilități unde licențiate | drept de construire, avize, utilities clashes, siguranță proiectată sau cost real fără inginer și teren |

**Resurse punctuale:** GTFS CTP Iași și portal local de open data sunt confirmate existențiale; acoperirea disponibilă pentru trafic semaforizat, accidente, cadastru și trotuare nu a fost confirmată dataset-by-dataset în această etapă. Asta rămâne task de cercetare, nu presupunere că aceste date nu există.

## 4. Metode pietonale și măsura preciziei

### Ce se poate calcula credibil pe date deschise

- conectivitate topologică, componente, lungimea/repartiția rețelei și shortest-path dacă graful este construit corect și eligibil;
- service-area și distanță de rețea către destinații cu praguri explicite, CRS/impedanță descrise; QGIS documentează network service-area și exporturi vectoriale [QGIS 3.44](https://docs.qgis.org/3.44/en/docs/user_manual/processing_algs/qgis/networkanalysis.html);
- schimbarea acestor metrici într-un graf ipotetic dacă modificarea este explicită, baseline-ul păstrat și rezultatul nu este prezentat ca realizare fizică;
- OSM QA: acoperire de tags, disconnected links, geometrie invalidă, candidate count, sample size, snapshot age.

### Ce cere date/validare suplimentară

- persoane sau gospodării care câștigă acces: populație geocodificată/areală cu metodă agregată, destinații și intrări corecte;
- rute accesibile: trotuar/crossing distinct și măsurat, curb ramps, pante, lățimi libere, suprafață și obstacole actuale, profil de mobilitate, audit în teren;
- siguranță: viteze, volume/exposure, accidente și conflict, condiții de observare, metodologia local acceptată;
- feasibility/design: topografie, parcelar/drepturi, utilități, standarde proiectare, geometrie de detaliu și proiectant.

Normativul NP 051-2012 este aprobat prin Ordinul 189/2013 [Portal Legislativ](https://legislatie.just.ro/Public/DetaliiDocument/145914). Reglementări ulterioare trimit lățimea/configurația circulațiilor pietonale pentru persoane cu handicap la NP 051 [reglementare 2023](https://legislatie.just.ro/public/DetaliiDocument/264751). Standardul EN 17210:2021 descrie cerințe/recomandări funcționale de accessibility & usability pentru mediul construit, inclusiv zone pietonale exterioare; standardul e cu acces licențiat, nu reproduceți tabelele comerciale fără drept [NEN overview](https://connect.nen.nl/Standard/Detail/3641676). CEN a anunțat revizuirea cu finalizare de draft până la finele lui 2026 și publicare estimată în toamna lui 2027; aceasta este estimare, nu ediție publicată [CEN-CENELEC](https://www.cencenelec.eu/news-events/news/2026/en-in-the-spotlight/2026-02-26-en-17210-2021/).

## 5. Traffic modeling, semaforizare și calibrare

FHWA Signal Timing Manual enumeră timpi/capacitate/faze și arată obiectivele multimodale, iar ghidul de date operaționale include volume, cozi, clasă vehicule, semnale, pietoni și bicicliști [manual chap. 2](https://ops.fhwa.dot.gov/publications/fhwahop08024/chapter2.htm), [date](https://www.fhwa.dot.gov/policyinformation/pubs/traffic-data-applications-highlights/traffic-data-for-operations.cfm). FHWA definește control delay și queue metrics și descrie măsurarea de teren [manual chap. 3](https://ops.fhwa.dot.gov/publications/fhwahop08024/chapter3.htm). Un ghid FHWA pentru semafoare notează input volume/turning movements în intervale, rolul pietonilor și limitele de delay/queue în oversaturated conditions [guide PDF](https://safety.fhwa.dot.gov/intersection/signal/fhwasa13027.pdf).

Aceste surse susțin necesitatea inputurilor și verificărilor, nu autoritatea normativă în România. HCM este o metodă TRB/SUA pentru operațiuni și capacitate, disponibilă comercial [TRB HCM 6th edition](https://trb.org/publications/hcm6e.aspx). Înainte de a calcula LOS în România, confirmați metoda/standardul cu autoritatea și inginerul local. Folosiți indicatori măsurați potrivit scenariului — control delay per vehicul/persoană, coadă mediană/P95, travel time, stops, throughput și pedestrian service — cu unități, perioadă, mod și sursă.

Codul current al ARTERIA folosește un delay formula determinist cu demanda și capacitate sintetice; aceasta nu este metodă calibrată. Dacă SUMO se conectează:

1. input rețea și turning flows pe perioade, OD/route choice, vehicule și transport public;
2. control plan și geometrie verificate, crossing/pietoni și logică intermodală;
3. calibrare pe flow/speed/travel time/queue observate și validare pe altă perioadă;
4. stochastic replications/seed și intervale sau variația run-to-run;
5. engine version, parameters, seed, dataset hashes, requested/executed/failed mode și replay ID în rezultat.

SIM dispune de runner local condiționat, dar etapa 1 a constatat că sumo și netconvert nu erau în PATH și că API/UI nu invocă runnerul. O demonstrație cu OD synthetic este simulare a scenariului sintetic, nu predicție locală. Chiar SUMO include warnings pentru demand random/nerealist [SUMO FAQ](https://github.com/eclipse-sumo/sumo/blob/main/docs/web/docs/FAQ.md). PTV subliniază explicit că acuratețea depinde de geometrie, cerere și calibrare de teren [PTV Vissim FAQ](https://www.ptvgroup.com/en/products/ptv-vissim/faqs); aceasta este și afirmația vânzătorului, susținută independent de cerințele FHWA/HCM pentru volume și field measures.

## 6. Reproductibilitate și modelul dovezilor

Fiecare rezultat profesional ar trebui să salveze:

- area ID, geometrie/CRS și lineage; dataset provider, license, timestamp/data-as-of, source version/hash, import transformations;
- metoda și versiunea, unități, impedanță, modes, thresholds, input parameters și sample OD;
- baseline/scenario IDs, intervention geometry, validation failures/unknowns, engine version, seed și run ID;
- semnal epistemic: observed, calculated, estimated, simulated, replayed sau unknown;
- coverage, limitations, uncertainty/sensitivity, warnings și legături la output machine-readable;
- reviewer/author/date pentru orice export dintr-un proiect colaborativ.

Legea 155 cere fundamentare ex ante și monitorizare ex post pentru măsuri de calmare; ghidul PMUD cere colectare/calibrare/validare a modelului. Deci dosarul reproductibil nu este ornament. ARTERIA are IDs, baseline validation, SIM revision, warnings și persistență limitată; îi lipsesc dataset snapshots/complete provenance, project history, export profesional și system-wide access controls.

## Ce nu este determinat de cercetare

- OSM coverage/accuracy pe fiecare cartier din Iași; un audit comparativ cu OSM, ortofoto, date oficiale și field walk este încă necesar.
- Accesul comercial și temporal de utilizare pentru fiecare set din Iași Open Data/CTP; pagina de prezentare nu substituie licența și feed validation.
- Metoda românească concretă pe care un inginer o folosește pentru LOS/capacitate la un anumit studiu; consultare profesională cerută.
- Seturi locale de accidente cu granularitate/utilizare permisă și seturi de trafic cu turning movement counts.
- Edițiile/interpretarea aplicabilă în proiectare a standardelor și normelor de accesibilitate; de stabilit cu proiectant și auditor local.
