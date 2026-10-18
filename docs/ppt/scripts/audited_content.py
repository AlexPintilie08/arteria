"""Authoritative factual/editorial corrections, applied after V2 shape creation.

Only DrawingML text, notes and the cropped demo bitmap content change.
No shapes, runs, paragraph properties, geometry, styles, transitions or
animation targets are reconstructed. The replacement is a real browser capture.
The original generation/refinement stages remain responsible for design.
"""
from pathlib import Path
import argparse
import copy
import json
import re
import posixpath
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reports/.qa/deps'))
from defusedxml import minidom
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'

# Exact old -> corrected text. Deliberately short enough for existing boxes.
EDITS = {
1: {
 'Planificare urbană pentru\nechipele de mobilitate': 'Comparații de mobilitate\npentru specialiști',
 'Compararea intervențiilor,\nînainte de implementare': 'Semaforizare demonstrativă\nși acces pietonal pe graf',
 'Captură din aplicație · © contributori OpenStreetMap': 'Previzualizare istorică · © contributori OpenStreetMap',
},
2: {
 'O intervenție. Mai multe efecte.': 'Ce schimbă o legătură nouă?',
 'Reconfigurarea unei străzi cere o comparație explicabilă.': 'Specialistul trebuie să compare rutele înainte și după.',
 'Intervenție': 'Legătură nouă',
 'Situație propusă · README.md și docs/ARCHITECTURE.md, audit 2026': 'Caz de utilizare propus · fără interviuri validate · 18.10.2026',
 'Ce se schimbă? Pe ce date ne bazăm?': 'Ce rute se schimbă? Ce rămâne necunoscut?',
},
3: {
 'PMUD Iași': 'Procesul de lucru',
 'Context de planificare locală': 'Pregătirea datelor și compararea variantelor',
 'ARTERIA propune un parcurs comun:': 'ARTERIA leagă pașii într-un prototip:',
 'Surse: qgis.org · sumo.dlr.de · Primăria Iași; consultate 2026': 'Surse: qgis.org · sumo.dlr.de · cod ARTERIA · consultate 18.10.2026',
},
4: {
 'Astăzi: API conectat și studii pe graf pietonal': 'Graf pietonal: alternative pe același eșantion de rute',
 'Urmează: calibrare și validare cu un specialist': 'Separat: semaforizare sintetică; impact real nevalidat',
},
5: {
 'Podu Roș, în prototip': 'Semaforizare: un compromis',
 'Demo local: localhost:3001/app · Captură din aplicația existentă': 'Captură verificată la 18.10.2026 · valori sintetice, nu trafic din Iași',
},
6: {
 'Frontend · Backend · Sim': 'Interfață · Backend · SIM',
 'Frontend': 'Interfață',
 'Sim': 'SIM',
 'Candidați și dovezi': 'Rute · candidați validați',
 'Graf pietonal / OSM\nCandidați și dovezi\nSUMO local opțional': 'Graf pietonal / OSM\nRute · candidați validați\nSUMO separat, local',
 'Semaforizare sintetică; graf pietonal conectat. Fără LLM cloud / SUMO în UI.': 'Graf: comparație salvată în SQLite. Semaforizare: estimări sintetice.',
 'AI planificat': 'LLM neintegrat',
 'Alternative structurate; validare înainte de evaluare': 'Există: dovezi, catalog și validare. Generarea LLM urmează.',
 'backend/main.py · backend/storage.py · sim/ · Audit după Git sync; întrerupt = AI viitor': 'Cod: backend/main.py · spatial_worker.py · sim/ · LLM și SUMO neconectate la UI',
},
7: {
 'ARTERIA / BUSINESS / CINE PLĂTEȘTE': 'ARTERIA / MODEL ECONOMIC',
 'Sursă preț: ipoteza din pitch-ul anterior, 2026': 'Ipoteză din pitch-ul anterior, 2026 · preț nevalidat prin interviuri',
 'Ipoteză de abonament,\nnevalidată': 'Abonament propus,\npreț nevalidat',
 'Niciun client plătitor confirmat': 'Nu avem dovezi de clienți plătitori',
},
8: {
 'Primii utilizatori, înainte de extindere': 'Validarea pieței începe în Iași',
 'Iași: primul specialist și un caz de lucru': 'Iași: propunem un prim caz cu un specialist',
 'Apoi: listă de 10 organizații de intervievat': 'Apoi: identificăm organizații de intervievat',
 'Exercițiu comercial': 'Criteriul propus pentru continuare',
 '10 × 18.000 € = 180.000 € / an': 'Utilitate și plată validate',
 'Scenariu ipotetic; organizațiile și conversia nu sunt validate': 'Fără listă validată de clienți sau dimensiune de piață măsurată',
 'Ipoteze de lucru, 2026 · Nu reprezintă venit sau piață măsurată': 'Plan propus · 18.10.2026 · nu reprezintă tracțiune comercială',
},
9: {
 'Frontend and\nweb experience': 'Interfață și\nexperiență web',
 'Bootstrap and\nsimulation foundation': 'Inițializare proiect\nși baza de simulare',
 'Backend': 'Dezvoltare backend',
 'Responsabilități confirmate de echipă · Cerința V2, 18 octombrie 2026': 'Nume și responsabilități furnizate de echipă · 18.10.2026',
},
10: {
 'Prima comparație pe date verificate': 'Următorul pas: un caz validat',
 'Date': 'Date locale',
 'documentate': 'verificate',
 'Calibrare și': 'LLM cu',
 'verificare': 'validare',
 'Măsurăm timpul pregătirii comparației și trasabilitatea rezultatului.': 'Măsurăm timpul de lucru și corectitudinea propunerilor.',
},
11: {
 'Ce este verificat astăzi': 'Verificări tehnice, nu impact urban',
 'Typecheck\nweb · mobile · shared': 'Verificare TypeScript\nweb · mobil · comun',
 'Build web\n/ și /app': 'Compilare web\n/ și /app',
 'API și graf pietonal implementate; calibrarea rămâne de făcut': 'API și SIM: teste offline; fără validare în teren',
 'AI cloud și SUMO din UI — neintegrate': 'LLM și SUMO în interfață: neintegrate',
 'Sursă: verificări locale ale repository-ului, 2026': 'Verificări reluate la 18.10.2026 · npm run check · detalii în note',
},
12: {
 'Rolul AI în fluxul propus': 'Dovezi și reguli înainte de LLM',
 'Sursă: docs/ARCHITECTURE.md; stare verificată în cod, 2026': 'Cod: sim/proposal_context.py · proposals.py · proposal_validation.py · 18.10.2026',
 'Astăzi: propuneri deterministe și validare': 'Astăzi: candidați calculați, verificați prin reguli',
 'Planificat: provider LLM; decizia rămâne la specialist': 'Planificat: generare LLM pe dovezi; specialistul decide',
},
13: {
 'Condițiile unei evaluări credibile': 'Cum comparăm alternativele',
 'Surse: docs/ARCHITECTURE.md · SUMO Calibrator · Audit repository, 2026': 'Cod: sim/impact.py · backend/spatial_routes.py · sim/sumo_engine.py · 18.10.2026',
 'Aceeași zonă și aceeași metodă': 'Același graf inițial și eșantion comun de rute',
 'Simulare': 'SUMO local',
 'Cerere documentată, versiune, seed și rezultate păstrate': 'Cerere sintetică; execuție separată de interfață',
 'Lipsă date → necunoscut\nPropunere AI → ipoteză\nRulare repetată → rezultat verificabil': 'Rute eșantionate ≠ călătorii observate\nLegătură ipotetică ≠ lucrare fezabilă\nRepetabilitate ≠ validare în teren',
 'Nu există încă efecte de trafic validate în repository.': 'Nu avem rezultate validate de trafic real.',
},
}
# One obsolete nested replacement is covered by the full-box replacement.
EDITS[6].pop('Candidați și dovezi')

