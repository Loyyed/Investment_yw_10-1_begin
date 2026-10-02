from pathlib import Path
import sys,json,re,hashlib,importlib.util
sys.stdout.reconfigure(encoding='utf-8')
WS=Path(__file__).resolve().parents[1]
from pypdf import PdfReader
(WS/'work/pdf-text').mkdir(exist_ok=True)
index=[]; seen={}
for p in sorted((WS/'sources').rglob('*')):
 if not p.is_file(): continue
 b=p.read_bytes(); h=hashlib.sha256(b).hexdigest()
 if h in seen: continue
 seen[h]=str(p.relative_to(WS))
 if p.suffix.lower() in ['.md','.py','.svg','.gitignore'] or p.name=='.gitignore':
  text=b.decode('utf-8-sig',errors='replace')
  sections=re.split(r'(?m)^(?=#{1,6} )',text)
  index.append({'file':str(p.relative_to(WS)),'sha256':h,'chars':len(text),'sections':[{'heading':s.splitlines()[0] if s.splitlines() else '', 'excerpt':s[:700]} for s in sections]})
for p in sorted((WS/'sources/annual_reports/pdf').glob('*.pdf')):
 r=PdfReader(p); pages=[]
 for i,page in enumerate(r.pages):
  t=page.extract_text() or ''; pages.append({'pdf_page':i+1,'text':t})
 year=re.search(r'_(20\d\d)_',p.name)[1]
 (WS/f'work/pdf-text/{year}.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
 index.append({'file':str(p.relative_to(WS)),'pages':len(pages),'chars':sum(len(x['text']) for x in pages),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 print('PDF',year,'pages',len(pages),'chars',sum(len(x['text']) for x in pages))
(WS/'work/reading-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
print('Unique textual documents',sum('sections' in x for x in index))
print('render libraries',{x:bool(importlib.util.find_spec(x)) for x in ['pypdfium2','reportlab','PIL','fitz']})
