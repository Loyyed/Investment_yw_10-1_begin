from pathlib import Path
import sys,json,hashlib,shutil,re,html
from decimal import Decimal as D
sys.stdout.reconfigure(encoding='utf-8')
r=Path(__file__).parent;w=Path('D:/投资学/投资学工作空间');b=Path('D:/投资学/投资学公司分析通用工作台')
sys.path.insert(0,str(b));sys.path.insert(0,str(w/'scripts'))
from companybench.research_depth import revenue_bridge
from review_store import ReviewStore
out=w/'work/deep-study-20261029';out.mkdir(exist_ok=True)
od=w/'outputs/04_研究深化';od.mkdir(exist_ok=True)
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=ReviewStore(w);domains={n:getattr(s,n)() for n in ['facts','change_facts','m01_metric_facts','m01_disclosure_facts','m01_scale_facts','lec03_agent_facts']}
facts={x['id']:x for x in domains['facts']};agent={x['id']:x for x in domains['lec03_agent_facts']}
spec=json.loads((w/'work/t5-forecast-20261027/report-spec.json').read_text(encoding='utf-8'))
for dep in spec['dependencies']:assert sha(w/dep['path'])==dep['sha256'],dep['path']
protected={str(p.relative_to(w)):sha(p) for p in (w/'evidence').iterdir() if p.is_file()}
sources=json.loads((r/'official/manifest.json').read_text(encoding='utf-8'))
for source in sources:
 if 'sha256' in source:assert sha(r/'official'/(source['id']+'.pdf'))==source['sha256']
def num(id,n=0):return D(facts[id]['numbers'][n].replace(',',''))
def yi(v):return f'{D(v)/D(10)**8:,.2f}'
def pct(v):return f'{D(v):.2f}'
def table(head,rows):return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)+'\n'
annual=[];annual_inputs=[]
for y in range(2021,2025):
 before={p['name']:{'revenue':p['revenue_yuan'],'quantity':p['sales_tonnes']} for p in agent[f'L03-A{y-1}-B']['data']['products']}
 after={p['name']:{'revenue':p['revenue_yuan'],'quantity':p['sales_tonnes']} for p in agent[f'L03-A{y}-B']['data']['products']}
 annual.append({'year':y,**revenue_bridge(before,after)});annual_inputs.append({'year':y,'before':before,'after':after,'ids':[f'L03-A{y-1}-B',f'L03-A{y}-B']})
before={p['name']:{'revenue':p['revenue_yuan'],'quantity':p['sales_tonnes']} for p in agent['L03-A2024-B']['data']['products']}
mt=num('R2025-03');wine=num('R2025-17')+num('R2025-17',2)
after={'茅台酒':{'revenue':str(mt),'quantity':str(num('R2025-01',1))},'其他系列酒':{'revenue':str(wine-mt),'quantity':str(num('R2025-01',3))}}
annual.append({'year':2025,**revenue_bridge(before,after)});annual_inputs.append({'year':2025,'before':before,'after':after,'ids':['L03-A2024-B','R2025-01','R2025-03','R2025-17'],'note':'系列酒收入为已核酒类合计减茅台酒派生；非新原值Fact'})
observations=[]
def ext(id,source,page,label,values,unit='人民币元',period='2026H1/2025H1'):
 ps=json.loads((r/'official'/(source+'.json')).read_text(encoding='utf-8'))
 for v in values:assert v in ps[page-1]['text'],(id,v)
 observations.append({'id':id,'source_id':source,'page':page,'label':label,'values':values,'unit':unit,'period':period,'scope':'合并','verifier':'Agent','human_confirmation':False,'state':'ExternalSourceChecked'})
 return [D(v.replace(',','')) for v in values]
