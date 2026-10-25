"""Current-bound FY2012 consolidated sensitivity, not an entity return model."""
from pathlib import Path
from decimal import Decimal,localcontext
import hashlib,json

def calculate_2012(p,raw,proxy):
    m=json.loads((p/'work/review-batches/20261025-B14.json').read_text(encoding='utf-8'))
    payload=dict(m);fp=payload.pop('display_payload_sha256')
    assert fp==hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    items=m['items'];ids=[x['id'] for x in items]
    if not all(id in raw for id in ids):
        return {'state':'Unknown','used_ids':[],'reason':'B14当前有效原数未齐；不使用候选'}
    for x in items:
        fact=raw[x['id']]
        assert fact['binding']==x['binding'] and fact['value']==x['value'] and fact['pdf_sha256']==x['source_sha256']
        assert json.loads(fact['note'])['display_payload_sha256']==fp
    f={key:None if value is None else Decimal(value) for x in items for key,value in x['fields'].items()}
    previous=next(x for x in proxy['panel'] if x['year']==2011)
    # Reuse the confirmed 2011 closing capital. The 2012 comparison was checked
    # separately against that same column; not a newly signed opening record.
    comparison=json.loads((p/'work/cash-20261024/b14-source-check.json').read_text(encoding='utf-8'))
    assert comparison['comparison_2011_columns_match_confirmed_B11']
    with localcontext() as ctx:
        ctx.prec=48
        ncwc=sum((f[k]*sign for k,sign in proxy['parameters']['ncwc_signs'].items()),Decimal(0))
        long=sum((f[k] for k in ['固定资产','在建工程','无形资产']),Decimal(0))
        close=ncwc+long;opening=Decimal(previous['selected_end_capital_arithmetic_yuan']);avg=(opening+close)/2
        pbt=f['四、利润总额'];tax=None if pbt==0 else f['减：所得税费用']/pbt
        op=f['三、营业利润'];whole=op+f['财务费用']-f['投资收益']
        components={k:f[k] for k in ['利息支出','利息收入（按费用表符号）','汇兑损益','其他手续费']}
        component_sum=sum((v for v in components.values() if v is not None),Decimal(0));assert component_sum==f['财务费用']
        detail=op+f['利息支出']+f['利息收入（按费用表符号）']-f['投资收益']
        scenarios={}
        for name,pretax in [('baseline',op),('whole_finance_line_removed',whole),('listed_interest_and_investment_removed',detail)]:
            after=None if tax is None else pretax*(1-tax)
            scenarios[name]={'pre_tax_formula_yuan':str(pretax),'conditional_after_tax_formula_yuan':None if after is None else str(after),'formula_over_selected_average':None if avg==0 or after is None else str(after/avg),'entity_roic':None}
        diff=None if tax is None else (detail-whole)*(1-tax)
        changes={'selected_capital_balance_delta_yuan':str(close-opening),'baseline_formula_delta_yuan':None if tax is None else str(op*(1-tax)-Decimal(previous['nopat_formula_arithmetic_yuan'])),'baseline_formula_ratio_change_pp':None if tax is None or avg==0 else str((op*(1-tax)/avg-Decimal(previous['formula_profit_over_selected_average']))*100),'formal_incremental_return':None,'reason':'2011→2012跨财务公司合并断点，仅列两端算术变化，不命名实体增量回报或成熟回报'}
        return {'year':2012,'state':'AgentCalculated','human_arithmetic_confirmation':False,'used_ids':ids+previous['input_ids'],'raw_fields_yuan':{k:None if v is None else str(v) for k,v in f.items()},'selected_ncwc_yuan':str(ncwc),'selected_long_assets_yuan':str(long),'selected_end_capital_yuan':str(close),'opening_selected_capital_yuan':str(opening),'opening_basis':'复用B11已核2011年末；Agent比较2012年初列相符，不冒作新人工确认','average_selected_capital_yuan':str(avg),'book_effective_tax_rate':None if tax is None else str(tax),'scenarios':scenarios,'financial_expense_components_yuan':{k:None if v is None else str(v) for k,v in components.items()},'nonblank_financial_components_sum_yuan':str(component_sum),'financial_components_residual_yuan':str(component_sum-f['财务费用']),'blank_policy':'汇兑本期原表空白保留null；已列非空金额勾稽相符不等于公司披露汇兑0','detail_minus_whole_after_tax_yuan':None if diff is None else str(diff),'detail_minus_whole_ratio_pp':None if diff is None or avg==0 else str(diff/avg*100),'changes_from_2011':changes,'entity_cfo_yuan':None,'economic_nopat_yuan':None,'economic_capital_yuan':None,'entity_roic':None,'boundary':'2012合并利润/资产代理，含财务公司。书面税率及选择性资本只是条件参数；明细情景仅移除已列应计利息和投资，保留手续费，不证明真实经营利润。不能从剔现金资本再扣完整金融子公司净资产，不能从营业利润机械扣子公司净利润；金融抵销/税费/经营范围不足则实体指标停止。','code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