NOTES = {
1: ('Ajutăm specialiștii în mobilitate să compare intervenții într-un prototip inspectabil. '
    'Astăzi există două fluxuri distincte: semaforizare sintetică și studiu pietonal pe graf. '
    'Captura este o previzualizare istorică, nu dovada unui geamăn digital complet. '
    'Nu revendicăm utilizatori, economii de timp sau efecte urbane măsurate.'),
2: ('Cazul de utilizare propus: înainte de a discuta o legătură pietonală nouă, specialistul verifică '
    'ce rute devin mai scurte sau accesibile și pe ce date se bazează comparația. '
    'Diagrama arată perspective de planificare, nu patru module validate. '
    'Nu avem interviuri sau un cost al problemei măsurat. Nu inventăm o mărturie de utilizator.'),
3: ('QGIS oferă analiză geografică, iar SUMO simulare microscopică. Nu afirmăm că aceste instrumente '
    'nu pot compara scenarii sau că ARTERIA le depășește. Diferențierea propusă este un parcurs comun '
    'cu dovezi și limite vizibile. Rândul despre procesul de lucru descrie un caz propus, nu o observație '
    'din interviuri. PMUD este context instituțional, nu produs concurent sau dovadă de adopție.'),
4: ('În modul conectat, utilizatorul poate analiza semaforizarea sintetică, cere o alternativă și compara '
    'valorile returnate de API. Separat, Acces pietonal creează un studiu dintr-un exemplu sintetic sau '
    'dintr-un poligon eligibil din catalogul OSM. SIM compară legături ipotetice pe același graf inițial '
    'și eșantion. Evaluarea aleasă returnează comparația deja calculată la crearea studiului. '
    'Catalogul conține 24 de poligoane și 7 puncte; punctele nu devin poligoane, iar extinderile OSM '
    'nu sunt limite municipale oficiale. Achiziția OSM online rămâne dependentă de serviciul extern.'),
5: ('Demo principal: analiză → propunere → reglaj verde nord–sud → comparație. '
    'Captura refăcută în browser la 18.10.2026 arată 13,89 secunde/vehicul inițial pe ambele direcții, apoi 2,22 nord–sud, '
    '125,56 est–vest și media 53,61, la verde nord–sud 70 s. Aceste valori sunt compatibile cu '
    'modelul actual la ciclu 90 s, pierderi 10 s și cerere sintetică 700/500 vehicule/oră. '
    'Media inițială este 13,89; media crește, deci exemplul demonstrează un compromis nefavorabil '
    'în ansamblu, nu o optimizare reușită. Formula folosește întârziere uniformă și penalizare '
    'sintetică de capacitate, nu SUMO. Reperul Podu Roș nu furnizează trafic local. '
    'Portul se ia din pornirea curentă, implicit 3000; captura de rezervă nu este o aplicație publicată. '
    'Pentru întrebări, demonstrați separat exemplul pietonal: creați studiul, selectați o opțiune '
    'validată și afișați perechile de rute îmbunătățite/devenite accesibile. Nu numiți aceste perechi locuitori.'),
6: ('Interfața Next.js folosește clientul HTTP comun. FastAPI validează cu Pydantic și persistă '
    'analize, propuneri, evaluări și studii în SQLite. Fluxul de semaforizare se calculează în '
    'backend/simulation_adapter.py. Studiul pietonal rulează SIM într-un subproces limitat la 90 s, '
    'cu verificarea structurii rezultatului; sursa, revizia motorului și comparațiile sunt păstrate. '
    'În calea OSM integrată se cere numai graful pietonal, fără achiziția straturilor de clădiri/POI. '
    'SIM are separat conversie de graf auto și executare SUMO locală cu cerere sintetică, fără '
    'integrare în UI sau calibrare. Nu există apel LLM conectat. Există deja catalog, pachet de dovezi '
    'cu hash al geometriei și validare a candidaților calculați. Procentul de cod sau fișierele generate '
    'cu asistență AI nu sunt confirmate; echipa trebuie să declare instrumentele folosite fără a inventa atribuții.'),
7: ('Model propus: abonament pentru administrații locale sau consultanțe de mobilitate. '
    '1.500 €/lună este exclusiv ipoteza din pitch-ul anterior, nu preț testat, ofertă acceptată sau '
    'disponibilitate de plată. Ar echivala aritmetic cu 18.000 €/an, fără a demonstra cerere. '
    'Nu avem dovezi în materialele auditate de clienți plătitori. Validăm timpul necesar unei comparații, '
    'utilitatea și costurile de date, calcul și suport înainte de a susține marjă sau economii.'),
8: ('Plan propus de acces la piață: un caz de lucru în Iași, interviuri cu specialiști și identificarea '
    'organizațiilor relevante prin mentori/comunități. Nu există o listă verificată de zece organizații. '
    'Calculul istoric 10 × 12 × 1.500 € = 180.000 €/an este aritmetic corect, dar presupune zece '
    'cumpărători, preț acceptat și un an întreg; nu este dimensiune de piață sau venit realizat. '
    'De aceea nu mai domină slide-ul. Continuarea comercială presupune utilitate, disponibilitate '
    'de plată și cost de livrare validate. Instituțiile locale sunt potențiali interlocutori, nu parteneri confirmați.'),
9: ('Echipa a furnizat numele și responsabilitățile: Iustin Fagateanu — interfață/frontend; '
    'Alex Pintilie — inițializarea proiectului și baza de simulare; Fagateanu Eusebiu — backend. '
    'Traducerea păstrează aceste roluri, fără atribuirea unor endpoint-uri, algoritmi sau rezultate '
    'individuale pe care dovezile nu le stabilesc. Continuitatea după eveniment, rolurile de scenă '
    'și experiența profesională nu sunt confirmate.'),
10: ('Priorități propuse: un caz pe date locale verificabile; conectarea unui LLM constrâns de dovezi '
     'și evaluarea corectitudinii propunerilor; test cu un specialist. Măsurăm timpul de lucru și '
     'trasabilitatea, nu promitem o reducere de trafic. Calibrarea cererii, integrarea SUMO în fluxul '
     'potrivit și verificarea fezabilității în teren rămân necesare înainte de rezultate urbane. '
     'Cerem o introducere către un specialist și acces la date. Nu există un acord de pilot în dovezi.'),
11: ('Verificare reluată la 18.10.2026: npm run check a trecut verificarea TypeScript pentru web, '
     'mobil și cod comun, 9/9 teste Node și compilarea Next.js pentru / și /app. Testele Node '
     'folosesc transport simulat și verifică geografia catalogului; nu sunt nouă teste complete de produs. '
     'Python: 138 teste trecute, un avertisment de depreciere, în runtime QA izolat, fără sincronizare uv.lock. '
     'Rularea curentă și limitele ei sunt în reports/audit-python-final.log și '
     'PPT_FINAL_CONTENT_AUDIT.md. Rezultatele istorice nu se confundă cu o rulare nouă. '
     'Testele offline verifică API-ul, stocarea, motorul de graf, validarea și conversia SUMO; '
     'nu demonstrează trafic real, calibrare, fezabilitate fizică sau execuție SUMO în UI.'),
12: ('Astăzi nu există integrare LLM sau model învățat conectat. Generarea semaforizării și a opțiunilor '
     'pietonale este deterministă. Există un pachet limitat de dovezi cu referință SHA-256 la geometrie, '
     'catalog de intervenții, candidați evaluați și verificări de identitate/acțiune, coordonate, unități '
     'și afirmații nesusținute. Validarea nu certifică fezabilitatea fizică și nu garantează eliminarea '
     'oricărei halucinații. Opțiunile pietonale nu primesc etichete inginerești minimal/moderat/transformator. '
     'Fluxul cu LLM din diagramă este viitor. AI este central în intenția produsului, dar componenta '
     'generativă lipsește din implementarea actuală; regulile deterministe nu se prezintă drept LLM.'),
13: ('Comparația pietonală folosește același graf inițial și un eșantion comun, cu sămânță fixată. '
     'Perechile folosite la descoperirea candidaților sunt excluse din eșantionul de clasare; '
     'diagnosticele locale sunt separate. Modificările se aplică pe copii ale grafului inițial. '
     'Studiul și comparațiile sunt persistate; selectarea unui candidat nu lansează o nouă simulare. '
     'Repetabilitatea presupune aceleași date, versiuni și parametri; marcajele temporale/ID-urile '
     'nu sunt identice la fiecare cerere. OSM are acoperire incompletă. Lipsa unui strat rămâne '
     'necunoscută. SUMO local are cerere sintetică și setări păstrate, dar nu rezultate de trafic '
     'calibrate pentru Iași. Nu confundăm simularea cu validarea în teren.'),
}

