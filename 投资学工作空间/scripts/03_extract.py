from pathlib import Path
from html.parser import HTMLParser
from decimal import Decimal
import json,re,sys,hashlib
sys.stdout.reconfigure(encoding='utf-8')
W=Path(__file__).resolve().parents[1]
class Tables(HTMLParser):
 def __init__(self): super().__init__(); self.tables=[]; self.table=None; self.row=None; self.cell=None
 def handle_starttag(self,tag,attrs):
  if tag=='table': self.table=[]
  elif tag=='tr' and self.table is not None: self.row=[]
  elif tag in ['td','th'] and self.row is not None: self.cell=''
 def handle_data(self,data):
  if self.cell is not None: self.cell+=data
 def handle_endtag(self,tag):
  if tag in ['td','th'] and self.cell is not None: self.row.append(re.sub(r'\s+','',self.cell)); self.cell=None
  elif tag=='tr' and self.row is not None: self.table.append(self.row); self.row=None
  elif tag=='table' and self.table is not None: self.tables.append(self.table); self.table=None

def read_tables(t):
 p=Tables(); p.feed(t); return p.tables

def norm(t): return re.sub(r'\s+','',t)
def numeric(s):
 try: return Decimal(s.replace(',',''))
 except: return None

def find_pages(pages,vals,limit=None):
 out=[]
 for p in pages:
  if limit and p['pdf_page']>limit: continue
  text=norm(p['text'])
  if all(norm(v) in text for v in vals): out.append(p['pdf_page'])
 return out
