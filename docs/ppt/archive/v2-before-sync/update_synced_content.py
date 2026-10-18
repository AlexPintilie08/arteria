"""One-time migration of V2 narrative after the authorized origin/main merge."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'research/PITCH_CONTENT.md'
s=p.read_text(encoding='utf-8')
replacements={
'Astăzi: interfață și scenarii demonstrative':'Astăzi: API conectat și studii pe graf pietonal',
'Urmează: date verificate și evaluare reproductibilă':'Urmează: calibrare și validare cu un specialist',
'Am implementat parcursul de interfață. Datele și alternativele din demo sunt predefinite; legătura cu analiza reală este etapa următoare.':'Am conectat interfața la API. Semaforizarea folosește date sintetice; separat, studiile pietonale evaluează alternative pe graf.',
'DEMO: date predefinite și ajustări locale':'DEMO: API conectat, date sintetice',
'Fără analiză urbană sau rulare SUMO din interfață':'Semaforizare estimată; fără SUMO din interfață',
'Demo local: localhost:3000/app':'Demo local verificat: localhost:3001/app',
'Frontend — Next.js / MapLibre; fixtures locale':'Frontend — Next.js / MapLibre; client API conectat',
'Backend — FastAPI: /health; demo HTTP: /analyze, /propose, /evaluate':'Backend — FastAPI / Pydantic / SQLite; analiză, propuneri, evaluare',
'Sim — NetworkX sintetic; utilitar smoke SUMO':'Sim — graf pietonal / candidați / dovezi; SUMO opțional local',
'Linii întrerupte: integrări de construit':'Linii continue: implementat · întrerupte: AI viitor',
'Date și contract unic → Un indicator reproductibil → Test cu un specialist':'Date documentate → Calibrare și verificare → Test cu un specialist',
'Vom unifica API-ul, documenta o zonă și calcula un indicator reproductibil.':'Vom documenta o zonă, verifica indicatorii și calibra ipotezele modelului.',
'5 / 5 teste ale clientului API':'9 / 9 teste frontend',
'Date urbane reale / AI generativ / SUMO din UI — neintegrate':'API și graf pietonal implementate; calibrarea rămâne de făcut',
'Testele Python și SUMO nu au fost rerulate în audit.':'AI cloud și SUMO din UI — neintegrate',
'cifra mare 5/5':'cifra mare 9/9',
'Dovezi și catalog → LLM: alternative → Reguli și geometrie → Evaluare independentă':'Dovezi și catalog → LLM viitor → Reguli și geometrie → Evaluare',
'Astăzi: catalog fix, fără apel LLM':'Astăzi: propuneri deterministe și validare',
'Planificat: validare pe server și aprobare de către specialist':'Planificat: provider LLM; decizia rămâne la specialist',
'Auth, jobs, persistență și Android sunt etape viitoare.':'Auth, jobs și Android complet rămân etape viitoare; persistența SQLite există.',
}
for a,b in replacements.items():s=s.replace(a,b)
# Replace superseded implementation descriptions, including presenter notes.
s=s.replace('Endpoint-urile serverului HTTP sunt implementate ca fixture, fără analiză urbană reală. Săgeți frontend→backend→sim întrerupte pentru fluxul urban neintegrat; o etichetă separată precizează că clientul `/analyze` există în non-demo.','Legături frontend→backend→sim continue pentru fluxurile implementate. LLM separat, întrerupt. Semaforizarea rămâne sintetică; studiile spațiale folosesc graf și candidați validați.')
s=s.replace('Prototipul web lucrează în principal local. FastAPI are health; serverul demonstrativ e separat și contractele trebuie unificate. Sim are un test sintetic și utilitar TraCI. Integrarea LLM este planificată: modelul va propune, calculele independente vor evalua.','Web-ul este conectat la FastAPI, cu validare Pydantic și persistență SQLite. SIM evaluează grafuri pietonale și candidați. Semaforizarea este sintetică. SUMO local este opțional, fără legătură la UI; providerul LLM rămâne viitor.')
s=s.replace('testele Node folosesc fetch mock și nu validează contractul serverului alternativ; smoke SUMO nu este o simulare de oraș.','testele Node acoperă transportul API și geografia; nu probează impactul urban. SUMO necesită binare externe și calibrare.')
s=s.replace('toate legăturile viitoare întrerupte','legăturile către LLM viitor întrerupte și evaluarea implementată continuă')
s=s.replace('alege Podu Roș, pornește previzualizarea, inspectează problema predefinită, deschide Scenarii, schimbă alternativa, mișcă un reglaj, aplică în UI și deschide Compară.','alege Podu Roș, analizează prin API, deschide propunerile, setează verde nord–sud la 70 s și compară. Verificarea conectată arată compromisul: nord–sud scade, est–vest crește. Modelul este sintetic.')
p.write_text(s,encoding='utf-8')
p=root/'scripts/build_deck.py';s=p.read_text(encoding='utf-8')
s=s.replace("'DEMO: date predefinite\\nși ajustări locale'","'DEMO: API conectat\\ndate sintetice'")
s=s.replace("'Fără analiză urbană sau\\nrulare SUMO din interfață'","'Semaforizare estimată\\nFără SUMO din interfață'")
s=s.replace("'comparison-demo.png'","'connected-comparison.png'")
s=s.replace('Demo local: localhost:3000/app','Demo local: localhost:3001/app')
s=s.replace("(.65,'Date și','contract unic'),(4.83,'Un indicator','reproductibil')","(.65,'Date','documentate'),(4.83,'Calibrare și','verificare')")
s=s.replace("'5 / 5'","'9 / 9'").replace("'teste ale clientului API'","'teste frontend'")
start=s.index('    exact_sources={');end=s.index('    manifest=[]',start)
old=s[start:end]
for n,source in {
1:'README.md; frontend/web/src/features/workspace/Workspace.tsx. Captură istorică a hărții demonstrative.',
4:'backend/main.py; backend/spatial_routes.py; frontend/web/src/features/workspace/ConnectedWorkspace.tsx. API conectat și studii spațiale; nu validare urbană.',
5:'backend/simulation.py; frontend/web/src/features/workspace/ConnectedWorkspace.tsx; assets/connected-comparison.png. Verificare UI pe API local: verde NS 70 s. Estimări sintetice, fără SUMO și fără măsurători reale.',
6:'backend/main.py; backend/storage.py; backend/spatial_routes.py; backend/spatial_adapter.py; sim/. FastAPI și SQLite implementate, graf pietonal conectat. SUMO local opțional; LLM cloud absent.',
11:'npm test: 9/9; npm run typecheck și npm run build: trecute după merge 00cf80c. Fetch mock și teste geografice; nu code coverage sau efect urban. Python: vezi raportul QA pentru rezultat și mediu.',
12:'sim/proposal_catalog.py; sim/proposal_validation.py; backend/spatial_routes.py. Propuneri deterministe și validarea dovezilor implementate. Provider LLM viitor; fără autorie AI cuantificată.',
13:'docs/API_CONTRACT.md; sim/sumo_engine.py; https://sumo.dlr.de/docs/Simulation/Calibrator.html. Cerere sintetică și SUMO local opțional; fără efect de trafic validat.'}.items():
 import re
 old=re.sub(r"        "+str(n)+r":'.*?(?<!\\)',(?=\n)",lambda m:'        '+str(n)+':'+repr(source)+',',old)
s=s[:start]+old+s[end:];p.write_text(s,encoding='utf-8')
p=root/'scripts/refine_v2.py';s=p.read_text(encoding='utf-8')
s=s.replace('backend/main.py · backend/server.py · sim/ · Audit 2026; legături întrerupte = integrări urbane viitoare','backend/main.py · backend/storage.py · sim/ · Audit după Git sync; întrerupt = AI viitor')
s=s.replace('Next.js / MapLibre\\nFixtures locale','Next.js / MapLibre\\nClient API conectat')
s=s.replace('FastAPI: GET /health\\nDemo HTTP: /analyze\\n/propose · /evaluate','FastAPI / Pydantic\\nSQLite · API evaluare\\nStudii spațiale')
s=s.replace('NetworkX sintetic\\nSmoke SUMO opțional','Graf pietonal / OSM\\nCandidați și dovezi\\nSUMO local opțional')
s=s.replace("b.link(s,x1,3.48,x2,3.48,'607B8B',True)","b.link(s,x1,3.48,x2,3.48,'607B8B',False)")
s=s.replace('Endpoint-uri demo: date fixe, fără LLM sau evaluare SUMO.','Semaforizare sintetică; graf pietonal conectat. Fără LLM cloud / SUMO în UI.')
s=s.replace("if j<3:b.link(s,x+2.58,3.55,x+3.15,3.55,b.BLUE,True)","if j<3:b.link(s,x+2.58,3.55,x+3.15,3.55,b.BLUE,j<2)")
s=s.replace("(3.8,'LLM','Alternative')","(3.8,'LLM viitor','Alternative')")
s=s.replace("matching(s,'5 / 5','teste ale clientului API')","matching(s,'9 / 9','teste frontend')")
p.write_text(s,encoding='utf-8')
p=root/'research/PRESENTATION_DESIGN_PLAN.md';s=p.read_text(encoding='utf-8')
s=s.replace('5/5','9/9').replace('teste client API','teste frontend')
s += '\n## Actualizare după sincronizarea Git — 18 octombrie 2026\n\nAceastă secțiune înlocuiește descrierile tehnice V1 de mai sus. Slide-urile 4–6 arată API-ul conectat, validarea Pydantic, SQLite și studiile pe graf pietonal. Legăturile implementate sunt continue; numai providerul LLM rămâne viitor. Slide-ul 5 folosește captura autentică connected-comparison.png; estimările de semaforizare sunt sintetice. Slide-ul 10 cere date documentate, calibrare și test cu specialistul. Slide-ul 11 prezintă 9/9 teste frontend, fără revendicare de impact. Slide-ul 12 distinge propunerile deterministe și validatorul existent de providerul LLM planificat. Rezultatele Python și limitele SUMO sunt documentate în raportul QA.\n'
p.write_text(s,encoding='utf-8')