EVIDENCE = {
1:'README.md; frontend/web/src/features/workspace/Workspace.tsx:App; ConnectedWorkspace.tsx; SpatialPanel.tsx.',
2:'sim/scenario.py:evaluate_scenario; sim/impact.py:evaluate_candidates. Nevoia utilizatorului este ipoteză, fără interviuri în repository.',
3:'https://qgis.org/project/overview/ ; https://sumo.dlr.de/docs/ ; backend/spatial_worker.py:calculate. Surse consultate 18.10.2026.',
4:'frontend/shared/core/api.ts:createApiClient; frontend/web/src/features/workspace/SpatialPanel.tsx; backend/spatial_worker.py:calculate; sim/impact.py:evaluate_candidates; frontend/web/tests/sim-geography.test.ts.',
5:'backend/models.py:Inputs; backend/simulation_adapter.py:SimulationAdapter.indicators; ConnectedWorkspace.tsx; assets/connected-comparison.png. Numerele descriu exclusiv modelul sintetic.',
6:'frontend/web/package.json; backend/main.py; storage.py:Store; spatial_adapter.py:SpatialAdapter.run; spatial_worker.py:calculate; sim/sumo_engine.py; sim/proposal_context.py; sim/proposal_validation.py.',
7:'Ipoteză preexistentă în archive/v2-before-content-audit-20261018/Template-Pitch-Hackathon.v2.pptx; nicio validare comercială găsită.',
8:'Absența listei și a contractelor în dovezile disponibile; plan propus. Aritmetică istorică, nu cercetare de piață.',
9:'Nume și responsabilități furnizate explicit în cererea de audit a echipei, 18.10.2026; nu se deduce autorie individuală din Git.',
10:'docs/ROADMAP.md comparat cu backend/main.py și sim/proposals.py/proposal_validation.py; goluri curente din PROJECT_REALITY_AUDIT.md.',
11:'reports/audit-frontend-check.log; reports/audit-python-final.log; tests/; sim/test_engine.py. Se consultă raportul final pentru acoperire și limite.',
12:'sim/proposal_context.py:build_proposal_context; proposals.py:prepare_candidate_options; proposal_validation.py:validate_proposal_set; backend/models.py:RecommendationModel; backend/spatial_worker.py:calculate.',
13:'sim/impact.py:evaluate_candidates; sim/scenario.py:_prepare_scenario_graph; backend/spatial_routes.py:evaluate; backend/spatial_models.py:SpatialEvaluation; sim/sumo_engine.py:run_real_area_simulation.',
}

