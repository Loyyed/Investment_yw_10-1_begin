"""Source-checked annual-report analysis under explicit delegated authorization."""
from pathlib import Path
from decimal import Decimal,localcontext,ROUND_HALF_UP
import copy,json,re,hashlib
from pypdf import PdfReader
import pymupdf
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def clean(value):return re.sub(r'\s+','',value).replace('−','-')
def dec(value):
 n=Decimal(str(value).replace(',',''))
 if not n.is_finite():raise ValueError('Nonfinite input')
 return n
def shown(value):return str(value.quantize(Decimal('.01'),rounding=ROUND_HALF_UP))
def percent(part,whole):
 if whole<=0:raise ValueError('Denominator must be positive')
 return part/whole*100
MONEY=r'-?\d{1,3}(?:,\d{3})+\.\d{2}'
CF_LABELS=['销售商品、提供劳务收到的现金','客户存款和同业存放款项净增加额','收取利息、手续费及佣金的现金',
 '收到的税费返还','收到其他与经营活动有关的现金','购买商品、接受劳务支付的现金','客户贷款及垫款净增加额',
 '存放中央银行和同业款项净增加额','拆出资金净增加额','支付利息、手续费及佣金的现金',
 '支付给职工及为职工支付的现金','支付的各项税费','支付其他与经营活动有关的现金','经营活动产生的现金流量净额',
 '购建固定资产、无形资产和其他长期资产支付的现金']
SPECS={2020:{'industry':12,'narrative':[16],'product':8,'volume':[13],'channel':14,'channel_volume':13,'inventory':12,'net':54,'cash':56,'storage':13},
 2021:{'industry':13,'narrative':[16,17],'product':8,'volume':[14],'channel':15,'channel_volume':15,'inventory':13,'net':55,'cash':57,'storage':14},
 2022:{'industry':14,'narrative':[18],'product':9,'volume':[14,15],'channel':16,'channel_volume':15,'inventory':14,'net':59,'cash':61,'storage':15},
 2023:{'industry':14,'narrative':[19],'product':9,'volume':[15],'channel':17,'channel_volume':16,'inventory':15,'net':64,'cash':66,'storage':15},
 2024:{'industry':14,'narrative':[20],'product':9,'volume':[15],'channel':9,'channel_volume':16,'inventory':14,'net':64,'cash':66,'storage':15}}
NARRATIVES={2020:'市场份额逐渐向头部企业集中',2021:'白酒行业产销总量趋于平稳',2022:'行业“马太效应”越发明显',2023:'全国白酒行业进入了“存量竞争”时期',2024:'白酒行业正处于宏观经济周期与产业调整周期的双重叠加时期'}
CASH_REASONS={2022:(8,'公司吸收存款减少','不可提前支取的同业定期存款增加'),2023:(9,'销售商品收到的现金增加','不可提前支取的定期存款净增加额减少'),2024:(9,'销售商品收到的现金增加','归集集团公司其他成员单位资金较上期增加')}
def row_text(text,label):
 needle=clean(label);start=clean(text).find(needle)
 if start<0:raise ValueError('Missing row '+label)
 tail=clean(text)[start+len(needle):]
 return re.match(r'[^\u4e00-\u9fff]*',tail).group(0)
def money_pair(text,label):
 pattern=r'\s*'.join(re.escape(c) for c in clean(label))
 for hit in re.finditer(pattern,text):
  tail=text[hit.end():].lstrip()
  tail=re.sub(r'^（.*?）','',tail,count=1,flags=re.S)
  values=re.findall(MONEY,re.match(r'[^\u4e00-\u9fff]*',tail).group(0))
  if len(values)>=2:return [v.replace(',','') for v in values[:2]]
 raise ValueError('Two monetary values required: '+label)
def check_contains(a,b,token):
 if clean(token) not in clean(a) or clean(token) not in clean(b):raise ValueError('Two independent engines disagree: '+token)
