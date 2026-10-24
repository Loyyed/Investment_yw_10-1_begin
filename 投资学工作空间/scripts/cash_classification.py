"""B13 disclosed-use decomposition, with unclassified and outside-proxy amounts retained."""
from pathlib import Path
from decimal import Decimal,localcontext
import json,hashlib
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def classify_disclosed_inputs(p,raw,proxy_rows):
 m=json.loads((Path(p)/'work/review-batches/20261024-B13.json').read_text(encoding='utf-8'));payload=dict(m);fp=payload.pop('display_payload_sha256');assert fp==digest(payload)
 verified=[]
 for x in m['items']:
  if x['id'] not in raw:continue
  f=raw[x['id']];assert f['binding']==x['binding'] and f['value']==x['value'] and json.loads(f['note'])['display_payload_sha256']==fp;verified.append(x)
 if len(verified)!=8:return {'state':'Unknown：B13当前有效原文未齐','used_ids':[x['id'] for x in verified],'missing_ids':[x['id'] for x in m['items'] if x['id'] not in raw],'economic_classification_complete':False}
 bykind={(x['year'],x['kind']):x for x in verified};rows={x['year']:x for x in proxy_rows}
 with localcontext() as ctx:
  ctx.prec=48
  def fields(year,kind):return {k:Decimal(v) for k,v in bykind[year,kind]['fields'].items()}
  material=sum(fields(2007,'materials-prepayments').values());server=fields(2007,'server-prepayment-and-listed-total')['预付服务器款'];listed07=fields(2007,'server-prepayment-and-listed-total')['主要单位合计'];assert material+server==listed07
  land11=sum(fields(2011,'land-prepayments').values());construction=fields(2011,'construction-prepayments-and-listed-total');listed11=construction.pop('前五名单位合计');engineering11=sum(construction.values());assert land11+engineering11==listed11
  decomposed=[]
  for year,working,capital_prepaid,listed in [(2007,material,server,listed07),(2011,Decimal(0),land11+engineering11,listed11)]:
   row=rows[year];total_prepaid=Decimal(row['raw_fields_yuan']['预付款项']);unclassified=total_prepaid-listed;assert unclassified>=0
   # The zero here means no daily-use item was identified among this list, not a disclosed zero.
   working_selected=Decimal(row['selected_ncwc_arithmetic_yuan'])-total_prepaid+working
   long_selected=Decimal(row['selected_long_assets_arithmetic_yuan'])+capital_prepaid
   total=working_selected+long_selected+unclassified;residual=total-Decimal(row['selected_end_capital_arithmetic_yuan']);assert residual==0
   decomposed.append({'year':year,'reported_total_prepayments_yuan':str(total_prepaid),'listed_materials_prepayments_yuan':str(working) if year==2007 else None,'listed_land_prepayments_yuan':str(land11) if year==2011 else None,'listed_construction_prepayments_yuan':str(engineering11) if year==2011 else None,'listed_equipment_prepayment_yuan':str(server) if year==2007 else None,'listed_capital_prepayment_yuan':str(capital_prepaid),'listed_total_yuan':str(listed),'unclassified_remainder_yuan':str(unclassified),'unclassified_share':str(unclassified/total_prepaid),'selected_working_balance_excluding_unclassified_yuan':str(working_selected),'selected_long_assets_plus_listed_capital_prepayments_yuan':str(long_selected),'sum_with_unclassified_bucket_yuan':str(total),'baseline_selected_end_capital_yuan':row['selected_end_capital_arithmetic_yuan'],'classification_residual_yuan':str(residual),'average_classified_capital_yuan':None,'actual_operating_ncwc_yuan':None,'actual_operating_capital_yuan':None,'boundary':'按公司已披露用途形成Agent分类，不将未列余额当日常周转或0；资本预付从周转桶转至长期桶，加未分类桶与原选择性资本守恒；未证明资产无重叠，年末用途不外推年初。'})
  gross_land07=sum(fields(2007,'land-other-receivables').values())
  finance=fields(2011,'financial-expense-components');interest=finance['利息收入（按费用表符号）'];fx=finance['汇兑损益'];fees=finance['其他手续费'];net=interest+fx+fees
  row=rows[2011];assert net==Decimal(row['finance_investment_raw_fields_yuan']['财务费用']);op=Decimal(row['raw_fields_yuan']['三、营业利润']);investment=Decimal(row['finance_investment_raw_fields_yuan']['投资收益']);tax=Decimal(row['book_effective_tax_rate']);average=Decimal(row['average_selected_capital_yuan'])
  before=op+interest-investment;after=before*(1-tax);ratio=after/average;whole=Decimal(row['whole_line_neutralized_formula_yuan']);delta=after-whole
  assert abs(delta+(fx+fees)*(1-tax))<Decimal('1e-30')
  sensitivity={'year':2011,'interest_income_as_expense_signed_yuan':str(interest),'fx_expense_yuan':str(fx),'fees_yuan':str(fees),'components_sum_yuan':str(net),'matches_confirmed_net':True,'conditional_profit_before_tax_yuan':str(before),'conditional_after_tax_formula_yuan':str(after),'conditional_formula_over_baseline_average':str(ratio),'difference_from_whole_line_after_tax_yuan':str(delta),'difference_from_whole_line_ratio_pp':str((ratio-Decimal(row['whole_line_formula_over_selected_average']))*100),'formula':'(营业利润+按费用表负号的利息收入−投资收益)×(1−报表有效税率)，保留已列汇兑与手续费','assumptions':'保留汇兑和手续费仅为明确的比较约定，未确认全部为酒类经营；税率和分母仍为原会计代理','actual_operating_nopat_yuan':None,'actual_operating_roic':None,'cross_year_same_scope_incremental_return':None,'cross_year_stop':'2007未获同口径应计利息明细，不以现金存款利息或整行净额与2011明细拼接比较。'}
 return {'date':'2026-10-25','state':'AgentCalculated / AgentInterpretation：原文Fact与分类判断分开','used_ids':[x['id'] for x in verified],'decomposition':decomposed,'outside_baseline_proxy':[{'year':2007,'source_id':bykind[2007,'land-other-receivables']['id'],'gross_land_other_receivables_yuan':str(gross_land07),'net_carrying_value_yuan':None,'added_to_selected_capital':False,'boundary':'原代理未含其他应收；原文坏账列空白不认成0。净值、长期资本重叠与期初对应未裁定，先列补查项，不直接加回。'}],'disclosed_component_sensitivity_2011':sensitivity,'investment_origins':[{'year':x['year'],'id':x['id'],'text':x['value']} for x in verified if x['kind']=='investment-origin'],'economic_classification_complete':False,'formal_incremental_return':None,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