TIMES = [0,25,20,10,50,30,10,10,10,15]  # 180 seconds including market; title is pre-roll.

def serialize(document):
    # minidom emits literal control characters in attributes; XML reparsing would
    # normalize them to spaces, changing existing shape names. Keep their values.
    xml=document.toxml()
    xml=re.sub(r'="([^"]*)"',lambda m:'="'+m.group(1).replace('\r','&#13;').replace('\n','&#10;').replace('\t','&#9;')+'"',xml)
    return xml.encode('utf-8')

def children(el, ns, name):
    return [x for x in el.childNodes if x.nodeType == x.ELEMENT_NODE and x.namespaceURI == ns and x.localName == name]

def tx_text(tx):
    return '\n'.join(''.join(t.firstChild.data if t.firstChild else '' for t in p.getElementsByTagNameNS(A,'t')) for p in children(tx,A,'p'))

def set_text(tx, value):
    paragraphs = children(tx,A,'p')
    lines = value.split('\n')
    if len(lines) > len(paragraphs):
        raise ValueError('Correction would add a paragraph; preserve the existing text architecture')
    for index,p in enumerate(paragraphs):
        ts = list(p.getElementsByTagNameNS(A,'t'))
        line = lines[index] if index < len(lines) else ''
        if not ts and line:
            raise ValueError('No styled text run available')
        for j,t in enumerate(ts):
            for node in list(t.childNodes): t.removeChild(node)
            t.appendChild(tx.ownerDocument.createTextNode(line if j == 0 else ''))