def spatial_cash(doc,first,year,pypdf_texts):
 words=[];parts=[]
 for page in range(first,first+4):
  words += [(page,w) for w in doc[page-1].get_text('words')]
  parts.append(pypdf_texts[page])
 full=''.join(clean(w[4]) for p,w in words)
 offsets=[];i=0
 for page,w in words:
  length=len(clean(w[4]));offsets.append((i,i+length,page,w));i+=length
 start=full.index('合并现金流量表');end=full.find('母公司现金流量表',start)
 if end<0:raise ValueError('Cannot identify consolidated/parent cash boundary')
 headers={str(y)+'年度':[(w[0]+w[2])/2 for a,b,p,w in offsets if start<=a<end and w[4]==str(y)+'年度'] for y in [year,year-1]}
 if any(not v for v in headers.values()):raise ValueError('Cash column headers absent')
 centers=[headers[str(y)+'年度'][0] for y in [year,year-1]]
 t=''.join(parts).split('合并现金流量表',1)[1].split('母公司现金流量表',1)[0]
 result={};pages={}
 for label in CF_LABELS:
  at=full.find(label,start,end)
  if at<0:raise ValueError('Cash label absent')
  tail=full[at+len(label):end];length=len(re.match(r'[^\u4e00-\u9fff]*',tail).group(0))
  span=tail[:length];cells=['0','0'];seen=[False,False]
  primary=re.findall(MONEY,row_text(t,label))
  matches=list(re.finditer(MONEY,span))
  if [m.group(0) for m in matches]!=primary:raise ValueError('Independent cash extraction differs')
  for m in matches:
   char=at+len(label)+m.start()
   offset=next(r for r in offsets if r[0]<=char<r[1]);page,w=offset[2:]
   center=(w[0]+w[2])/2;column=min(range(2),key=lambda k:abs(center-centers[k]))
   if abs(center-centers[column])>45 or seen[column]:raise ValueError('Ambiguous current/prior cash column')
   cells[column]=m.group(0).replace(',','');seen[column]=True
  page=next(p for a,b,p,w in offsets if a<=at<b)
  result[label]={'current_yuan':cells[0],'previous_yuan':cells[1],'current_blank':not seen[0],
   'previous_blank':not seen[1],'page':page,'blank_policy':'原表空白按本算术的0处理，不移动上期数填入本期'}
  pages[label]=page
 return result
