"""Arithmetic on explicitly selected accounts; no economic scope approval implied."""
from decimal import Decimal, localcontext
from pathlib import Path
import json, hashlib

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def calculate_proxy(p:Path,raw:dict):
    manifest=json.loads((p/'work/review-batches/20261024-B11.json').read_text(encoding='utf-8'))
    payload=dict(manifest);fp=payload.pop('display_payload_sha256');assert fp==digest(payload)
    verified=[]
    for item in manifest['items']:
        if item['id'] not in raw:continue
        fact=raw[item['id']]
        assert fact['binding']==item['binding'] and fact['value']==item['value']
        assert json.loads(fact['note'])['display_payload_sha256']==fp
        verified.append(item)
    b12=json.loads((p/'work/review-batches/20261024-B12.json').read_text(encoding='utf-8'));bp=dict(b12);b12fp=bp.pop('display_payload_sha256');assert b12fp==digest(bp)
    b12verified=[]
    for item in b12['items']:
        if item['id'] not in raw:continue
        fact=raw[item['id']];assert fact['binding']==item['binding'] and fact['value']==item['value'] and json.loads(fact['note'])['display_payload_sha256']==b12fp
        b12verified.append(item)
    panel=[]
    rules={'存货':1,'应收票据':1,'应收账款':1,'预付款项':1,'应付账款':-1,'预收款项':-1}
    with localcontext() as ctx:
        ctx.prec=48
        for year in [2007,2011]:
            items=[x for x in verified if x['year']==year]
            if len(items)!=3:continue
            fields={key:Decimal(value) for item in items for key,value in item['fields'].items()}
            ncwc=sum((fields[key]*sign for key,sign in rules.items()),Decimal(0))
            long_assets=sum((fields[key] for key in ['固定资产','在建工程','无形资产']),Decimal(0))
            pbt=fields['四、利润总额'];tax=fields['减：所得税费用'];op=fields['三、营业利润']
            tax_rate=None if pbt==0 else tax/pbt
            nopat=None if tax_rate is None else op*(1-tax_rate)
            panel.append({'year':year,'raw_fields_yuan':{key:str(value) for key,value in fields.items()},'input_ids':[x['id'] for x in items],
              'selected_ncwc_arithmetic_yuan':str(ncwc),'selected_long_assets_arithmetic_yuan':str(long_assets),'selected_end_capital_arithmetic_yuan':str(ncwc+long_assets),
              'book_effective_tax_rate':None if tax_rate is None else str(tax_rate),'nopat_formula_arithmetic_yuan':None if nopat is None else str(nopat),
              'average_selected_capital_yuan':None,'operating_nopat_yuan':None,'entity_roic':None,
              'status':'AgentCalculated：按明示选择科目做附条件算术，非本人范围裁决或真实经营回报',
              'stops':['年初/平均资本当前有效原数未齐，B12待核','营业利润中的利息/投资及税率经营适用性待核','工程物资/其他等未裁定，不将其设成0或全部非经营','选择性资本非完整资本，不与全口径利润直接配对认定经营ROIC']})
            row=panel[-1];opening_items=[x for x in b12verified if x['year']==year and x['kind'] in ['proxy-opening-ncwc','proxy-opening-long-assets']]
            if len(opening_items)==2:
                opening={key:Decimal(value) for item in opening_items for key,value in item['fields'].items()};opening_ncwc=sum((opening[key]*sign for key,sign in rules.items()),Decimal(0));opening_capital=opening_ncwc+sum((opening[key] for key in ['固定资产','在建工程','无形资产']),Decimal(0));average=(opening_capital+ncwc+long_assets)/2
                row.update(opening_raw_fields_yuan={key:str(value) for key,value in opening.items()},opening_source_period=year-1,opening_source_basis='同份当年年报年初列；不冒作上年原年报原披露',opening_selected_ncwc_yuan=str(opening_ncwc),opening_selected_capital_yuan=str(opening_capital),average_selected_capital_yuan=str(average),formula_profit_over_selected_average=None if average==0 or nopat is None else str(nopat/average))
                row['input_ids'] += [x['id'] for x in opening_items];row['stops'].remove('年初/平均资本当前有效原数未齐，B12待核')
            finance_items=[x for x in b12verified if x['year']==year and x['kind']=='proxy-finance-investment']
            if len(finance_items)==1:
                item=finance_items[0];fin={key:Decimal(value) for key,value in item['fields'].items()};neutral_pre_tax=op+fin['财务费用']-fin['投资收益'];neutral=None if tax_rate is None else neutral_pre_tax*(1-tax_rate)
                row.update(finance_investment_raw_fields_yuan={key:str(value) for key,value in fin.items()},whole_line_neutralized_profit_before_tax_yuan=str(neutral_pre_tax),whole_line_neutralized_formula_yuan=None if neutral is None else str(neutral),whole_line_sensitivity_status='整行财务费用和投资收益移除的算术敏感性，非真实去利息经营利润；税率仍为报表有效税率')
                avg=row['average_selected_capital_yuan'];row['whole_line_formula_over_selected_average']=None if avg in [None,'0'] or neutral is None else str(neutral/Decimal(avg));row['input_ids'].append(item['id'])
        window=None
        if len(panel)==2 and all(x['nopat_formula_arithmetic_yuan'] is not None for x in panel):
            first,last=panel;delta_cap=Decimal(last['selected_end_capital_arithmetic_yuan'])-Decimal(first['selected_end_capital_arithmetic_yuan']);delta_nopat=Decimal(last['nopat_formula_arithmetic_yuan'])-Decimal(first['nopat_formula_arithmetic_yuan'])
            scale=max(abs(Decimal(first['selected_end_capital_arithmetic_yuan'])),abs(Decimal(last['selected_end_capital_arithmetic_yuan'])))
            valid=delta_cap>0
            window={'start_year':2007,'end_year':2011,'elapsed_years':4,'year_end_points':2,
              'delta_selected_capital_balance_yuan':str(delta_cap),'delta_nopat_formula_yuan':str(delta_nopat),
              'denominator_to_end_capital_scale':None if scale==0 else str(delta_cap/scale),'near_zero_policy':'小分母阈值尚未裁定；保留分母与规模之比供人工判断，正式回报仍停止',
              'arithmetic_delta_profit_over_delta_capital':str(delta_nopat/delta_cap) if valid else None,
              'denominator_positive':valid,'annualized':False,'cumulative_cash_reinvestment_yuan':None,'formal_incremental_return':None,
              'maturity_validated':False,'scope_matched':False,
              'stops':['资本余额之差不是逐年累计现金再投资','4年跨度及两个端点不证明每笔投入达到长生产成熟期','利润税率与选择性资本尚未核准同范围','缺经营现金/Capex分解，正式增量回报停止Unknown'],
              'status':'仅余额与利润代理的算术诊断，不命名成熟增量回报率'}
            a,b=panel;t0,t1=Decimal(a['book_effective_tax_rate']),Decimal(b['book_effective_tax_rate']);op0,op1=Decimal(a['raw_fields_yuan']['三、营业利润']),Decimal(b['raw_fields_yuan']['三、营业利润'])
            op_effect=(op1-op0)*((1-t0)+(1-t1))/2;tax_effect=-(t1-t0)*(op0+op1)/2
            window['formula_change_decomposition']={'method':'两路径平均，NOPAT公式=OP*(1-t)，只分解算式不认定税法因果','operating_profit_factor_yuan':str(op_effect),'book_tax_factor_yuan':str(tax_effect),'sum_yuan':str(op_effect+tax_effect),'residual_yuan':str(delta_nopat-op_effect-tax_effect)}
            if all('whole_line_neutralized_formula_yuan' in x for x in panel):
                d=Decimal(panel[1]['whole_line_neutralized_formula_yuan'])-Decimal(panel[0]['whole_line_neutralized_formula_yuan']);window['whole_line_sensitivity_delta_formula_yuan']=str(d);window['whole_line_sensitivity_delta_profit_over_delta_capital']=str(d/delta_cap) if valid else None
    return {'state':'AgentCalculated','human_scope_approval':False,'source_confirmation':'B11/B12实际原数确认，当前来源绑定重检；与范围/算术认可分开',
      'used_ids':[x['id'] for x in verified+b12verified],'panel':panel,'window_diagnostic':window,
      'formulas':{'selected_ncwc':'存货+应收票据+应收账款+预付款项−应付账款−预收款项','selected_end_capital':'selected_ncwc+固定资产+在建工程+无形资产','nopat_formula':'营业利润×(1−所得税费用/利润总额)'},
      'parameters':{'ncwc_signs':rules,'other_accounts':'逐项待判，未整体纳入/排除','profit_capital_scope':'Unknown','operating_tax_rate':'Unknown；书面有效税率只供附条件公式','average_capital':'本年报年初与年末选定资本均值；只为附条件代理，不是完整经济资本','maturity':'Unknown：项目投入到成熟映射未齐'},
      'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
