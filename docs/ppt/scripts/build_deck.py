"""Audited, editable ARTERIA pitch; run after completing the three planning MDs.

Loads preserved template slides, never rewrites backup/pre-audit sources.
Dependencies: python-pptx, Pillow. Run from any directory.
"""
from pathlib import Path
import json, re, hashlib
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
RESEARCH=ROOT/"research"
REPORTS=ROOT/"reports"
NAVY='101820'; WHITE='FFFFFF'; INK=NAVY; PALE='EDF2F6'; MUTED='A8BAC9'
BLUE='8BC9ED'; AMBER='EFC47C'; LIGHT='EFF4F7'; SECOND='486476'

def text(slide,value,x,y,w,h,size=22,color=INK,bold=False,align=None):
    sh=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
    sh.name=f'Text: {value[:42]}'
    tf=sh.text_frame;tf.clear();tf.word_wrap=True
    tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    tf.vertical_anchor=MSO_ANCHOR.TOP
    for i,line in enumerate(value.split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.space_after=Pt(7);p.line_spacing=1.06
        if align is not None:p.alignment=align
        r=p.add_run();r.text=line;r.font.name='Calibri';r.font.size=Pt(size)
        r.font.bold=bold;r.font.color.rgb=RGBColor.from_string(color)
    return sh

def link(s,x1,y1,x2,y2,color=BLUE,dashed=False):
    sh=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y1),Inches(x2),Inches(y2))
    sh.line.color.rgb=RGBColor.from_string(color);sh.line.width=Pt(1.8)
    if dashed:sh.line.dash_style=MSO_LINE_DASH_STYLE.DASH

def node(s,title,body,x,y,w,h,dark=False,size=21):
    sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
    sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string('1D2C37' if dark else LIGHT)
    sh.line.fill.background()
    text(s,title,x+.2,y+.18,w-.4,.55,24,BLUE if dark else INK,True)
    if body:text(s,body,x+.2,y+.87,w-.4,h-.97,size,PALE if dark else INK)

def pic(s,name,x,y,w,h):
    p=ROOT/'assets'/name;im=Image.open(p);iw,ih=im.size
    scale=min(w/iw,h/ih);pw,ph=iw*scale,ih*scale
    s.shapes.add_picture(str(p),Inches(x+(w-pw)/2),Inches(y+(h-ph)/2),width=Inches(pw),height=Inches(ph))

def base(s,n,section,title,dark=False,source=''):
    for sh in list(s.shapes):sh._element.getparent().remove(sh._element)
    s._element.set('showMasterSp','0')
    for el in list(s._element):
        if el.tag.endswith('}transition') or el.tag.endswith('}timing'):s._element.remove(el)
    bg=s.background.fill;bg.solid();bg.fore_color.rgb=RGBColor.from_string(NAVY if dark else WHITE)
    text(s,f'ARTERIA / {section}',.65,.45,10,.3,13,BLUE if dark else SECOND,True)
    text(s,f'{n:02d}',11.9,.42,.77,.35,14,MUTED if dark else SECOND,align=PP_ALIGN.RIGHT)
    if title:text(s,title,.65,1.04,12,1.0,36,PALE if dark else INK,True)
    if source:text(s,source,.65,7.03,12,.27,11,MUTED if dark else SECOND)

def table(s,rows,x,y,widths,rowh=.95):
    sh=s.shapes.add_table(len(rows),len(widths),Inches(x),Inches(y),Inches(sum(widths)),Inches(rowh*len(rows)))
    t=sh.table;t.first_row=False;t.horz_banding=False
    for col,w in zip(t.columns,widths):col.width=Inches(w)
    for i,row in enumerate(rows):
        t.rows[i].height=Inches(rowh)
        for j,v in enumerate(row):
            c=t.cell(i,j);c.fill.solid();c.fill.fore_color.rgb=RGBColor.from_string(LIGHT if i%2==0 else WHITE)
            c.margin_left=Inches(.2);c.margin_right=Inches(.15);c.margin_top=Inches(.12);c.margin_bottom=Inches(.1)
            c.vertical_anchor=MSO_ANCHOR.MIDDLE;c.text=v
            for p in c.text_frame.paragraphs:
                p.space_after=Pt(0)
                for r in p.runs:r.font.name='Calibri';r.font.size=Pt(21);r.font.bold=(j==0);r.font.color.rgb=RGBColor.from_string(INK)