def extract(workspace):
 root=Path(workspace);manifest=json.loads((root/'sources/manifest.json').read_text(encoding='utf-8'))
 output=[]
 for year,spec in SPECS.items():
  source=next(r for r in manifest if r['year']==year);path=root/source['pdf']
  if sha(path)!=source['pdf_sha256']:raise ValueError('PDF changed')
  reader=PdfReader(path);doc=pymupdf.open(path);text={};secondary={}
  wine_page=8 if year==2022 else spec['product']
  pages=set([spec[k] for k in ['industry','product','channel','channel_volume','inventory','net','storage']]+[wine_page]+spec['volume']+spec['narrative']+list(range(spec['cash'],spec['cash']+4)))
  if year==2024:pages.update([7,8])
  if year in CASH_REASONS:pages.add(CASH_REASONS[year][0])
  for page in pages:
   text[page]=reader.pages[page-1].extract_text();secondary[page]=doc[page-1].get_text()
  industry_page=spec['industry'];paragraph=clean(text[industry_page])
  patterns={'production_wan_kl':r'(?:酿酒总产量|累计白酒产量)([\d,.]+)万千升',
    'sales_revenue_yi':r'实现销售收入([\d,.]+)亿元','total_profit_yi':r'实现利润总额([\d,.]+)亿元'}
  industry={}
  for key,pattern in patterns.items():
   match=re.search(pattern,paragraph)
   if not match:raise ValueError('Industry field absent '+key)
   check_contains(text[industry_page],secondary[industry_page],match.group(0))
   industry[key]=match[1].replace(',','')
  rates=re.findall(r'同比(?:下降|微降)([\d.]+)%',paragraph)
  rises=re.findall(r'同比增长([\d.]+)%',paragraph)
  industry.update(reported_production_yoy_percent='-'+rates[0] if rates else None,
   reported_revenue_yoy_percent=rises[0] if rises else None,reported_profit_yoy_percent=rises[1] if len(rises)>1 else None,
   scope='年报引用的全国规模以上白酒；非高端酱香市场统计',location=industry_page)
  for v in rates+rises:check_contains(text[industry_page],secondary[industry_page],v+'%')
  narrative=''.join(text[p] for p in spec['narrative']);second=''.join(secondary[p] for p in spec['narrative'])
  check_contains(narrative,second,NARRATIVES[year]);industry['company_narrative']=NARRATIVES[year];industry['narrative_pages']=spec['narrative']
  products=[];volume_text=' '.join(text[p] for p in spec['volume'])
  for label in ['茅台酒','其他系列酒']:
   values=money_pair(text[spec['product']],label)
   second_values=money_pair(secondary[spec['product']],label)
   if values!=second_values:raise ValueError('Product financial rows differ')
   name=r'\s*'.join(label);numbers=r'([\d,]+\.\d{2})\s+(-?[\d.]+)\s+([\d,]+\.\d{2})\s+(-?[\d.]+)'
   match=re.search(name+r'\s+'+numbers,volume_text)
   if not match:raise ValueError('Volume row absent '+label)
   nums=[v.replace(',','') for v in match.groups()]
   secondvolume=''.join(secondary[p] for p in spec['volume'])
   check_contains(volume_text,secondvolume,label+''.join(match.groups()))
   products.append({'name':label,'revenue_yuan':values[0],'cost_yuan':values[1],
    'production_tonnes':nums[0],'reported_production_yoy_percent':nums[1],'sales_tonnes':nums[2],'reported_sales_yoy_percent':nums[3],
    'amount_page':spec['product'],'volume_pages':spec['volume']})
  wine_values=money_pair(text[wine_page],'酒类')
  if wine_values!=money_pair(secondary[wine_page],'酒类'):raise ValueError('Wine rows differ')
  if [sum(dec(p[k]) for p in products) for k in ['revenue_yuan','cost_yuan']]!=[dec(v) for v in wine_values]:raise ValueError('Wine product sum differs '+str(year)+' '+repr(products)+' '+repr(wine_values))
  channels=[]
  for label in ['直销','批发代理']:
   channel_text=text[spec['channel']];channel_second=secondary[spec['channel']]
   if year!=2024:
    channel_text=channel_text.split('按销售渠道',1)[1];channel_second=channel_second.split('按销售渠道',1)[1]
   values=money_pair(channel_text,label)
   if values!=money_pair(channel_second,label):raise ValueError('Channel financial rows differ')
   four=re.search(label+r'\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})',text[spec['channel_volume']])
   if not four:raise ValueError('Channel volume row absent')
   check_contains(text[spec['channel_volume']],secondary[spec['channel_volume']],label+''.join(four.groups()))
   channels.append({'name':label,'revenue_yuan':values[0],'cost_yuan':values[1],'sales_tonnes':four[3].replace(',',''),
    'display_revenue_wanyuan':four[1].replace(',',''),'amount_page':spec['channel'],'volume_page':spec['channel_volume']})
  if [sum(dec(c[k]) for c in channels) for k in ['revenue_yuan','cost_yuan']]!=[dec(v) for v in wine_values]:raise ValueError('Channel/wine totals differ '+str(year)+' '+repr(channels)+' '+repr(wine_values))
  net=money_pair(text[spec['net']],'五、净利润')[0]
  if net!=money_pair(secondary[spec['net']],'五、净利润')[0]:raise ValueError('Consolidated profit differs')
  cash=spatial_cash(doc,spec['cash'],year,text)
  cash_reason=None
  if year in CASH_REASONS:
   rp,*tokens=CASH_REASONS[year]
   for token in tokens:check_contains(text[rp],secondary[rp],token)
   cash_reason={'page':rp,'management_explanations':tokens,'boundary':'核准管理层确实如此解释；现金分解作独立数字对照，不把自述等同完整因果证明'}
  inv_text=clean(text[spec['inventory']]);match=re.search(r'成品酒半成品酒（含基础酒）([\d,]+\.\d{2})([\d,]+\.\d{2})',inv_text)
  if not match:raise ValueError('Physical inventory row absent')
  check_contains(text[spec['inventory']],secondary[spec['inventory']],match.group(0))
  storage=text[spec['storage']];storage2=secondary[spec['storage']]
  check_contains(storage,storage2,'至少五年' if year==2020 else '至少需要五年')
  check_contains(storage,storage2,'不同年份、不同轮次、不同浓度')
  output.append({'year':year,'pdf_path':source['pdf'],'pdf_sha256':source['pdf_sha256'],'industry':industry,
   'products':products,'wine':{'revenue_yuan':wine_values[0],'cost_yuan':wine_values[1]},'channels':channels,
   'physical_inventory':{'finished_tonnes':match[1].replace(',',''),'semi_finished_tonnes':match[2].replace(',',''),'page':spec['inventory']},
   'storage_disclosure':{'minimum_years':5,'multi_vintage_blending':True,'page':spec['storage'],'boundary':'仅证明公司持续披露工艺与储存安排，不证明壁垒独有性'},
   'consolidated_net_profit_yuan':net,'net_profit_page':spec['net'],'cash_rows':cash,'cash_pages':list(range(spec['cash'],spec['cash']+4)),'cash_reason':cash_reason,
   'two_independent_pdf_engines':'pypdf+pymupdf; cash columns spatially resolved'})
  doc.close()
 # Explicitly attributable 2024 wine projects and current disclosed operating process.
 last=output[-1];source=next(r for r in manifest if r['year']==2024);reader=PdfReader(root/source['pdf']);doc=pymupdf.open(root/source['pdf'])
 capital=[]
 for label in ['3万吨酱香系列酒技改工程及其配套设施项目','“十四五”酱香酒习水同民坝一期建设项目','茅台酒“十四五”技改建设项目']:
  values=re.findall(r'\d{1,3}(?:,\d{3})+\.\d{2}',row_text(reader.pages[13].extract_text(),label))
  if len(values)<3:raise ValueError('Project investments absent')
  check_contains(reader.pages[13].extract_text(),doc[13].get_text(),label+''.join(values[:3]))
  capital.append({'name':label,'planned_wanyuan':values[0].replace(',',''),'current_investment_wanyuan':values[1].replace(',',''),'accumulated_wanyuan':values[2].replace(',',''),'page':14})
 op=reader.pages[6].extract_text()+reader.pages[7].extract_text();op2=doc[6].get_text()+doc[7].get_text()
 for token in ['制曲—制酒—贮存—勾兑—包装','自营和“i茅台”等数字营销平台渠道']:
  check_contains(op,op2,token)
 doc.close()
 return {'schema_version':1,'years':output,'capital_2024':capital,'operating_process_2024':{'pages':[7,8],'process':'制曲—制酒—贮存—勾兑—包装','direct':'自营及i茅台等数字营销平台','wholesale':'经销商、商超、电商等'},
  'industry_comparability':'年度引用统计的样本/基数未形成完整统一桥接；用各报告披露同比，不从跨年绝对值重算行业CAGR或细分市占率',
  'authority':'Agent在本人明确授权下原文核准；不替代或伪造本人窗口确认'}