rev=ext('X01','2026H1',5,'营业收入',['90,703,260,964.48','89,389,354,416.84'])
parent=ext('X02','2026H1',5,'归母净利润',['44,516,880,421.86','45,402,962,298.10'])
cfo=ext('X03','2026H1',5,'合并CFO',['70,690,750,119.06','13,119,061,031.33'])
cost=ext('X04','2026H1',7,'营业成本',['9,473,762,565.88','7,777,491,083.93'])
selling=ext('X05','2026H1',7,'销售费用',['3,206,308,341.53','3,260,462,949.46'])
tax=ext('X06','2026H1',75,'税金及附加',['14,682,159,453.47','13,942,384,581.48'])
pbt=ext('X07','2026H1',31,'利润总额',['61,438,419,177.29','62,778,000,766.82'])
q1r=ext('X08','2026Q1',1,'一季度营业收入',['53,909,252,220.51','50,600,957,885.78'],period='2026Q1/2025Q1')
q1p=ext('X09','2026Q1',1,'一季度归母',['27,242,512,886.45','26,847,474,238.76'],period='2026Q1/2025Q1')
h26=ext('X10','2026H1',8,'产品/渠道/地区/平台',['7,772,443.79','1,293,418.65','5,196,204.70','3,869,657.74','8,962,212.26','103,650.18','4,026,356.42'],unit='人民币万元',period='2026H1')
h25=ext('X11','2025H1',8,'产品/渠道/地区/平台',['7,558,994.89','1,376,252.94','4,000,959.89','4,934,287.94','8,645,947.06','289,300.77','1,076,043.75'],unit='人民币万元',period='2025H1')
deposit=ext('X12','2026H1',33,'客户存款及同业净增',['7,383,004,563.78','-2,516,653,584.50'])
interbank=ext('X13','2026H1',34,'存放央行和同业净增',['-21,895,452,284.18','25,410,788,169.25'])
salescash=ext('X14','2026H1',33,'销售商品提供劳务收到现金',['98,421,697,395.39','95,086,614,960.23'])
contract=ext('X15','2026H1',9,'合同负债期末/年初',['3,177,561,597.07','8,006,739,780.94'],period='2026-06-30/2025-12-31')
change=cfo[0]-cfo[1];dep_con=deposit[0]-deposit[1];ib_con=interbank[1]-interbank[0];cash_res=change-dep_con-ib_con
q2r=[rev[i]-q1r[i] for i in range(2)];q2p=[parent[i]-q1p[i] for i in range(2)]
h26=[v*10000 for v in h26];h25=[v*10000 for v in h25]
assert h26[0]+h26[1]==h26[2]+h26[3]==h26[4]+h26[5]
assert h25[0]+h25[1]==h25[2]+h25[3]==h25[4]+h25[5]
gp=[rev[i]-cost[i] for i in range(2)];gm=[gp[i]/rev[i]*100 for i in range(2)]
other=(pbt[0]-pbt[1])-((gp[0]-gp[1])-(tax[0]-tax[1])-(selling[0]-selling[1]))
calc={'annual_bridges':annual,'external_observations':observations,'h1':{'q2_revenue':list(map(str,q2r)),'q2_parent_np':list(map(str,q2p)),'gross_margin_percent':list(map(str,gm)),'pretax_bridge':{'gross_profit':str(gp[0]-gp[1]),'tax_surcharge':str(tax[1]-tax[0]),'selling':str(selling[1]-selling[0]),'other_net':str(other),'pbt_change':str(pbt[0]-pbt[1])},'cash_bridge':{'total_change':str(change),'deposit_contribution':str(dep_con),'interbank_contribution':str(ib_con),'other_net':str(cash_res)}}}
save(out/'calculations.json',calc);save(out/'revenue-inputs.json',annual_inputs)
save(out/'external-source-register.json',{'authorization':'2026-10-29本人允许突破数据来源限制，广泛取可信数据并标出处；不等于原数人工确认','sources':sources,'observations':observations})
local=out/'local-source-payloads';local.mkdir(exist_ok=True)
for p in (r/'official').glob('*.pdf'):shutil.copy2(p,local/p.name)
save(out/'.gitignore','local-source-payloads/\nocr/\nqa/\n')
save(out/'current-authority-audit.json',{'date':'2026-10-29','domains':{k:len(v) for k,v in domains.items()},'current_dependencies':len(spec['dependencies']),'new_human_confirmation':False})
annualrows=[[x['year'],yi(x['change']),yi(x['aggregate']['volume']),yi(x['aggregate']['product_mix']),yi(x['aggregate']['within_product_asp']),x['aggregate']['residual']] for x in annual]
prows=[[name,yi(v['change']),yi(v['volume']),yi(v['asp']),yi(v['interaction']),pct(v['quantity_change_percent'])+'%',pct(v['asp_change_percent'])+'%'] for name,v in annual[-1]['products'].items()]
labels=['茅台酒','系列酒','直销','批发代理','国内','国外','i茅台']
channelrows=[[labels[i],yi(h25[i]),yi(h26[i]),yi(h26[i]-h25[i]),pct((h26[i]/h25[i]-1)*100)+'%'] for i in range(7)]
channelrows.append(['其余直销（差额）',yi(h25[2]-h25[6]),yi(h26[2]-h26[6]),yi((h26[2]-h26[6])-(h25[2]-h25[6])),'不命名新业态'])
target=D(spec['forecast_results']['base'][0]['revenue']);h225=num('R2025-18')-rev[1];needed=target-rev[0]
repls={
'ANNUAL_TABLE':table(['年份','收入增量','总销量项','产品结构项','组内ASP项','精确残差'],annualrows),
'PRODUCT_TABLE':table(['产品','收入变化','量变项','ASP项','交互项','销量同比','ASP同比'],prows),
'CHANNEL_TABLE':table(['项目/切面','2025H1','2026H1','增减','同比/边界'],channelrows),
'QUARTER_TABLE':table(['同期间','2025收入','2026收入','收入同比','2025归母','2026归母','归母同比'],[[name,yi(rr[1]),yi(rr[0]),pct((rr[0]/rr[1]-1)*100)+'%',yi(pp[1]),yi(pp[0]),pct((pp[0]/pp[1]-1)*100)+'%'] for name,rr,pp in [('Q1',q1r,q1p),('Q2=H1−Q1',q2r,q2p)]]),
'PROFIT_TABLE':table(['合并项','2025H1','2026H1','变化/利润影响'],[['营业收入',yi(rev[1]),yi(rev[0]),yi(rev[0]-rev[1])],['营业成本',yi(cost[1]),yi(cost[0]),yi(cost[1]-cost[0])],['毛利',yi(gp[1]),yi(gp[0]),yi(gp[0]-gp[1])],['毛利率',pct(gm[1])+'%',pct(gm[0])+'%',pct(gm[0]-gm[1])+'pp'],['税金及附加',yi(tax[1]),yi(tax[0]),yi(tax[1]-tax[0])],['销售费用',yi(selling[1]),yi(selling[0]),yi(selling[1]-selling[0])],['其余损益净影响','单列金融/管理等','非渠道归属',yi(other)],['利润总额',yi(pbt[1]),yi(pbt[0]),yi(pbt[0]-pbt[1])]]),
'CASH_TABLE':table(['CFO同比变动桥','亿元','边界'],[['集团总增量',yi(change),'合并，非酒类实体'],['存款及同业净增贡献',yi(dep_con),'经营流入行'],['央行及同业存放贡献',yi(ib_con),'净支出行转向'],['其余净影响',yi(cash_res),'保留所有其他项目'],['两行贡献占总变动',pct((dep_con+ib_con)/change*100)+'%','约99.36%，其余为净增加']]),
'FORECAST_TABLE':table(['条件','金额/门槛','身份'],[['旧全年收入基准',yi(target),'旧Forecast'],['H1实际',yi(rev[0]),'新公告Agent核查'],['达旧基准所需H2',yi(needed),'条件算术'],['2025H2营业收入',yi(h225),'全年减半年'],['所需H2同比',pct((needed/h225-1)*100)+'%','门槛，无概率']]),
'PIPELINE_TABLE':table(['环节','本轮实质改进','保留边界'],[
['材料/第一次','公告、参考观点、历史估计与最新数据分层','标题official不证明来源'],['第二次收入','五组年度总量/结构/ASP桥及2025产品三项桥','无交叉表不编SKU贡献'],['第三次指标','合并/归母/主营/金融利息对齐','公司组ASP不当单品净价'],['第四次变化','旧change_facts复查，新Q2累计差','新算术不写旧人工Fact'],['第五次商业模式','价值形成→交付→收入→税费→资本现金','图存在不代表机制成立'],['生产库存延伸','供给参照与承接分开，缺销售吨数即停','基酒产量不代销量'],['渠道延伸','平台/其余直销/批发变化精确闭合','毛利迁移不代净贡献'],['现金资本延伸','金融两行贡献桥与残余','残余不改名实体CFO/ROIC'],['第六次竞争','壁垒转成净价/责任/再投资/持续时间','网页份额不当行业分母'],['第七次叙事','反方及可区分观测一起写','P04冻结内容不改'],['Lec05估值','现金流与折现率前置检查','教学算例不当目标价'],['预测/路演','旧目标H2门槛，新Q2检验','旧稿信息集保留，附新研究入口'],['通用工作台','方法可检索，收入精确桥，估值资格检查','不复制公司授权/数值'],['交接/Git','成果与方法分仓，原载荷本地','发布不产生Fact或签署']])}
srcmap={x['id']:x for x in sources if 'sha256'in x}
repls.update({'SOURCE_H1':srcmap['2026H1']['url'],'SOURCE_P1':srcmap['price-0331']['url'],'SOURCE_P2':srcmap['price-0718']['url']})
md=(r/'report-template.md').read_text(encoding='utf-8')
for k,v in repls.items():md=md.replace(k,v)
save(od/'增长质量与价值兑现.md',md)
try:
 import mistune
 body=mistune.create_markdown(plugins=['table'])(md)