def note_text(slide):
    timing = f'Buget orientativ: {TIMES[slide-1]} secunde.' if slide <= 10 else 'Anexă pentru întrebări; nu intră în pitch.'
    if slide == 1: timing = 'Coperta rămâne pe ecran înaintea cronometrului; începeți cu problema.'
    return (f'ARTERIA — slide {slide}\n\n{NOTES[slide]}\n\nDovezi: {EVIDENCE[slide]}\n\n{timing}\n'
            'Pitch: 3 minute, apoi întrebări. Sursa de adevăr: codul curent și verificările reproductibile; '
            'inventarul este în reports/PROJECT_REALITY_AUDIT.md. Documentele pitch sunt materiale de comunicare. '
            'Structură adaptată din template-ul Andrei Margelatu. Exemplarul de depunere are 10 slide-uri; '
            'acest exemplar complet păstrează anexele pentru întrebări.')

def update_notes(document, text):
    for shape in document.getElementsByTagNameNS(P,'sp'):
        placeholders = shape.getElementsByTagNameNS(P,'ph')
        if not any(p.getAttribute('type') == 'body' for p in placeholders): continue
        tx = shape.getElementsByTagNameNS(P,'txBody')[0]
        paragraphs = children(tx,A,'p')
        template = paragraphs[0].cloneNode(True)
        for p in paragraphs: tx.removeChild(p)
        for line in text.split('\n'):
            p = template.cloneNode(True)
            for node in list(p.childNodes):
                if node.nodeType == node.ELEMENT_NODE and node.localName != 'pPr': p.removeChild(node)
            run = document.createElementNS(A,'a:r')
            t = document.createElementNS(A,'a:t'); t.appendChild(document.createTextNode(line))
            run.appendChild(t); p.appendChild(run); tx.appendChild(p)
        return
    raise ValueError('Missing speaker notes body')