def calculate(inputs):
 output=copy.deepcopy(inputs);conflicts=[]
 with localcontext() as ctx:
  ctx.prec=40
  for year in output['years']:
   for p in year['products']:
    p['asp_wanyuan_per_sales_tonne']=shown(dec(p['revenue_yuan'])/dec(p['sales_tonnes'])/10000)
    p['gross_margin_percent']=shown(percent(dec(p['revenue_yuan'])-dec(p['cost_yuan']),dec(p['revenue_yuan'])))
   for c in year['channels']:
    c['gross_margin_percent']=shown(percent(dec(c['revenue_yuan'])-dec(c['cost_yuan']),dec(c['revenue_yuan'])))
    c['revenue_share_percent']=shown(percent(dec(c['revenue_yuan']),dec(year['wine']['revenue_yuan'])))
    c['asp_wanyuan_per_sales_tonne']=shown(dec(c['revenue_yuan'])/dec(c['sales_tonnes'])/10000)
   year['wine']['gross_margin_percent']=shown(percent(dec(year['wine']['revenue_yuan'])-dec(year['wine']['cost_yuan']),dec(year['wine']['revenue_yuan'])))
   vals={label:dec(row['current_yuan']) for label,row in year['cash_rows'].items()}
   incoming=['销售商品、提供劳务收到的现金','收到的税费返还','收到其他与经营活动有关的现金']
   outgoing=['购买商品、接受劳务支付的现金','支付给职工及为职工支付的现金','支付的各项税费','支付其他与经营活动有关的现金']
   residual=sum(vals[k] for k in incoming)-sum(vals[k] for k in outgoing)
   financial=vals['客户存款和同业存放款项净增加额']+vals['收取利息、手续费及佣金的现金']-sum(vals[k] for k in ['客户贷款及垫款净增加额','存放中央银行和同业款项净增加额','拆出资金净增加额','支付利息、手续费及佣金的现金'])
   cfo=vals['经营活动产生的现金流量净额'];capex=vals['购建固定资产、无形资产和其他长期资产支付的现金']
   if residual+financial!=cfo:raise ValueError('Cash classification does not reconcile')
   year['cash_analysis']={'cfo_yuan':str(cfo),'explicit_financial_items_net_yuan':str(financial),'after_listed_financial_items_residual_yuan':str(residual),
    'capex_cash_yuan':str(capex),'simplified_cfo_minus_capex_yuan':str(cfo-capex),'cfo_to_consolidated_profit_percent':shown(percent(cfo,dec(year['consolidated_net_profit_yuan']))),
    'boundary':'集团原报年度口径；金融剔除余额仍含金融业务分摊税费薪酬、酒店/冰淇淋及银行利息等，不是准确酒类CFO；CFO减购建长期资产现金仅简化代理，不是完整FCFF/FCFE。'}
  for old,new in zip(output['years'],output['years'][1:]):
   for level,rate in [('production_wan_kl','reported_production_yoy_percent'),('sales_revenue_yi','reported_revenue_yoy_percent'),('total_profit_yi','reported_profit_yoy_percent')]:
    naive=(dec(new['industry'][level])/dec(old['industry'][level])-1)*100
    quoted=new['industry'][rate]
    if quoted is not None and abs(naive-dec(quoted))>dec('.10'):
     conflicts.append({'year':new['year'],'variable':level,'naive_cross_report_yoy_percent':shown(naive),'report_disclosed_yoy_percent':quoted,
      'resolution':'保留两个年度原披露；不认定报告出错，也不把跨报告绝对值直接拼接为同口径增速'})
  output['industry_cross_report_conflicts']=conflicts
  output['capital_2024_current_investment_yuan']=str(sum(dec(r['current_investment_wanyuan'])*10000 for r in inputs['capital_2024']))
  a,b=output['years'][0]['products'][0],output['years'][-1]['products'][0]
  output['maotai_2020_2024_change_percent']={key:shown((dec(b[key])/dec(a[key])-1)*100) for key in ['revenue_yuan','sales_tonnes']}
  output['maotai_2020_2024_asp_change_percent']=shown(((dec(b['revenue_yuan'])/dec(b['sales_tonnes']))/(dec(a['revenue_yuan'])/dec(a['sales_tonnes']))-1)*100)
 output['industry_stage']={'state':'Interpretation','classification':'成熟期（存量竞争、结构升级），叠加调整周期','author':'本人暂定成熟期，Agent用跨年年报补证',
  'boundary':'较强支持广义白酒的工作判断；不是高端酱香细分市场阶段已独立证实的Fact，成熟也不等于全行业衰退'}
 return output
