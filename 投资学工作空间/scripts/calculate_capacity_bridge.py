"""Source-bound capacity/capital observations; no human approvals or causal assignment."""
from pathlib import Path
from decimal import Decimal,localcontext,ROUND_HALF_UP
import sys,json,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def nums(t):return [Decimal(x.replace(',','')) for x in re.findall(r'(?<!\d)-?\d[\d,]*\.\d+',t)]
def fmt(x):return format(x.quantize(Decimal('.01'),rounding=ROUND_HALF_UP),',.2f')
def main(p=ROOT):
 sys.path.insert(0,str(p/'scripts'));from review_store import ReviewStore
 s=ReviewStore(p);raw={x['id']:x for x in s.facts()};groups={x['id']:x for x in s.lec03_agent_facts()}
 ids=['R2024-25','R2025-04','R2024-26','R2025-05','R2025-06','R2025-07','R2025-08','R2025-01','R2016-05']+[f'R2025-{n:02}' for n in range(9,17)];assert all(x in raw for x in ids)
 groupids=['L03-A2024-B','L03-A2024-C','L03-A2024-P'];assert all(x in groups for x in groupids)
 state_before=sha(p/'evidence/review-state.json');design24=nums(raw['R2024-25']['value']);design25=nums(raw['R2025-04']['value']);assert len(design24)==len(design25)==2
 products=groups['L03-A2024-B']['data']['products'];prod24=[Decimal(next(x for x in products if x['name']==name)['production_tonnes']) for name in ['茅台酒','其他系列酒']];p25=nums(raw['R2025-01']['value']);assert len(p25)==4;prod25=[p25[0],p25[2]]
 capacity=[];finance=[]
 with localcontext() as ctx:
  ctx.prec=48
  for i,product in enumerate(['茅台酒','其他系列酒']):
   capacity.append({'product':product,'design_2024_tonnes':str(design24[i]),'design_2025_tonnes':str(design25[i]),'design_delta_tonnes':str(design25[i]-design24[i]),'actual_base_production_2024_tonnes':str(prod24[i]),'actual_base_production_2025_tonnes':str(prod25[i]),'production_delta_tonnes':str(prod25[i]-prod24[i]),'production_growth_percent':str((prod25[i]/prod24[i]-1)*100),'actual_to_design_2024_percent':str(prod24[i]/design24[i]*100),'actual_to_design_2025_percent':str(prod25[i]/design25[i]*100),'ratio_is_utilization_rate':False,'state':'AgentCalculated'})
  for name,id in [('固定资产账面列报金额','R2025-06'),('在建工程账面列报金额','R2025-07')]:
   amounts=nums(raw[id]['value']);assert len(amounts)==2;current,previous=amounts
   finance.append({'name':name,'current_2025_yuan':str(current),'previous_2024_yuan':str(previous),'delta_yuan':str(current-previous),'growth_percent':str((current/previous-1)*100),'period_type':'期末存量','source_id':id,'state':'AgentCalculated'})
  cash25=nums(raw['R2025-08']['value']);assert len(cash25)==1;cash24=Decimal(groups['L03-A2024-C']['data']['cash_rows']['购建固定资产、无形资产和其他长期资产支付的现金']['current_yuan'])
  finance.append({'name':'购建固定资产、无形资产和其他长期资产支付的现金','current_2025_yuan':str(cash25[0]),'previous_2024_yuan':str(cash24),'delta_yuan':str(cash25[0]-cash24),'growth_percent':str((cash25[0]/cash24-1)*100),'period_type':'年度现金流出','source_id':'R2025-08 / L03-A2024-C','state':'AgentCalculated'})
  release=[]
  for year,id in [(2024,'R2024-26'),(2025,'R2025-05')]:
   value=raw[id]['value'];amounts=nums(value);months=re.findall(r'(\d{4})年(\d{1,2})月',value);future=re.search(r'将在(\d{4})年释放',value)
   assert len(amounts)==2 and len(months)==2 and future
   release.append({'disclosure_year':year,'new_capacity_tonnes':dict(zip(['茅台酒','其他系列酒'],map(str,amounts))),'commission_month':{name:a+'-'+z.zfill(2) for name,(a,z) in zip(['茅台酒','其他系列酒'],months)},'company_expected_release_year':int(future[1]),'actual_release_verified':False,'source_id':id})
  # Timings are explicit source disclosures; attribution to observed production remains Unknown.
  projects=groups['L03-A2024-P']['data']['capital']
  # B06 enters only through current source-bound original disclosure facts.
  projects25=[]
  for n,previous in zip(range(9,12),projects):
   id=f'R2025-{n:02}';current,cumulative=nums(raw[id]['value']);assert previous['name'] in raw[id]['claim'] if 'claim' in raw[id] else True
   old_cumulative=Decimal(previous['accumulated_wanyuan'])
   projects25.append({'name':previous['name'],'source_id':id,'current_investment_wanyuan':str(current),'accumulated_investment_wanyuan':str(cumulative),'previous_accumulated_wanyuan':str(old_cumulative),'accumulated_rollforward_residual_wanyuan':str(cumulative-old_cumulative-current),'residual_reason':'Unknown，不修改源披露；舍入仅为可能解释，未确认'})
  gi,gd=nums(raw['R2025-12']['value']);di,dd=nums(raw['R2025-13']['value']);purchase,transfer,charge=nums(raw['R2025-14']['value']);imp0,imp1=nums(raw['R2025-15']['value']);co,ca,ct,ce=nums(raw['R2025-16']['value'])
  assert '空白' in raw['R2025-16']['value']
  calculated_net_delta=(gi-gd)-(di-dd)-(imp1-imp0);reported_net_delta=Decimal(finance[0]['delta_yuan']);fa_residual=reported_net_delta-calculated_net_delta
  assert fa_residual==0,'Fixed asset bridge mismatch: stop and recheck source'
  cip_trial_residual=co+ca-ct-ce
  assert cip_trial_residual==0,'Important CIP listed-amount mismatch: stop; blank remains blank'
  asset_bridge={'gross_increase_yuan':str(gi),'gross_decrease_yuan':str(gd),'depreciation_increase_yuan':str(di),'depreciation_decrease_yuan':str(dd),'impairment_opening_yuan':str(imp0),'impairment_closing_yuan':str(imp1),'calculated_net_delta_yuan':str(calculated_net_delta),'reported_net_delta_yuan':str(reported_net_delta),'independent_residual_yuan':str(fa_residual),'gross_purchase_yuan':str(purchase),'gross_cip_transfer_yuan':str(transfer),'depreciation_charge_yuan':str(charge),'gross_increase_other_components_residual_yuan':str(gi-purchase-transfer),'depreciation_increase_other_components_residual_yuan':str(di-charge),'state':'AgentCalculated'}
  important_cip={'opening_yuan':str(co),'additions_yuan':str(ca),'transfers_yuan':str(ct),'closing_yuan':str(ce),'other_decrease_raw':None,'other_decrease_arithmetic_assumption_yuan':None,'assumption_is_disclosed_zero':False,'human_arithmetic_confirmation':False,'listed_amounts_residual_yuan':str(cip_trial_residual),'all_fixed_asset_transfer_minus_important_project_transfer_yuan':str(transfer-ct),'scope':'仅重要在建项目；不同表范围差额尚未逐项归因','state':'AgentCalculated（仅已列金额勾稽，空白不代填）'}
  evidence=[{'domain':'facts','id':id,'binding':raw[id]['binding'],'pdf_path':raw[id]['pdf_path'],'pdf_sha256':raw[id]['pdf_sha256']} for id in ids]+[{'domain':'lec03_agent_facts','id':id,'validated_snapshot_sha256':digest(groups[id]),'pdf_path':groups[id]['pdf_path'],'pdf_sha256':groups[id]['pdf_sha256'],'human_confirmation':False} for id in groupids]
  lines=['<!-- generated-by: calculate_capacity_bridge.py; manual edits protected -->','# 生产库存合同G5：产能、投产与资本投入连接分析','','2026-10-24。B05七项及B06八项原披露由leo真实聊天核验（review55—69）；计算为AgentCalculated，解释待人工审阅，不代表G5已全部验收。2025仅后验窗口，不回填2024历史信息集。','','## 1. 设计能力与实际生产','','| 产品 | 2024设计（吨） | 2025设计（吨） | 设计增加（吨） | 2024实际基酒（吨） | 2025实际基酒（吨） | 实际基酒增幅 |','| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
  for x in capacity:lines.append('| '+' | '.join([x['product']]+[fmt(Decimal(x[key])) for key in ['design_2024_tonnes','design_2025_tonnes','design_delta_tonnes','actual_base_production_2024_tonnes','actual_base_production_2025_tonnes']]+[fmt(Decimal(x['production_growth_percent']))+'%'])+' |')
  lines+=['','来源：2024年报14页、2025年报15页；实际基酒产量复用当前有效L03-A2024-B与R2025-01。设计产能按工艺、厂房规格及窖池数量计算；报告的实际产能按实际基酒产量计算，因此两者具有不同计量基础。实际/设计比只作算术观察，不能直接称利用率或据此认定超负荷。为何可高于设计的具体工艺/班次/改造贡献，现有原数不能分解。','','## 2. 新增、投产与预计释放分开','','| 披露年度 | 产品 | 新增设计产能（吨） | 披露投产月份 | 公司预计释放年 | 是否已核实际释放 |','| --- | --- | ---: | --- | --- | --- |']
  for x in release:
   for product in ['茅台酒','其他系列酒']:lines.append(f"| {x['disclosure_year']} | {product} | {x['new_capacity_tonnes'][product]} | {x['commission_month'][product]} | {x['company_expected_release_year']} | 否，Unknown |")
  lines+=['','公司当年披露的将来释放是Forecast内容的披露Fact，不是实现Fact。2024新增项目与2025新增项目按各自批次分开；2025年总产量增加不能全部归给2024新增产能。2026超出本合同FY2025冻结点，不能当作已观察结果。','','## 3. 合并资产存量与年度现金流量','','| 指标 | 2024原数（元） | 2025原数（元） | 机械差额（元） | 机械增幅 | 经济对象 |','| --- | ---: | ---: | ---: | ---: | --- |']
  for x in finance:lines.append('| '+' | '.join([x['name'],fmt(Decimal(x['previous_2024_yuan'])),fmt(Decimal(x['current_2025_yuan'])),fmt(Decimal(x['delta_yuan'])),fmt(Decimal(x['growth_percent']))+'%',x['period_type']])+' |')
  lines+=['','来源：2025年报56页合并资产负债表头及57页续表、64页合并现金流量表头及65页续表；2024购建现金复用L03-A2024-C（2024年报67页）。上述为来源绑定后的机械变化，未新增人工可比性或变化Fact。固定资产/在建工程为期末账面存量，购建现金为年度流量，不能以余额差代替投入或将三者相加。合并购建现金也不是纯酒类、纯扩张Capex或完整FCFF。','','## 4. 从项目到销售／现金的时间链','','项目计划/承诺 → 建设与支付（可能跨年） → 在建及转固 → 实际基酒生产 → 贮存/勾兑 → 包装投放 → 销售与收款。各箭头需要项目、产品和期间映射，不能只用公司合计强配。支付与工程确认也可能跨期。','','2024酒类三项目当期投资已获有效年度组核准（万元，非合并购建现金）：','','| 项目 | 计划投资（万元） | 当期投资（万元） | 累积投资（万元） |','| --- | ---: | ---: | ---: |']
  for x in projects:lines.append('| '+' | '.join([x['name'],x['planned_wanyuan'],x['current_investment_wanyuan'],x['accumulated_wanyuan']])+' |')
  lines+=['','这里只复用2024年报14页L03-A2024-P，不能将三项目当期投资合计认作全部酒类Capex，不能与集团购建现金的差额命名非酒类投资。B06已补2025对应项目当期/累积投资与固定资产、重要在建工程合计变动；逐项目现金/转固/折旧明细映射仍不足。','','## 5. 当前判断与停止边界','','已有证据支持“新增产能投产与生产释放存在时差，生产到销售还经过贮存和勾兑”的研究方向。基酒最少五年工艺披露不能机械变成每笔投资固定五年回收；混合勾兑也阻止单批追踪。年度合计增长不能识别某项目贡献或证明高增量资本回报。','','可核数字连接已补齐固定资产净变动和重要在建工程条件勾稽。仍未知：逐项目转固/折旧与付款调节、维护/扩张拆分、实际释放贡献及同批产品销售/现金映射。缺少上述证据时，完整桥、资本回报、库存经济价值继续Unknown；不补估值或投资建议。','','[B05真实回执](../evidence/20261024-b05-chat-confirmation.json)；[精确计算、公式及输入绑定](../work/lag-20261022/capacity-bridge.json)。复算：`D:/Anaconda/python.exe scripts/calculate_capacity_bridge.py`。','']
  lines+=['## 6. B06固定资产与重要在建工程复算','','2025年报97页原值增加减减少，再减累计折旧净增加及减值准备净增加：','',f"({fmt(gi)} − {fmt(gd)}) − ({fmt(di)} − {fmt(dd)}) − ({fmt(imp1)} − {fmt(imp0)}) = {fmt(calculated_net_delta)}元。",'',f"与B05已核固定资产账面价值增加{fmt(reported_net_delta)}元独立核对，差额{fmt(fa_residual)}元。购置{fmt(purchase)}元、在建转入{fmt(transfer)}元已含在原值增加内，不再重复加总；折旧计提{fmt(charge)}元已含在累计折旧增加内。原值增加其余分项差额{fmt(gi-purchase-transfer)}元，累计折旧增加其余分项差额{fmt(di-charge)}元，仅作差额保留，不擅自命名。",'',f"2025年报98页重要在建工程已列金额：{fmt(co)} + {fmt(ca)} − {fmt(ct)} = {fmt(ce)}元，已列四项差额为{fmt(cip_trial_residual)}元。其他减少原表空白并保持空白，不代填0，也不将已列金额勾稽等同全部项目明细已获证。",'',f"97页全部固定资产转固与98页重要项目转固列示相差{fmt(transfer-ct)}元。重要项目表覆盖范围较窄，不能强行相等；差额具体项目来源未核，不命名付款差异或认定漏记。",'','## 7. B06项目投资与累计数检查','','| 项目 | 2025当期投资（万元） | 2025累积投资（万元） | 2024累积＋2025当期与2025累积的差额（万元） |','| --- | ---: | ---: | ---: |']
  for x in projects25:lines.append('| '+' | '.join([x['name'],x['current_investment_wanyuan'],x['accumulated_investment_wanyuan'],x['accumulated_rollforward_residual_wanyuan']])+' |')
  lines+=['','差额定义为2025累积−2024累积−2025当期，两个年度按原披露保留。第二项目差额−0.01万元（−100元）；可能与万元保留两位小数等因素有关，但未取得调节说明，不直接认定舍入或错误，不强改任何原数。第15页项目投资不直接等同第98页会计在建增加或现金流量表付款。','','[B06真实回执](../evidence/20261024-b06-chat-confirmation.json)。可核数字连接稿已形成，G5的完整项目归因仍保留Unknown，下一步为G6有范围的判断审阅；不以更多无从取得的资料无限延长核验。','']
  text='\n'.join(lines);out=p/'outputs/student-capacity-capital-bridge.md';dest=p/'work/lag-20261022/capacity-bridge.json'
  if out.exists():assert dest.exists() and sha(out)==json.loads(dest.read_text(encoding='utf-8'))['generated_output_sha256'],'Human edits detected; stop'
  result={'date':'2026-10-24','state':'AgentCalculated','human_arithmetic_confirmation':False,'code_sha256':sha(Path(__file__)),'capacity':capacity,'release_disclosures':release,'finance':finance,'projects_2024':projects,'projects_2025':projects25,'fixed_asset_bridge':asset_bridge,'important_cip_bridge':important_cip,'input_evidence':evidence,'formulas':{'delta':'2025−2024','growth_percent':'(2025/2024−1)*100','actual_to_design_percent':'actual_base_production/design*100, not identified utilization','fixed_asset_net_delta':'gross increase−gross decrease−depreciation increase+depreciation decrease−(impairment closing−opening)','important_cip_listed_amounts':'opening+additions−transfers−closing; other decrease raw blank remains None, no imputed zero','project_accumulation_residual':'2025 accumulated−2024 accumulated−2025 current, in 万元'},'precision':48,'generated_output_sha256':hashlib.sha256(text.encode()).hexdigest(),'complete_project_cash_production_sales_bridge':'Unknown'}
  out.write_text(text,encoding='utf-8',newline='\n');dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 assert sha(p/'evidence/review-state.json')==state_before
 print(json.dumps({'capacity_rows':len(capacity),'finance_rows':len(finance),'G5':'可核数字连接稿完成，完整项目归因Unknown','new_approvals':0},ensure_ascii=False))
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
