"""Recompute B01 analysis from current original ReviewStore facts; no approvals."""
from pathlib import Path
from decimal import Decimal, localcontext, ROUND_HALF_UP
import hashlib,json,re,sys
sys.stdout.reconfigure(encoding='utf-8')

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from review_store import ReviewStore

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def show(value,places='0.01'):return format(value.quantize(Decimal(places),rounding=ROUND_HALF_UP),'f')
def main(workspace=ROOT):
 p=Path(workspace);store=ReviewStore(p);facts={x['id']:x for x in store.facts()}
 ids=['R2024-09','R2024-10','R2024-11','R2024-12','R2024-15']+[f'R2024-{i}' for i in range(16,24)]
 used=ids+['N2024-08'];assert all(i in facts for i in used),'Required current facts are missing or stale'
 before=sha(p/'evidence/review-state.json')
 manifest=p/'work/review-batches/20261022-B01.json';m=json.loads(manifest.read_text(encoding='utf-8'))
 assert all(facts[x['id']]['binding']==x['binding'] for x in m['items'])
 def pair(i):
  numbers=re.findall(r'(?<!\d)-?\d[\d,]*\.\d+',facts[i]['value'])
  assert len(numbers)==2,(i,numbers)
  return [Decimal(n.replace(',','')) for n in numbers]
 with localcontext() as context:
  context.prec=48
  data={}
  for i in ids:
   a,z=pair(i);delta=a-z
   data[i]={'label':facts[i]['claim'],'current_yuan':str(a),'previous_yuan':str(z),'delta_yuan':str(delta),'delta_yi_display':show(delta/Decimal(10)**8),'raw_signed_percent':str(delta/z*100),'growth_percent_display':show(delta/z*100) if z>0 else None,'source_binding':facts[i]['binding'],'scope':facts[i]['scope']}
   if z<0:
    assert i=='R2024-23' and a<0
    data[i]['negative_base_note']='费用为负数；净收益绝对额减少，避免将负基数普通同比读成经营改善。'
    data[i]['net_benefit_decline_percent']=str(delta/abs(z)*100)
  D=lambda i:Decimal(data[i]['delta_yuan'])
  A=lambda i:Decimal(data[i]['current_yuan'])
  Z=lambda i:Decimal(data[i]['previous_yuan'])
  sales_children=['R2024-10','R2024-11','R2024-21','R2024-22']
  assert sum((A(i) for i in sales_children),Decimal(0))==A('R2024-09')
  assert sum((Z(i) for i in sales_children),Decimal(0))==Z('R2024-09')
  sales_residual=D('R2024-09')-sum((D(i) for i in sales_children),Decimal(0));assert sales_residual==0
  mgmt_ids=['R2024-12','R2024-19','R2024-20']
  mgmt_other_delta=D('R2024-15')-sum((D(i) for i in mgmt_ids),Decimal(0))
  assert mgmt_other_delta==Decimal('85236973.01')
  core_ids=['R2024-17','R2024-09','R2024-15','R2024-16']
  four_delta=sum((D(i) for i in core_ids),Decimal(0))
  five_delta=four_delta+D('R2024-23')
  revenue,cost=pair('N2024-08');gross=revenue-cost;four=sum((A(i) for i in core_ids),Decimal(0));subtotal=gross-four
  assert revenue==cost+four+subtotal
  bridge={'revenue_yuan':str(revenue),'operating_cost_yuan':str(cost),'gross_yuan':str(gross),'tax_sales_management_rd_yuan':str(four),'analytical_subtotal_yuan':str(subtotal),'analytical_subtotal_percent_revenue':str(subtotal/revenue*100),'four_expense_increase_yuan':str(four_delta),'including_finance_expense_increase_yuan':str(five_delta),'other_items_held_constant_pretax_impact_yuan':str(-five_delta),'formula':'分析小计=营业收入−营业成本−税金及附加−销售费用−管理费用−研发费用','boundary':'不是报表营业利润、正式实体EBIT/NOPAT、渠道净利润或FCFF。加财务费用的变化仅为其他项目不变的税前算术影响；不把它称为净利润实际归因。'}
  diagnostics={'sales_children_delta_sum_residual_yuan':str(sales_residual),'market_service_share_of_sales_expense_increase_percent':str(D('R2024-10')/D('R2024-09')*100),'consumption_tax_share_of_tax_expense_increase_percent':str(D('R2024-18')/D('R2024-17')*100),'remaining_management_items_delta_yuan':str(mgmt_other_delta),'scope_and_duplicate_policy':'消费税不再叠加到税金及附加；商标许可费、职工薪酬与其他不再叠加到管理费用；销售明细不再叠加到销售总额；第三方代收手续费不额外扣一次。'}
  directory=p/'work/e04-20261022-b01';directory.mkdir(parents=True,exist_ok=True)
  output={'date':'2026-10-22','state':'AgentCalculated','human_arithmetic_confirmation':False,'decimal_precision':48,'rounding':'ROUND_HALF_UP, only final display','formulas':{'delta':'current−previous','positive_base_percent':'(current−previous)/previous×100','negative_finance_benefit_decline':'(current−previous)/abs(previous)×100'},'input_facts':[{key:facts[i][key] for key in ['id','claim','value','scope','binding','pdf_path','pdf_sha256']} for i in used],'code_path':'scripts/calculate_b01_expenses.py','code_sha256':sha(Path(__file__)),'rows':data,'bridge':bridge,'diagnostics':diagnostics}
  (directory/'calculations.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  lines=['# B01核验后的税费与费用分析','', '2026-10-22。原披露由leo真实聊天核验，见[回执](../../evidence/20261022-b01-chat-confirmation.json)。下列变化为AgentCalculated，未登记为人工变化Fact；展示2024年报本期／2023比较列的机械变化，不假定各年原报分类完全不变。','', '| 项目 | 两期差额（元） | 差额（亿元） | 正基数变化率 |','| --- | ---: | ---: | ---: |']
  for i in ids:
   x=data[i];pct=x['growth_percent_display'];lines.append(f"| {x['label']} | {x['delta_yuan']} | {x['delta_yi_display']} | {pct+'%' if pct is not None else '负基数另释'} |")
  lines+=['','## 支持哪些具体判断','',f"1. 销售费用增加{show(D('R2024-09')/Decimal(10)**8)}亿元，其中市场推广及服务费增加{show(D('R2024-10')/Decimal(10)**8)}亿元，解释其净增额的{show(Decimal(diagnostics['market_service_share_of_sales_expense_increase_percent']))}%。广告宣传费下降被其他分项增长抵消。四个销售分项在两期分别精确勾稽为合计，差额残差为0。该分解没有证明推广效果、需求或渠道归属。",'',f"2. 管理费用减少{show(-D('R2024-15')/Decimal(10)**8)}亿元。职工薪酬费用减少{show(-D('R2024-19')/Decimal(10)**8)}亿元，其他减少{show(-D('R2024-20')/Decimal(10)**8)}亿元；商标许可使用费增加{show(D('R2024-12')/Decimal(10)**8)}亿元，剩余管理费用分项净增{show(mgmt_other_delta/Decimal(10)**8)}亿元。不能据此认定裁员、效率提升或全公司人工成本下降。",'',f"3. 税金及附加增加{show(D('R2024-17')/Decimal(10)**8)}亿元，其中消费税增加{show(D('R2024-18')/Decimal(10)**8)}亿元，占其净增额{show(Decimal(diagnostics['consumption_tax_share_of_tax_expense_increase_percent']))}%。这不是所得税率变化或现金缴税变化的证明。",'',f"4. 税金及附加、销售、管理和研发四项合计较比较列增加{show(four_delta/Decimal(10)**8)}亿元；财务费用负值绝对额缩小，相应净收益减少{show(D('R2024-23')/Decimal(10)**8)}亿元（{show(D('R2024-23')/abs(Z('R2024-23'))*100)}%）。这五项在其他项目不变时合计使税前结果减少{show(five_delta/Decimal(10)**8)}亿元，不是实际税后利润归因。",'','## 2024年毛利之后的分析小计','',f"营业收入{revenue}元−营业成本{cost}元＝{gross}元；再扣税金及附加、销售／管理／研发共{four}元，余{subtotal}元（{show(subtotal/Decimal(10)**8)}亿元）。",'',bridge['boundary'],'','## 复算与待解决问题','','[逐项输入、绑定、公式和精确结果](calculations.json)，复算：`D:/Anaconda/python.exe scripts/calculate_b01_expenses.py`。代码只读取当前facts()，缺输入或绑定变化即停止；不保存任何人工确认。','','尚需独立厘清金融与实体范围、其他收益／投资与减值、经营税负和经营资本，才能形成正式实体利润、现金和回报。渠道共享费用分摊没有依据，不按收入比例擅分；不将推广支出增多直接解释为品牌变弱或变强。','']
  (directory/'expense-analysis.md').write_text('\n'.join(lines),encoding='utf-8')
 assert sha(p/'evidence/review-state.json')==before
 print(json.dumps({'rows':len(data),'bridge':bridge,'diagnostics':diagnostics,'authority_unchanged':True},ensure_ascii=False))

if __name__=='__main__':main()
