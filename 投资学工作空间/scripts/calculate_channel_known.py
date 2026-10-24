"""Ten-year main-channel arithmetic from current reviewed original facts only."""
from pathlib import Path
from decimal import Decimal,localcontext,ROUND_HALF_UP
import sys,json,re,hashlib,statistics,math
ROOT=Path(__file__).resolve().parents[1]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def nums(t):return [Decimal(x.replace(',','')) for x in re.findall(r'(?<!\d)-?\d[\d,]*\.\d+',t)]
def display(x,step='.01'):return str(x.quantize(Decimal(step),rounding=ROUND_HALF_UP))
def main(p=ROOT):
 sys.path.insert(0,str(p/'scripts'));from review_store import ReviewStore
 s=ReviewStore(p);raw={x['id']:x for x in s.facts()};groups={x['id']:x for x in s.lec03_agent_facts()};before=sha(p/'evidence/review-state.json');manifest=json.loads((p/'work/review-batches/20261024-B07.json').read_text(encoding='utf-8'));payload=dict(manifest);fingerprint=payload.pop('display_payload_sha256');assert fingerprint==digest(payload)
 manifest_path=p/'work/review-batches/20261024-B07.json';receipt=json.loads((p/'evidence/20261024-b07-chat-confirmation.json').read_text(encoding='utf-8'));assert sha(manifest_path)==receipt['display_manifest_sha256'],'Reviewed B07 display changed'
 panel={};used_raw={'C01','R2024-09'};used_groups=set();rates={year:{'company_revenue_yuan':None,'sales_expense_yuan':None,'input_ids':[]} for year in range(2016,2026)}
 for item in manifest['items']:
  id=item['id'];assert id in raw and raw[id]['binding']==item['binding'];values=nums(raw[id]['value']);assert len(values)==4
  panel[item['year']]={'dr':values[0],'dc':values[1],'wr':values[2],'wc':values[3],'input_ids':[id],'independently_reported_total_check':None};used_raw.add(id)
 for year in range(2020,2025):
  id=f'L03-A{year}-B';assert id in groups;d=groups[id]['data'];direct=next(x for x in d['channels'] if x['name']=='直销');wholesale=next(x for x in d['channels'] if x['name'].startswith('批发'))
  panel[year]={'dr':Decimal(direct['revenue_yuan']),'dc':Decimal(direct['cost_yuan']),'wr':Decimal(wholesale['revenue_yuan']),'wc':Decimal(wholesale['cost_yuan']),'input_ids':[id],'independently_reported_total_check':{'revenue_yuan':d['wine']['revenue_yuan'],'cost_yuan':d['wine']['cost_yuan']}};used_groups.add(id)
 assert sorted(panel)==list(range(2016,2026));rates[2024]['company_revenue_yuan']=nums(raw['C01']['value'])[0];expense24,expense23=nums(raw['R2024-09']['value']);rates[2024]['sales_expense_yuan']=expense24;rates[2024]['input_ids']=['C01','R2024-09'];rates[2023]['sales_expense_yuan']=expense23;rates[2023]['input_ids']=['R2024-09（2023比较列）']
 next_path=p/'work/review-batches/20261024-B08.json';breakpoint_verified=False;note={}
 if next_path.exists():
  upcoming=json.loads(next_path.read_text(encoding='utf-8'))
  next_payload=dict(upcoming);next_fp=next_payload.pop('display_payload_sha256');assert next_fp==digest(next_payload),'Pending display was modified'
  confirmed_receipt=json.loads((p/'evidence/20261024-b08-chat-confirmation.json').read_text(encoding='utf-8'));assert sha(next_path)==confirmed_receipt['display_manifest_sha256'],'Reviewed B08 display changed'
  for item in upcoming['items']:
   id=item['id']
   if id not in raw:continue
   assert raw[id]['binding']==item['binding'];used_raw.add(id);kind=item['kind'];year=item['year'];values=nums(raw[id]['value'])
   if kind=='company-income-sales-expense':
    assert len(values)==2;rates[year].update(company_revenue_yuan=values[0],sales_expense_yuan=values[1]);rates[year]['input_ids'].append(id)
   elif kind=='company-income-only':
    assert len(values)==1;rates[year]['company_revenue_yuan']=values[0];rates[year]['input_ids'].append(id)
   elif kind=='channel-definition':breakpoint_verified=True
   elif kind=='note-channel':
    assert len(values)==2;note[item['channel']]={'revenue':values[0],'cost':values[1],'input_id':id}
 inventory=[];decompositions=[]
 with localcontext() as ctx:
  ctx.prec=48
  for year,row in sorted(panel.items()):
   dr,dc,wr,wc=[row[x] for x in ['dr','dc','wr','wc']];revenue=dr+wr;cost=dc+wc;assert min(dr,wr)>0 and min(dc,wc)>=0
   share=dr/revenue;dg=(dr-dc)/dr;wg=(wr-wc)/wr;g=(revenue-cost)/revenue;assert abs(share*dg+(1-share)*wg-g)<Decimal('1e-42')
   reported=row['independently_reported_total_check']
   if reported:assert revenue==Decimal(reported['revenue_yuan']) and cost==Decimal(reported['cost_yuan'])
   inventory.append({'year':year,'direct_revenue_yuan':str(dr),'direct_cost_yuan':str(dc),'wholesale_revenue_yuan':str(wr),'wholesale_cost_yuan':str(wc),'channel_revenue_sum_yuan':str(revenue),'channel_cost_sum_yuan':str(cost),'direct_gross_profit_yuan':str(dr-dc),'wholesale_gross_profit_yuan':str(wr-wc),'direct_share':str(share),'direct_gross_margin':str(dg),'wholesale_gross_margin':str(wg),'gross_margin_gap':str(dg-wg),'combined_gross_margin':str(g),'independent_reported_total_check':reported,'input_ids':row['input_ids'],'channel_net_contribution':None,'state':'AgentCalculated'})
  for a,z in zip(inventory,inventory[1:]):
   s0,s1=[Decimal(x['direct_share']) for x in [a,z]];d0,d1=[Decimal(x['direct_gross_margin']) for x in [a,z]];w0,w1=[Decimal(x['wholesale_gross_margin']) for x in [a,z]]
   mix=(s1-s0)*((d0+d1)/2-(w0+w1)/2);within=(s0+s1)/2*(d1-d0)+(1-(s0+s1)/2)*(w1-w0);change=Decimal(z['combined_gross_margin'])-Decimal(a['combined_gross_margin']);residual=change-mix-within;assert abs(residual)<Decimal('1e-42')
   # Independent endpoint averaging of both factor-change paths (two-factor Shapley).
   def gross(s,d,w):return s*d+(1-s)*w
   mix2=((gross(s1,d0,w0)-gross(s0,d0,w0))+(gross(s1,d1,w1)-gross(s0,d1,w1)))/2;assert abs(mix-mix2)<Decimal('1e-42')
   decompositions.append({'from_year':a['year'],'to_year':z['year'],'direct_share_change_pp':str((s1-s0)*100),'combined_margin_change_pp':str(change*100),'mix_effect_pp':str(mix*100),'within_channel_margin_effect_pp':str(within*100),'identity_residual_pp':str(residual*100),'definition_breakpoint':a['year']==2021,'boundary':'披露分类的代数分解；非因果。2021→2022涉及平台并入定义变化。' if a['year']==2021 else '披露原数的代数分解，非渠道调整因果或净贡献','state':'AgentCalculated'})
  rate_rows=[];pairs=[]
  for year,x in rates.items():
   valid=x['company_revenue_yuan'] is not None and x['sales_expense_yuan'] is not None
   rate=None if not valid else x['sales_expense_yuan']/x['company_revenue_yuan'];share=Decimal(next(z['direct_share'] for z in inventory if z['year']==year))
   if valid:pairs.append((year,share,rate))
   rate_rows.append({'year':year,'company_revenue_yuan':None if x['company_revenue_yuan'] is None else str(x['company_revenue_yuan']),'sales_expense_yuan':None if x['sales_expense_yuan'] is None else str(x['sales_expense_yuan']),'sales_expense_rate':None if rate is None else str(rate),'input_ids':x['input_ids'],'state':'AgentCalculated' if valid else 'Unknown：该期分子或分母缺有效输入'})
  n=len(pairs);corr=None
  if n>=3:
   xm=sum(x[1] for x in pairs)/n;ym=sum(x[2] for x in pairs)/n;xx=sum((x[1]-xm)**2 for x in pairs);yy=sum((x[2]-ym)**2 for x in pairs)
   if xx and yy:corr=str(sum((x[1]-xm)*(x[2]-ym) for x in pairs)/(xx*yy).sqrt())
  sensitivity=[]
  for label,selected in [('全部2016—2025',pairs),('定义前2016—2021',[x for x in pairs if x[0]<=2021]),('定义后2022—2025',[x for x in pairs if x[0]>=2022])]:
   count=len(selected);value=None
   if count>=3:
    ax=sum(x[1] for x in selected)/count;ay=sum(x[2] for x in selected)/count;vx=sum((x[1]-ax)**2 for x in selected);vy=sum((x[2]-ay)**2 for x in selected)
    if vx and vy:
     r=sum((x[1]-ax)*(x[2]-ay) for x in selected)/(vx*vy).sqrt();value=str(r);cross=statistics.correlation([float(x[1]) for x in selected],[float(x[2]) for x in selected]);assert math.isclose(float(r),cross,abs_tol=1e-12)
   sensitivity.append({'window':label,'n':count,'years':[x[0] for x in selected],'r':value,'boundary':'描述性Pearson；分段仅作定义断点敏感性检查，小样本、不识别因果'})
  assert sensitivity[0]['r']==corr
  corr_display=display(Decimal(corr),'.0001') if corr is not None else 'Unknown（样本/方差不足）'
  rate24=next(x for x in rate_rows if x['year']==2024);rate25=next(x for x in rate_rows if x['year']==2025)
  observations={'year':2025,'sales_expense_rate_2024_percent':str(Decimal(rate24['sales_expense_rate'])*100),'sales_expense_rate_2025_percent':str(Decimal(rate25['sales_expense_rate'])*100),'sales_expense_rate_change_pp':str((Decimal(rate25['sales_expense_rate'])-Decimal(rate24['sales_expense_rate']))*100),'sales_expense_delta_yuan':str(Decimal(rate25['sales_expense_yuan'])-Decimal(rate24['sales_expense_yuan'])),'direct_share_2025_percent':str(Decimal(inventory[-1]['direct_share'])*100),'state':'AgentCalculated','boundary':'公司级费用与主营渠道结构分别观察，不按收入分摊费用，不裁定因果或渠道净贡献'}
  scope_comparison=None
  if len(note)==2:
   current=next(x for x in inventory if x['year']==2025);scope_comparison={}
   for name,prefix in [('直销','direct'),('批发代理','wholesale')]:
    x=note[name];scope_comparison[name]={'note_revenue_yuan':str(x['revenue']),'note_cost_yuan':str(x['cost']),'main_revenue_yuan':current[prefix+'_revenue_yuan'],'main_cost_yuan':current[prefix+'_cost_yuan'],'note_minus_main_revenue_yuan':str(x['revenue']-Decimal(current[prefix+'_revenue_yuan'])),'note_minus_main_cost_yuan':str(x['cost']-Decimal(current[prefix+'_cost_yuan'])),'input_id':x['input_id']}
  assert n==10 and breakpoint_verified and scope_comparison is not None,'B08 complete current inputs required; stop if stale'
  assert sum(x['revenue'] for x in note.values())==rates[2025]['company_revenue_yuan'],'Note channel revenue must reconcile to separately reviewed company revenue'
  scope_totals={'note_minus_main_revenue_yuan':str(sum(Decimal(x['note_minus_main_revenue_yuan']) for x in scope_comparison.values())),'note_minus_main_cost_yuan':str(sum(Decimal(x['note_minus_main_cost_yuan']) for x in scope_comparison.values())),'note_revenue_to_company_revenue_residual_yuan':str(sum(x['revenue'] for x in note.values())-rates[2025]['company_revenue_yuan']),'boundary':'附注全营业收入与主营酒类范围差额，仅用于范围核对；不等同i茅台费用或渠道净贡献'}
  evidence=[{'domain':'facts','id':id,'binding':raw[id]['binding'],'pdf_path':raw[id]['pdf_path'],'pdf_sha256':raw[id]['pdf_sha256']} for id in sorted(used_raw)]+[{'domain':'lec03_agent_facts','id':id,'validated_snapshot_sha256':digest(groups[id]),'pdf_path':groups[id]['pdf_path'],'pdf_sha256':groups[id]['pdf_sha256'],'human_confirmation':False} for id in sorted(used_groups)]
  lines=['<!-- generated-by: calculate_channel_known.py; saved hash protects manual edits -->','# 贵州茅台渠道净贡献验证','','2026-10-24，工作稿。B07五项20金额及B08十二项原披露已由leo真实聊天核验；2020—2024复用当前有效年度组。所有新运算为AgentCalculated，N03为待人工审阅Interpretation。2025仅后验，不回填2024。','','## 数据与口径断点','','本任务以FY2016—FY2025构建主渠道面板；2016年报14页已核主营业务按销售渠道分表。2015原件关键词未检出仅是检索观察，不证明此前没有直销或直销为0。FY2022原文已定位直销含自营及i茅台，'+('B08原文已核。' if breakpoint_verified else '该定义尚待B08确认。')+'2021→2022保留分类断点，不能将直销份额跳升全部当成同口径效率变化。i茅台不另加直销。','','## 渠道份额、成本与毛利','','| 年度 | 直销收入份额 | 直销毛利率 | 批发毛利率 | 毛利率差（百分点） | 两渠道合计毛利率 | 来源ID |','| --- | ---: | ---: | ---: | ---: | ---: | --- |']
  for x in inventory:lines.append('| '+' | '.join([str(x['year'])]+[display(Decimal(x[key])*100)+('%' if key!='gross_margin_gap' else '') for key in ['direct_share','direct_gross_margin','wholesale_gross_margin','gross_margin_gap','combined_gross_margin']]+['；'.join(x['input_ids'])])+' |')
  lines+=['','分母为两主营渠道收入之和；直接毛利＝渠道收入−对应营业成本，尚未扣除按渠道归属的销售、平台及履约投入。2020—2024另与有效酒类合计勾稽；其余年度仅求分项合计，不冒充独立报告总量已核。精确原数、公式和当前绑定见JSON。','','## 结构效应分解','','采用midpoint恒等分解：结构效应＝Δ直销份额×两期平均（直销毛利率−批发毛利率）；渠道内效应＝平均直销份额×Δ直销毛利率＋平均批发份额×Δ批发毛利率。独立计算两条因素替换路径的平均值，与结构效应一致；不是因果识别。','','| 年份 | 总毛利率变化（百分点） | 结构效应 | 渠道内毛利效应 | 口径提示 |','| --- | ---: | ---: | ---: | --- |']
  for x in decompositions:lines.append('| '+' | '.join([str(x['from_year'])+'→'+str(x['to_year'])]+[display(Decimal(x[key]),'.0001') for key in ['combined_margin_change_pp','mix_effect_pp','within_channel_margin_effect_pp']]+['FY2022定义断点' if x['definition_breakpoint'] else '仅代数分解'])+' |')
  lines+=['','48位十进制计算下各项恒等残差绝对值小于1e−42（毛利率原比值）。年度份额/毛利率显示两位小数，分解显示四位小数；显示舍入差与精确恒等残差分别保留。','','## 销售费用和回款约束','',f'销售费用率严格取合并利润表“销售费用÷其中：营业收入”，不使用含金融利息的营业总收入、母公司收入或酒类主营渠道收入代替。当前有效年对n={n}，年度为'+('、'.join(str(x[0]) for x in pairs) or '无')+'。'+('n<3，停止相关系数计算与解释。' if n<3 else f'Pearson r={corr_display}，仅描述公司级费用率与直销份额共变，不识别渠道因果。'),'','各年度分子/分母独立保存；缺任一项不补0、不插值。公司销售费用不按收入比例分到渠道，回款与库存的渠道归属未获证，渠道净贡献保持Unknown。','','## N03 当前判断','','拟采用意见：2025直销收入占比及正向结构效应得到数值支持，渠道内毛利率下降超过该结构效应，两渠道合计直接毛利率下降。按渠道归属的费用、回款和库存不足，渠道净贡献的增减方向保持Unknown；不以高直接毛利率或公司级费用率相关性代替净贡献证据。状态为Interpretation待人工内容审阅；未自动采纳或签署。','','## 替代解释、反证与 Unknown','','直销结构提升可来自渠道迁移/归类变化，毛利差也可来自产品组合或确认价格；同SKU终端成交、终端需求、净费用及渠道资本占用不足，不能识别完整价值归属。若毛利改善被新增平台/履约费用、回款或库存占用抵消，应削弱净贡献改善解释，当前不冒称这些情况已经发生。','','2025主营渠道表和附注收入分解范围不同，后者含其他业务，独立列示，不混入主渠道面板。'+('B08附注两渠道均已核，精确跨表差额见JSON。' if scope_comparison else '附注两渠道原数尚待B08核验。'),'','费用率分子/分母、FY2022定义及2025附注范围已核，当前可计算研究已完成；下一步为N03判断内容审阅，不重复核旧原数。无按渠道归属的费用、回款及库存时停止净贡献估算。','','[B07实际回执](../evidence/20261024-b07-chat-confirmation.json)；[精确运算与来源](../work/channel-20261024/calculations.json)。复算：`D:/Anaconda/python.exe scripts/calculate_channel_known.py`。','']
  supplemental=['','### 销售费用率逐年复算','','| 年度 | 合并营业收入（元） | 合并销售费用（元） | 销售费用率 | 来源ID |','| --- | ---: | ---: | ---: | --- |']
  for x in rate_rows:supplemental.append('| '+' | '.join([str(x['year']),x['company_revenue_yuan'],x['sales_expense_yuan'],display(Decimal(x['sales_expense_rate'])*100)+'%','；'.join(x['input_ids'])])+' |')
  supplemental+=['','### 定义断点敏感性检查','','| 报告窗口 | n | Pearson r |','| --- | ---: | ---: |']
  for x in sensitivity:supplemental.append(f"| {x['window']} | {x['n']} | {display(Decimal(x['r']),'.0001') if x['r'] is not None else 'Unknown'} |")
  supplemental+=['','整体与分段相关系数可能不同，反映时期选择、定义与其他因素共同变化；不能挑一段或一个符号作为直销提高/降低费用的因果证明。分段后样本更小，不作显著性或因果裁决。',f"2025公司销售费用率由{display(Decimal(observations['sales_expense_rate_2024_percent']))}%升至{display(Decimal(observations['sales_expense_rate_2025_percent']))}%，增加{display(Decimal(observations['sales_expense_rate_change_pp']),'.0001')}个百分点；公司费用增加{observations['sales_expense_delta_yuan']}元，不能全部归给直销或i茅台。",'']
  position=lines.index('## N03 当前判断');lines[position:position]=supplemental
  supplemental=['','### 2025附注减主营的渠道范围差额','','| 渠道 | 收入差额（元） | 营业成本差额（元） |','| --- | ---: | ---: |']
  for name,x in scope_comparison.items():supplemental.append(f"| {name} | {x['note_minus_main_revenue_yuan']} | {x['note_minus_main_cost_yuan']} |")
  supplemental+=[f"| 合计 | {scope_totals['note_minus_main_revenue_yuan']} | {scope_totals['note_minus_main_cost_yuan']} |",'','附注两渠道收入之和与独立已核公司营业收入勾稽差额0元。附注含其他业务，主营渠道表为酒类，两表完整原数和差额均保留；不改旧数，也不据差额推断具体平台费用或渠道效率。','','[B08实际核验回执](../evidence/20261024-b08-chat-confirmation.json)。所有新计算仍AgentCalculated，未新增人工算术或N03采纳。','']
  lines+=supplemental
  lines+=['','[N03判断集中审阅稿](student-channel-n03-review.md)：研究判断与原数/运算确认分开，尚未本人采纳或正式签署。','']
  text='\n'.join(lines);out=p/'outputs/student-channel-net-check.md';dest=p/'work/channel-20261024/calculations.json'
  if out.exists():assert dest.exists() and sha(out)==json.loads(dest.read_text(encoding='utf-8'))['generated_output_sha256'],'Manual edits detected; stop'
  result={'date':'2026-10-24','state':'AgentCalculated','human_arithmetic_confirmation':False,'code_path':'scripts/calculate_channel_known.py','code_sha256':sha(Path(__file__)),'sample_years':list(range(2016,2026)),'panel':inventory,'midpoint_decompositions':decompositions,'sales_expense_inputs':rate_rows,'sales_expense_correlation':{'n':n,'years':[x[0] for x in pairs],'r':corr,'boundary':'n<3停止；公司级费用率非渠道归属费用，相关不识别因果'},'sales_expense_correlation_sensitivity':sensitivity,'observations_2025':observations,'definition_2022_source_confirmed':breakpoint_verified,'main_vs_note_2025':scope_comparison,'main_vs_note_2025_totals':scope_totals,'channel_net_contribution':None,'input_evidence':evidence,'formulas':{'direct_share':'direct revenue/(direct revenue+wholesale revenue)','gross_margin':'(revenue−corresponding cost)/revenue','mix_effect':'Δs*(mean(g_direct)−mean(g_wholesale))','within_effect':'mean(s)*Δg_direct+(1−mean(s))*Δg_wholesale','sales_expense_rate':'consolidated sales expense / consolidated operating revenue excluding financial interest'},'precision':48,'identity_tolerance_raw_rate':'1e-42','generated_output_sha256':hashlib.sha256(text.encode()).hexdigest()};out.write_text(text,encoding='utf-8',newline='\n');dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 assert before==sha(p/'evidence/review-state.json');print(json.dumps({'years':10,'decompositions':9,'current_expense_rate_n':n,'last_decomposition':decompositions[-1],'2025_direct_share_percent':display(Decimal(inventory[-1]['direct_share'])*100),'net_contribution':'Unknown','new_approvals':0},ensure_ascii=False))
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
