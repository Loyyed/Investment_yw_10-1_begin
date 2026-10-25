"""Verified annual selected-capital path, with an explicit 2008 opening gate."""
from pathlib import Path
from decimal import Decimal,localcontext
import hashlib,json
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def annual_path(p,raw,proxy,intermediate):
    def read(f):return json.loads(f.read_text(encoding='utf-8'))
    m=read(p/'work/review-batches/20261025-B16.json');payload=dict(m);fp=payload.pop('display_payload_sha256');assert fp==digest(payload)
    if not all(x['id'] in raw for x in m['items']):return {'state':'Unknown','used_ids':[],'panel':[],'cash_assignments':[]}
    for x in m['items']:
        fact=raw[x['id']];assert fact['binding']==x['binding'] and fact['value']==x['value'] and fact['pdf_sha256']==x['source_sha256'] and json.loads(fact['note'])['display_payload_sha256']==fp
    comparison=read(p/'work/cash-20261024/annual-capital-source-comparison.json')
    for x in comparison['comparisons']:assert hashlib.sha256((p/x['source_path']).read_bytes()).hexdigest()==x['source_sha256']
    b12=read(p/'work/review-batches/20261024-B12.json');keys=['存货','应收票据','应收账款','预付款项','应付账款','预收款项','固定资产','在建工程','无形资产'];signs={'存货':1,'应收票据':1,'应收账款':1,'预付款项':1,'应付账款':-1,'预收款项':-1};panel=[]
    base={x['year']:x for x in proxy['panel']};mid={x['year']:x for x in intermediate['panel']};cap={};ids={}
    for year in [2007,2008,2009,2010,2011]:
        if year in base:fields={k:base[year]['raw_fields_yuan'][k] for k in keys};source_ids=base[year]['input_ids']
        elif year==2010:
            chosen=[x for x in b12['items'] if x['id'] in ['R2011-04','R2011-05']];fields={k:v for x in chosen for k,v in x['fields'].items()};source_ids=[x['id'] for x in chosen]
            for x in chosen:assert raw[x['id']]['binding']==x['binding'] and raw[x['id']]['value']==x['value']
        else:
            chosen=[x for x in m['items'] if x['year']==year];fields={k:v for x in chosen for k,v in x['fields'].items()};source_ids=[x['id'] for x in chosen]
        cap[year]={k:Decimal(v) for k,v in fields.items()};ids[year]=source_ids
    with localcontext() as ctx:
        ctx.prec=48
        totals={year:sum((f[k]*sign for k,sign in signs.items()),Decimal(0))+sum((f[k] for k in ['固定资产','在建工程','无形资产']),Decimal(0)) for year,f in cap.items()}
        for year in range(2007,2012):
            fields=cap[year];ncwc=sum((fields[k]*sign for k,sign in signs.items()),Decimal(0));long=sum((fields[k] for k in ['固定资产','在建工程','无形资产']),Decimal(0));profit=base.get(year) or mid[year];nopat=Decimal(profit['nopat_formula_arithmetic_yuan'] if year in base else profit['nopat_formula_yuan']);neutral=Decimal(profit['whole_line_neutralized_formula_yuan'] if year in base else profit['whole_finance_line_formula_yuan'])
            opening=Decimal(base[year]['opening_selected_capital_yuan']) if year in base else totals[year-1];gate=True;matches=None
            if year in [2008,2009,2010]:
                comp=next(x for x in comparison['comparisons'] if x['year']==year);matches=all(Decimal(x['opening_yuan'])==cap[year-1][x['field']] for x in comp['rows']);gate=matches
            average=(opening+totals[year])/2 if gate else None
            row={'year':year,'raw_capital_fields_yuan':{k:str(v) for k,v in fields.items()},'capital_input_ids':ids[year],'profit_input_ids':profit['input_ids'],'selected_ncwc_yuan':str(ncwc),'selected_long_assets_yuan':str(long),'selected_end_capital_yuan':str(totals[year]),'confirmed_prior_capital_yuan':str(opening),'same_report_opening_component_match':matches,'average_selected_capital_yuan':None if average is None else str(average),'baseline_profit_formula_yuan':str(nopat),'whole_line_profit_formula_yuan':str(neutral),'baseline_formula_over_average':None if average in [None,0] else str(nopat/average),'whole_line_formula_over_average':None if average in [None,0] else str(neutral/average),'cross_report_original_average_capital_yuan':str((opening+totals[year])/2),'same_scope_ncwc_change_yuan':None,'entity_roic':None,'formal_incremental_return':None,'status':'AgentCalculated；选择科目会计路径，真实经济资本/利润范围仍未齐'}
            if year>2007:
                prior_ncwc=sum((cap[year-1][k]*sign for k,sign in signs.items()),Decimal(0));row.update(cross_report_original_ncwc_delta_yuan=str(ncwc-prior_ncwc),selected_capital_balance_delta_yuan=str(totals[year]-totals[year-1]));row['same_scope_ncwc_change_yuan']=str(ncwc-prior_ncwc) if gate else None
            if year==2008:
                comp=next(x for x in comparison['comparisons'] if x['year']==2008);diff={x['field']:str(Decimal(x['opening_yuan'])-Decimal(x['confirmed_previous_closing_yuan'])) for x in comp['rows'] if not x['opening_matches']};assert sum((Decimal(v) for v in diff.values()),Decimal(0))==0
                row.update(opening_differences_yuan=diff,selected_capital_total_difference_yuan='0.00',opening_gate='B17待本人核2008调整后年初数及公司会计政策变更；不把资本合计抵消当科目可比',cross_report_original_average_status='仅两份原值均值，非已核2008同报告基期；不输出对应回报比率')
            panel.append(row)
        delta_sum=sum((Decimal(x['selected_capital_balance_delta_yuan']) for x in panel[1:]),Decimal(0));window_delta=totals[2011]-totals[2007];assert delta_sum==window_delta
    return {'state':'AgentCalculated','used_ids':list(dict.fromkeys([x['id'] for x in m['items']]+[id for a in ids.values() for id in a])),'panel':panel,'cash_assignments':[x for x in m['items'] if x['kind']=='cash-revenue-basic-year'],'capital_balance_telescope':{'annual_deltas_sum_yuan':str(delta_sum),'endpoint_delta_yuan':str(window_delta),'residual_yuan':str(delta_sum-window_delta),'cumulative_cash_reinvestment_yuan':None,'boundary':'年度余额差加总只勾稽端点；不等于累计现金再投资/成熟增量回报'},'human_arithmetic_confirmation':False,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
