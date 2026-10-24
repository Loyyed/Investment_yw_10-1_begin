"""Consolidated cash observations with explicit unreviewed years and entity stop gates."""
from pathlib import Path
from decimal import Decimal,localcontext,ROUND_HALF_UP
import sys,json,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def nums(t):return [Decimal(x.replace(',','')) for x in re.findall(r'(?<!\d)-?\d[\d,]*\.\d+',t)]
def fmt(x,step='.01'):return str(x.quantize(Decimal(step),rounding=ROUND_HALF_UP))
def main(p=ROOT):
 sys.path.insert(0,str(p/'scripts'));from review_store import ReviewStore
 s=ReviewStore(p);raw={x['id']:x for x in s.facts()};groups={x['id']:x for x in s.lec03_agent_facts()};state_sha=sha(p/'evidence/review-state.json');used_raw=set();used_groups=set()
 fields=['net_profit_yuan','cfo_yuan','capex_cash_yuan','operating_revenue_yuan','inventory_yuan'];panel={year:{'year':year,**{key:None for key in fields},'input_roles':{},'entity_cfo_yuan':None,'fcff_yuan':None,'nopat_proxy_yuan':None,'selected_ncwc_yuan':None,'selected_invested_capital_yuan':None,'selective_reinvestment_proxy_yuan':None,'entity_roic':None} for year in range(2001,2026)}
 def assign(year,field,value,id):panel[year][field]=Decimal(value);panel[year]['input_roles'][field]=id
 # Revenue facts were independently confirmed in the channel work, no repeat human check.
 manifest=json.loads((p/'work/review-batches/20261024-B08.json').read_text(encoding='utf-8'));payload=dict(manifest);fp=payload.pop('display_payload_sha256');assert fp==digest(payload)
 for item in manifest['items']:
  if item['kind'] not in ['company-income-sales-expense','company-income-only']:continue
  id=item['id'];assert id in raw and raw[id]['binding']==item['binding'];assign(item['year'],'operating_revenue_yuan',nums(raw[id]['value'])[0],id);used_raw.add(id)
 assign(2024,'operating_revenue_yuan',nums(raw['C01']['value'])[0],'C01');used_raw.add('C01');assign(2025,'capex_cash_yuan',nums(raw['R2025-08']['value'])[0],'R2025-08');used_raw.add('R2025-08')
 financial=[]
 with localcontext() as ctx:
  ctx.prec=48
  for year in range(2020,2025):
   id=f'L03-A{year}-C';assert id in groups;data=groups[id]['data'];rows=data['cash_rows'];assign(year,'net_profit_yuan',data['consolidated_net_profit_yuan'],id);assign(year,'cfo_yuan',rows['经营活动产生的现金流量净额']['current_yuan'],id);assign(year,'capex_cash_yuan',rows['购建固定资产、无形资产和其他长期资产支付的现金']['current_yuan'],id);used_groups.add(id)
   net=Decimal(0);details=[]
   for label,sign in [('客户存款和同业存放款项净增加额',1),('收取利息、手续费及佣金的现金',1),('客户贷款及垫款净增加额',-1),('存放中央银行和同业款项净增加额',-1),('拆出资金净增加额',-1),('支付利息、手续费及佣金的现金',-1)]:
    row=rows[label];amount=Decimal(row['current_yuan']);net+=sign*amount;details.append({'label':label,'sign':sign,'amount_yuan':str(amount),'raw_current_blank':row['current_blank'],'blank_policy':row['blank_policy']})
   assert net==Decimal(data['cash_analysis']['explicit_financial_items_net_yuan']);financial.append({'year':year,'listed_financial_rows_net_yuan':str(net),'CFO_minus_listed_rows_yuan':str(panel[year]['cfo_yuan']-net),'details':details,'input_id':id,'full_finance_company_contribution':None,'boundary':'已列金融现金行的带符号算术，空白处理沿用已核组明示约定；未含全部税费薪酬/内部抵销，不是完整金融净贡献或实体CFO'})
  b09_path=p/'work/review-batches/20261024-B09.json';explanations=[]
  if b09_path.exists():
   batch=json.loads(b09_path.read_text(encoding='utf-8'));check=dict(batch);fp=check.pop('display_payload_sha256');assert fp==digest(check)
   for item in batch['items']:
    id=item['id']
    if id not in raw:continue
    assert raw[id]['binding']==item['binding'];note=json.loads(raw[id]['note']);assert note['display_payload_sha256']==fp;used_raw.add(id);values=nums(raw[id]['value']);year=item['year']
    if item['kind']=='cash-basic-year':
     assert len(values)==4
     for key,value in zip(['net_profit_yuan','cfo_yuan','capex_cash_yuan','inventory_yuan'],values):assign(year,key,value,id)
    elif item['kind']=='cash-current-year':
     assert len(values)==2
     for key,value in zip(['net_profit_yuan','cfo_yuan'],values):assign(year,key,value,id)
    elif item['kind']=='inventory-pair':
     assert len(values)==2
     for period,value in zip(item['period_years'],values):assign(period,'inventory_yuan',value,id+f'（{period}期末列）')
    elif item['kind']=='cash-explanation':explanations.append({'id':id,'text':raw[id]['value'],'boundary':'公司披露叙事Fact，不是完整因果或金融净贡献证明'})
  result_rows=[];cash_years=[]
  for year,row in panel.items():
   profit,cfo,capex,revenue,inventory=[row[x] for x in fields];complete=profit is not None and cfo is not None and capex is not None
   conversion=cfo/profit if profit not in [None,0] and cfo is not None else None;remainder=cfo-capex if cfo is not None and capex is not None else None;capex_intensity=capex/revenue if revenue not in [None,0] and capex is not None else None;inventory_intensity=inventory/revenue if revenue not in [None,0] and inventory is not None else None
   if complete:cash_years.append(year)
   r={key:(str(value) if isinstance(value,Decimal) else value) for key,value in row.items()};r.update(cash_conversion=None if conversion is None else str(conversion),arithmetic_CFO_minus_capex_yuan=None if remainder is None else str(remainder),capex_to_operating_revenue=None if capex_intensity is None else str(capex_intensity),inventory_to_operating_revenue=None if inventory_intensity is None else str(inventory_intensity),missing_current_reviewed_fields=[key for key in fields if row[key] is None],cash_base_state='AgentCalculated（合并范围）' if complete else 'Unknown：本项目当前有效输入未齐，不表示没有原件',profit_definition='旧准则原年报净利润口径待核' if year<2007 else '新准则合并净利润，含少数股东；不能换归母',entity_stop_reason='金融完整贡献/内部抵销及同范围经营投入未裁定' if year>=2013 else '选择性NCWC/NOPAT及资本原数和范围裁定未齐');result_rows.append(r)
  evidence=[{'domain':'facts','id':id,'binding':raw[id]['binding'],'pdf_path':raw[id]['pdf_path'],'pdf_sha256':raw[id]['pdf_sha256']} for id in sorted(used_raw)]+[{'domain':'lec03_agent_facts','id':id,'validated_snapshot_sha256':digest(groups[id]),'pdf_path':groups[id]['pdf_path'],'pdf_sha256':groups[id]['pdf_sha256'],'human_confirmation':False} for id in sorted(used_groups)]
  lines=['<!-- generated-by: calculate_cash_known.py; saved hash protects manual edits -->','# 贵州茅台现金与资本回报验证：阶段性工作稿','','2026-10-24。当前只复用有效原数/年度组，未知候选不入计算。所有新运算AgentCalculated，N06/N07尚未形成最终采纳意见；原数、解释与签署分开。FY2025仅后验。','','## 一页计算表：25年面板与显式缺口','','合并CFO÷同年合并净利润；算术剩余＝CFO−购建固定资产/无形资产/其他长期资产现金。现金为年度流量，存货为账面期末金额。强度分母为合并“其中：营业收入”，不换营业总收入或主营酒类收入。未核不是0。','','| 年度 | 合并现金转换（倍） | 算术剩余（亿元） | 购建现金/营业收入 | 账面存货/营业收入 |','| --- | ---: | ---: | ---: | ---: |']
  for x in result_rows:
   values=[str(x['year']), '未核' if x['cash_conversion'] is None else fmt(Decimal(x['cash_conversion']),'.0001'),'未核' if x['arithmetic_CFO_minus_capex_yuan'] is None else fmt(Decimal(x['arithmetic_CFO_minus_capex_yuan'])/Decimal(10)**8),'未核' if x['capex_to_operating_revenue'] is None else fmt(Decimal(x['capex_to_operating_revenue'])*100)+'%','未核' if x['inventory_to_operating_revenue'] is None else fmt(Decimal(x['inventory_to_operating_revenue'])*100)+'%'];lines.append('| '+' | '.join(values)+' |')
  lines+=['',f'当前完整合并现金基础有效年度n={len(cash_years)}：'+('、'.join(map(str,cash_years)) or '无')+'。原数、公式、来源ID和各年缺口逐行见JSON；统计只覆盖实际有效年度，不把课堂参考结果或HV标签移植成本项目事实。','','## 一页范围与停止账本','','| 层级 | 当前可做 | 停止边界 |','| --- | --- | --- |','| A 合并事实 | 当前有效净利润、CFO、购建现金及原表定义 | 未核年度不插值，不把归母换合并净利润 |','| B 合并会计代理 | 现金转换、CFO减购建现金、具备输入时的两项强度 | 算术剩余不命名FCFF/FCFE，购建现金不当全部再投资 |','| C 已列金融行 | 2020—2024带符号净额及CFO减该净额 | 税费薪酬/内部抵销不足，剩余不命名实体CFO |','| D NOPAT/选择性NCWC/资本 | 待2007—2012前财务公司窗口原数与逐项范围裁定 | 其他项目不整体纳入；当前没有完整代理结果 |','| E 增量回报/分配 | 待同范围多年窗口、合理成熟期和分配口径 | 小/负分母、跨断点、未成熟时停止，不以静态ROIC证明持续高回报 |','','合同提出的三个研究关口：FY2007新旧准则、FY2013财务公司范围、FY2020收入准则与预收/合同负债。这些规则单列用于防止混算，历史说明原文与本项目核准仍需逐项绑定，不以课件摘要替代原件。','','## N06阶段性判断','','现阶段能观察合并现金转换及年度波动，并识别已列金融行的影响范围。现有资料不足以将其命名为稳定的核心酒类现金转换。反证条件：若同范围实体CFO在合理观察窗持续弱于利润，应削弱现金兑现命题；目前尚未取得完整实体CFO，不把该反证当已发生。状态：Interpretation工作候选，实体现金转换Unknown。','','## N07阶段性判断','','尚未建立2007—2012选择性NCWC、同范围NOPAT、平均资本及多年累计增量窗口，暂不判断新增资本回报。反证条件：成熟后新增库存/长期资产不能形成可核NOPAT与实体现金，应削弱资本有效性解释。当前静态/增量回报及可自由分配现金均Unknown，不用高毛利或CFO剩余代证。','','## 错误公式核辨与纠正','','材料中的教学错误示范为：CFO−购建现金−ΔNCWC。CFO本已包含经营性应收、应付及存货等现金调整，再扣同一营运资本变化会重复扣减。本项目采用透明的CFO−购建现金观察；从NOPAT另建FCFF须先核D&A、经营Capex及NCWC同范围。此处是对教学错误公式的实际识别，不伪造本人曾使用错误公式的历史。固定资产某项计提不自动等于完整D&A。','','## 下一步','','B09补2016—2019/2025现金与2016—2025账面存货；2020—2024有效现金组、公司收入和2025购建现金不重复核。随后继续2007—2012代理所需逐项输入/范围、至少一个多年增量窗口及三断点；材料不能支持的实体指标按规则停止。','','[B09当前核验清单](../work/review-batches/20261024-B09.md)；[精确面板、输入绑定和金融行明细](../work/cash-20261024/calculations.json)。复算：`D:/Anaconda/python.exe scripts/calculate_cash_known.py`。','']
  text='\n'.join(lines);out=p/'outputs/student-cash-capital-check.md';dest=p/'work/cash-20261024/calculations.json'
  if out.exists():assert dest.exists() and sha(out)==json.loads(dest.read_text(encoding='utf-8'))['generated_output_sha256'],'Manual output edits; stop'
  result={'date':'2026-10-24','state':'AgentCalculated','human_arithmetic_confirmation':False,'code_sha256':sha(Path(__file__)),'panel':result_rows,'complete_cash_years':cash_years,'complete_cash_n':len(cash_years),'listed_financial_rows':financial,'company_disclosure_explanations':explanations,'input_evidence':evidence,'research_breakpoint_rules':[{'year':year,'reason':reason,'status':'合同研究规则，历史原文/本项目核准待补'} for year,reason in [(2007,'新旧会计准则'),(2013,'财务公司进入合并范围'),(2020,'预收/合同负债及新收入准则')]],'selective_ncwc_rule':'inventory+notes/accounts receivable+receivable financing+prepayments−accounts payable−advances/contract liabilities; only current source-confirmed items, no whole other items','pre_finance_proxy_window':[2007,2012],'minimum_multiyear_incremental_window_status':'Unknown：输入与范围未齐','formulas':{'cash_conversion':'consolidated CFO/consolidated net profit','arithmetic_cash_residual':'consolidated CFO−cash paid for acquisition/construction of fixed/intangible/other long-term assets','capex_intensity':'purchased long-term asset cash/consolidated operating revenue','inventory_intensity':'book inventory/consolidated operating revenue'},'precision':48,'generated_output_sha256':hashlib.sha256(text.encode()).hexdigest()};out.write_text(text,encoding='utf-8',newline='\n');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 assert state_sha==sha(p/'evidence/review-state.json');print(json.dumps({'panel_years':25,'complete_cash_n':len(cash_years),'cash_years':cash_years,'entity_CFO':'Unknown','NOPAT_ROIC_proxy':'Unknown','new_approvals':0},ensure_ascii=False))
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
