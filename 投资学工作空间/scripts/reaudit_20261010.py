from pathlib import Path
from decimal import Decimal,localcontext,ROUND_HALF_UP
import argparse,json,sys,hashlib
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path);a=p.parse_args();w=a.workspace.resolve();out=a.output or w/'work/20261010-recheck'
sys.path.insert(0,str(w/'scripts'))
from review_store import ReviewStore
D=lambda x:Decimal(str(x).replace(',',''))
def fmt(x,n=2):return str(x.quantize(Decimal('1').scaleb(-n),rounding=ROUND_HALF_UP))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=['evidence/review-state.json','evidence/change-review-state.json','evidence/m01-disclosure-review.json','evidence/m01-metric-review.json','evidence/m01-scale-review.json','evidence/lec03-agent-facts.json','sources/manifest.json','work/structured-data.json']
manifest=json.loads((w/'sources/manifest.json').read_text('utf8'))
protected += [r['pdf'] for r in manifest]
before={r:sha(w/r) for r in protected}
s=ReviewStore(w);domains={name:getattr(s,name)() for name in ['facts','change_facts','m01_disclosure_facts','m01_metric_facts','m01_scale_facts','lec03_agent_facts']}
f={r['id']:r for r in domains['facts']};agent={r['id']:r for r in domains['lec03_agent_facts']}
checks=[]
def check(name,condition):
    if not condition:raise ValueError(name)
    checks.append({'check':name,'passed':True})
check('第一次两项当前原值Fact',all(k in f for k in ['C01','C02']))
check('第二次至少3行商品维度有效Fact',all(k in f for k in ['N2024-01','N2024-02','N2024-03','N2024-08']))
for col in range(2):check('第二次商品分项与合计列'+str(col),sum(D(f[k]['numbers'][col]) for k in ['N2024-01','N2024-02','N2024-03'])==D(f['N2024-08']['numbers'][col]))
check('第三次12项当前原值有效',all('C'+str(i).zfill(2) in f for i in range(1,13)))
check('收入组成C03=C01+C04',D(f['C03']['value'])==D(f['C01']['value'])+D(f['C04']['value']))
check('主营其他C01=C06+C07',D(f['C01']['value'])==D(f['C06']['value'])+D(f['C07']['value']))
check('利润归属C09=C02+C10',D(f['C09']['value'])==D(f['C02']['value'])+D(f['C10']['value']))
for r in domains['change_facts']:check('第四次复算'+r['id'],fmt((D(r['current'])-D(r['previous']))/D(r['previous'])*100)==r['percent'])
check('第四次CH01/02独立绑定有效',set(r['id'] for r in domains['change_facts'])=={'CH01','CH02'})
rows=[];events=[]
with localcontext() as ctx:
    ctx.prec=50
    for y in range(2020,2025):
        b=agent[f'L03-A{y}-B']['data'];c=agent[f'L03-A{y}-C']['data'];i=agent[f'L03-A{y}-I']['data']['industry']
        check(str(y)+'产品收入合计',sum(D(x['revenue_yuan']) for x in b['products'])==D(b['wine']['revenue_yuan']))
        check(str(y)+'渠道收入合计',sum(D(x['revenue_yuan']) for x in b['channels'])==D(b['wine']['revenue_yuan']))
        check(str(y)+'产品成本合计',sum(D(x['cost_yuan']) for x in b['products'])==D(b['wine']['cost_yuan']))
        cash=c['cash_analysis'];cr=c['cash_rows'];get=lambda k:D(cr[k]['current_yuan'])
        fin=get('客户存款和同业存放款项净增加额')+get('收取利息、手续费及佣金的现金')-get('客户贷款及垫款净增加额')-get('存放中央银行和同业款项净增加额')-get('拆出资金净增加额')-get('支付利息、手续费及佣金的现金')
        check(str(y)+'金融现金桥接',fin==D(cash['explicit_financial_items_net_yuan']))
        check(str(y)+'现金剔除余额',D(cash['cfo_yuan'])-fin==D(cash['after_listed_financial_items_residual_yuan']))
        check(str(y)+'现金转换率',fmt(D(cash['cfo_yuan'])/D(c['consolidated_net_profit_yuan'])*100)==cash['cfo_to_consolidated_profit_percent'])
        prod=b['products'][0];channel=next(x for x in b['channels'] if x['name']=='直销')
        asp=D(prod['revenue_yuan'])/D(prod['sales_tonnes'])/10000
        check(str(y)+'匹配销量ASP',fmt(asp)==prod['asp_wanyuan_per_sales_tonne'])
        rows.append({'year':y,'revenue_yuan':prod['revenue_yuan'],'sales_tonnes':prod['sales_tonnes'],'asp_wanyuan_per_sales_tonne':fmt(asp),'gross_margin_percent':prod['gross_margin_percent'],'direct_share_percent':channel['revenue_share_percent'],'cfo_to_all_profit_percent':cash['cfo_to_consolidated_profit_percent'],'finished_inventory_tonnes':b['physical_inventory']['finished_tonnes'],'source_ids':[f'L03-A{y}-B',f'L03-A{y}-C',f'L03-A{y}-I']})
        events.append({'year':y,'company_industry_disclosure':i['company_narrative'],'industry_location':i['narrative_pages'],'cash_reason':c.get('cash_reason'),'support_boundary':'公司披露内容与已核算术；机制及行业阶段另列Interpretation'})
    b0=agent['L03-A2023-B']['data'];b1=agent['L03-A2024-B']['data'];x0=b0['products'][0];x1=b1['products'][0]
    r0,r1,q0,q1=map(D,[x0['revenue_yuan'],x1['revenue_yuan'],x0['sales_tonnes'],x1['sales_tonnes']]);p0,p1=r0/q0,r1/q1
    delta=r1-r0;parts=[p0*(q1-q0),q0*(p1-p0),(q1-q0)*(p1-p0)]
    check('量价恒等分解残差小于一分',abs(sum(parts)-delta)<D('.01'))
    decomposition={'input_ids':['L03-A2023-B','L03-A2024-B'],'input_scope':'茅台酒产品组、销售收入人民币元/销售量吨；年度组统计，非固定SKU','formula':'ΔR=P0ΔQ+Q0ΔP+ΔPΔQ, P=R/Q','revenue_change_yuan':str(delta),'quantity_term_yuan':fmt(parts[0]),'group_asp_term_yuan':fmt(parts[1]),'interaction_yuan':fmt(parts[2]),'revenue_yoy_percent':fmt(delta/r0*100),'quantity_yoy_percent':fmt((q1-q0)/q0*100),'group_asp_yoy_percent':fmt((p1-p0)/p0*100),'state':'Agent复算参考；未新增人工计算Fact','support_boundary':'算术分解，不将组ASP变化归因为同款提价/纯品牌效应'}
    direct0=D(next(x for x in b0['channels'] if x['name']=='直销')['revenue_yuan'])/D(b0['wine']['revenue_yuan'])*100
    direct1=D(next(x for x in b1['channels'] if x['name']=='直销')['revenue_yuan'])/D(b1['wine']['revenue_yuan'])*100
    signals={'direct_share_change_pp':fmt(direct1-direct0),'finished_inventory_yoy_percent':fmt((D(b1['physical_inventory']['finished_tonnes'])/D(b0['physical_inventory']['finished_tonnes'])-1)*100),'industry_production_cross_report_2023_percent':fmt((D(agent['L03-A2023-I']['data']['industry']['production_wan_kl'])/D(agent['L03-A2022-I']['data']['industry']['production_wan_kl'])-1)*100),'industry_reported_2023_percent':agent['L03-A2023-I']['data']['industry']['reported_production_yoy_percent'],'state':'排查/复算信号，不是新增因果Fact'}
