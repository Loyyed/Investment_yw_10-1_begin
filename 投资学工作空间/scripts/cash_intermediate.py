"""Confirmed intermediate-year cash and explicitly conditional profit arithmetic."""
from pathlib import Path
from decimal import Decimal,localcontext
import json,hashlib
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def calculate_intermediate(p,raw):
    m=json.loads((p/'work/review-batches/20261025-B15.json').read_text(encoding='utf-8'));payload=dict(m);fp=payload.pop('display_payload_sha256');assert fp==digest(payload)
    if not all(x['id'] in raw for x in m['items']):return {'state':'Unknown','used_ids':[],'panel':[]}
    for x in m['items']:
        f=raw[x['id']];assert f['binding']==x['binding'] and f['value']==x['value'] and f['pdf_sha256']==x['source_sha256'] and json.loads(f['note'])['display_payload_sha256']==fp
    old=json.loads((p/'work/review-batches/20261024-B12.json').read_text(encoding='utf-8'));op=dict(old);oldfp=op.pop('display_payload_sha256');assert oldfp==digest(op)
    capital=[x for x in old['items'] if x['id'] in ['R2011-04','R2011-05']]
    for x in capital:assert raw[x['id']]['binding']==x['binding'] and raw[x['id']]['value']==x['value'] and json.loads(raw[x['id']]['note'])['display_payload_sha256']==oldfp
    out=[]
    with localcontext() as ctx:
        ctx.prec=48
        for year in [2008,2009,2010]:
            items=[x for x in m['items'] if x['year']==year];f={k:Decimal(v) for x in items for k,v in x['fields'].items()};tax=None if f['四、利润总额']==0 else f['减：所得税费用']/f['四、利润总额'];np_residual=f['四、利润总额']-f['减：所得税费用']-f['合并净利润'];assert np_residual==0
            row={'year':year,'input_ids':[x['id'] for x in items],'raw_fields_yuan':{k:str(v) for k,v in f.items()},'book_effective_tax_rate':None if tax is None else str(tax),'nopat_formula_yuan':None if tax is None else str(f['三、营业利润']*(1-tax)),'whole_finance_line_formula_yuan':None if tax is None else str((f['三、营业利润']+f['财务费用']-f['投资收益'])*(1-tax)),'net_profit_reconciliation_residual_yuan':str(np_residual),'selected_end_capital_yuan':None,'average_selected_capital_yuan':None,'formula_over_average_capital':None,'economic_nopat_yuan':None,'entity_roic':None,'boundary':'利润公式采用报表有效税率；财务费用整行移除是敏感性，不是准确经营利润。缺必要资本/经济范围/成熟投入，正式回报Unknown。'}
            if year==2010:
                c={k:Decimal(v) for x in capital for k,v in x['fields'].items()};signs={'存货':1,'应收票据':1,'应收账款':1,'预付款项':1,'应付账款':-1,'预收款项':-1};ncwc=sum((c[k]*sign for k,sign in signs.items()),Decimal(0));cap=ncwc+sum((c[k] for k in ['固定资产','在建工程','无形资产']),Decimal(0))
                row.update(selected_ncwc_yuan=str(ncwc),selected_end_capital_yuan=str(cap),reused_inventory_yuan=str(c['存货']),capital_input_ids=[x['id'] for x in capital],capital_source_basis='2011年报已核年初列，对应2010期末本报告口径；不冒作2010原年报新增人工核验')
            out.append(row)
    return {'state':'AgentCalculated','used_ids':[x['id'] for x in m['items']]+[x['id'] for x in capital],'panel':out,'human_arithmetic_confirmation':False,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