structure=[]; totals=[]; checks=[]; manifests=[]; full_structure=[]
for year in range(2020,2025):
 md=W/f'sources/annual_reports/md/SH600519_贵州茅台_{year}.md'
 text=md.read_text(encoding='utf-8'); pages=json.loads((W/f'work/pdf-text/{year}.json').read_text(encoding='utf-8'))
 pdf=next((W/'sources/annual_reports/pdf').glob(f'*_{year}_*.pdf'))
 tables=read_tables(text)
 table=next(t for t in tables if any(r and r[0]=='主营业务分行业情况' for r in t))
 dim=None; rs=[]
 for row in table:
  if len(row)==1:
   if '分行业' in row[0]: dim='合计'
   elif '分产品' in row[0]: dim='商品类型'
   elif '分地区' in row[0]: dim='经营地区'
   elif '分销售模式' in row[0]: dim='销售渠道'
  elif len(row)>=3 and numeric(row[1]) is not None and numeric(row[2]) is not None:
   rs.append((dim,row[0],row[1],row[2],'主营业务分行业、分产品、分地区'+('、分销售模式' if year>=2022 else '')+'情况'))
 if not any(r[0]=='销售渠道' for r in rs):
  table2=next(t for t in tables if any(r and '按销售渠道' in r[0] for r in t))
  for row in table2:
   if row and row[0] in ['直销','批发代理'] and len(row)>=4:
    rs.append(('销售渠道',row[0],row[1],row[3],'按不同类型披露公司主营业务构成—按销售渠道'))
 for dim,label,rv,cs,title in rs:
  ps=find_pages(pages,[rv,cs]); assert ps,(year,label,rv,cs)
  r={'id':f'R{year}-{len([r for r in structure if r["year"]==year])+1:02}','year':year,'dimension':dim,'item':label,'revenue':str(numeric(rv)),'cost':str(numeric(cs)),'revenue_raw':rv,'cost_raw':cs,'unit':'元','currency':'人民币','entity':'贵州茅台酒股份有限公司及纳入合并范围的子公司','scope':'管理层讨论与分析：酒类主营业务分解；不是全部营业收入','table':title,'pdf':pdf.relative_to(W).as_posix(),'pdf_pages':ps,'report_pages':ps,'md':md.relative_to(W).as_posix(),'agent_pdf_check':'数值及位置匹配','human_verification':'待核验','state':'Unknown'}
  structure.append(r)
 base=next(r for r in structure if r['year']==year and r['dimension']=='合计')
 for dim in ['商品类型','经营地区','销售渠道']:
  rows=[r for r in structure if r['year']==year and r['dimension']==dim]
  dr=sum(Decimal(r['revenue']) for r in rows)-Decimal(base['revenue']); dc=sum(Decimal(r['cost']) for r in rows)-Decimal(base['cost'])
  checks.append({'year':year,'dimension':dim,'revenue_difference':str(dr),'cost_difference':str(dc),'pass':dr==0 and dc==0})
 summary=next(t for t in tables if any(r and r[0]=='营业收入' for r in t) and any(r and '归属于上市公司股东的净利润'==r[0] for r in t))
 for row in summary:
  if not row: continue
  if row[0] in ['营业收入','归属于上市公司股东的净利润','经营活动产生的现金流量净额']:
   vals=[x for x in row[1:] if numeric(x) is not None]
   rv=vals[0]; ps=find_pages(pages,[rv],10); assert ps,(year,row)
   totals.append({'year':year,'metric':row[0],'current':str(numeric(rv)),'raw_current':rv,'previous':str(numeric(vals[1])),'raw_previous':vals[1],'pdf_pages':ps,'pdf':pdf.relative_to(W).as_posix(),'scope':'合并','unit':'元','human_verification':'待核验','state':'Unknown'})
 for tab in [t for t in tables if t and t[0] and t[0][0]=='合同分类'][:1]:
  dim=None; note_rows=[]
  for row in tab:
   if row[0]=='商品类型': dim='商品类型'
   elif '按经营地区分类' in row[0]: dim='经营地区'
   elif '按销售渠道分类' in row[0]: dim='销售渠道'
   elif len(row)>=3 and numeric(row[1]) is not None and numeric(row[2]) is not None:
    dd='合计' if row[0]=='合计' else dim
    if dd is None: continue
    ps=[p for p in find_pages(pages,[row[1],row[2]]) if p>40]
    assert ps,(year,row)
    note_rows.append({'id':f'N{year}-{len(note_rows)+1:02}','year':year,'dimension':dd,'item':row[0],'revenue':str(numeric(row[1])),'cost':str(numeric(row[2])),'revenue_raw':row[1],'cost_raw':row[2],'unit':'元','currency':'人民币','entity':'贵州茅台酒股份有限公司及纳入合并范围的子公司','scope':'合并附注：全部营业收入（主营业务+其他业务），不含利息收入','table':'合并财务报表项目注释：营业收入、营业成本的分解信息','pdf':pdf.relative_to(W).as_posix(),'pdf_pages':ps,'report_pages':ps,'md':md.relative_to(W).as_posix(),'agent_pdf_check':'数值及位置匹配','human_verification':'待核验','state':'Unknown'})
  full_structure.extend(note_rows)
  total=next((r for r in note_rows if r['dimension']=='合计'),None)
  if total:
   for dd in ['商品类型','经营地区','销售渠道']:
    rr=[r for r in note_rows if r['dimension']==dd]
    dr=sum(Decimal(r['revenue']) for r in rr)-Decimal(total['revenue']); dc=sum(Decimal(r['cost']) for r in rr)-Decimal(total['cost'])
    checks.append({'year':year,'dimension':'合并附注-'+dd,'revenue_difference':str(dr),'cost_difference':str(dc),'pass':dr==0 and dc==0})
 manifests.append({'year':year,'pdf':pdf.relative_to(W).as_posix(),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'md':md.relative_to(W).as_posix(),'md_sha256':hashlib.sha256(md.read_bytes()).hexdigest(),'pages':len(pages)})
(W/'work/structured-data.json').write_text(json.dumps({'structure':structure,'full_structure':full_structure,'summary':totals,'reconciliations':checks,'reports':manifests},ensure_ascii=False,indent=2),encoding='utf-8')
print('STRUCTURE ROWS',len(structure),'FULL NOTE ROWS',len(full_structure),'SUMMARY ROWS',len(totals),'RECONCILIATIONS',len(checks),'PASSED',sum(x['pass'] for x in checks))
for r in structure: print(r['id'],r['dimension'],r['item'],r['revenue_raw'],r['cost_raw'],'PDF',r['pdf_pages'])
for r in totals: print(r['year'],r['metric'],r['current'],r['previous'],'PDF',r['pdf_pages'])
