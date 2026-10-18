"""Run the repository skill validator with original-template baseline."""
from pathlib import Path
import sys,tempfile,runpy
r=Path(__file__).resolve().parents[1];repo=r.parents[1]
deps=r/'reports/.qa/deps'
if deps.exists():sys.path.insert(0,str(deps))
temp=r/'reports/.qa/tmp';temp.mkdir(parents=True,exist_ok=True);tempfile.tempdir=str(temp)
office=repo/'.agents/skills/pptx/scripts/office';sys.path.insert(0,str(office))
deck=sys.argv[1] if len(sys.argv)>1 else str(r/'Template-Pitch-Hackathon.pptx')
sys.argv=['validate.py',deck,'--original',str(r/'archive/original-backup/Template-Pitch-Hackathon.backup.pptx')]
runpy.run_path(str(office/'validate.py'),run_name='__main__')