def apply(deck, output=None):
    deck=Path(deck); output=Path(output or deck)
    with zipfile.ZipFile(deck) as z:
        infos=z.infolist(); parts={i.filename:z.read(i.filename) for i in infos}
    # One necessary content-image correction: replace the cropped historical
    # comparison by a real current capture, preserving the picture's geometry.
    slide=minidom.parseString(parts['ppt/slides/slide5.xml'])
    picture=slide.getElementsByTagNameNS(P,'pic')[0]
    rid=picture.getElementsByTagNameNS(A,'blip')[0].getAttribute('r:embed')
    rels=minidom.parseString(parts['ppt/slides/_rels/slide5.xml.rels'])
    rel=next(r for r in rels.documentElement.childNodes if r.nodeType==r.ELEMENT_NODE and r.getAttribute('Id')==rid)
    media=posixpath.normpath(posixpath.join('ppt/slides',rel.getAttribute('Target')))
    suffix=Path(media).suffix.lower()
    asset=ROOT/'assets'/('connected-comparison-audited.jpg' if suffix in ('.jpg','.jpeg') else 'connected-comparison-audited.png')
    parts[media]=asset.read_bytes()
    for number, edits in EDITS.items():
        name=f'ppt/slides/slide{number}.xml'; d=minidom.parseString(parts[name])
        containers=list(d.getElementsByTagNameNS(P,'txBody'))+list(d.getElementsByTagNameNS(A,'txBody'))
        values={tx_text(tx):tx for tx in containers}
        for old,new in edits.items():
            if old in values: set_text(values[old],new)
            elif new not in values: raise ValueError(f'Slide {number}: missing original/corrected text {old!r}')
        parts[name]=serialize(d)
        name=f'ppt/notesSlides/notesSlide{number}.xml'; d=minidom.parseString(parts[name])
        update_notes(d,note_text(number)); parts[name]=serialize(d)
    temp=output.with_suffix('.audit.tmp')
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
        for info in infos: z.writestr(info,parts[info.filename])
    temp.replace(output)
    return output