def main():
    for name in ['PROJECT_RESEARCH_FULL.md','PITCH_CONTENT.md','PRESENTATION_DESIGN_PLAN.md']:
        assert (RESEARCH/name).exists(),f'Complete {name} before generation.'
    backup=ROOT/'archive/original-backup/Template-Pitch-Hackathon.backup.pptx';before=hashlib.sha256(backup.read_bytes()).hexdigest()
    prs=Presentation(ROOT/'archive/v1/Template-Pitch-Hackathon.v1.pptx');assert len(prs.slides)==13
    s=list(prs.slides)
    chunks=re.split(r'\n## (?=\d+\.)',(RESEARCH/'PITCH_CONTENT.md').read_text(encoding='utf-8'))
    sections={i:next(c for c in chunks if c.startswith(str(i)+'.')) for i in range(1,14)}
    copy={i:[line[2:] for line in c.splitlines() if line.startswith('> ')] for i,c in sections.items()}
    # Every content line is kept in native elements; secondary narrative is in notes.
    base(s[0],1,'TITLU','',True)
    text(s[0],'ARTERIA',.65,1.52,6.6,1.1,64,PALE,True)
    text(s[0],'Planificare urbană pentru\nechipele de mobilitate',.68,2.86,6.15,1.25,28,PALE)
    text(s[0],'Compararea intervențiilor,\nînainte de implementare',.68,4.48,6,1.0,23,BLUE)
    text(s[0],copy[1][3],.68,6.05,6.2,.45,17,PALE)
    text(s[0],copy[1][4],.68,6.57,6,.35,15,AMBER)
    pic(s[0],'workspace-demo.png',7.25,1.4,5.42,4.95)
    text(s[0],'Captură din aplicație · © contributori OpenStreetMap',7.25,6.5,5.42,.4,11,MUTED)

    base(s[1],2,'P / PROBLEMA',copy[2][0],source='Situație propusă · README.md și docs/ARCHITECTURE.md, audit 2026')
    text(s[1],copy[2][1],.65,2.12,12,.6,25,INK,True)
    text(s[1],copy[2][2],.65,2.86,12,.65,23)
    node(s[1],'Intervenție','',4.95,3.87,3.35,.85)
    for x,label in [(0.65,'Transport public'),(3.75,'Pietoni'),(6.85,'Biciclete'),(9.95,'Trafic auto')]:
        link(s[1],6.625,4.72,x+1.35,5.22,'718C9C')
        text(s[1],label,x,5.45,2.7,.55,22,INK,True,PP_ALIGN.CENTER)
    text(s[1],copy[2][4],.65,6.19,12,.55,25)
    text(s[1],copy[2][5],.65,6.72,12,.3,14,SECOND)

    base(s[2],3,'R / ALTERNATIVE',copy[3][0],source=copy[3][-1])
    table(s[2],[['QGIS','Date și analiză geografică'],['SUMO','Simulare microscopică de trafic'],['PMUD Iași','Context de planificare locală']],.65,2.2,[3,9.03],.92)
    text(s[2],'ARTERIA propune un parcurs comun:',.65,5.35,12,.5,25,INK,True)
    text(s[2],'zonă → alternative → comparație',.65,5.99,12,.5,28,'315B70')
    text(s[2],copy[3][-2],.65,6.62,12,.35,16,SECOND)

    base(s[3],4,'B / SOLUȚIA',copy[4][0],True)
    for x,n,label in [(0.65,'01','Alege zona'),(4.83,'02','Examinează\nalternativele'),(9.01,'03','Compară\nscenariul')]:
        text(s[3],n,x,2.45,3.55,.85,48,BLUE,True);text(s[3],label,x,3.5,3.55,1.25,27,PALE,True)
    link(s[3],3.8,3,4.4,3);link(s[3],7.99,3,8.58,3)
    text(s[3],copy[4][-2],.65,5.45,12,.6,24,AMBER)
    text(s[3],copy[4][-1],.65,6.2,12,.6,24,PALE)

    base(s[4],5,'A / DEMO',copy[5][0],True)
    text(s[4],'Selectează reperul\n↓\nAlege o alternativă\n↓\nDeschide comparația',.65,2.25,4.05,2.85,23,PALE,True)
    text(s[4],'DEMO: date predefinite\nși ajustări locale',.65,5.2,4.1,.95,22,AMBER,True)
    text(s[4],'Fără analiză urbană sau\nrulare SUMO din interfață',.65,6.24,4.1,.65,16,PALE)
    pic(s[4],'comparison-demo.png',5.05,2.05,7.62,4.65)
    text(s[4],'Demo local: localhost:3000/app · Captură din aplicația existentă',5.05,6.81,7.62,.35,12,MUTED)

    base(s[5],6,'B / CONSTRUCȚIE',copy[6][0],source='Cod repository, audit 2026 · Linii întrerupte: integrări de construit')
    node(s[5],'Frontend','Next.js / MapLibre\nFixtures locale',.65,2.28,3.65,2.05)
    node(s[5],'Backend','FastAPI: /health\nServer demo separat',4.83,2.28,3.65,2.05)
    node(s[5],'Sim','NetworkX sintetic\nUtilitar smoke SUMO',9.01,2.28,3.65,2.05)
    link(s[5],4.3,3.3,4.8,3.3,'607B8B',True);link(s[5],8.48,3.3,8.98,3.3,'607B8B',True)
    link(s[5],6.65,4.33,6.65,4.85,'607B8B',True)
    node(s[5],'AI planificat','Alternative structurate, validate înainte de evaluare',3.05,4.88,7.25,1.6,size=20)

    base(s[6],7,'BUSINESS / CINE PLĂTEȘTE',copy[7][0],source=copy[7][-1])
    text(s[6],'1.500 €',.65,2.65,5.2,1.1,58,INK,True)
    text(s[6],'/ lună',.68,3.85,4.9,.55,28,'315B70')
    text(s[6],'Ipoteză de abonament,\nnevalidată',.68,4.67,4.9,1.05,25,INK,True)
    text(s[6],'Cumpărător vizat',6.2,2.2,6.45,.4,18,SECOND,True)
    text(s[6],'Administrație locală /\nconsultanță de mobilitate',6.2,2.72,6.45,1.05,25,INK,True)
    text(s[6],'Valoare de verificat: timpul\npregătirii unei comparații',6.2,4.1,6.45,.95,23)
    text(s[6],'Costuri de măsurat:\ndate, calcul și suport',6.2,5.42,6.45,.9,23)
    text(s[6],copy[7][-2],.65,6.5,12,.45,18,SECOND)

    base(s[7],8,'R / PIAȚA',copy[8][0],source=copy[8][-1])
    for value,y,size,bold in [(copy[8][1],2.2,27,True),(copy[8][2],3.08,24,False),(copy[8][3],3.95,22,False)]:text(s[7],value,.65,y,12,.85,size,INK,bold)
    text(s[7],'Exercițiu comercial',.65,5.05,12,.4,18,SECOND)
    text(s[7],'10 × 18.000 € = 180.000 € / an',.65,5.57,12,.73,35,INK,True)
    text(s[7],copy[8][5],.65,6.45,12,.45,18,SECOND)

    base(s[9],10,'A / CE URMEAZĂ',copy[10][0],True)
    for x,title,body in [(.65,'Date și','contract unic'),(4.83,'Un indicator','reproductibil'),(9.01,'Test cu','un specialist')]:
        text(s[9],title,x,2.22,3.65,.5,23,BLUE,True);text(s[9],body,x,2.83,3.65,.6,23,PALE)
    link(s[9],3.75,2.65,4.4,2.65);link(s[9],7.98,2.65,8.6,2.65)
    text(s[9],copy[10][2],.65,3.72,12,.85,22,PALE)
    text(s[9],'Cererea noastră',.65,4.75,12,.4,17,BLUE,True)
    text(s[9],'O introducere către un specialist\nși acces la un set de date local.',.65,5.22,12,1.32,32,PALE,True)
    text(s[9],copy[10][-1],.65,6.64,12,.5,22,AMBER)

    base(s[10],11,'ANEXA A / DOVEZI',copy[11][0],source=copy[11][-1])
    text(s[10],'5 / 5',.65,2.28,4.8,1.3,72,INK,True)
    text(s[10],'teste ale clientului API',.65,3.83,4.8,.65,25)
    text(s[10],'Typecheck\nweb · mobile · shared',6.2,2.35,6.45,1.2,26,INK,True)
    text(s[10],'Build web\n/ și /app',6.2,4,6.45,1.2,26,INK,True)
    text(s[10],copy[11][4],.65,5.8,12,.75,21,INK,True)
    text(s[10],copy[11][5],.65,6.59,12,.45,18,SECOND)

    base(s[11],12,'ANEXA B / AI',copy[12][0],True,copy[12][-1])
    for x,title,body in [(.65,'Dovezi','și catalog'),(3.8,'LLM','Alternative'),(6.95,'Reguli','și geometrie'),(10.1,'Evaluare','independentă')]:node(s[11],title,body,x,2.4,2.58,1.8,True,size=20)
    for x in [3.24,6.39,9.54]:link(s[11],x,3.3,x+.5,3.3,BLUE,True)
    text(s[11],copy[12][2],.65,4.72,12,.6,27,AMBER,True)
    text(s[11],copy[12][3],.65,5.57,12,.65,23,PALE)
    text(s[11],copy[12][4],.65,6.38,12,.6,25,BLUE)

    base(s[12],13,'ANEXA C / METODĂ',copy[13][0],source='Surse: docs/ARCHITECTURE.md · SUMO Calibrator · Audit repository, 2026')
    table(s[12],[['Date','Sursă, dată, acoperire, licență'],['Comparație','Aceeași zonă și aceeași metodă'],['Simulare','Cerere documentată, versiune, seed și rezultate păstrate']],.65,2.18,[2.8,9.23],.98)
    text(s[12],'Lipsă date → necunoscut\nPropunere AI → ipoteză\nRulare repetată → rezultat verificabil',.65,5.28,12,1.35,21)
    text(s[12],copy[13][-1],.65,6.72,12,.38,17,SECOND)

    from refine_v2 import refine
    motion_plan=refine(s,copy,globals())
    REPORTS.mkdir(exist_ok=True)
    (REPORTS/"motion-plan.json").write_text(json.dumps(motion_plan,ensure_ascii=False,indent=2),encoding="utf-8")

    exact_sources={
        1:'README.md; frontend/web/src/features/workspace/Workspace.tsx. Captură actuală, geometrii fixtures.',
        2:'README.md; docs/ARCHITECTURE.md. Nu există interviuri sau cost numeric verificat.',
        3:'https://www.qgis.org/project/overview/\nhttps://sumo.dlr.de/docs/\nhttps://www.primaria-iasi.ro/dm_iasi/portal.nsf/pagini/consultare%2Bpublica%2Bplanul%2Bde%2Bmobilitate%2Burbana%2Bdurabila%2Bpentru%2Bpolul%2Bde%2Bcrestere%2Biasi%2Bpmud%2Biasi-0002E4D6?Open%3FOpen=\nPMUD este context, nu dovadă de adopție.',
        4:'frontend/web/src/features/workspace/Workspace.tsx; frontend/shared/core/fixtures.ts. Scenariul schimbă starea React, nu rețeaua pe backend.',
        5:'frontend/web/src/features/comparison/ComparisonPanel.tsx. Valorile sunt fixtures și euristici locale; etichetele din UI nu constituie validare. Captură ca Plan B, fără video existent.',
        6:'backend/main.py; backend/server.py; sim/smoke_test.py; sim/sumo_support.py; frontend/shared/core/api.ts. Clientul /analyze există în non-demo, fluxul urban complet nu este integrat.',
        7:'docs/ppt/archive/pre-audit/Template-Pitch-Hackathon.pre-audit.pptx. Preț nevalidat; fără cost de serving măsurat, marjă, prag juridic sau clienți confirmați.',
        8:'18000=12×1500; 180000=10×18000 numai dacă toate organizațiile ar cumpăra. Nu există o listă verificată de zece organizații. Nu este TAM/SAM sau ARR realizat.',
        9:'Componență și responsabilități confirmate explicit de utilizator în cerința V2, 18 octombrie 2026: Iustin Fagateanu — Frontend and web experience; Alex Pintilie — Bootstrap and simulation foundation; Fagateanu Eusebiu — Backend. Codul și Git nu stabilesc autorie individuală pe handlere. Rolurile de scenă și disponibilitatea nu sunt confirmate.',
        10:'docs/ROADMAP.md și docs/ppt/research/PROJECT_RESEARCH_FULL.md §19. Plan propus, fără acord de pilot. Oprirea pitch-ului aici; anexele se deschid doar la întrebare.',
        11:'frontend/shared/tests/api.test.ts: 5 passed, fetch mock. npm run typecheck și npm run build au trecut. Testele Python/SUMO nereexecutate: runtime fără dependențele proiectului. Niciun procent code coverage măsurat.',
        12:'docs/ARCHITECTURE.md; backend/server.py: rule-catalog-v1, tokeni zero, validation=True constant. Flux viitor, fără provider LLM implementat. Autoría AI a codului nu este cuantificabilă.',
        13:'docs/ARCHITECTURE.md; docs/API_CONTRACT.md; sim/sumo_support.py. https://sumo.dlr.de/docs/Simulation/Calibrator.html. Literalul observed nu dovedește achiziția datelor. Fără efect de trafic validat.'}
    manifest=[]
    for i,slide in enumerate(s,1):
        c=sections[i];tail=c[c.index('**Dovezi:'):]
        slide.notes_slide.notes_text_frame.text=f'ARTERIA — {i}\n{tail}\n\nSurse exacte și precizări:\n{exact_sources[i]}\n\nSursa de adevăr: docs/ppt/research/PROJECT_RESEARCH_FULL.md. Structură adaptată din template-ul de Andrei Margelatu, ordinea păstrată.'
        manifest.append({'slide':i,'text':[sh.text for sh in slide.shapes if sh.has_text_frame],
            'shape_count':len(slide.shapes),'tables':sum(sh.has_table for sh in slide.shapes),'pictures':sum(sh.shape_type==13 for sh in slide.shapes)})
    prs.core_properties.title='ARTERIA — pitch de hackathon';prs.core_properties.author='ARION'
    prs.core_properties.subject='Prototip de planificare urbană; implementare și ipoteze delimitate'
    output=REPORTS/'.qa/build/static.pptx'
    output.parent.mkdir(parents=True,exist_ok=True)
    prs.save(output)
    assert hashlib.sha256(backup.read_bytes()).hexdigest()==before
    (REPORTS/'deck-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Saved static staging deck: {output}; 13 slides; backup unchanged: {before}')

if __name__=='__main__':main()
