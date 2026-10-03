"""Compute auditable group averages; machine results never confirm themselves."""
from decimal import Decimal, ROUND_HALF_UP, localcontext
from pathlib import Path
import hashlib,json,re

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(data):return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def dec(value):
 number=Decimal(value)
 if not number.is_finite():raise ValueError('Non-finite input')
 return number
def ratio(numerator,denominator):
 if denominator<=0:raise ValueError('Denominator must be positive')
 return numerator/denominator
def displayed(value):
 return str(value.quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))

def calculate(workspace):
 from review_store import ReviewStore
 root=Path(workspace)
 payload=json.loads((root/'work/m01-calculation-inputs.json').read_text(encoding='utf-8'))
 if sha(root/payload['pdf_path'])!=payload['pdf_sha256']:raise ValueError('Source PDF changed; stop and recheck')
 import pymupdf
 clean=lambda s:re.sub(r'\s+','',str(s)).replace(',','')
 with pymupdf.open(root/payload['pdf_path']) as pdf:
  pages={page:clean(pdf[page-1].get_text()) for page in [10,15,16]}
 for row in payload['products']:
  tokens=row['source_row_numbers']
  if clean(row['name'])+''.join(clean(v) for v in tokens) not in pages[15]:
   raise ValueError('Product table row no longer matches source')
  if dec(row['sales_tonnes'])!=dec(tokens[2].replace(',','')):raise ValueError('Sales/production column mismatch')
 for row in payload['channels']:
  tokens=row['source_row_numbers']
  if clean(row['name'])+''.join(clean(v) for v in tokens) not in pages[16]:raise ValueError('Channel table row differs')
  names=['revenue_wanyuan_2024','revenue_wanyuan_2023','sales_tonnes_2024','sales_tonnes_2023']
  if any(dec(row[key])!=dec(token.replace(',','')) for key,token in zip(names,tokens)):
   raise ValueError('Channel inputs differ from their original columns')
 if clean(payload['wine']['sales_tonnes']) not in pages[10]:raise ValueError('Wine sales volume not located')
 facts={r['id']:r for r in ReviewStore(root).facts()}
 for identifier,binding in payload['required_fact_bindings'].items():
  if identifier not in facts or facts[identifier]['binding']!=binding:raise ValueError('Original human fact binding changed: '+identifier)
 results=[]
 def result(identifier,label,value,unit,formula,source_inputs,scope,locations):
  results.append({'id':identifier,'label':label,'value':displayed(value),'exact':str(value),'unit':unit,
   'formula':formula,'inputs':source_inputs,'scope':scope,'source_pages':locations,'state':'Unknown',
   'rounding':'ROUND_HALF_UP 2 decimal places','note':'程序复算；数量及新增计算结果尚待本人核验，不证明品牌机制'})
 with localcontext() as ctx:
  ctx.prec=50
  products=payload['products']
  sums={'revenue':Decimal(0),'cost':Decimal(0),'volume':Decimal(0)}
  for index,row in enumerate(products,1):
   original=facts[row['fact_id']]['value'].split('／')
   if [str(dec(v.replace(',',''))) for v in original]!=[row['revenue_yuan'],row['cost_yuan']]:
    raise ValueError('Product income/cost differs from valid Fact')
   revenue,cost,volume=dec(row['revenue_yuan']),dec(row['cost_yuan']),dec(row['sales_tonnes'])
   sums['revenue']+=revenue;sums['cost']+=cost;sums['volume']+=volume
   result('M01-A0'+str(index),row['name']+'公司组合均价',ratio(revenue,volume)/10000,'万元/销售吨',
    'revenue_yuan/sales_tonnes/10000',row,'产品组；跨规格、渠道和地区组合均价，不是单品成交价',[15,108])
   result('M01-G0'+str(index),row['name']+'毛利率',ratio(revenue-cost,revenue)*100,'%',
    '(revenue_yuan-cost_yuan)/revenue_yuan*100',row,'营业毛利率；不是净利率、经济利润或ROIC',[9,16,108])
  wine=payload['wine']
  if dec(facts['C06']['value'].replace(',',''))!=dec(wine['revenue_yuan']):
   raise ValueError('Wine income differs from valid C06 Fact')
  if sums['volume']!=dec(wine['sales_tonnes']) or sums['revenue']!=dec(wine['revenue_yuan']) or sums['cost']!=dec(wine['cost_yuan']):
   raise ValueError('Wine group and product totals differ')
  result('M01-A03','酒类整体公司组合均价',ratio(sums['revenue'],sums['volume'])/10000,'万元/销售吨',
   'sum(product_revenue_yuan)/sum(product_sales_tonnes)/10000',wine,
   '仅酒类收入与酒类销量匹配；不加其他业务或金融业务利息',[9,10,15,108])
  result('M01-G03','酒类整体加权毛利率',ratio(sums['revenue']-sums['cost'],sums['revenue'])*100,'%',
   'sum(product_revenue_yuan-product_cost_yuan)/sum(product_revenue_yuan)*100',wine,
   '收入加权毛利率；不取两个产品毛利率的简单算术平均',[9,16,108])
  channel_totals={2024:{'revenue':Decimal(0),'volume':Decimal(0)},2023:{'revenue':Decimal(0),'volume':Decimal(0)}}
  for index,row in enumerate(payload['channels'],4):
   current=ratio(dec(row['revenue_wanyuan_2024']),dec(row['sales_tonnes_2024']))
   previous=ratio(dec(row['revenue_wanyuan_2023']),dec(row['sales_tonnes_2023']))
   for year in [2024,2023]:
    channel_totals[year]['revenue']+=dec(row['revenue_wanyuan_'+str(year)])
    channel_totals[year]['volume']+=dec(row['sales_tonnes_'+str(year)])
   result('M01-A0'+str(index),row['name']+'2024组合均价',current,'万元/销售吨',
    'revenue_wanyuan_2024/sales_tonnes_2024',row,'同页公司渠道组销售口径；不代表全渠道终端动销或同款成交价',[16])
   result('M01-A0'+str(index)+'-P',row['name']+'2023比较组合均价',previous,'万元/销售吨',
    'revenue_wanyuan_2023/sales_tonnes_2023',row,'同页2023比较列；相同渠道组仍可能有产品组合变化',[16])
   result('M01-C0'+str(index-3),row['name']+'组合均价同比',ratio(current-previous,previous)*100,'%',
    '((revenue24/volume24)/(revenue23/volume23)-1)*100',row,
    '组合均价变化，不是固定SKU提价或降价幅度',[16])
  if channel_totals[2024]['volume']!=sums['volume']:raise ValueError('Channel and product sales-volume totals differ')
  current=ratio(channel_totals[2024]['revenue'],channel_totals[2024]['volume'])
  previous=ratio(channel_totals[2023]['revenue'],channel_totals[2023]['volume'])
  result('M01-C03','渠道表酒类组合均价同比',ratio(current-previous,previous)*100,'%',
   '((sum(channel_revenue24)/sum(channel_volume24))/(sum(channel_revenue23)/sum(channel_volume23))-1)*100',
   payload['channels'],'同第16页展示收入/销量口径；万元展示精度保留',[16])
  direct=payload['channels'][0]
  result('M01-S01','2024直销酒类收入占比',ratio(dec(direct['revenue_wanyuan_2024']),channel_totals[2024]['revenue'])*100,'%',
   'direct_revenue24/sum(channel_revenue24)*100',payload['channels'],'渠道收入组合指标，不等于渠道控制力',[16])
  result('M01-S02','2023直销酒类收入占比',ratio(dec(direct['revenue_wanyuan_2023']),channel_totals[2023]['revenue'])*100,'%',
   'direct_revenue23/sum(channel_revenue23)*100',payload['channels'],'同页2023比较列',[16])
 checks={'product_sales_equal_wine_sales':True,'channel_sales_equal_wine_sales':True,
  'product_revenue_equal_wine_revenue':True,'product_cost_equal_wine_cost':True,
  'gross_margin_matches_report_displays':{r['label']:r['value'] for r in results if r['id'].startswith('M01-G')}}
 if [r['value'] for r in results if r['id'].startswith('M01-G')]!=['94.06','79.87','92.01']:
  raise ValueError('Recomputed margins differ from the source display')
 return {'schema_version':1,'status':'calculated-awaiting-human-verification','input_digest':digest(payload),
  'pdf_path':payload['pdf_path'],'pdf_sha256':payload['pdf_sha256'],'required_fact_bindings':payload['required_fact_bindings'],
  'checks':checks,'results':results,
  'page15_direct_averages':[{'name':r['name'],'revenue_wanyuan':r['source_row_numbers'][4],
    'sales_tonnes':r['sales_tonnes'],'average_wanyuan_per_tonne':displayed(ratio(dec(r['source_row_numbers'][4].replace(',','')),dec(r['sales_tonnes']))),
    'average_yuan_per_tonne':displayed(ratio(dec(r['source_row_numbers'][4].replace(',','')),dec(r['sales_tonnes']))*10000),
    'state':'Unknown'} for r in products],
  'support_boundary':'仅支持公司披露口径的组合统计；终端动销、同款价格、因果机制及持续性Unknown'}

if __name__=='__main__':
 import sys
 sys.stdout.reconfigure(encoding='utf-8')
 root=Path(__file__).resolve().parents[1]
 output=calculate(root)
 from m01_metric_review import M01MetricReview
 output=M01MetricReview(root).annotate(output)
 destination=root/'work/m01-calculated-metrics.json'
 from review_store import ReviewStore
 ReviewStore._atomic_text(destination,json.dumps(output,ensure_ascii=False,indent=2)+'\n')
 ReviewStore._atomic_text(root/'evidence/m01-metric-facts.json',json.dumps(M01MetricReview(root).export(),ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(output,ensure_ascii=False,indent=2))
