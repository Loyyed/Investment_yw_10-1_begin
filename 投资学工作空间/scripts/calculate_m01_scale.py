"""Compare selling costs and a conditional inventory bridge, without promotion."""
from pathlib import Path
from decimal import Decimal,localcontext,ROUND_HALF_UP
import hashlib,json,re
from pypdf import PdfReader
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def dec(value):
 result=Decimal(value)
 if not result.is_finite():raise ValueError('Invalid number')
 return result
def shown(value):return str(value.quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
def divide(amount,quantity):
 if quantity<=0:raise ValueError('Quantity denominator must be positive')
 return amount/quantity
def change(current,previous):return divide(current-previous,previous)*100

def calculate(workspace,payload=None):
 from review_store import ReviewStore
 root=Path(workspace)
 if payload is None:payload=json.loads((root/'work/m01-scale-inputs.json').read_text(encoding='utf-8'))
 facts={r['id']:r for r in ReviewStore(root).facts()}
 metrics={r['id']:r for r in ReviewStore(root).m01_metric_facts()}
 for identifier,binding in payload['required_fact_bindings'].items():
  if identifier not in facts or facts[identifier]['binding']!=binding:raise ValueError('Original Fact binding changed')
 for identifier,key in payload['required_metric_keys'].items():
  if identifier not in metrics or metrics[identifier]['confirmation_key']!=key:raise ValueError('Previously confirmed M01 metric changed')
 manifest=json.loads((root/'sources/manifest.json').read_text(encoding='utf-8'))
 clean=lambda s:re.sub(r'\s+','',str(s)).replace(',','')
 sources={}
 for source in payload['reports']:
  path=(root/source['pdf']).resolve()
  if not path.is_relative_to(root.resolve()/'sources/annual_reports/pdf'):raise ValueError('Source path outside reports')
  original=next(r for r in manifest if r['year']==source['year'])
  if source['pdf']!=original['pdf'] or source['pdf_sha256']!=original['pdf_sha256'] or hashlib.sha256(path.read_bytes()).hexdigest()!=source['pdf_sha256']:
   raise ValueError('Report version changed')
  reader=PdfReader(path)
  year=next(r for r in payload['years'] if r['year']==source['year'])
  sources[source['year']]={page:clean(reader.pages[page-1].extract_text()) for page in [9,10,14,15,year['inventory_page'],year['policy_page']]}
 for year in payload['years']:
  text=sources[year['year']]
  for row in year['products']:
   tokens=row['product_row_tokens']
   if clean(row['name'])+''.join(clean(t) for t in tokens) not in text[15]:raise ValueError('Product volume/revenue row no longer matches PDF')
   if dec(row['production_tonnes'])!=dec(clean(tokens[0])) or dec(row['sales_tonnes'])!=dec(clean(tokens[2])):
    raise ValueError('Sales and production columns differ from original')
   if clean(row['name'])+clean(row['revenue_yuan'])+clean(row['cost_yuan'])+row['report_margin'] not in text[9]:
    raise ValueError('Product income/cost row no longer matches PDF')
   if year['year']==2024:
    identifier='N2024-01' if row['name']=='茅台酒' else 'N2024-02'
    if clean(facts[identifier]['value'])!=row['revenue_yuan']+'／'+row['cost_yuan']:
     raise ValueError('2024 product income/cost differs from current Fact')
  if '酒类吨'+clean(year['wine']['production_tonnes'])+clean(year['wine']['sales_tonnes']) not in text[10]:
   raise ValueError('Wine production/sales columns no longer match')
  for label,amount in year['cost_components'].items():
   if label+amount not in text[10]:raise ValueError('Cost component no longer matches its source row')
  for label,(opening,closing) in year['inventory_gross'].items():
   inventory=text[year['inventory_page']];start=inventory.find(label+closing)
   if start<0 or opening not in inventory[start:start+140]:raise ValueError('Inventory gross opening/closing columns do not match')
  if '移动加权平均法' not in text[year['policy_page']]:raise ValueError('Inventory accounting policy changed')
 yearly={};product_results=[];component_results=[]
 with localcontext() as context:
  context.prec=50
  for year in payload['years']:
   number=year['year'];products=year['products']
   sums={key:sum(dec(row[key]) for row in products) for key in ['revenue_yuan','cost_yuan','production_tonnes','sales_tonnes']}
   if any(sums[key]!=dec(year['wine'][key]) for key in ['production_tonnes','sales_tonnes']):raise ValueError('Product/wine quantity totals differ')
   if sums['cost_yuan']!=sum(dec(v) for v in year['cost_components'].values()):raise ValueError('Cost components do not reconcile')
   derived={'revenue_yuan':sums['revenue_yuan'],'cost_yuan':sums['cost_yuan'],
    'production_tonnes':sums['production_tonnes'],'sales_tonnes':sums['sales_tonnes'],
    'unit_selling_cost_yuan':divide(sums['cost_yuan'],sums['sales_tonnes']),
    'average_sales_price_yuan':divide(sums['revenue_yuan'],sums['sales_tonnes']),
    'gross_margin_percent':divide(sums['revenue_yuan']-sums['cost_yuan'],sums['revenue_yuan'])*100}
   if number==2024 and sums['revenue_yuan']!=dec(facts['C06']['value'].replace(',','')):raise ValueError('Wine revenue differs from C06')
   productive=['在产品','自制半成品','库存商品']
   opening=sum(dec(year['inventory_gross'][name][0]) for name in productive)
   closing=sum(dec(year['inventory_gross'][name][1]) for name in productive)
   bridge=sums['cost_yuan']+closing-opening
   derived.update(productive_inventory_opening_gross=opening,productive_inventory_closing_gross=closing,
    inventory_bridge_production_input_yuan=bridge,
    bridge_per_reported_base_wine_tonne=divide(bridge,sums['production_tonnes']))
   yearly[number]=derived
  for index,name in enumerate(['茅台酒','其他系列酒']):
   rows={r['year']:r['products'][index] for r in payload['years']}
   units={y:divide(dec(r['cost_yuan']),dec(r['sales_tonnes'])) for y,r in rows.items()}
   product_results.append({'name':name,'unit_selling_cost_2023':shown(units[2023]),'unit_selling_cost_2024':shown(units[2024]),
    'unit_cost_change_percent':shown(change(units[2024],units[2023])),
    'sales_change_percent':shown(change(dec(rows[2024]['sales_tonnes']),dec(rows[2023]['sales_tonnes']))),
    'production_change_percent':shown(change(dec(rows[2024]['production_tonnes']),dec(rows[2023]['production_tonnes']))),
    'average_price_2023_wanyuan_per_tonne':shown(divide(dec(rows[2023]['revenue_yuan']),dec(rows[2023]['sales_tonnes']))/10000),
    'gross_margin_2023':shown(divide(dec(rows[2023]['revenue_yuan'])-dec(rows[2023]['cost_yuan']),dec(rows[2023]['revenue_yuan']))*100),
    'state':'Unknown','note':'本轮新增两期输入及结果待本人核验；统计变化不单独证明规模机制'})
  for name in payload['years'][0]['cost_components']:
   amounts={r['year']:dec(r['cost_components'][name]) for r in payload['years']}
   units={year:divide(amount,yearly[year]['sales_tonnes']) for year,amount in amounts.items()}
   component_results.append({'component':name,'amount_2023_yuan':str(amounts[2023]),'amount_2024_yuan':str(amounts[2024]),
    'unit_selling_cost_2023':shown(units[2023]),'unit_selling_cost_2024':shown(units[2024]),
    'unit_change_percent':shown(change(units[2024],units[2023])),'state':'Unknown',
    'boundary':'已结转营业成本的生产相关构成；不是本年生产投入分项，制造费用也不等于全部固定成本'})
  within=Decimal(0);mix=Decimal(0)
  for index in range(2):
   old=payload['years'][0]['products'][index];new=payload['years'][1]['products'][index]
   u0=divide(dec(old['cost_yuan']),dec(old['sales_tonnes']));u1=divide(dec(new['cost_yuan']),dec(new['sales_tonnes']))
   w0=divide(dec(old['sales_tonnes']),yearly[2023]['sales_tonnes']);w1=divide(dec(new['sales_tonnes']),yearly[2024]['sales_tonnes'])
   within+=w0*(u1-u0);mix+=(w1-w0)*u1
  delta=yearly[2024]['unit_selling_cost_yuan']-yearly[2023]['unit_selling_cost_yuan']
  if abs(within+mix-delta)>Decimal('1e-35'):raise ValueError('Mix decomposition does not reconcile')
  aggregate={key:shown(change(yearly[2024][key],yearly[2023][key])) for key in
   ['production_tonnes','sales_tonnes','cost_yuan','unit_selling_cost_yuan','inventory_bridge_production_input_yuan','bridge_per_reported_base_wine_tonne']}
  decomposition={'within_product_cost_effect_yuan_per_tonne':shown(within),'product_mix_effect_yuan_per_tonne':shown(mix),
   'total_change_yuan_per_tonne':shown(delta),'formula':'sum(w23*(u24-u23)) + sum((w24-w23)*u24)',
   'boundary':'仅控制两大产品组销量占比；组内规格、渠道、酒龄与投入品价格未固定','state':'Unknown'}
  years=[{'year':year,**{key:shown(value) for key,value in row.items()},'state':'Unknown'} for year,row in yearly.items()]
 return {'schema_version':1,'input_digest':digest(payload),'reports':payload['reports'],'status':'calculated-awaiting-human-verification',
  'products':product_results,'years':years,'cost_components':component_results,'aggregate_change_percent':aggregate,
  'mix_decomposition':decomposition,'checks':{'quantity_totals':True,'cost_component_totals':True,'mix_decomposition':True},
  'production_bridge':{'formula':'wine_COGS + (closing_WIP+semi_finished+finished)-(opening_WIP+semi_finished+finished)',
   'inventory_basis':'账面余额；排除未投料原材料；不是全部存货净增加',
   'assumptions':payload['production_bridge_assumptions'],'state':'Unknown',
   'boundary':'条件情景估算；未单列披露的当期生产成本不能被此估算直接确认为Fact。分母为实际基酒产量，不是可直接匹配的完工包装成品量。'},
  'conclusion_state':'Interpretation','support_boundary':'只作两期成本统计与附条件敏感性分析；不充分证明有或无规模经济，不证明品牌因果或持续性'}

if __name__=='__main__':
 import sys
 sys.stdout.reconfigure(encoding='utf-8')
 root=Path(__file__).resolve().parents[1];result=calculate(root)
 from m01_scale_review import M01ScaleReview
 result=M01ScaleReview(root).annotate(result)
 from review_store import ReviewStore
 ReviewStore._atomic_text(root/'work/m01-scale-results.json',json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 ReviewStore._atomic_text(root/'evidence/m01-scale-facts.json',json.dumps(M01ScaleReview(root).export(),ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))