except ImportError:raise RuntimeError('需markdown用于可审阅网页输出，不能用整页pre替代')
css='body{max-width:1160px;margin:auto;padding:32px;font:17px/1.85 system-ui;background:#f6f5ef;color:#173d37}h1{font-size:38px;line-height:1.35}h2{margin-top:56px;border-top:2px solid #bad0c3;padding-top:22px}h3{margin-top:32px}table{border-collapse:collapse;width:100%;font-size:14px;display:block;overflow:auto}td,th{border-bottom:1px solid #c9d6cc;padding:12px;text-align:left;min-width:90px}th{background:#e2eade}a{color:#235f53}p{max-width:92ch}svg{width:100%;height:auto}small{color:#607369}@media(max-width:700px){body{padding:16px}h1{font-size:28px}table{font-size:13px}}'
items=[('平台',h26[6]-h25[6]),('其余直销',(h26[2]-h26[6])-(h25[2]-h25[6])),('批发',h26[3]-h25[3]),('主营总增量',sum(h26[:2])-sum(h25[:2]))]
sv='<svg viewBox="0 0 1000 270" role="img" aria-label="半年收入增量，亿元"><line x1="430" y1="15" x2="430" y2="240" stroke="#758b80"/>'
for i,(label,val) in enumerate(items):
 y=30+i*58;v=float(val/D(10)**8);width=abs(v)*1.15;x=430 if v>=0 else 430-width;color='#277661' if v>=0 else '#af6a4c'
 sv+=f'<text x="15" y="{y+19}" font-size="20">{label}</text><rect x="{x}" y="{y}" width="{width}" height="28" fill="{color}"/><text x="890" y="{y+20}" font-size="20">{v:+.2f}</text>'