def groups(result):
 records=[]
 for year in result['years']:
  y=year['year'];common={'year':y,'pdf_path':year['pdf_path'],'pdf_sha256':year['pdf_sha256'],'verifier':'Agent（本人明确授权）','human_confirmation':False}
  for suffix,label,fields,boundary in [
   ('I','年度行业引用与管理层行业叙事',['industry'],'证明公司引用这些统计并作出叙事；生命周期为Interpretation，不把管理层预测当期后事实'),
   ('B','产品与渠道单位经济、实物库存及储存披露',['products','wine','channels','physical_inventory','storage_disclosure'],'公司口径单位经济与自述工艺，非固定SKU净价或消费者终端动销，不证明独有壁垒'),
   ('C','集团现金转换及金融现金分解',['consolidated_net_profit_yuan','net_profit_page','cash_rows','cash_pages','cash_analysis','cash_reason'],'集团原报内计算；金融剔除余额非酒类CFO，简化现金代理非完整FCFF/FCFE')]:
   records.append({'id':f'L03-A{y}-{suffix}','label':label,**common,'support_boundary':boundary,'data':{key:year[key] for key in fields}})
 last=result['years'][-1]
 records.append({'id':'L03-A2024-P','label':'可直接归属的酒类项目投入与经营流程','year':2024,'pdf_path':last['pdf_path'],'pdf_sha256':last['pdf_sha256'],
  'verifier':'Agent（本人明确授权）','human_confirmation':False,'support_boundary':'所列酒类项目当期投资与公司经营流程；不是全部酒类资本支出/资本或分部ROIC',
  'data':{'capital':result['capital_2024'],'current_investment_yuan':result['capital_2024_current_investment_yuan'],'operating_process':result['operating_process_2024']}})
 return records