def submission(deck, output):
    """Create 10-slide derivative, leaving the full deck and its objects intact."""
    with zipfile.ZipFile(deck) as z:
        infos=z.infolist(); parts={i.filename:z.read(i.filename) for i in infos}
    doc=minidom.parseString(parts['ppt/presentation.xml'])
    ids=list(doc.getElementsByTagNameNS(P,'sldId'))
    removed_rids=[]
    for item in ids[10:]:
        removed_rids.append(item.getAttribute('r:id')); item.parentNode.removeChild(item)
    assert len(ids)==13
    parts['ppt/presentation.xml']=serialize(doc)
    rels=minidom.parseString(parts['ppt/_rels/presentation.xml.rels'])
    for item in list(rels.documentElement.childNodes):
        if item.nodeType==item.ELEMENT_NODE and item.getAttribute('Id') in removed_rids: item.parentNode.removeChild(item)
    parts['ppt/_rels/presentation.xml.rels']=serialize(rels)
    removed=set()
    for i in range(11,14):
        removed.update([f'ppt/slides/slide{i}.xml',f'ppt/slides/_rels/slide{i}.xml.rels',
                        f'ppt/notesSlides/notesSlide{i}.xml',f'ppt/notesSlides/_rels/notesSlide{i}.xml.rels'])
    ct=minidom.parseString(parts['[Content_Types].xml'])
    for item in list(ct.documentElement.childNodes):
        if item.nodeType==item.ELEMENT_NODE and item.getAttribute('PartName').lstrip('/') in removed: item.parentNode.removeChild(item)
    parts['[Content_Types].xml']=serialize(ct)
    # Keep office package metadata accurate without touching any slides.
    app=minidom.parseString(parts['docProps/app.xml'])
    slides=app.getElementsByTagName('Slides')
    if slides and slides[0].firstChild: slides[0].firstChild.data='10'
    parts['docProps/app.xml']=serialize(app)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for info in infos:
            if info.filename not in removed: z.writestr(info,parts[info.filename])

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('deck',type=Path)
    parser.add_argument('--output',type=Path); parser.add_argument('--submission',type=Path)
    args=parser.parse_args(); result=apply(args.deck,args.output)
    if args.submission: submission(result,args.submission)
    print(f'Applied verified content and notes; design/motion preserved: {result}')
