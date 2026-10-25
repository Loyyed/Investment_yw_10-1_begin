"""Read-only reproduction of selected source matches and analytical aggregates.
Original attachments remain local. This script never submits reviews or creates signatures.
"""
import argparse,csv,hashlib,json,re,statistics,zipfile
from decimal import Decimal as D
from pathlib import Path
import pymupdf

def audit(project):
 p=Path(project).resolve();root=p/'work/content-fusion-20261025';data=json.loads((root/'analysis-data.json').read_text(encoding='utf-8'));checks=json.loads((root/'primary-source-checks.json').read_text(encoding='utf-8'))['checks'];documents={};zips={}
 for source in data['sources']:
  f=p/'sources/library'/source['path'];assert hashlib.sha256(f.read_bytes()).hexdigest()==source['sha256'],str(f)
 for row in checks:
  identity=row['pdf'];key=(identity['path'],identity.get('member',''))
  if key not in documents:
   f=p/key[0]
   if key[1]:
    if key[0] not in zips:zips[key[0]]=zipfile.ZipFile(f)
    payload=zips[key[0]].read(key[1])
   else:payload=f.read_bytes()
   assert hashlib.sha256(payload).hexdigest()==identity['sha256'],key
   documents[key]=pymupdf.open(stream=payload,filetype='pdf')
  text=documents[key][row['physical_page']-1].get_text(sort=True);normalized=text.replace(',','').replace('，','');v=D(row['raw_value']);forms={str(v),f'{v:.2f}'}
  if v==int(v):forms.add(str(int(v)))
  assert any(re.search(r'(?<![0-9.])'+re.escape(n)+r'(?![0-9.])',normalized) for n in forms),row
 positive=0
 for row in data['cash_panel']:
  amount=D(row['cfo_yuan'])-D(row['long_asset_purchase_cash_yuan']);assert amount==D(row['cash_surplus_yuan']);positive+=amount>0
 assert positive==23 and len(data['cash_panel'])==25
 for row in data['imoutai']:
  assert D(row['direct_revenue_yuan'])-D(row['revenue_yuan'])==D(row['other_direct_yuan'])
  assert D(row['revenue_yuan'])/D(row['direct_revenue_yuan'])*100==D(row['share_of_direct_percent'])
 for summary in data['peer_summary']:
  inputs=[r for r in data['peer_inputs'] if r['entity']==summary['entity']];assert len(inputs)==5
  for r in inputs:
   revenue=D(r['revenue']);assert (1-D(r['cost'])/revenue)*100==D(r['gross_margin_percent']);assert D(r['operating_profit'])/revenue*100==D(r['op_margin_percent']);assert D(r['selling_expense'])/revenue*100==D(r['selling_ratio_percent'])
  for key in ['gross_margin_percent','op_margin_percent','selling_ratio_percent']:assert statistics.median(D(r[key]) for r in inputs)==D(summary[key])
 fields={'飞天茅台 53° 500ml':'S004210536','五粮液普五 52° 500ml':'S004210537','洋河梦之蓝 M3 52° 500ml':'S004210538','国窖1573 52° 500ml':'S004210540','青花汾酒30年 53° 500ml':'S004210543'};prices={}
 f=p/'sources/library/补充材料/白酒行业_iFinD字段全集_上市以来.csv'
 for row in csv.DictReader(f.open(encoding='utf-8-sig',newline='')):
  if row['id'] in fields.values() and row['time'][:4] in ['2018','2019','2020'] and row['value']:prices[row['id'],row['time'][:10]]=D(row['value'])
 for summary in data['price_summary']:
  year=str(summary['year']);peer=fields[summary['peer']];values=[v/prices[peer,date] for (id,date),v in prices.items() if id=='S004210536' and date.startswith(year) and (peer,date) in prices and prices[peer,date]>0]
  assert len(values)==summary['n'];assert statistics.median(values)==D(summary['median_same_day_ratio'])
 for doc in documents.values():doc.close()
 for z in zips.values():z.close()
 return {'primary_pdf_value_page_matches':len(checks),'pdf_entities':len(documents),'source_files_sha_checked':len(data['sources']),'cash_positive_years':positive,'cash_sample_years':25,'platform_years':4,'peer_company_years':25,'historical_price_annual_pairs':12,'human_confirmation':False,'note':'程序复核数值/页码/运算，不替代口径裁决、人工Fact或机制确认。'}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--project',default=str(Path(__file__).resolve().parents[1]));args=ap.parse_args();print(json.dumps(audit(args.project),ensure_ascii=False))