def current_facts(workspace):
 root=Path(workspace);path=root/'evidence/lec03-agent-facts.json'
 if not path.exists():return []
 value=json.loads(path.read_text(encoding='utf-8'))
 try:
  if value['authority']!='explicit-delegated-agent-source-verification':return []
  if value['code_sha256']!=sha(root/'scripts/lec03_agent_analysis.py'):return []
  auth=root/'evidence/lec03-content-review.json'
  if value['authorization_sha256']!=sha(auth):return []
  authorization=json.loads(auth.read_text(encoding='utf-8'))
  if authorization['delegation']['authorized_by']!='本人' or not authorization['delegation']['agent_source_verification']:return []
  if '给你极大权限' not in authorization['statement_original']:return []
  inputs=extract(root)
  if inputs!=json.loads((root/'work/lec03-agent-inputs.json').read_text(encoding='utf-8')):return []
  result=calculate(inputs)
  if digest(result)!=value['result_digest']:return []
  if result!=json.loads((root/'work/lec03-agent-results.json').read_text(encoding='utf-8')):return []
  if value['facts']!=[{**r,'state':'Fact','verification_method':'Agent双引擎原文+空间列核对+算术校验'} for r in groups(result)]:return []
  return value['facts']
 except (OSError,ValueError,KeyError,TypeError,StopIteration):return []
if __name__=='__main__':
 import sys
 sys.stdout.reconfigure(encoding='utf-8')
 print(json.dumps(calculate(extract(Path(__file__).resolve().parents[1])),ensure_ascii=False,indent=2))