sv+='</svg>'
sv='<h3>三条销售路径的收入增量（亿元）</h3><div style="overflow-x:auto">'+sv.replace('<svg viewBox','<svg style="min-width:700px" viewBox')+'</div>'
body=body.replace('<h2>五、',sv+'<h2>五、',1)
page='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>增长质量与价值兑现</title><style>'+css+'</style></head><body><a href="../00_从这里开始.html">返回统一入口</a>'+body+'</body></html>'
save(od/'增长质量与价值兑现.html',page)
entry=w/'outputs/00_从这里开始.html';s0=entry.read_text(encoding='utf-8')
banner='<section style="padding:24px;margin:20px;border:2px solid #48806c;border-radius:12px"><h2>2026-10-29 · 研究深化与新公告检验</h2><p>年度收入精确拆解、2026半年渠道迁移、利润与金融现金桥。新增研究未继承旧认可；原路演仍按原信息集阅读。</p><p><a href="04_研究深化/增长质量与价值兑现.html">阅读增长质量与价值兑现 →</a>　<a href="04_研究深化/学习与方法知识库.md">学习覆盖与知识库 →</a></p></section>'
if '2026-10-29 · 研究深化与新公告检验' not in s0:
 s0=re.sub(r'(<body[^>]*>)',lambda m:m[0]+banner,s0,count=1) if re.search(r'<body[^>]*>',s0) else s0.replace('<main>', '<main>'+banner,1)
 save(entry,s0)
assert all(sha(w/rel)==digest for rel,digest in protected.items())
save(out/'validation.json',{'authority_domains':{k:len(v) for k,v in domains.items()},'old_spec_dependencies_current':len(spec['dependencies']),'protected_ledgers_unchanged':len(protected),'exact_annual_bridges':len(annual),'external_observation_groups':len(observations),'external_string_page_checks':sum(len(x['values']) for x in observations),'h1_three_dimensions_equal':True,'new_human_fact_or_signature':False})
print(json.dumps({'annual2025':annual[-1],'Q2_revenue_yoy':str((q2r[0]/q2r[1]-1)*100),'Q2_profit_yoy':str((q2p[0]/q2p[1]-1)*100),'cash_financial_share':str((dep_con+ib_con)/change*100),'gross_margin':list(map(str,gm)),'H2_required_yoy':str((needed/h225-1)*100),'report_chars':len(md)},ensure_ascii=False,indent=2))
