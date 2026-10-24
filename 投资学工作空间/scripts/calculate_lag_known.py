"""Calendar-based lag diagnostics from current source-bound facts, no approvals."""
from pathlib import Path
from decimal import Decimal,localcontext,ROUND_HALF_UP
import sys,json,re,hashlib,statistics,math
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from review_store import ReviewStore
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def numbers(text):return [Decimal(x.replace(',','')) for x in re.findall(r'(?<!\d)-?\d[\d,]*\.\d+',text)]
def display(x,precision='.01'):return str(x.quantize(Decimal(precision),rounding=ROUND_HALF_UP))
def main(p=ROOT):
 p=Path(p);s=ReviewStore(p);raw={x['id']:x for x in s.facts()};groups={x['id']:x for x in s.lec03_agent_facts()};assert all(i in raw for i in ['R2015-01','R2016-01','R2016-02','R2016-03','R2016-04','R2016-05'])
 required_b03=[f'R{year}-{n:02}' for year in [2017,2018,2019,2025] for n in [1,2]]+['R2025-03'];assert all(id in raw for id in required_b03),'Full-window inputs missing or stale; stop rather than reuse old output'
 before=sha(p/'evidence/review-state.json');used_raw=set(['R2015-01','R2016-01','R2016-02','R2016-03','R2016-04','R2016-05']);used_groups=set();panel={}
 total16=numbers(raw['R2016-01']['value'])[2];finished,semi=numbers(raw['R2016-02']['value']);mt_prod,mt_sales=numbers(raw['R2016-03']['value']);sr_prod,sr_sales=numbers(raw['R2016-04']['value'])
 panel[2016]={'finished':finished,'semi':semi,'reported_total':total16,'mt_prod':mt_prod,'mt_sales':mt_sales,'sr_prod':sr_prod,'sr_sales':sr_sales,'mt_revenue':None,'ids':['R2016-01','R2016-02','R2016-03','R2016-04']}
 for year in range(2020,2025):
  key=f'L03-A{year}-B';assert key in groups;used_groups.add(key);d=groups[key]['data'];stock=d['physical_inventory'];mt=next(x for x in d['products'] if x['name']=='茅台酒');series=next(x for x in d['products'] if x['name']=='其他系列酒')
  total_id=f'R{year}-08' if year<2024 else 'R2024-24';assert total_id in raw,'Independent total missing or stale';used_raw.add(total_id)
  total_value=numbers(raw[total_id]['value']);assert len(total_value)==1
  panel[year]={'finished':Decimal(stock['finished_tonnes']),'semi':Decimal(stock['semi_finished_tonnes']),'reported_total':total_value[0],'mt_prod':Decimal(mt['production_tonnes']),'mt_sales':Decimal(mt['sales_tonnes']),'sr_prod':Decimal(series['production_tonnes']),'sr_sales':Decimal(series['sales_tonnes']),'mt_revenue':Decimal(mt['revenue_yuan']),'ids':[key,total_id]}
 # Prepared B03 values only enter after the original ReviewStore returns Fact.
 for year in [2017,2018,2019,2025]:
  prod_id=f'R{year}-01';stock_id=f'R{year}-02'
  if prod_id not in raw or stock_id not in raw:continue
  mt_p,mt_s,sr_p,sr_s=numbers(raw[prod_id]['value']);fin,sem,tot=numbers(raw[stock_id]['value']);used_raw.update([prod_id,stock_id]);rev=None
  if year==2025 and 'R2025-03' in raw:rev=numbers(raw['R2025-03']['value'])[0];used_raw.add('R2025-03')
  panel[year]={'finished':fin,'semi':sem,'reported_total':tot,'mt_prod':mt_p,'mt_sales':mt_s,'sr_prod':sr_p,'sr_sales':sr_s,'mt_revenue':rev,'ids':[prod_id,stock_id]+(['R2025-03'] if rev is not None else [])}
 assert sorted(panel)==list(range(2016,2026))
 inventory=[];diagnostics=[];cohorts=[]
 with localcontext() as ctx:
  ctx.prec=48
  for year,row in sorted(panel.items()):
   total=row['finished']+row['semi'];assert total>0;residual=None if row['reported_total'] is None else row['reported_total']-total
   if residual is not None:assert residual==0,(year,residual)
   inventory.append({'year':year,'finished_tonnes':str(row['finished']),'semi_finished_tonnes':str(row['semi']),'component_sum_tonnes':str(total),'reported_total_tonnes':None if row['reported_total'] is None else str(row['reported_total']),'independent_total_residual_tonnes':None if residual is None else str(residual),'semi_share_percent':str(row['semi']/total*100),'semi_share_percent_display':display(row['semi']/total*100),'input_ids':row['ids']})
  for product,prefix in [('茅台酒','mt'),('其他系列酒','sr')]:
   for lag in range(8):
    pairs=[(year,year+lag,row[prefix+'_prod'],panel[year+lag][prefix+'_sales']) for year,row in sorted(panel.items()) if year+lag in panel and year+lag<=2025]
    n=len(pairs);correlation=None;reason='n<3，停止相关系数解释'
    if n>=3:
     xs=[x[2] for x in pairs];ys=[x[3] for x in pairs];xm=sum(xs)/n;ym=sum(ys)/n;xx=sum((x-xm)**2 for x in xs);yy=sum((y-ym)**2 for y in ys)
     if xx and yy:
      corr=sum((x-xm)*(y-ym) for x,y in zip(xs,ys))/(xx*yy).sqrt();correlation=str(corr);check=statistics.correlation([float(x) for x in xs],[float(y) for y in ys]);assert math.isclose(float(corr),check,abs_tol=1e-12);reason='描述性共变；非成熟期或因果'
     else:reason='常数序列，相关系数未定义'
    diagnostics.append({'product':product,'lag':lag,'n':n,'calendar_pairs':[[x[0],x[1]] for x in pairs],'source_year_range':None if not pairs else [pairs[0][0],pairs[-1][0]],'outcome_year_range':None if not pairs else [pairs[0][1],pairs[-1][1]],'r':correlation,'reason':reason})
  for year in range(2016,2021):
   outcome=year+5;row=panel.get(year);later=panel.get(outcome)
   cohorts.append({'production_year':year,'outcome_year':outcome,'production_tonnes':None if row is None else str(row['mt_prod']),'later_sales_tonnes':None if later is None else str(later['mt_sales']),'later_revenue_yuan':None if later is None or later['mt_revenue'] is None else str(later['mt_revenue']),'state':'AgentCalculated并列观察' if row is not None and later is not None and later['mt_revenue'] is not None else 'Unknown：对应原数尚待有效确认','not_a_conversion_rate':True})
  annual_changes=[]
  for year in [2024,2025]:
   now=panel[year];previous=panel[year-1];metrics={}
   for metric,a,z in [('finished',now['finished'],previous['finished']),('semi_finished',now['semi'],previous['semi']),('company_shipments',now['mt_sales']+now['sr_sales'],previous['mt_sales']+previous['sr_sales'])]:
    delta=a-z;rate=delta/z*100;metrics[metric]={'current_tonnes':str(a),'previous_tonnes':str(z),'delta_tonnes':str(delta),'growth_percent':str(rate),'growth_percent_display':display(rate)}
   annual_changes.append({'year':year,'metrics':metrics,'state':'AgentCalculated','boundary':'各自同阶段年度变化的描述对照；公司出货非终端动销，不直接证明积压或需求下降。2025为后验观察。'})
  evidence=[{'domain':'facts','id':id,'binding':raw[id]['binding'],'pdf_path':raw[id]['pdf_path'],'pdf_sha256':raw[id]['pdf_sha256']} for id in sorted(used_raw)]+[{'domain':'lec03_agent_facts','id':id,'validated_group_snapshot_sha256':digest(groups[id]),'pdf_path':groups[id]['pdf_path'],'pdf_sha256':groups[id]['pdf_sha256'],'human_confirmation':False} for id in sorted(used_groups)]
  lines=['<!-- generated-by: calculate_lag_known.py; manual edits protected by saved output hash -->','# 贵州茅台生产库存销售滞后验证','','2026-10-24，工作稿。新增原披露B02、B03及B04由leo真实聊天核验；旧年度组通过原API复用。以下运算为AgentCalculated，判断为待人工审阅Interpretation；不冒称教师验收或签署。','','## 1. 材料与定义','','只按当前facts()与lec03_agent_facts()读取已有效输入；材料冻结和引用使用实际PDF SHA。B02六项review35—40覆盖成品脚注、库存组成与至少五年/混合勾兑等高影响披露。[真实回执](../evidence/20261022-b02-chat-confirmation.json)。合同FY2001—2025共25年完整材料版本登记尚未单独验收；本稿为FY2016—FY2025十年窗口，不冒充25年全样本。','','## 2. FY2015—FY2016断点','','2015表注三项均指成品酒；2016生产为基酒，库存包括成品和半成品。2015成品库存9,867.79吨，不能与2016含半成品总库存252,506.16吨直接算同口径增长。两类库存和生产阶段分别保留，停止跨定义总库存同比。该方法裁决不是自动新增人工可比性Fact。','','## 3. 库存组成复算','','| 年度 | 成品（吨） | 半成品（吨） | 两项合计（吨） | 半成品占比 | 独立报告总量勾稽 |','| --- | ---: | ---: | ---: | ---: | --- |']
  for x in inventory:lines.append(f"| {x['year']} | {x['finished_tonnes']} | {x['semi_finished_tonnes']} | {x['component_sum_tonnes']} | {x['semi_share_percent_display']}% | {x['independent_total_residual_tonnes'] if x['reported_total_tonnes'] is not None else '待单独补总量原行；不以相加当勾稽'} |")
  lines+=['','FY2016—FY2025十年有效数量输入完整；B04补齐五个独立报告总量后，十年均以报告总量减成品及半成品复算，差额均为0吨。不插值，不以分项合计代替独立总量。半成品数量占比较高说明库存主体处于生产/贮存阶段，不能证明稀缺、升值或未来一定高价出售。','','## 4. t+5对照','','| 生产年 | 基酒产量（吨） | 五年后 | 该年茅台酒销量（吨） | 该年茅台酒收入（元） | 状态 |','| --- | ---: | --- | ---: | ---: | --- |']
  for x in cohorts:lines.append('| '+' | '.join(str(x[key]) if x[key] is not None else 'Unknown' for key in ['production_year','production_tonnes','outcome_year','later_sales_tonnes','later_revenue_yuan','state'])+' |')
  lines+=['','两边不属于同一可追踪批次，不命名转化率、成熟率或兑现率。系列酒2016基酒20,575.44吨与2021销量30,177.38吨均有有效来源；即便后期销量大于前期单年产量，也不能解释为物理转化率超过100%。','','## 5. k=0…7诊断','','| 产品 | k | n | 生产年度→销售年度配对 | r | 使用限制 |','| --- | ---: | ---: | --- | ---: | --- |']
  for x in diagnostics:lines.append(f"| {x['product']} | {x['lag']} | {x['n']} | {', '.join(str(a)+'→'+str(z) for a,z in x['calendar_pairs']) or '无'} | {display(Decimal(x['r']),'.0001') if x['r'] is not None else 'Unknown'} | {x['reason']} |")
  lines+=['','按真实年份year+k匹配，不按缺年表格的行号平移。完整十年窗口逐lag列有效样本数和年对；不同冻结点/报告版本的n、r不能混用，不只挑最高r。Decimal计算与Python统计库独立复算在有效项一致；电子表格公式交叉核验与CSV交付的实际状态另见本目录交付回执，不以Python统计库冒充电子表格。','','## 6. N02当前判断','','候选主张：长周期生产与贮存支持未来供给。机制假设为前期基酒经贮存/勾兑形成后期可售产品；工艺原文和库存组成提供有范围支持。已有五组跨期并列观察，但未跟踪同一批基酒去向；需求、规格、损耗、组合及投放也能改变结果。当前状态：Interpretation，待人工内容审阅；非独有壁垒或因果Fact。','','## 7. N05当前判断','','候选主张：增长可能需要前置库存、产能及等待时间。库存组成与至少五年的工艺限制支持研究这一命题；尚不能据此认定资本回报高、存货全部有经济价值或维护/扩张Capex已分开。B05/B06已补设计能力、实际生产、投产/预计释放与资产变动，见[产能资本连接稿](student-capacity-capital-bridge.md)。固定资产及重要在建的可证数字已连接，项目现金/实际释放归因仍Unknown；[G6两项判断](student-lag-g6-review.md)待本人集中审阅。','','## 8. 替代解释与反证','','成熟库存增加也可能来自需求不足；收入增长也可能由价格与结构主导。若达到可售阶段的库存长期无法销售、实际净价走弱或新增投入未带来后续现金，应削弱有价值供给/时间资本解释。缺终端量、库龄和同SKU净价时保留不能区分。','','## 9. Unknown与下一步','','B03已补齐2017—2019及2025数量/库存与2025茅台酒收入；复用2020—2024有效组，不重复核旧原数。B04已由leo真实聊天核验2020—2024五个独立报告总库存原行，十年勾稽全部完成；不重复核旧分项，不将原数确认扩为人工运算确认。完整资本/产能时差、25年版本冻结、全部验收与教师裁决尚未完成。','','以FY2025为本合同冻结点，2021—2025生产年的t+5分别为2026—2030，属于右删失、尚未观察，不能写尚未兑现；2020的t+5为2025，在窗口内且已有有效数量/收入输入，不属于右删失。FY2025后验观察不回填主研究FY2024当时信息集。','','[精确运算、配对、输入绑定与独立复算](../work/lag-20261022/calculations.json)；复算命令：`D:/Anaconda/python.exe scripts/calculate_lag_known.py`。原始披露核验、运算、观点采纳、合同验收与签署分别处理。','']
  current_change=next(x for x in annual_changes if x['year']==2025)['metrics']
  note=f"2025后验变化：公司成品库存由{current_change['finished']['previous_tonnes']}吨增至{current_change['finished']['current_tonnes']}吨，增加{current_change['finished']['delta_tonnes']}吨（{current_change['finished']['growth_percent_display']}%）；公司两产品组销售/出货合计由{current_change['company_shipments']['previous_tonnes']}吨增至{current_change['company_shipments']['current_tonnes']}吨（{current_change['company_shipments']['growth_percent_display']}%）。成品库存增长快于当年出货是应核查库龄、包装/投放节奏及需求的线索；公司库存不是渠道库存，出货不是终端动销，尚不能据此裁定积压。"
  lines.insert(lines.index('## 7. N05当前判断')-1,note)
  lines+=['','交付补充：[B04独立总量实际核验回执](../evidence/20261023-b04-chat-confirmation.json)、[B03实际核验回执](../evidence/20261022-b03-chat-confirmation.json)、[诊断CSV](student-lag-diagnostics.csv)、[电子表格公式复算](生产库存销售滞后复算.xlsx)。电子表格引擎与Python已核对10项占比、16项相关和5组收入；未冒称原生Excel已打开或本人手工操作，真实状态见work/lag-20261022/spreadsheet-validation.json。','']
  from lag_g6_review import current_g6_adoption
  adoption=current_g6_adoption(p)
  if adoption['status']=='accepted-current':
   lines=[line.replace('待人工审阅Interpretation','本人已采纳的有范围Interpretation').replace('Interpretation，待人工内容审阅','Interpretation，本人已于2026-10-24采纳有范围意见').replace('解释待人工审阅','有范围解释已获本人采纳').replace('待本人集中审阅','两项已获本人采纳，当前见结论稿').replace('下一步为G6有范围的判断审阅','G6有范围的判断已获本人采纳').replace('[G6两项判断](student-lag-g6-review.md)','[G6已采纳结论](student-lag-conclusion.md)') for line in lines]
   lines+=['','[本人已采纳的当前结论](student-lag-conclusion.md)；[真实内容采纳回执](../evidence/20261024-g6-chat-adoption.json)。采纳不把Interpretation升级为Fact，Unknown与反证继续保留。','']
  text='\n'.join(lines).rstrip()+'\n';directory=p/'work/lag-20261022';out=p/'outputs/student-lag-check.md';previous=directory/'calculations.json'
  if out.exists():
   assert previous.exists() and sha(out)==json.loads(previous.read_text(encoding='utf-8'))['generated_output_sha256'],'Manual output edits detected; stop instead of overwrite'
  result={'date':'2026-10-24','state':'AgentCalculated','human_arithmetic_confirmation':False,'code_path':'scripts/calculate_lag_known.py','code_sha256':sha(Path(__file__)),'sample_years':sorted(panel),'freeze_year':2025,'inventory':inventory,'annual_changes':annual_changes,'cohorts':cohorts,'diagnostics':diagnostics,'formulas':{'semi_share':'semi/(finished+semi)*100','inventory_residual':'independently_reported_total−finished−semi, Unknown when total not source-confirmed','pearson':'sum((x−mean(x))*(y−mean(y)))/sqrt(sum((x−mean(x))²)*sum((y−mean(y))²))','pairing':'actual calendar year t with t+k; no interpolation or positional shift'},'input_evidence':evidence,'correlation_crosscheck':'Decimal precision48 vs statistics.correlation float; abs_tol1e-12','right_censored_production_years':list(range(2021,2026)),'generated_output_sha256':hashlib.sha256(text.encode()).hexdigest()}
  directory.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding='utf-8',newline='\n');previous.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 assert before==sha(p/'evidence/review-state.json');print(json.dumps({'sample_years':sorted(panel),'2016_semi_share_percent':inventory[0]['semi_share_percent_display'],'2016_residual':inventory[0]['independent_total_residual_tonnes'],'lag_n_maotai':[x['n'] for x in diagnostics if x['product']=='茅台酒'],'new_approvals':0,'report':str(out)},ensure_ascii=False))
if __name__=='__main__':main()
