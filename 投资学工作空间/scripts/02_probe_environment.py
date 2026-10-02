import sys,json,importlib.util,os
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
p=Path(sys.prefix)
m=['numpy','pandas','matplotlib','pypdf','pdfplumber','pypdfium2','fitz','nbformat','jupyter','PIL']
x={'python':sys.executable,'version':sys.version,'conda':(p/'conda-meta').exists(),'modules':{n:bool(importlib.util.find_spec(n)) for n in m}}
print(json.dumps(x,ensure_ascii=False,indent=2))
if x['conda']: print('envs', [str(q) for q in (p/'envs').glob('*/python.exe')])
Path(__file__).resolve().parents[1].joinpath('config/environment-'+('anaconda' if x['conda'] else 'python')+'.json').write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
