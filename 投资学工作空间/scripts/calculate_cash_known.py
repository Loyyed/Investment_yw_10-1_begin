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
  b10=json.loads((p/'work/review-batches/20261024-B10.json').read_text(encoding='utf-8'));bp=dict(b10);b10fp=bp.pop('display_payload_sha256');assert b10fp==digest(bp)
  b10valid=[]
  for item in b10['items']:
   id=item['id']
   if id not in raw:continue
   assert raw[id]['binding']==item['binding'] and raw[id]['value']==item['value'];assert json.loads(raw[id]['note'])['display_payload_sha256']==b10fp
   b10valid.append(item);used_raw.add(id)
  bridge_items=[x for x in b10valid if x['kind']=='cash-reconciliation'];bridge=None
  if len(bridge_items)==5 and panel[2025]['net_profit_yuan'] is not None and panel[2025]['cfo_yuan'] is not None:
   details=[{'label':key,'raw_amount_yuan':value,'input_id':item['id'],'arithmetic_policy':'原文空白不产生加项；raw仍null，非披露0' if value is None else '原披露带符号加项，不另翻转符号'} for item in bridge_items for key,value in item['fields'].items()]
   adjustment=sum((Decimal(x['raw_amount_yuan']) for x in details if x['raw_amount_yuan'] is not None),Decimal(0));wc_labels=['存货的减少','经营性应收项目的减少','经营性应付项目的增加'];wc=sum((Decimal(x['raw_amount_yuan']) for x in details if x['label'] in wc_labels),Decimal(0));computed=panel[2025]['net_profit_yuan']+adjustment;residual=computed-panel[2025]['cfo_yuan']
   da_labels=['固定资产折旧、油气资产折耗、生产性生物资产折旧','使用权资产摊销','无形资产摊销','长期待摊费用摊销'];da=sum((Decimal(x['raw_amount_yuan']) for x in details if x['label'] in da_labels),Decimal(0))
   bridge={'year':2025,'net_profit_yuan':str(panel[2025]['net_profit_yuan']),'reported_cfo_yuan':str(panel[2025]['cfo_yuan']),'listed_adjustments_yuan':str(adjustment),'listed_working_capital_cash_adjustments_yuan':str(wc),'other_listed_adjustments_yuan':str(adjustment-wc),'reconstructed_cfo_yuan':str(computed),'residual_yuan':str(residual),'balanced':residual==0,'listed_depreciation_amortization_yuan':str(da),'details':details,'input_ids':[x['id'] for x in bridge_items]+['R2025-21'],'state':'AgentCalculated；原数已核，算术未另经本人确认','boundary':'合并调节表三类营运现金调整已进入CFO；不能再扣同一ΔNCWC。已列折旧摊销加总不自动成为同范围经营D&A；经营应收/应付不等于实体单科目或完整金融净贡献。'}
  breakpoint_facts=[{'year':x['year'],'id':x['id'],'kind':x['kind'],'text':x['value'],'binding':x['binding'],'status':'当前原披露Fact；可比性裁决另列'} for x in b10valid if x['kind']!='cash-reconciliation']
  from cash_proxy import calculate_proxy
  proxy=calculate_proxy(p,raw,groups);used_raw.update(proxy['used_ids'])
  from cash_2012_sensitivity import calculate_2012
  sensitivity=calculate_2012(p,raw,proxy);used_raw.update(sensitivity['used_ids'])
  if sensitivity['state']=='AgentCalculated':
   f2012=sensitivity['raw_fields_yuan']
   for key,label in [('net_profit_yuan','合并净利润'),('cfo_yuan','合并CFO'),('capex_cash_yuan','购建长期资产支付现金'),('operating_revenue_yuan','合并营业收入')]:assign(2012,key,f2012[label],'R2012-02')
   assign(2012,'inventory_yuan',f2012['存货'],'R2012-03')
  for observation in proxy['panel']:
   year=observation['year'];assign(year,'inventory_yuan',observation['raw_fields_yuan']['存货'],next(id for id in observation['input_ids'] if '存货' in raw[id]['value']))
  from cash_intermediate import calculate_intermediate
  intermediate=calculate_intermediate(p,raw);used_raw.update(intermediate['used_ids'])
  for item in intermediate['panel']:
   year=item['year'];values=item['raw_fields_yuan'];source=item['input_ids'][0]
   for key,label in [('net_profit_yuan','合并净利润'),('cfo_yuan','合并CFO'),('capex_cash_yuan','购建长期资产支付现金'),('operating_revenue_yuan','合并营业收入')]:assign(year,key,values[label],source)
   if year==2010 and 'reused_inventory_yuan' in item:assign(year,'inventory_yuan',item['reused_inventory_yuan'],'R2011-04（2011报告年初列）')
  from cash_annual_path import annual_path
  capital_path=annual_path(p,raw,proxy,intermediate);used_raw.update(capital_path['used_ids'])
  for item in capital_path['cash_assignments']:
   for key,label in [('net_profit_yuan','合并净利润'),('cfo_yuan','合并CFO'),('capex_cash_yuan','购建长期资产支付现金'),('operating_revenue_yuan','合并营业收入')]:assign(item['year'],key,item['fields'][label],item['id'])
  for row in capital_path['panel']:
   if row['year'] in [2008,2009]:assign(row['year'],'inventory_yuan',row['raw_capital_fields_yuan']['存货'],next(id for id in row['capital_input_ids'] if '存货' in raw[id]['value']))
  result_rows=[];cash_years=[]
  for year,row in panel.items():
   profit,cfo,capex,revenue,inventory=[row[x] for x in fields];complete=profit is not None and cfo is not None and capex is not None
   conversion=cfo/profit if profit not in [None,0] and cfo is not None else None;remainder=cfo-capex if cfo is not None and capex is not None else None;capex_intensity=capex/revenue if revenue not in [None,0] and capex is not None else None;inventory_intensity=inventory/revenue if revenue not in [None,0] and inventory is not None else None
   if complete:cash_years.append(year)
   r={key:(str(value) if isinstance(value,Decimal) else value) for key,value in row.items()};r.update(cash_conversion=None if conversion is None else str(conversion),arithmetic_CFO_minus_capex_yuan=None if remainder is None else str(remainder),capex_to_operating_revenue=None if capex_intensity is None else str(capex_intensity),inventory_to_operating_revenue=None if inventory_intensity is None else str(inventory_intensity),missing_current_reviewed_fields=[key for key in fields if row[key] is None],cash_base_state='AgentCalculated（合并范围）' if complete else 'Unknown：本项目当前有效输入未齐，不表示没有原件',profit_definition='旧准则原年报净利润口径待核' if year<2007 else '新准则合并净利润，含少数股东；不能换归母',entity_stop_reason='金融完整贡献/内部抵销及同范围经营投入未裁定' if year>=2012 else '选择性NCWC/NOPAT及资本原数和范围裁定未齐');result_rows.append(r)
  evidence=[{'domain':'facts','id':id,'binding':raw[id]['binding'],'pdf_path':raw[id]['pdf_path'],'pdf_sha256':raw[id]['pdf_sha256']} for id in sorted(used_raw)]+[{'domain':'lec03_agent_facts','id':id,'validated_snapshot_sha256':digest(groups[id]),'pdf_path':groups[id]['pdf_path'],'pdf_sha256':groups[id]['pdf_sha256'],'human_confirmation':False} for id in sorted(used_groups)]
  complete_rows=[x for x in result_rows if x['year'] in cash_years]
  sum_cfo=sum((Decimal(x['cfo_yuan']) for x in complete_rows),Decimal(0));sum_profit=sum((Decimal(x['net_profit_yuan']) for x in complete_rows),Decimal(0))
  vals=[Decimal(x['cash_conversion']) for x in complete_rows]
  diagnostics={'sample_years':cash_years,'n':len(cash_years),'sum_consolidated_cfo_yuan':str(sum_cfo),'sum_consolidated_net_profit_yuan':str(sum_profit),'ratio_of_sums':None if sum_profit==0 else str(sum_cfo/sum_profit),'minimum_annual_ratio':None if not vals else str(min(vals)),'maximum_annual_ratio':None if not vals else str(max(vals)),'annual_ratio_below_one_years':[x['year'] for x in complete_rows if Decimal(x['cash_conversion'])<1],'boundary':'仅实际有效年份的合并原表口径加总及比率，不是稳定实体现金或因果证明，FY2025只用于后验'}
  diagnostics['sample_is_contiguous']=cash_years==list(range(min(cash_years),max(cash_years)+1)) if cash_years else False
  diagnostics['period_note']='实际有效年份逐项列明，分段/稀疏样本不称连续多年；缺口不插值'
  ten=[x for x in result_rows if 2016<=x['year']<=2025 and x['cfo_yuan'] is not None and x['net_profit_yuan'] is not None]
  ten_cfo=sum((Decimal(x['cfo_yuan']) for x in ten),Decimal(0));ten_np=sum((Decimal(x['net_profit_yuan']) for x in ten),Decimal(0))
  continuous_ten={'years':[x['year'] for x in ten],'n':len(ten),'sum_consolidated_cfo_yuan':str(ten_cfo),'sum_consolidated_net_profit_yuan':str(ten_np),'ratio_of_sums':None if ten_np==0 else str(ten_cfo/ten_np),'boundary':'2016—2025连续十年单独保留；不与稀疏年度合计混称连续期间，仍是合并范围'}
  primary_cash=[x for x in result_rows if 2007<=x['year']<=2011 and x['cfo_yuan'] is not None and x['net_profit_yuan'] is not None]
  primary_cfo=sum((Decimal(x['cfo_yuan']) for x in primary_cash),Decimal(0));primary_np=sum((Decimal(x['net_profit_yuan']) for x in primary_cash),Decimal(0));primary_capex=sum((Decimal(x['capex_cash_yuan']) for x in primary_cash),Decimal(0))
  primary_cash_window={'years':[x['year'] for x in primary_cash],'n':len(primary_cash),'sum_consolidated_cfo_yuan':str(primary_cfo),'sum_consolidated_net_profit_yuan':str(primary_np),'ratio_of_sums':None if primary_np==0 else str(primary_cfo/primary_np),'sum_reported_purchase_cash_yuan':str(primary_capex),'CFO_minus_purchase_cash_sum_yuan':str(primary_cfo-primary_capex),'boundary':'2007—2011五个完整年度的合并原表观察，不是实体经营现金或成熟项目回报；购建现金不等于全部再投资，2012另列'}
  byyear={x['year']:x for x in result_rows}
  if byyear[2025]['cfo_yuan'] is not None and byyear[2024]['cfo_yuan'] is not None:
   changes={}
   for key in ['net_profit_yuan','cfo_yuan','inventory_yuan','arithmetic_CFO_minus_capex_yuan']:
    a,z=Decimal(byyear[2025][key]),Decimal(byyear[2024][key]);changes[key]={'previous':str(z),'current':str(a),'difference_yuan':str(a-z),'change_ratio':None if z==0 else str((a-z)/z)}
   changes['inventory_intensity_change_pp']=str((Decimal(byyear[2025]['inventory_to_operating_revenue'])-Decimal(byyear[2024]['inventory_to_operating_revenue']))*100);diagnostics['FY2024_to_FY2025']=changes
  lines=['<!-- generated-by: calculate_cash_known.py; saved hash protects manual edits -->','# 贵州茅台现金与资本回报验证：阶段性工作稿','','2026-10-25。当前只复用有效原数/年度组，未知候选不入计算。所有新运算AgentCalculated，N06/N07阶段性意见的当前采纳状态另由独立接口校验；原数、解释与签署分开。FY2025仅后验。','','## 一页计算表：25年面板与显式缺口','','合并CFO÷同年合并净利润；算术剩余＝CFO−购建固定资产/无形资产/其他长期资产现金。现金为年度流量，存货为账面期末金额。强度分母为合并“其中：营业收入”，不换营业总收入或主营酒类收入。未核不是0。','','| 年度 | 合并现金转换（倍） | 算术剩余（亿元） | 购建现金/营业收入 | 账面存货/营业收入 | 输入来源ID |','| --- | ---: | ---: | ---: | ---: | --- |']
  for x in result_rows:
   values=[str(x['year']), '未核' if x['cash_conversion'] is None else fmt(Decimal(x['cash_conversion']),'.0001'),'未核' if x['arithmetic_CFO_minus_capex_yuan'] is None else fmt(Decimal(x['arithmetic_CFO_minus_capex_yuan'])/Decimal(10)**8),'未核' if x['capex_to_operating_revenue'] is None else fmt(Decimal(x['capex_to_operating_revenue'])*100)+'%','未核' if x['inventory_to_operating_revenue'] is None else fmt(Decimal(x['inventory_to_operating_revenue'])*100)+'%'];values.append('；'.join(dict.fromkeys(x['input_roles'].values())) or '未核');lines.append('| '+' | '.join(values)+' |')
  lines+=['',f'当前完整合并现金基础有效年度n={len(cash_years)}：'+('、'.join(map(str,cash_years)) or '无')+'。原数、公式、来源ID和各年缺口逐行见JSON；统计只覆盖实际有效年度，不把课堂参考结果或HV标签移植成本项目事实。','','## 一页范围与停止账本','','| 层级 | 当前可做 | 停止边界 |','| --- | --- | --- |','| A 合并事实 | 当前有效净利润、CFO、购建现金及原表定义 | 未核年度不插值，不把归母换合并净利润 |','| B 合并会计代理 | 现金转换、CFO减购建现金、具备输入时的两项强度 | 算术剩余不命名FCFF/FCFE，购建现金不当全部再投资 |','| C 已列金融行 | 2020—2024带符号净额及CFO减该净额 | 税费薪酬/内部抵销不足，剩余不命名实体CFO |','| D NOPAT/选择性NCWC/资本 | 2007/2011两端选定科目算术已做；经营范围待裁定；平均选定资本已算，2012三种合并敏感性已算 | 其他项目不整体纳入；尚非完整经济资本/经营NOPAT |','| E 增量回报/分配 | 待同范围多年窗口、合理成熟期和分配口径 | 小/负分母、跨断点、未成熟时停止，不以静态ROIC证明持续高回报 |','','合同研究关口及本轮细分：FY2007新旧准则、FY2012财务公司已纳入合并、FY2013正式营业、FY2020收入准则与预收/合同负债。这些规则单列用于防止混算，2007/2012/2013/2020说明原文已由B10核准；此前把2013说成首次合并的表述已按原件纠偏，具体重分类金额与逐年可比性仍单列，不以课件摘要替代原件。','','## N06阶段性判断','','现阶段能观察合并现金转换及年度波动，并识别已列金融行的影响范围。现有资料不足以将其命名为稳定的核心酒类现金转换。反证条件：若同范围实体CFO在合理观察窗持续弱于利润，应削弱现金兑现命题；目前尚未取得完整实体CFO，不把该反证当已发生。状态：Interpretation工作候选，实体现金转换Unknown。','','## N07阶段性判断','','B11已支持2007/2011两端选定科目和附条件利润公式的算术诊断；平均选择性资本已按B12年初列计算；利润/资本同范围、逐年再投资及成熟期未齐，正式新增资本回报保持Unknown。2012另列敏感性，不混回纯前财务公司窗口。反证条件：成熟后新增库存/长期资产不能形成可核NOPAT与实体现金，应削弱资本有效性解释。当前静态/增量回报及可自由分配现金均Unknown，不用高毛利或CFO剩余代证。','','## 错误公式核辨与纠正','','材料中的教学错误示范为：CFO−购建现金−ΔNCWC。CFO本已包含经营性应收、应付及存货等现金调整，再扣同一营运资本变化会重复扣减。本项目采用透明的CFO−购建现金观察；从NOPAT另建FCFF须先核D&A、经营Capex及NCWC同范围。此处是对教学错误公式的实际识别，不伪造本人曾使用错误公式的历史。固定资产某项计提不自动等于完整D&A。','','## 下一步','','B09已由leo确认，2016—2025十年现金基础及金额存货入表；旧有效数据不重核。B10已核2025净利润→CFO调节行和2007/2012/2013/2020口径原文。B11两端24原金额已由leo确认；B12年初和利润范围22原金额已确认，平均选定资本及整行移除敏感性已算；P01四项方法已认可，B13用途和利润明细已核，B14已核并完成2012独立合并敏感性；P02已记录本人两项阶段性意见认可，B15六项已核并补入2008—2010利润与现金；B16已补资本/两端现金，B17核2008年初调整及会计政策变更；随后补主窗必要资本/经济范围及多年成熟再投资缺口；合同2007—2012参考窗不改原件，但2012须另列敏感性，不能称纯财务公司前窗口。现金转换/调节与资本代理三类电子表格公式复算已完成，原生Excel未打开；实体指标按规则停止。','','[B09实际确认回执](../evidence/20261024-b09-chat-confirmation.json)；[B10实际确认回执](../evidence/20261024-b10-chat-confirmation.json)；[B11实际确认回执](../evidence/20261024-b11-chat-confirmation.json)；[B12真实回执](../evidence/20261024-b12-chat-confirmation.json)；[P01已认可方法及后续事项](student-cash-p01-approved.md)；[B13真实回执](../evidence/20261025-b13-chat-confirmation.json)；[B14真实确认回执](../evidence/20261025-b14-chat-confirmation.json)；[电子表格复算](cash-20261024/现金与资本代理复算.xlsx)；[精确面板、输入绑定和金融行明细](../work/cash-20261024/calculations.json)。复算：`D:/Anaconda/python.exe scripts/calculate_cash_known.py`。','']
  insert=lines.index('## 一页范围与停止账本')
  summary=['## 有效年度合并现金观察（AgentCalculated，非连续样本）','',f"实际有效年度n={diagnostics['n']}；合并CFO加总÷合并净利润加总＝{fmt(Decimal(diagnostics['ratio_of_sums']),'.0001')}倍；年度最小/最大分别{fmt(Decimal(diagnostics['minimum_annual_ratio']),'.0001')}/{fmt(Decimal(diagnostics['maximum_annual_ratio']),'.0001')}倍，低于1的年份："+'、'.join(map(str,diagnostics['annual_ratio_below_one_years']))+'。这是合并原表口径算术，不据此称实体现金稳定。','']
  if 'FY2024_to_FY2025' in diagnostics:
   change=diagnostics['FY2024_to_FY2025'];summary += [f"2025合并CFO同比{fmt(Decimal(change['cfo_yuan']['change_ratio'])*100)}%，合并净利润同比{fmt(Decimal(change['net_profit_yuan']['change_ratio'])*100)}%；账面存货同比{fmt(Decimal(change['inventory_yuan']['change_ratio'])*100)}%，存货/营业收入增加{fmt(Decimal(change['inventory_intensity_change_pp']))}个百分点。",'', 'B09已核公司将CFO变化主要解释为财务公司吸收成员单位存款减少及不可随时支取同业存款增加；这只证明公司这样披露，不能量化全部原因或推出酒类经营恶化。调节表与断点原文B10已核准；加总为AgentCalculated，逐年同口径裁决另列。','']
  lines[insert:insert]=summary
  insert=lines.index('## N06阶段性判断')
  bridge_lines=['## 2025净利润到CFO的调节勾稽（AgentCalculated）','']
  if bridge is None:bridge_lines += ['Unknown：当前调节原数/净利润/CFO未齐，不复用旧勾稽结果。','']
  else:
   bridge_lines += [f"合并净利润{bridge['net_profit_yuan']}元＋已列调节合计({bridge['listed_adjustments_yuan']})元＝{bridge['reconstructed_cfo_yuan']}元；与已核CFO差额{bridge['residual_yuan']}元。",'',f"其中存货、经营性应收、经营性应付三项现金调整合计{bridge['listed_working_capital_cash_adjustments_yuan']}元；其余已列调整合计{bridge['other_listed_adjustments_yuan']}元。两处原表空白保留null，仅在加总中不产生加项，未改写为披露0。",'',f"四项已列折旧摊销合计{bridge['listed_depreciation_amortization_yuan']}元，不能直接套为完整经营D&A。",'',bridge['boundary'],'','[逐项金额、符号、空白规则与来源ID](../work/cash-20261024/calculations.json)。FY2025仅后验，不回填FY2024。','']
  lines[insert:insert]=bridge_lines
  insert=lines.index('## N07阶段性判断')
  proxy_lines=['## 2007/2011选择性资本与利润公式诊断（AgentCalculated）','','选择性NCWC＝存货＋应收票据＋应收账款＋预付款项−应付账款−预收款项；选定资本余额＝该NCWC＋固定资产＋在建工程＋无形资产。附条件利润公式＝营业利润×（1−所得税费用/利润总额）。这是明示科目的会计算术，P01四项方法已获本人认可；逐项经济分类及真实回报仍待补证，真实经营指标仍Unknown。','','| 年度 | 选定NCWC（元） | 选定期末资本（元） | 报表有效税率 | 附条件利润公式值（元） | 来源ID |','| --- | ---: | ---: | ---: | ---: | --- |']
  for row in proxy['panel']:
   proxy_lines.append('| '+' | '.join([str(row['year']),fmt(Decimal(row['selected_ncwc_arithmetic_yuan'])),fmt(Decimal(row['selected_end_capital_arithmetic_yuan'])),fmt(Decimal(row['book_effective_tax_rate'])*100)+'%',fmt(Decimal(row['nopat_formula_arithmetic_yuan'])),'；'.join(row['input_ids'])])+' |')
  window=proxy['window_diagnostic']
  if window is not None:
   proxy_lines += ['',f"2007→2011经过{window['elapsed_years']}年，选择性资本余额差{window['delta_selected_capital_balance_yuan']}元；附条件利润公式差{window['delta_nopat_formula_yuan']}元。两者相除的纯算术诊断＝{window['arithmetic_delta_profit_over_delta_capital']}倍，未年化；**不命名为成熟增量回报率**。",'', '正式回报停止原因：'+'；'.join(window['stops'])+'。小分母阈值尚未裁定，JSON保留分母相对资本规模供判断，未自定回报通过线。']
  proxy_lines += ['', 'B12年初资本和财务费用/投资收益已核，平均选定资本及整行移除敏感性已算；其他/工程物资归属与经营税率仍未裁定。未纳入的科目不是0，也不自动是非经营。完整NOPAT/资本/ROIC和累计现金再投资保持Unknown。','']
  proxy_lines += ['| 年度 | 平均选定资本（元） | 基准公式/平均资本 | 整行移除公式/平均资本 |','| --- | ---: | ---: | ---: |']
  for row in proxy['panel']:
   if row['average_selected_capital_yuan'] is not None:
    proxy_lines.append('| '+' | '.join([str(row['year']),fmt(Decimal(row['average_selected_capital_yuan'])),fmt(Decimal(row['formula_profit_over_selected_average'])*100)+'%',fmt(Decimal(row['whole_line_formula_over_selected_average'])*100)+'%'])+' |')
  if window is not None and 'formula_change_decomposition' in window:
   d=window['formula_change_decomposition'];proxy_lines += ['',f"利润公式增量拆分：营业利润因子{d['operating_profit_factor_yuan']}元，报表税率因子{d['book_tax_factor_yuan']}元，加总残差{d['residual_yuan']}元。只解释算式，不把税率因子命名税法变化的因果贡献。",'', '整行移除敏感性使用（营业利润＋原财务费用−投资收益）×（1−报表有效税率）。财务费用为净额、可能包含手续费/汇兑，整行移除不等于准确去除存款利息；两种公式均不命名实体ROIC。','']
  lines[insert:insert]=proxy_lines
  detail=proxy['classification_and_profit_details'];classification_lines=['## B13用途分解与2011利润明细（原文已核，分类为Agent判断）','']
  if 'decomposition' not in detail:classification_lines += ['当前B13明细未齐，新增分类与敏感性停止Unknown。','']
  else:
   classification_lines += ['| 年度 | 已识别周转净额（元，不含用途待判） | 长期选定资产及已列建设/设备预付（元） | 预付用途待判余额（元） | 三桶合计与原资本差额（元） |','| --- | ---: | ---: | ---: | ---: |']
   for row in detail['decomposition']:classification_lines.append('| '+' | '.join([str(row['year']),fmt(Decimal(row['selected_working_balance_excluding_unclassified_yuan'])),fmt(Decimal(row['selected_long_assets_plus_listed_capital_prepayments_yuan'])),fmt(Decimal(row['unclassified_remainder_yuan'])),fmt(Decimal(row['classification_residual_yuan']))])+' |')
   classification_lines += ['', '这是一组互斥金额桶的附条件分解，未知桶保留在合计中，不能因暂未分类就缩小回报分母。2011已列征地/工程预付774,532,871.71元，剩余1,086,494,552.32元未列明用途；2007材料预付3,670,891.19元、服务器预付165,000.00元，剩余2,989,733.43元未列明用途。年末用途不外推年初；完整经营NCWC、资本与分类后平均资本仍Unknown。', '', '2007土地性质其他应收账面余额61,806,080.00元为原选择性资本之外的补查项，未直接加回；坏账列空白不当0，净值、重叠与期初对应待查。', '']
   s=detail['disclosed_component_sensitivity_2011'];classification_lines += [f"2011保留已列汇兑/手续费、扣除已列利息/投资收益的条件税后公式值{fmt(Decimal(s['conditional_after_tax_formula_yuan']))}元，除以原平均选择性资本为{fmt(Decimal(s['conditional_formula_over_baseline_average'])*100)}%；比整行移除方案变动{fmt(Decimal(s['difference_from_whole_line_ratio_pp']),'.0000')}个百分点。", '', s['assumptions']+'。这只是另一明示情景，不称实体ROIC。'+s['cross_year_stop'], '', '[B13真实核验回执](../evidence/20261025-b13-chat-confirmation.json)；[精确分类与敏感性](../work/cash-20261024/calculations.json)。旧工作簿仍复算截至B12的基础公式，B13新增分类采用Decimal/Fraction复核，未宣称旧工作簿已含新明细。','']
  insert=lines.index('## N07阶段性判断');lines[insert:insert]=classification_lines
  from cash_conclusion_review import current_cash_conclusion_adoption
  from cash_p02_impact import assess_p02_support
  prospective={'panel':result_rows,'continuous_2016_2025_diagnostics':continuous_ten,'cash_reconciliation_2025':bridge,'selected_capital_proxy_diagnostics':proxy,'fy2012_sensitivity':sensitivity}
  content_adoption=assess_p02_support(p,raw,groups,prospective)
  opinions_path=p/'work/review-batches/20261025-P02-content-review.json'
  if opinions_path.exists():
   opinion_manifest=json.loads(opinions_path.read_text(encoding='utf-8'));opinion_payload=dict(opinion_manifest);opinion_fp=opinion_payload.pop('display_payload_sha256');assert opinion_fp==digest(opinion_payload)
   for opinion in opinion_manifest['opinions']:
    title='## '+opinion['id']+'阶段性判断';i=lines.index(title)+2
    lines[i]=opinion['judgment']+' 计算依据：'+opinion['supported']+' 替代解释：'+opinion['alternative_explanations']+' 反证条件：'+opinion['refutation']+' 停止边界：'+opinion['stop']+' 当前内容状态：'+content_adoption['status']+'。'
   lines += ['','[P02已认可的N06/N07阶段性判断及真实回执](student-cash-conclusion.md)。不重复原数核验；意见采纳不关闭数据缺口或代替正式验收。','']
  sensitivity_lines=['## B14：2012单列合并敏感性（AgentCalculated）','']
  if sensitivity['state']=='AgentCalculated':
   y=sensitivity;pr=next(x for x in result_rows if x['year']==2012)
   sensitivity_lines += [f"2012合并CFO/合并净利润{fmt(Decimal(pr['cash_conversion']),'.0000')}倍；CFO−购建长期资产现金{pr['arithmetic_CFO_minus_capex_yuan']}元；购建现金/营业收入{fmt(Decimal(pr['capex_to_operating_revenue'])*100)}%；账面存货/营业收入{fmt(Decimal(pr['inventory_to_operating_revenue'])*100)}%。",'',f"选择性NCWC{y['selected_ncwc_yuan']}元，期末选定资本{y['selected_end_capital_yuan']}元，平均选定资本{y['average_selected_capital_yuan']}元（复用已核2011期末；2012年初列Agent比较相符）。",'','| 条件利润情景 | 条件税后公式值（元） | 公式/平均选定资本 |','| --- | ---: | ---: |']
   for key,label in [('baseline','营业利润基础'),('whole_finance_line_removed','整行财务费用及投资移除'),('listed_interest_and_investment_removed','仅移除已列利息及投资、保留手续费')]:
    case=y['scenarios'][key];sensitivity_lines.append('| '+label+' | '+fmt(Decimal(case['conditional_after_tax_formula_yuan']))+' | '+fmt(Decimal(case['formula_over_selected_average'])*100)+'% |')
   sensitivity_lines += ['',f"已列非空财务费用明细与净额勾稽差{y['financial_components_residual_yuan']}元。{y['blank_policy']}。明细情景比整行情景差{fmt(Decimal(y['detail_minus_whole_after_tax_yuan']))}元、{fmt(Decimal(y['detail_minus_whole_ratio_pp']),'.0000')}个百分点。",'',y['boundary'],'','2012已含财务公司；不把三种公式称实体ROIC。2011→2012变化跨合并断点，仅列账面变化，不认定成熟增量回报。2007—2011两端旧结果保持。2012单列合并敏感性；当前完整现金样本的实际年份与数量见上表，2016—2025十年独立统计保留，不把稀疏样本称连续多年。','']
  else:sensitivity_lines += ['Unknown：当前B14绑定未齐，不采用旧情景。','']
  insert=lines.index('## N07阶段性判断');lines[insert:insert]=sensitivity_lines
  intermediate_lines=['## B15：2008—2010新增观察（AgentCalculated）','','| 年度 | 合并CFO/净利润 | CFO−购建现金（元） | 报表有效税率 | 基准利润公式（元） | 整行敏感性公式（元） |','| --- | ---: | ---: | ---: | ---: | ---: |']
  for item in intermediate['panel']:
   row=next(x for x in result_rows if x['year']==item['year'])
   intermediate_lines.append('| '+' | '.join([str(item['year']),fmt(Decimal(row['cash_conversion']),'.0001'),row['arithmetic_CFO_minus_capex_yuan'],fmt(Decimal(item['book_effective_tax_rate'])*100)+'%',fmt(Decimal(item['nopat_formula_yuan'])),fmt(Decimal(item['whole_finance_line_formula_yuan']))])+' |')
  intermediate_lines += ['','三年利润总额−所得税−合并净利润的差额均0元。2010存货与选定期末资本复用B12的2011年初列，资本来源身份保留；2008/2009年末资本已由B16补入，年度路径另列；2008年初调整与变更说明B17待核，不输出真实经营ROIC。新增明细经独立有理数复核，旧工作簿未包含B13—B15新分析。','','P02本人原版本认可及原支持保留；新增三年补证未被自动算作本人新意见采纳。完整计算包与原审阅版本不同，原严格校验器如实提示版本变化；原十年/两端/2012判断的数值支持未变，不要求重复确认旧原数。[B15实际原数回执](../evidence/20261025-b15-chat-confirmation.json)；[B16已核回执](../evidence/20261025-b16-chat-confirmation.json)。','']
  insert=lines.index('## N07阶段性判断');lines[insert:insert]=intermediate_lines
  path_lines=['## B16：2007—2011年度资本路径与2008基期差异','',f"2007—2011五年合并CFO合计{primary_cash_window['sum_consolidated_cfo_yuan']}元、合并净利润合计{primary_cash_window['sum_consolidated_net_profit_yuan']}元，比值{fmt(Decimal(primary_cash_window['ratio_of_sums']),'.0001')}倍；购建现金合计{primary_cash_window['sum_reported_purchase_cash_yuan']}元。统计仍为原合并口径，不能以五年加总掩盖单年波动，也不证明成熟投入回报。",'','| 年度 | 选择性NCWC（元） | 选定期末资本（元） | 已对齐平均资本（元） | 基准公式/平均资本 | 整行敏感性/平均资本 |','| --- | ---: | ---: | ---: | ---: | ---: |']
  for row in capital_path['panel']:
   path_lines.append('| '+' | '.join([str(row['year']),row['selected_ncwc_yuan'],row['selected_end_capital_yuan'],'待核2008年初桥接' if row['average_selected_capital_yuan'] is None else row['average_selected_capital_yuan'],'Unknown' if row['baseline_formula_over_average'] is None else fmt(Decimal(row['baseline_formula_over_average'])*100)+'%','Unknown' if row['whole_line_formula_over_average'] is None else fmt(Decimal(row['whole_line_formula_over_average'])*100)+'%'])+' |')
  path_lines += ['','2007原报年末与2008年报年初的预付款项/在建工程有等额反向差632,936,687.20元；选定资本合计差0不表示营运资本分项可直接跨年比较。2008年报物理48页已定位公司会计政策变更说明，属于B17待本人核的新披露；不改旧Fact，不将候选说明预先当人工Fact。2008同报告平均资本/营运资本变动的正式代理暂止，跨报原值平均情景另存JSON，未用该情景输出回报率。','','2009/2010年初九科目与上年已核年末逐项匹配，2010原报期末与已核2011年初也匹配；这些为Agent来源比较，不冒作新的人工事件。年度资本余额差之和与2007→2011端点差均为'+capital_path['capital_balance_telescope']['endpoint_delta_yuan']+'元，勾稽差0；仍不等于累计现金再投资。所有百分比为条件会计代理，真实经营回报Unknown。','','[B16真实回执](../evidence/20261025-b16-chat-confirmation.json)；[B17两项三金额及政策说明](../work/review-batches/20261025-B17.md)。','']
  insert=lines.index('## N07阶段性判断');lines[insert:insert]=path_lines
  text='\n'.join(lines);out=p/'outputs/student-cash-capital-check.md';dest=p/'work/cash-20261024/calculations.json'
  if out.exists():assert dest.exists() and sha(out)==json.loads(dest.read_text(encoding='utf-8'))['generated_output_sha256'],'Manual output edits; stop'
  result={'date':'2026-10-25','state':'AgentCalculated','human_arithmetic_confirmation':False,'code_sha256':sha(Path(__file__)),'panel':result_rows,'complete_cash_years':cash_years,'complete_cash_n':len(cash_years),'consolidated_cash_diagnostics':diagnostics,'continuous_2016_2025_diagnostics':continuous_ten,'fy2012_sensitivity':sensitivity,'cash_conclusion_adoption':content_adoption,'intermediate_2008_2010':intermediate,'annual_selected_capital_path':capital_path,'continuous_2007_2011_cash_diagnostics':primary_cash_window,'selected_capital_proxy_diagnostics':proxy,'listed_financial_rows':financial,'cash_reconciliation_2025':bridge,'breakpoint_source_facts':breakpoint_facts,'company_disclosure_explanations':explanations,'input_evidence':evidence,'research_breakpoint_rules':[{'year':year,'reason':reason,'status':'原文已核；跨年同口径裁决/逐项调整金额仍分开' if any(x['year']==year for x in breakpoint_facts) else 'Unknown：当前有效原文未齐'} for year,reason in [(2007,'新旧会计准则'),(2012,'财务公司已纳入合并，旧2013首次合并说法需修正'),(2013,'财务公司正式营业'),(2020,'预收/合同负债及新收入准则')]],'selective_ncwc_rule':'inventory+notes/accounts receivable+receivable financing+prepayments−accounts payable−advances/contract liabilities; only current source-confirmed items, no whole other items','contract_reference_proxy_window':[2007,2012],'primary_candidate_proxy_window':[2007,2011],'FY2012_sensitivity_status':'B14已核并接入2012合并基础及三种条件利润敏感性；不混入2007—2011主窗，真实经济回报仍Unknown','minimum_multiyear_incremental_window_status':'Unknown：输入与范围未齐','formulas':{'cash_conversion':'consolidated CFO/consolidated net profit','arithmetic_cash_residual':'consolidated CFO−cash paid for acquisition/construction of fixed/intangible/other long-term assets','capex_intensity':'purchased long-term asset cash/consolidated operating revenue','inventory_intensity':'book inventory/consolidated operating revenue'},'precision':48,'generated_output_sha256':hashlib.sha256(text.encode()).hexdigest()};out.write_text(text,encoding='utf-8',newline='\n');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 assert state_sha==sha(p/'evidence/review-state.json');print(json.dumps({'panel_years':25,'complete_cash_n':len(cash_years),'cash_years':cash_years,'entity_CFO':'Unknown','NOPAT_ROIC_proxy':'Unknown','new_approvals':0},ensure_ascii=False))
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
