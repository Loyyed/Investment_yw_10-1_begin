from pathlib import Path
import fitz,json,sys
sys.stdout.reconfigure(encoding='utf-8')
W=Path(__file__).resolve().parents[1]
D=json.loads((W/'work/structured-data.json').read_text(encoding='utf-8'))
sel={2020:{8,9,14,15},2021:{8,9,15,16},2022:{8,9,16,17},2023:{9,17,86},2024:{5,7,8,9,14,16,17,55,63,64,65,66,108,120,121}}
for r in D['full_structure']:
 sel[r['year']].add(r['pdf_pages'][0])
for y,ns in sel.items():
 p=next((W/'sources/annual_reports/pdf').glob(f'*_{y}_*.pdf')); d=fitz.open(p)
 for n in sorted(ns):
  d[n-1].get_pixmap(matrix=fitz.Matrix(1.7,1.7),alpha=False).save(W/f'docs/images/pdf-{y}-p{n}.png')
 print('Rendered',y,len(ns),'pages')