check('原件与八项受保护账本/输入未改变',before=={r:sha(w/r) for r in protected})
result={'checked_date':'2026-10-10','domain_counts':{k:len(v) for k,v in domains.items()},'domain_ids':{k:[r['id'] for r in v] for k,v in domains.items()},'checks':checks,'year_rows':rows,'events':events,'decomposition':decomposition,'signals':signals,'protected_sha256':before,'script_sha256':sha(Path(__file__)),'authority_note':'快照仅作本轮底稿；下次须重运行ReviewStore；未改任何事实核验或签署历史'}
out.mkdir(parents=True,exist_ok=True);(out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
md=['# 逐合同复算与五年证据批注','', '2026-10-10；Agent本轮检查，复用原有效Fact，不生成新本人点击。脚本：scripts/reaudit_20261010.py；精确输入、公式及源SHA见同目录results.json。','',f'有效检查{len(checks)}项；原件及原权威账本均未改变。','', '| 年度 | 茅台酒收入（元） | 销售量（吨） | ASP（万元/销售吨） | 产品毛利率 | 直销酒类收入占比 | 集团CFO/全部净利润 | 成品库存（吨） | 当前原证据编号 |','| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
for r in rows:md.append('| '+' | '.join(str(r[k]) for k in ['year','revenue_yuan','sales_tonnes','asp_wanyuan_per_sales_tonne','gross_margin_percent','direct_share_percent','cfo_to_all_profit_percent','finished_inventory_tonnes'])+' | '+','.join(r['source_ids'])+' |')
md+=['','## 2023—2024茅台酒收入变化：算术分解','',f'收入增加{decomposition["revenue_change_yuan"]}元；量项{decomposition["quantity_term_yuan"]}元；产品组ASP项{decomposition["group_asp_term_yuan"]}元；交叉项{decomposition["interaction_yuan"]}元。收入增长{decomposition["revenue_yoy_percent"]}%，销量增长{decomposition["quantity_yoy_percent"]}%，组ASP增长{decomposition["group_asp_yoy_percent"]}%。','',decomposition['support_boundary']+'。输入为当年已核组数据，期间/定义匹配；未控制SKU/渠道/产品构成，不作为净因果。','', '## 需要解释的变化信号','',f'2024直销占比变动{signals["direct_share_change_pp"]}个百分点；成品库存增长{signals["finished_inventory_yoy_percent"]}%；公司生产/陈酿库存不能直接视为经销商或终端库存。',f'2023行业跨报告绝对量重算{signals["industry_production_cross_report_2023_percent"]}%，原报披露{signals["industry_reported_2023_percent"]}%；基数/样本桥接Unknown，停止统一行业序列与份额计算。','', '以上新分解及信号为Agent复算参考，未写入原披露、变化或人工计算权威账本。研究机制及最终裁决另列。','']
(out/'calculation-notes.md').write_text('\n'.join(md),encoding='utf8')
print(json.dumps({'checks':len(checks),'counts':result['domain_counts'],'decomposition':decomposition,'signals':signals,'protected_unchanged':True},ensure_ascii=False))
