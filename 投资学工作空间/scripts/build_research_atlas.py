"""Company-specific synthesis builder; reads current ReviewStore, never submits reviews."""
import sys,json,re,hashlib,argparse,importlib.util,csv
from pathlib import Path
from decimal import Decimal,localcontext
from fractions import Fraction
sys.stdout.reconfigure(encoding='utf-8')
ap=argparse.ArgumentParser();ap.add_argument('--project',default='D:/投资学/投资学工作空间');ap.add_argument('--toolkit',default='D:/投资学/投资学公司分析通用工作台');ap.add_argument('--stage',default=str(Path(__file__).resolve().parents[1]/'runtime/research-atlas-build'));args=ap.parse_args()
p=Path(args.project);kit=Path(args.toolkit);stage=Path(args.stage);stage.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(p/'scripts'))
from review_store import ReviewStore
modspec=importlib.util.spec_from_file_location('atlas_insight',stage/'companybench/insight.py' if (stage/'companybench/insight.py').exists() else kit/'companybench/insight.py');ir=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(ir)
D=Decimal
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def load(rel):return json.loads((p/rel).read_text(encoding='utf-8'))
def nums(v):return [D(x.replace(',','')) for x in re.findall(r'(?<!\d)-?\d[\d,]*\.\d+',v)]
def n(v):return float(v)
def yi(v):return float(D(v)/D(10**8))
def f(v,prec=2):return f'{float(v):,.{prec}f}'
def pct(v):return f(v)+'%'
def block(title,*paragraphs,refs=None):return {'title':title,'paragraphs':list(paragraphs),'refs':refs or []}
sources=[];used={};deps={};derived=[]
store=ReviewStore(p);domains={name:getattr(store,name)() for name in ['facts','change_facts','lec03_agent_facts','m01_metric_facts','m01_disclosure_facts','m01_scale_facts']};lookup={(k,r['id']):r for k,rows in domains.items() for r in rows}
def take(domain,id):
 r=lookup[(domain,id)];assert r['state']=='Fact',(domain,id);used[(domain,id)]={'domain':domain,'id':id,'record_digest':ir.digest(r)};return r
def raw(id):return take('facts',id)
def dep(rel):deps[rel]={'path':rel,'sha256':sha(p/rel)}
def src(id,title,records,rel=None,note=''):
 rr=[]
 for domain,key in records:
  r=take(domain,key);rr.append(f"{key}：{r.get('value',r.get('claim',r.get('calculation',{}).get('value','有效年度组')))}；{r.get('location',r.get('page','组内各字段页码'))}；{r.get('scope',r.get('support_boundary','依原记录范围'))}；原件SHA {r.get('pdf_sha256','见当前组绑定')}")
 path=rel or (take(*records[0]).get('pdf_path','') if records else '')
 if rel:dep(rel)
 sources.append({'id':id,'title':title,'status':'当前原接口有效披露／已核计算；后续解释与预测不自动升级Fact' if records else 'Agent计算／研究底稿，非新增人工Fact','note':note+'\n'+'\n'.join(rr),'path':path,'sha256':sha(p/path) if path and (p/path).is_file() else ''})
def calc(id,formula,inputs,value,unit):
 derived.append({'id':id,'state':'AgentCalculated','formula':formula,'inputs':inputs,'exact':str(value),'unit':unit});return float(value)
def chart(title,subtitle,kind,unit,rows,series,refs,reading,formula='',**extra):return dict(title=title,subtitle=subtitle,kind=kind,unit=unit,rows=rows,series=[{'key':k,'label':v} for k,v in series],refs=refs,reading=reading,formula=formula,**extra)

lag=load('work/lag-20261022/calculations.json');channel=load('work/channel-20261024/calculations.json');cash=load('work/cash-20261024/calculations.json')
# Cached calculations can only contribute after each original dependency is current.
for rel,data in [('work/lag-20261022/calculations.json',lag),('work/channel-20261024/calculations.json',channel),('work/cash-20261024/calculations.json',cash)]:
 dep(rel)
 for ref in data['input_evidence']:
  row=take(ref['domain'],ref['id'])
  if 'binding' in ref:assert row['binding']==ref['binding'],ref['id']
  if 'validated_group_snapshot_sha256' in ref:assert ir.digest(row)==ref['validated_group_snapshot_sha256'],ref['id']
  assert row['pdf_sha256']==ref['pdf_sha256'],ref['id']
  if row.get('pdf_path'):dep(row['pdf_path'])
src('E01','2024报表收入与利润：三组不同边界',[('facts',x) for x in ['C01','C02','C03','C04','C05','C06','C07','C08','C09','C10','C11','C12']],note='来源批注用于学习，不把排除某用途误写为撤销原Fact。')
src('E02','2024产品收入、成本与匹配销量',[('facts',x) for x in ['N2024-01','N2024-02','N2024-03']]+[('m01_metric_facts',x) for x in ['M01-A01','M01-A02','M01-A03','M01-G01','M01-G02','M01-G03']],rel='work/m01-calculated-metrics.json',note='产品组统计ASP含规格、渠道和地区组合；原输入旧quantity_state字段不是当前Fact权威。')
src('E03','2024同口径变化的独立确认',[('change_facts','CH01'),('change_facts','CH02')],rel='outputs/change-verification-record.md',note='CH01营业收入；CH02归母净利润。两者不替换合并全部净利润。')
src('E04','2016—2025渠道结构与代数分解',[],rel='work/channel-20261024/calculations.json',note='全部24项输入当前来源绑定已核；主营酒类渠道与附注全营业收入范围分开，费用率分母为公司营业收入。')
src('E05','2016—2025生产、库存与销售诊断',[],rel='work/lag-20261022/calculations.json',note='25项原接口输入已核当前绑定；至少五年与混合勾兑仅证明工艺安排，十年独立库存残差均0。')
src('E06','现金与资本当前计算包',[],rel='work/cash-20261024/calculations.json',note='75项当前输入逐项对照有效来源。16个有效年度不是25年完整序列；2016—2025连续十年另列。合并CFO不等于白酒实体CFO。')
src('E07','2024费用、税费与收入自述',[('facts',x) for x in ['R2024-09','R2024-10','R2024-11','R2024-12','R2024-15','R2024-16','R2024-17']]+[('m01_disclosure_facts','M01-D02'),('m01_disclosure_facts','M01-D03')],note='推广服务费、广告宣传费与商标许可费分属原科目，不能都加进销售费用再重复扣除。原因自述不是独立因果。')
src('E08','2025后验原披露与预测基期',[('facts',x) for x in ['R2025-01','R2025-02','R2025-03','R2025-17','R2025-18','R2025-21','R2025-22']],note='2025仅作独立后验与本次新预测基期，不回填2024历史研究的信息集。')
src('E09','2020—2024广义行业年报引述',[('lec03_agent_facts',f'L03-A{y}-I') for y in range(2020,2025)],note='原文由既有授权Agent核准，human_confirmation=false；只证明年报引述，不是同样本连续行业面板，不替代高端酱香分母。')
src('E10','五项核心竞争力与工艺安排',[('m01_disclosure_facts','M01-D01'),('facts','R2016-05')],note='管理层五项标签与至少五年工艺披露可以定位；独立经济效果、不可复制性与持续年数仍分别研究。')
src('E11','2024合同负债与2025金融现金原因自述',[('facts','R2024-08'),('facts','R2025-23')],note='合同负债为时点余额，不等于销量或消费需求；公司对CFO下降的说明只是已披露原因，不能排除其他因素。')
src('E12','2008期初重分类及资本年度桥接',[('facts','R2008-05'),('facts','R2008-06')],rel='work/cash-20261024/calculations.json',note='632,936,687.20元的预付款/CIP重分类由B17原文确认，调整后期初与2007原报分别保留；非现金释放。')
# Explicitly include B17 facts rather than treating the calculation cache as proof.
b17=load('work/review-batches/20261025-B17.json')
dep('work/review-batches/20261025-B17.json')
src('E13','当前合同与已有认可边界',[],rel='docs/20261025-contract-overview.md',note='本图册是用户2026-10-25要求的新研究扩展稿，P04等旧受审成果冻结，不把旧认可转移到新预测。第五主稿updated=2026-10-10，第六七2026-10-21。')
src('E14','产能、资产与项目时间桥',[],rel='outputs/student-capacity-capital-bridge.md',note='只据当前有效原数观察设计能力、实际产出、预计释放及资产余额；完整项目现金和成熟回报仍未识别。')
src('E15','已采纳H04及现货语义的历史研究记录',[],rel='work/20261012-supplement/brand-conclusion-revision-20261013.json',note='这里只引用已采纳的有范围研究意见：公司组合ASP不等于固定SKU现货价。完整CSV原件不随图册上传，本图册不新增未绑定现货数列。')
industry_dual=load('work/20261012-supplement/industry-separate-calculations-20261013.json');csvrel='sources/library/补充材料/白酒行业_iFinD字段全集_上市以来.csv';csvpath=p/csvrel
assert sha(csvpath)==industry_dual['source_sha256'];dep(csvrel);dep('work/20261012-supplement/industry-separate-calculations-20261013.json')
csvlines=csvpath.read_text(encoding='utf-8-sig').splitlines();headers=next(csv.reader([csvlines[0]]));dualrow=industry_dual['rows'][-1];csv_extract=[]
for role,line in dualrow['source_lines'].items():
 row=dict(zip(headers,next(csv.reader([csvlines[line-1]]))));assert D(row['value'])==D(dualrow[{'current':'current_raw','previous':'previous_raw','reported_yoy':'reported_yoy_percent'}[role]]);csv_extract.append({'role':role,'source_line':line,'id':row['id'],'time':row['time'],'value':row['value']})
src('E17','行业2024双口径：附件同比候选与年报原量',[],rel='work/20261012-supplement/industry-separate-calculations-20261013.json',note='本次实际重读并核CSV当前SHA和三条输入行。S000009429原量414.5/449.2，S000009430材料同比-1.8%；二者相互不覆盖。状态仍为附件候选+Agent复算，旧流程采纳不是新数值Fact；不用此同比填写细分需求或预测分母。')

with localcontext() as ctx:
 ctx.prec=48
 v={i:nums(raw(i)['value'])[0] for i in ['C01','C02','C03','C04','C05','C06','C07','C08','C09','C10','C11','C12']}
 assert v['C03']==v['C01']+v['C04'];assert v['C01']==v['C06']+v['C07'];assert v['C09']==v['C02']+v['C10']
 products={}
 for y in range(2020,2025):products[y]=take('lec03_agent_facts',f'L03-A{y}-B')['data']['products']
 mt24=products[2024][0];mt23=products[2023][0];sr24=products[2024][1];sr23=products[2023][1]
 R=lambda a:D(a['revenue_yuan']);Q=lambda a:D(a['sales_tonnes']);P=lambda a:R(a)/Q(a)
 qeff=(Q(mt24)-Q(mt23))*(P(mt24)+P(mt23))/2;peff=(P(mt24)-P(mt23))*(Q(mt24)+Q(mt23))/2;assert abs(qeff+peff-(R(mt24)-R(mt23)))<D('1e-30')
 calc('A01','ΔQ×(P1+P0)/2',{'Q2024':str(Q(mt24)),'Q2023':str(Q(mt23)),'P2024':str(P(mt24)),'P2023':str(P(mt23))},qeff,'元')
 calc('A02','ΔP×(Q1+Q0)/2',{'Q2024':str(Q(mt24)),'Q2023':str(Q(mt23)),'P2024':str(P(mt24)),'P2023':str(P(mt23))},peff,'元')
 volpct=(Q(mt24)/Q(mt23)-1)*100;asppct=(P(mt24)/P(mt23)-1)*100
 parentmargin=v['C02']/v['C01']*100;allmargin=v['C09']/v['C01']*100
 cost24=nums(raw('N2024-01')['value'])[1]+nums(raw('N2024-02')['value'])[1]+nums(raw('N2024-03')['value'])[1]
 bridge24={'gross':v['C01']-cost24,'tax':nums(raw('R2024-17')['value'])[0],'selling':nums(raw('R2024-09')['value'])[0],'management':nums(raw('R2024-15')['value'])[0],'rd':nums(raw('R2024-16')['value'])[0]}
 bridge24['other_net']=v['C09']-(bridge24['gross']-bridge24['tax']-bridge24['selling']-bridge24['management']-bridge24['rd'])
 # Remaining net includes interest, finance expenses, investment/non-op items and income tax; do not call it one expense.
 c24=next(x for x in cash['panel'] if x['year']==2024);c25=next(x for x in cash['panel'] if x['year']==2025);ch25=channel['panel'][-1];ch24=channel['panel'][-2];mid=channel['midpoint_decompositions'][-1]
 inv=lag['inventory'];i24=inv[-2];i25=inv[-1];flow25=lag['annual_changes'][-1]['metrics']
 inventory_days24=D(i24['finished_tonnes'])/D(flow25['company_shipments']['previous_tonnes'])*365;inventory_days25=D(i25['finished_tonnes'])/D(flow25['company_shipments']['current_tonnes'])*365
 calc('A03','finished year-end tonnes / company annual shipments tonnes *365',{'year':2024,'inventory':i24['finished_tonnes'],'shipments':flow25['company_shipments']['previous_tonnes']},inventory_days24,'期末成品/年出货折算天数；非DIO')
 calc('A04','finished year-end tonnes / company annual shipments tonnes *365',{'year':2025,'inventory':i25['finished_tonnes'],'shipments':flow25['company_shipments']['current_tonnes']},inventory_days25,'期末成品/年出货折算天数；非DIO')
 mtq25,mtship25,srq25,srship25=nums(raw('R2025-01')['value']);mtrev25=nums(raw('R2025-03')['value'])[0];wr25=D(ch25['channel_revenue_sum_yuan']);srrev25=wr25-mtrev25;rev25=D(c25['operating_revenue_yuan']);other25=rev25-wr25
 assert srship25+mtship25==D(flow25['company_shipments']['current_tonnes'])
 # Independent Fraction check of main price-volume decomposition and inventory normalization.
 qr0,qr1=map(Fraction,[Q(mt23),Q(mt24)]);pr0=Fraction(R(mt23))/qr0;pr1=Fraction(R(mt24))/qr1
 assert abs(float((qr1-qr0)*(pr1+pr0)/2)-float(qeff))<.001
 oneasp=mtrev25*D('.01');oneqty=mtrev25*D('.01');onefee=rev25*D('.01')
 central_break_p=1/(D('1.01'))-1

def series_rows(a,b,label):return [{'label':str(x['year']),a:n(x[b]) if x.get(b) is not None else None} for x in label]
chapters=[]
def chapter(id,no,nav,kicker,title,question,thesis,refs,blocks,charts,alternative,falsifier,next,**extra):
 c=dict(id=id,number=no,nav=nav,kicker=kicker,title=title,question=question,thesis=thesis,refs=refs,blocks=blocks,charts=charts,alternative=alternative,falsifier=falsifier,next=next,**extra);chapters.append(c);return c

chapter('overview','00','先读：核心判断','研究总览 / 新增综合观点','从供给扩张，转向需求承接与利润守成','把所有合同放在一起，哪件变化最值得投资者重视？',
 '我的基准判断：茅台仍能把酒类收入中的大部分留在毛利层，但2025年的边际变化更接近“增长承压、销售代价上升”，而非品牌持续强化的直线故事。未来一至三年的关键，是新增和成熟供给能否在不明显牺牲组合价格与费用效率的情况下被承接。',['E04','E05','E06','E08'],[
 block('结论来自相互牵制的三组变化，而不是一个孤立比率',f"2025主营酒类渠道毛利率仍为{f(D(ch25['combined_gross_margin'])*100)}%，说明会计毛利空间依然很厚；但同比下降{f(-D(mid['combined_margin_change_pp']))}个百分点。直销份额提高{f(D(mid['direct_share_change_pp']))}个百分点，本应提供正向结构帮助，实际却被渠道内部毛利率下降抵消。",f"公司成品库存增加39.47%，出货仅增加2.13%；期末成品库存相当于年出货的折算天数由{f(inventory_days24,1)}升到{f(inventory_days25,1)}天。这个值不是会计DIO，却提示同样出货规模背后，公司需要持有更多已完成产品。",'利润仍厚与边际承压可以同时成立。把“仍然赚钱”当作“增长机制没有变化”，会漏掉后者；把库存上升直接当作需求崩塌，也超出了现有证据。',refs=['E04','E05','E08']),
 block('未来的关键约束，可能从“做出来”转向“卖出去并留住利润”','至少五年的生产贮存安排意味着供给决策在需求实现之前作出。需求承接如果弱于原计划，企业可选择调投放、换渠道、调组合或加推广；这些动作会先改变公司ASP、费用和成品库存，再影响现金。我的工作假说是：2025出现了需要更多调节才能完成销售的迹象，接下来应优先验证销售效率，不能只以基酒扩产推演收入。','置信判断：对已经出现的会计结构变化把握较高；对“需求承接是主要原因”的把握中等偏低，因为缺少终端动销、渠道库存和同SKU成交面板。后者是优先假说，并非已确认事实。',refs=['E05','E10','E11'])],[
 chart('四项指标，指向同一研究优先级','2025较2024；不同指标以各自百分比表示，绝不相加。','bar','%',[
 {'label':'营业收入','v':(D(c25['operating_revenue_yuan'])/D(c24['operating_revenue_yuan'])-1)*100},{'label':'公司出货','v':D(flow25['company_shipments']['growth_percent'])},{'label':'成品库存','v':D(flow25['finished']['growth_percent'])},{'label':'合并CFO','v':(D(c25['cfo_yuan'])/D(c24['cfo_yuan'])-1)*100}], [('v','同比变化')],['E05','E06','E08'],'收入和出货的承接速度落后于成品库存；CFO还混有金融资金变化，因此不能把四项直接串成已证实因果。','同比=(本期−上期)/上期×100'),
 chart('增长之外，要看利润和现金怎样分化','合并全体净利润与合并CFO；范围保持一致。','bar','亿元',[{'label':str(y),'np':yi(row['net_profit_yuan']),'cfo':yi(row['cfo_yuan'])} for y,row in [(2024,c24),(2025,c25)]],[('np','合并净利润'),('cfo','合并CFO')],['E06','E08'],'现金下降明显快于利润，必须走调节表和金融范围桥接，而非直接宣布盈利质量恶化。')],
 ['也可能是投放与期末备货节奏','如果2025成品上升主要是主动备货，后续应看到库存回落、公司组合ASP稳定、销售费用率下降；这会削弱“承接压力加大”的解释。'],
 ['库存与费用改善而净价保持','连续后续报告显示成品/出货比恢复、公司量价同步改善、费用率回落，且终端成交和渠道库存支持，就应转向更积极的修复判断。'],
 '先读第五次四环及三项延伸，再看第六七次如何裁决品牌解释，最后在预测实验室修改假设。',
 flow=[['收入','产品组量价和渠道结构'],['毛利与费用','增加销售究竟留下多少'],['库存与资本','成熟供给能否被承接'],['现金','经营与金融资金分开'],['预测','条件路径与反证反馈']])

chapter('task01','01','第一次 · 披露地图','第一次合同 / 找到正确入口','同一份年报，回答的是几种不同问题','哪些披露能用于理解公司，哪些数字看着相近却不能替换？',
 '第一次合同的核心成果是一张可追索的披露地图。对投资分析最关键的启发是：先确定研究主体与索取权，再谈增长；集团营业收入、母公司收入和归母利润并不是一组可任意拼接的数字。',['E01'],[
 block('先明确研究对象：集团经营，还是母公司股东所得',f"2024集团营业收入为{f(yi(v['C01']))}亿元；母公司个别营业收入为{f(yi(v['C05']))}亿元。差距来自主体和合并体系的不同，不能把两者相除当成新增外部收入。合并全体净利润为{f(yi(v['C09']))}亿元，其中归母{f(yi(v['C02']))}亿元、少数股东{f(yi(v['C10']))}亿元。",'需要解释公司经营时，收入、成本、现金应以同范围合并数据搭桥；要解释母公司股东盈利时，转到归母口径。第一步选错，后面的利润率、现金转换和估值都会带偏。',refs=['E01']),
 block('披露地图如何服务后续任务','业务概要与经营讨论回答生产和销售怎样组织；产品/渠道表解释收入和成本的切面；财务附注澄清科目含义；风险与关联交易提示利润归属、费用和资金边界。审计报告和会计政策用来辨认比较基数及跨期断点。','这是从“找到数字”到“找准问题”的入口。原第一合同的披露地图、异常线索和核验记录继续保留；本章的研究含义是按最新用户授权新增，不改写旧训练阶段只定位的成果。',refs=['E01','E13'])],[
 chart('合并与个别报表的规模不同','2024年度；不同主体并列，只展示边界差异。','bar','亿元',[{'label':'集团营业收入','v':yi(v['C01'])},{'label':'母公司收入','v':yi(v['C05'])},{'label':'合并净利润','v':yi(v['C09'])},{'label':'归母净利润','v':yi(v['C02'])}],[('v','披露值')],['E01'],'这是口径识别图，不是主体之间的增长或效率比较。')],
 ['“名称相近就是同一个数”会带来系统偏差','例如以集团CFO除归母利润，会将少数股东利润从分母删掉；以母公司收入作集团费用率分母，也会人为放大比率。'],['来源或合并边界改变','一旦报告版本、表头、重述或合并范围变化，应重建受影响指标，不能只复制旧披露地图。'],'后续每项计算先写“谁的什么指标、什么期间、什么单位”，再代入公式。',deliverables=['原披露地图与线索：outputs/first-analysis.md；work/notes.md；work/pending-checks.md。','历史原值与真实核验继续以ReviewStore和当前来源绑定为准；本报告没有新增亲查或签署。'])

chapter('task02','02','第二次 · 收入结构','第二次合同 / 结构化提取','收入主要靠茅台酒，但渠道是另一张切面','卖什么、通过什么渠道卖，怎样共同决定收入？',
 f"2024茅台酒占集团营业收入{f(R(mt24)/v['C01']*100)}%，是核心收入和利润来源；其他系列酒提供第二组收入，但吨均收入和毛利率明显不同。产品、渠道、地区是同一收入的不同切面，不能把直销再加到产品收入上。",['E01','E02','E04'],[
 block('先结构化，再做经济解释',f"2024茅台酒收入{f(yi(R(mt24)))}亿元，其他系列酒{f(yi(R(sr24)))}亿元，其他业务{f(yi(v['C07']))}亿元。前两项构成酒类主营业务，再加其他业务才等于公司营业收入；金融利息另进营业总收入。",'公司收入对茅台酒产品组高度集中意味着：茅台酒量价或渠道政策的小变化，比小业务的高增速更容易左右总结果。这是由权重推导的敏感度判断，并非说全部收入都由飞天53°500ml单品贡献。地区切面与具体客户场景仍需单独证据，不能把产品集中度当客户集中度。',refs=['E01','E02']),
 block('销量相近不代表经济贡献相近',f"茅台酒2024公司组合ASP为{f(P(mt24)/10000)}万元/吨，系列酒{f(P(sr24)/10000)}万元/吨。将不同价位产品的吨数直接合成，会让整体ASP同时受产品权重变化影响。理解增长必须至少分两组看量价。",'原结构化表保存所有候选和定位。报告突出能改变判断的结构，未采用的候选不会因未展示而被删除。',refs=['E02'])],[
 chart('产品结构：核心在哪里','2024集团营业收入拆分，金融利息不在本图。','stack','亿元',[{'label':'2024','mt':yi(R(mt24)),'sr':yi(R(sr24)),'other':yi(v['C07'])}],[('mt','茅台酒'),('sr','其他系列酒'),('other','其他业务')],['E01','E02'],'主要暴露在茅台酒产品组，不能用小业务增长替代对核心产品的研究。','收入按产品相加，与C01核对；分项残差0。'),
 chart('同为一吨，单位收入差别很大','匹配销售收入÷公司销量；不是固定SKU终端价格。','bar','万元/吨',[{'label':'茅台酒','v':P(mt24)/10000},{'label':'其他系列酒','v':P(sr24)/10000}],[('v','公司组合ASP')],['E02'],'系列酒销量扩张可能拉低整体ASP，即使每个产品组自己的ASP没有下降。')],
 ['结构变化可以伪装成“提价”','高价规格占比、直销占比或地区结构改变，都可以抬高组均价，不必发生任何同款提价。'],['核心产品组权重出现持续变化','如果系列酒在收入和毛利中的权重持续提高，预测模型应调整产品分层，不能一直只外推茅台酒。'],'按产品组建立量×ASP模型，再用渠道和地区做解释与交叉校验，避免把多维切面重复相加。',deliverables=['结构化候选及完整范围：outputs/revenue-structure-table.md；work/revenue-structure-extraction.md。','本章新增分析只使用当前有效披露及已核M01统计量，不把整张候选表批量认定Fact。'])

chapter('task03','03','第三次 · 指标口径','第三次合同 / 选择口径','选对分母，才看得清盈利','集团收入总体、收入组成和股东盈利应分别采用哪些指标？',
 '采用C01描述商品与服务营业收入，C03单列含金融利息的营业总收入，C02描述未扣非归母净利润；C04/C06/C07作为结构项，C12为扣非补充。排除替代用途不等于否定原数值。',['E01'],[
 block('同一利润，换一个分母会产生不同的叙事',f"归母利润÷营业收入为{f(parentmargin)}%，合并全体净利润÷营业收入为{f(allmargin)}%。前者可用于特别定义的股东盈利/收入观察，后者才与合并CFO转换分析的利润范围一致。两项都不能直接当白酒实体净利率。",'C08是财务费用中的利息收入抵减项，不能与营业总收入中的C04利息收入混同。C05/C11为母公司个别报表；C10是少数股东桥接项；C12扣非归母不替代C02。',refs=['E01']),
 block('真实修正比一个漂亮比率更有学习价值','本项目曾保留收入和利润初选冲突，再按表头、主体与归属修正。后续现金、渠道及资本分析同样遵守这个经验：数值本身真实，不代表能回答当前研究问题。','如果讨论证券价值，还需要股本、资本结构、金融资产归属和价格时点。本章不因为已经找到归母利润，就跳成买卖或目标价结论。',refs=['E01'])],[
 chart('收入总体和股东归属各有一座桥','2024；三组分项分别勾稽，不跨桥相加。','bar','亿元',[{'label':'营业收入','v':yi(v['C01'])},{'label':'金融利息','v':yi(v['C04'])},{'label':'营业总收入','v':yi(v['C03'])}],[('v','收入边界')],['E01'],'营业总收入=营业收入+单列金融利息。金融业务使全集团指标与纯酒类经营指标出现距离。','C03=C01+C04；误差0。'),
 chart('合并净利润怎样归属','2024；各利润率的分母固定为C01，仅用于说明范围差异。','stack','亿元',[{'label':'合并净利润','parent':yi(v['C02']),'minority':yi(v['C10'])}],[('parent','归母净利润'),('minority','少数股东损益')],['E01'],'合并现金转换用全部合并净利润，不能漏掉少数股东部分。','C09=C02+C10；误差0。')],
 ['高比率可能只是范围缩小','删去部分利润或资本，不一定发现了高效率，也可能只是把分子与分母拆开。'],['表头或归属发生变化','出现合并范围或会计分类调整时，重核用途与桥接，不依赖相同科目名称。'],'复用当前口径卡，每个新模型都明确收入、利润和资本的范围及各自用途。',deliverables=['当前口径卡：outputs/metric-scope-decision.md；冲突与取舍：work/scope-adjudication.md。','原主指标3项、结构3项、补充1项；C10单列桥接，未混入七项采用清单。'])

chapter('task04','04','第四次 · 年度变化','第四次合同 / 变化与驱动','2024增长真实，但“为什么增长”要继续拆','什么变化已确认？增长能否直接证明品牌和需求更强？',
 f"2024营业收入同比15.71%、归母净利润同比15.38%已有独立变化确认。把茅台酒收入进一步分解，销量增长{f(volpct)}%、组合ASP增长{f(asppct)}%；收入增长更多由公司销量贡献，不能只讲涨价或品牌增强。",['E02','E03'],[
 block('变化事实是解释的起点',f"以中点法将茅台酒2023→2024收入变化分开：销量项贡献{f(yi(qeff))}亿元，组合ASP项贡献{f(yi(peff))}亿元，两项精确加回收入增量。中点法平均分配量价交互项，避免选先量后价或先价后量导致叙述偏向。",'这里的“销量贡献”是公司出货层面的代数分解；“ASP贡献”仍混含规格、渠道和地区变化。它没有证明终端需求增长，也没有识别同款提价效果。',refs=['E02','E03']),
 block('2025改变了外推起点',f"茅台酒2025销量增长{f((mtship25/Q(mt24)-1)*100)}%，收入增长{f((mtrev25/R(mt24)-1)*100)}%，推得公司组合ASP变化{f((mtrev25/mtship25/P(mt24)-1)*100)}%。这比把2024两位数增速一路外推更值得重视。",'2025是事后观察，不能反过来声称2024时已经知道结果；但本次2026—2028新预测应使用它作为最新有效年度基期。',refs=['E08'])],[
 chart('2024茅台酒增长：量比组合价格更重要','中点法代数贡献，单位亿元；不是因果分摊。','bar','亿元',[{'label':'公司销量项','v':yi(qeff)},{'label':'组合ASP项','v':yi(peff)}],[('v','收入增量贡献')],['E02','E03'],'增长更多来自出货增加；将它直接归因于品牌定价权会跨过证据边界。','ΔR=ΔQ×(P1+P0)/2+ΔP×(Q1+Q0)/2；代数残差0。'),
 chart('销量、收入和ASP在2025不再同速前进','茅台酒产品组；2024 / 2025分别相对前一年。','bar','%',[
 {'label':'2024','q':n(volpct),'r':n((R(mt24)/R(mt23)-1)*100),'p':n(asppct)},
 {'label':'2025','q':n((mtship25/Q(mt24)-1)*100),'r':n((mtrev25/R(mt24)-1)*100),'p':n((mtrev25/mtship25/P(mt24)-1)*100)}],[('q','公司销量'),('r','产品收入'),('p','组合ASP')],['E02','E08'],'增速放缓和ASP承压提示重新设预测基准，而不是自动证明长期品牌失效。')],
 ['一次增速放缓不等于永久衰退','主动调整投放、渠道变化和年度组合也能造成单年放缓。需要后续量价、成品库存及费用共同验证。'],['量价和现金同时重新加速','后续同范围量价增长恢复且库存、费用不恶化，应提高修复情景权重；反之降低基准增长假设。'],'从同比记录转向变化机制卡：每项异常写传导链、替代解释和下一年度可检验结果。',deliverables=['CH01/CH02使用ReviewStore.change_facts()独立重检，未仅凭原值Fact推定变化已确认。','原第四合同结果继续保留；本章量价推理属于按最新授权增补的研究层，不回写原训练成果。'])

chapter('task05','05','第五次 · 商业模式','第五次主合同及历史两版 / 四环与价值解释','一台用时间形成供给、靠价格和渠道获取利润的机器','它为谁创造什么价值，如何交付，又怎样留住经济收益？',
 '我的解释是：公司将生产工艺、长期贮存与产品组合转成可交付酒品，通过品牌识别与稀缺感降低部分客户选择的不确定性，再以批发和直销实现价值获取。高毛利证实已获取的会计价差很厚；未来是否还能维持，取决于客户承接和销售代价，而非仅由生产时间决定。',['E02','E04','E05','E07','E10'],[
 block('价值创造：产品之外，还可能是识别与信任','核心消费价值可能包括饮用品质、品牌识别、社交场景中的认知共识。后两者可以解释“为什么部分客户愿付高价”，但现有材料没有客户支付、复购或场景比例面板。因此将它们列为与历史结果相容的客户价值假说，不能宣布每种场景需求已被证明。','工艺安排和半成品占比较高，说明供给依靠前置生产与等待；这使短期复制供给不容易，却尚不足以证明对手无法形成替代品，或等待本身一定产生高经济回报。',refs=['E05','E10']),
 block('价值交付：直销扩大，改变利润被确认的位置','批发商承担分销、客户触达和一定库存资金；直销让上市公司直接确认更多终端链条收入与毛利，也可能增加履约、推广和组织责任。渠道迁移的经济效果需要看拿回的毛利是否超过新增费用与资本。','产品组销售不是最终消费，直销也不天然等于新增需求。若消费者在不同渠道间转移，上市公司收入可能上升，而行业需求并未同幅增加。',refs=['E04']),
 block('价值获取：把收入留成毛利，还要跨过税费、营销和资本',f"2024营业毛利{f(yi(bridge24['gross']))}亿元；税金及附加{f(yi(bridge24['tax']))}亿元、销售费用{f(yi(bridge24['selling']))}亿元、管理费用{f(yi(bridge24['management']))}亿元、研发费用{f(yi(bridge24['rd']))}亿元，均不能因为毛利率高而忽略。其他净项合计{f(yi(bridge24['other_net']))}亿元，包含金融、非经营与所得税等净影响，不当单一费用解释。",'我更看重“高毛利下边际销售代价是否上升”：它直接决定同样的收入增长还能留下多少利润。费用率上升并不单独证明品牌弱化，却会抬高维持增长所需的贡献。',refs=['E01','E07']),
 block('增长的再投资：库存和时间可能比当年购建现金更关键','生产和贮存安排使一部分投入先进入库存，数年后才与收入匹配。仅看购建长期资产现金占收入较低，就称“几乎不需要再投资”，会漏掉营运资本和时间错配。相反，把所有库存增加都当扩张投资也不准确，因为其中可能有正常生产安排或承接不足。','收入三乘数中的公司销量与组合ASP可计算；细分市场需求和份额缺兼容分母，不能拆出份额增长。将这个缺口保留，同时仍可用公司产品量价完成条件预测。',refs=['E05','E06'])],[
 chart('2024高毛利之后，还要经过哪些项目','正向毛利、各扣减项与其他净项并列；此图不是完整利润表瀑布。','bar','亿元',[{'label':'营业毛利','v':yi(bridge24['gross'])},{'label':'税金附加','v':-yi(bridge24['tax'])},{'label':'销售费用','v':-yi(bridge24['selling'])},{'label':'管理研发','v':-yi(bridge24['management']+bridge24['rd'])},{'label':'其余净项','v':yi(bridge24['other_net'])}],[('v','对合并净利润的桥接项')],['E01','E07'],'毛利减税金、销售、管理、研发，再加其余净项，等于合并全部净利润；商标费已含管理费，不另扣一次。','其余净项=合并净利润−(营业毛利−税金附加−销售−管理−研发)；勾稽0。'),
 chart('库存资本强度在上升，购建现金占比却下降','合并账面存货/营业收入为时点强度；购建现金/收入为年度流量强度，两者不相加。','bar','%',[
 {'label':'2024','stock':D(c24['inventory_to_operating_revenue'])*100,'capex':D(c24['capex_to_operating_revenue'])*100},
 {'label':'2025','stock':D(c25['inventory_to_operating_revenue'])*100,'capex':D(c25['capex_to_operating_revenue'])*100}],[('stock','存货/收入'),('capex','购建现金/收入')],['E06'],'低购建支出并不能单独说明增长轻资本；资本可能更多表现为库存占用。')],
 ['毛利优势也可能来自结构、供给与会计范围','高端规格、渠道分工、税费或历史成本可以解释部分结果；缺同业可比反事实，不能把全额利润都归品牌。'],['用更多库存和营销换来收入，但回报持续恶化','若公司ASP弱、成品/出货比升、费用率升并持续挤压可比利润，应降低“优势可扩张”的判断。'],
 '把商业模式转成三个预测变量：产品组公司销量、组合ASP、销售费用率；把库存结构和现金范围作为约束与复盘变量。',flow=[['价值创造','酒品、识别与信任假说'],['价值交付','批发与直销，责任各异'],['价值获取','量价→毛利→税费与费用'],['再投资反馈','前置库存、产能和时间']],deliverables=['本章合并回答第五次综合、第一部分及补充材料3主合同的四环问题；三份历史版本保留各自验收，不混称同一版本。','原四环成果：outputs/task05-business-model-map.md；三项延伸见后续独立章；旧P04四份受审成果不改。','主合同新增Fact与替代解释/Unknown的既有记录复用；本图册没有因新写作而创造一个新Fact。'])

chapter('lag','5A','延伸 · 生产库存销售','第五次延伸 / N02、N05','时间是供给的约束，也可能成为需求错配的放大器','至少五年能否预测销量？库存究竟是有价值的供给，还是压力？',
 '长生产周期与半成品库存主体，支持“增长需要前置安排”的解释；它既能形成供给缓冲，也让错误扩张更难快速纠正。2025成品增长明显快于出货，提示预测要把成熟供给和需求承接分开，不能机械使用“某年基酒×固定比率=五年后销量”。',['E05','E08','E10','E14'],[
 block('N02：有价值供给有支持，但价值要由后续销售实现','至少五年、跨年份勾兑和高半成品占比，使“今年生产即今年销售”的模型失效。时间和储存是实际经营安排；但只有后续销售价格、售出量与现金支持，库存才兑现为经济收益。现有材料没有将每个年份基酒逐批跟到成品及现金。','五组t+5并列只能看是否与长周期安排相容。多个滞后都相关，且k越大样本越少，共同趋势可能造成高r；最高r不能被选为真实成熟期。',refs=['E05','E10']),
 block('N05：扩大供给需要先投入，后收回',f"2025半成品仍占数量库存{f(D(i25['semi_share_percent']))}%。这解释为什么仅用固定资产或当年购建现金判断投入不足：等待中的酒也占用资源。设计产能、按实际产量计的“实际产能”、新项目投产与成熟可售供给分别看，预计释放不当实现。",'2021—2025生产年的t+5为2026—2030，在原FY2025冻结窗内尚未被观察，不写成“没有兑现”。现在做前瞻，可以把它作为供给线索，但不能把单年基酒量直接命名为当年总销量上限：跨年库存可释放，产品与勾兑关系也未定。',refs=['E05','E14']),
 block('一个更能解释变化的指标：成品库存相对公司出货',f"期末成品/全年公司出货×365，由2024的{f(inventory_days24,1)}天升至2025的{f(inventory_days25,1)}天。它是在年末存量和全年流量间做规模标准化，不是平均库存周转天数，更不是终端渠道库存天数。",'我的推断是：已经完成的产品相对年销售规模变多，短期供给调节负担可能上升。也可能是跨年包装或备货时点，因此下一报告的成品回落和ASP/费用表现，比再增加一个相关系数更能区分机制。',refs=['E05','E08'])],[
 chart('库存主要还在生产与等待中','2016—2025公司数量库存，成品与半成品分开。','stack','万吨',[{'label':str(x['year']),'fin':D(x['finished_tonnes'])/10000,'semi':D(x['semi_finished_tonnes'])/10000} for x in inv],[('semi','半成品含基础酒'),('fin','成品酒')],['E05'],'半成品是主体；图中不能把半成品全称为当年可售成品，FY2015成品口径不接入。','原独立总量−两分项=0吨，十年全部成立。'),
 chart('成品库存相对出货规模明显抬高','年末成品吨数÷全年公司出货吨数×365。','bar','折算天数',[{'label':'2024','v':inventory_days24},{'label':'2025','v':inventory_days25}],[('v','期末成品/年出货')],['E05','E08'],'这比只说库存增加更贴近承接能力；仍不等于会计DIO或终端动销。','A03/A04；分母为公司两产品组销量之和，非产量。'),
 chart('滞后越长，样本越少：不要挑最高r','茅台酒基酒与后续销量；每柱标签显示k与实际n。','bar','相关系数',[{'label':f"k{x['lag']} n{x['n']}",'v':D(x['r'])} for x in lag['diagnostics'] if x['product']=='茅台酒'],[('v','Pearson r')],['E05'],'共同上升趋势和小样本使高相关不足以解释生产成熟期；缺年按真实年份配对。',domain=[0,1],axis_precision=2,precision=3)],
 ['主动备货，未必滞销','若成品增加是投放节奏安排，后续减少成品库存不必靠降价或加营销，现金也可能回归。'],['库存继续积累且组合价格与销售效率恶化','连续出现成品/出货比升、ASP跌、费用率升，应下修有价值供给的兑现速度；反向改善则提高兑现假设。'],'取得同范围库龄、成熟可售量与后续成品变化，和公司ASP/费用共同跟踪；不把基酒单年量当销量硬上限。',deliverables=['G0材料25份PDF/25份MD技术配对、G1定义断点、G2独立总量、G3五组配对、G4 16项相关诊断、G5项目数字桥均保留在原底稿。','G6已采纳有范围意见继续有效；完整项目归因与教师版本批准未因此完成。','原成果：outputs/student-lag-check.md；student-lag-diagnostics.csv；student-capacity-capital-bridge.md；生产库存销售滞后复算.xlsx。'])

chapter('channel','5B','延伸 · 渠道净贡献','第五次延伸 / N03','直销拿回毛利，却没有自动改善整体毛利率','直销多了，是否就一定更赚钱？',
 f"2025直销份额升到{f(D(ch25['direct_share'])*100)}%，但渠道加权毛利率下降{f(-D(mid['combined_margin_change_pp']))}个百分点。我的判断是：渠道结构迁移确实有毛利算术帮助，然而渠道内部盈利率与公司销售费用的变化更值得警惕；不能用更高直销份额直接预测净利率上升。",['E04','E07','E08'],[
 block('这次到底是谁在抵消谁',f"中点分解显示，2024→2025渠道组合效应为+{f(D(mid['mix_effect_pp']))}个百分点，渠道内部毛利率效应为{f(D(mid['within_channel_margin_effect_pp']))}个百分点，两者合计{f(D(mid['combined_margin_change_pp']))}个百分点。也就是说，假如只看渠道迁移，会漏掉方向相反而且更大的另一项。",'渠道内部毛利率下降可来自产品组合、确认价格、成本或分类，现有表不能唯一归因。它不证明直销政策导致损失，但足以反驳“只要直销多就会自动提高整体毛利率”。',refs=['E04']),
 block('毛利之后，还要算新增销售责任',f"公司销售费用率从2024的{f(D(c24['operating_revenue_yuan']) and D(channel['observations_2025']['sales_expense_rate_2024_percent']))}%升到2025的{f(D(channel['observations_2025']['sales_expense_rate_2025_percent']))}%。在2025收入规模上，费用率每提高1个百分点，年费用约增加{f(yi(onefee))}亿元。",'这是一项公司级敏感度，不将费用机械按收入分给渠道。净贡献方向仍缺渠道费用、履约、回款和库存归属，但研究决策不应停在“Unknown”：在取得归属前，应让预测中的直销扩张同时接受费用压力测试。',refs=['E04','E08']),
 block('定义断点和表格差异会影响解释','2016是本次渠道分表起点，2022起直销含自营及i茅台；全窗与分段相关方向不稳定，因此不能用单一r证明直销压低或抬高费用。2025附注相对主营渠道表收入多0.6352亿元、成本多0.8638亿元，来自范围差异，不能拿它反推i茅台手续费。',refs=['E04'])],[
 chart('直销成为更大的收入入口','2016—2025主营酒类口径；2022定义扩展。','line','%',[{'label':str(x['year']),'v':D(x['direct_share'])*100} for x in channel['panel']],[('v','直销收入份额')],['E04'],'2016—2021与2022以后须结合定义分段；趋势图展示披露份额，不证明同一种服务份额的无缝连续增长。',domain=[0,100]),
 chart('结构帮助，仍被渠道内部变化抵消','2024→2025；三项为毛利率百分点的代数关系。','waterfall','pp',[{'label':'组合效应','v':D(mid['mix_effect_pp'])},{'label':'内部效应','v':D(mid['within_channel_margin_effect_pp'])},{'label':'合计变化','v':D(mid['combined_margin_change_pp'])}],[('v','毛利率变化')],['E04'],'这张图给出“为什么看直销占比会误判”的直接证据；效应是代数命名，不是净因果估计。','ΔG=Δs×(gD均值−gW均值)+s均值×ΔgD+(1−s均值)×ΔgW。',axis_precision=1),
 chart('公司费用率走高，直销毛利率不代表到手利润','2016—2025公司销售费用/营业收入；不分摊至渠道。','line','%',[{'label':str(x['year']),'v':D(x['sales_expense_rate'])*100} for x in channel['sales_expense_inputs']],[('v','公司销售费用率')],['E04'],'直销与费用的全窗相关r=-0.2533，前段n6为-0.5815、后段n4为+0.9485；窗口敏感而非因果。',domain=[0,6],axis_precision=1)],
 ['产品组合或成本变动，不一定是直销效率恶化','只有渠道内固定产品净价、成本与增量费用桥，才能区分渠道经营能力与产品结构影响。'],['渠道归属净现金贡献改善','若可比产品下直销新增毛利覆盖新增费用与资金占用，且持续成立，可上调净贡献判断；若费用和库存吸收大部分毛利，则下调。'],'先用公司费用率做预测敏感性；有渠道归属数据后替换，不能把按收入分摊的费用伪装成实际归属。',deliverables=['已完成份额、毛利、毛利差、中点分解、n/r分窗及主营/附注范围桥。','原渠道N03认可保留；本章新的研究优先级与Forecast不继承旧采纳。原结果：outputs/student-channel-conclusion.md。'])

chapter('cash','5C','延伸 · 现金与资本','第五次延伸 / N06、N07','厚利润不等于可分配现金，高代理回报也不是答案','利润兑现了吗？扩张是不是仍然创造高回报？',
 'N06：合并层面长期有显著经营现金，但2025转换转弱，需要分解经营周转与金融资金。N07：前置库存和时间资本确实重要；旧账面资本代理很高，只能暴露范围和成熟期问题，不能据此承诺未来扩张回报。',['E06','E11','E12'],[
 block('N06：长期与单年可以给出不同信号',f"2016—2025连续十年合并CFO累计{f(yi(cash['continuous_2016_2025_diagnostics']['sum_consolidated_cfo_yuan']))}亿元，合并净利润累计{f(yi(cash['continuous_2016_2025_diagnostics']['sum_consolidated_net_profit_yuan']))}亿元，两者比值0.9414。2025单年只有0.7212，并非整段累计比例那么平稳。",'2025调节表从853.10亿元净利润，经三类营运现金调整-248.74亿元及其他列示调整+10.86亿元，回到615.22亿元CFO，残差0。公司另说明财务公司吸收成员存款减少和受限同业存款增加，说明金融资金需要单列；不能把列示金融净额直接当完整子公司贡献。',refs=['E06','E11']),
 block('N07：当前资本代理不足以证明成熟扩张回报','2007—2011选择科目资本从43.45亿元到85.89亿元；五年平均资本口径利润代理收益率很高，但历史成本、经营分类、金融损益、有效税率与成熟期均未被完全解决。112%、148%等公式结果不能被换个名字当真实ROIC。','2007→2011期末选定资本变化42.45亿元，只是余额差；它不是五年累计现金再投资。净资本投入应沿现金、折旧、营运资本、分类和项目成熟过程建立，不允许用一个端点差冒充全部投入。',refs=['E06']),
 block('两次口径修正直接改变研究含义','第一，财务公司2012已并表、2013正式营业，因此主代理窗口为2007—2011，2012独立敏感性。第二，2008年初将6.3294亿元从在建工程调入预付款，选择资本总额不变，但NCWC分项和年变动会变；未桥接就会把分类当资金释放。原数及旧算法保留并注明差异。','现金公式的关键纠错：从CFO减购建长期资产现金得到的算术余量，不再次扣已经进入CFO的ΔNCWC，也不改称实体FCFF、股东可分配现金。',refs=['E06','E12'])],[
 chart('十年现金转换并不恒定','2016—2025合并CFO÷合并全体净利润。','line','倍',[{'label':str(x['year']),'v':D(x['cash_conversion'])} for x in cash['panel'] if x['year']>=2016],[('v','现金转换比率')],['E06'],'不能仅以某年大于1认定质量更高，也不能把2025下降全部归结于消费需求。',axis_precision=1),
 chart('2025利润怎样走到现金','调节表列示金额的合并桥；原表空白保持空白，未冒充披露0。','bar','亿元',[{'label':'合并净利润','v':yi(cash['cash_reconciliation_2025']['net_profit_yuan'])},{'label':'营运调整','v':yi(cash['cash_reconciliation_2025']['listed_working_capital_cash_adjustments_yuan'])},{'label':'其余调整','v':yi(cash['cash_reconciliation_2025']['other_listed_adjustments_yuan'])},{'label':'合并CFO','v':yi(cash['cash_reconciliation_2025']['reported_cfo_yuan'])}],[('v','现金调节')],['E06'],'前三项相加=最后一项；这条桥是会计勾稽，不是单独识别客户需求。','净利润+营运调整+其余调整=CFO；残差0。'),
 chart('资本余额沿年度增长，未被冒称现金投入','2007—2011选择科目年末资本；逐年不是端点插值。','bar','亿元',[{'label':str(x['year']),'v':yi(x['selected_end_capital_yuan'])} for x in cash['annual_selected_capital_path']['panel']],[('v','选择科目期末资本')],['E06','E12'],'2008期初重分类合计守恒；图展示代理余额，不是实体资本或项目投资额。')],
 ['金融现金管理，而非白酒经营恶化','财务公司存贷款与同业变化可能是CFO下降的重要因素；需要完整单体现金和抵销，不能只凭公司一句说明归因全部。'],['实体口径利润与现金仍同步恶化','在剔清金融和重分类后，若现金仍持续弱于利润且存货/应收周转变差，就应降低经营现金兑现假设。'],'优先取白酒实体/财务公司单体现金和抵销、存货库龄与资本用途；九个缺有效字段年按影响补齐，不为凑25年先填零。',deliverables=['四项基础比率、NCWC选择科目、2007—2011年度代理、2012独立敏感性与2008桥接见当前现金计算包。','多年端点诊断已计算，但成熟累计现金再投资与真实增量回报仍未识别。2007/2008/2012/2013/2020断点分别处理。','原合同误写2013首并表的冲突保留SC34；原现金工作簿只截至B12，不冒称含全部后续补充。'])

industry=[(y,take('lec03_agent_facts',f'L03-A{y}-I')['data']['industry']) for y in range(2020,2025)]
ind23=D(industry[-2][1]['production_wan_kl']);ind24=D(industry[-1][1]['production_wan_kl']);indnaive=(ind24/ind23-1)*100
calc('A05','(414.5/449.2−1)×100',{'2024':'414.5万千升','2023':'449.2万千升'},indnaive,'%跨年原值算术；非固定样本同比')
chapter('task06','06','第六次 · 行业与品牌','第六次合同 / 五步与一项优势','品牌有解释力，核心矛盾却已转向兑现','竞争边界在哪里？优势究竟能支持多大、多久和多少扩张？',
 '我把品牌作为优先解释假说，而不把五项竞争力合称已证实护城河。核心矛盾暂定为：公司能否在更弱的数量环境和供给逐步成熟时，维持高价产品承接并保留利润。该判断比“高毛利所以品牌强”更具体，也能被后续量价、库存和费用推翻。',['E02','E04','E05','E09','E10'],[
 block('第一步定边界，第二步给出有条件阶段判断','研究边界沿已认可范围：中国大陆高端酱香，飞天53°500ml为价格观察焦点；其他高端白酒是替代比较对象。公司产品组、全国规模以上白酒和这一细分市场不相等，数字价格带、客户结构和兼容市场分母仍缺。','对于广义环境，我倾向“数量增长压力下的存量利润争夺”这一工作判断；依据是年报引述产量水平回落，而非直接认定目标细分市场处于衰退。生命周期的精确阶段仍缺需求、进入退出和集中度面板，保留未定。',refs=['E09','E13']),
 block('双口径继续保留，不能挑更符合故事的一种','2024行业产量由相邻年原值414.5/449.2计算下降7.72%；同附件公布同比字段为-1.8%。本次重读CSV哈希及对应输入行，两者均按原状态保留：前者是跨年原量算术，后者是材料原列示同比候选，其统计可比基数尚未重建。','如果仅为演示以2024产量水平外推一年，按-7.72%会得到约382.48万千升，按-1.8%会得到约407.04万千升；两项均是条件推演，不能冒充实际2025产量，也未被用作本次公司产品预测的需求分母。',refs=['E09','E17']),
 block('第三步识别矛盾：谁拿走利润，新增供给由谁承接','公司仍能以高会计毛利获取价值，而直销提高了部分渠道毛利的确认份额。2025结构收益抵不过内部毛利变化，说明价值归属改善不能自动抵消价格、结构或成本压力。品牌作用若要继续兑现，必须能让成熟供给以足够的净价销售，而不是只证明名称被消费者知道。',refs=['E04','E05']),
 block('第四五步：用少量变量验证，而不是把风险词堆满一页','第一组看匹配产品量价：出货增长若靠组合ASP持续下降，价值获取可能承压。第二组看成品/出货比：供给先行而销售不足会抬高持有压力。第三组看费用率与同范围利润：为维持销售付出更多，可能吸收渠道拿回的毛利。三组一起观察，单项异常只触发复查。',refs=['E02','E04','E05']),
 block('品牌五环与护城河三问的明确回答','来源是被识别的品牌及长期产品体系；候选机制是降低选择不确定性、提高支付意愿；结果证据为高产品组单位收入和毛利，辅以已认可H04中的价量挑战；模仿障碍可能来自时间、认知和渠道积累，但尚未独立量化；反证是净价/出货承接弱化且销售成本上升。','优势多大：会计毛利空间大，独立品牌溢价金额不知。持续多久：没有证据支持填固定年数。扩张后能否维持：2025已出现需要降低乐观外推的线索，基准预测采用低增速和ASP压力，而非永续历史增速。',refs=['E02','E04','E10','E15'])],[
 chart('广义行业数量环境偏弱，但不能拼成同样本增长','年报引述规模以上白酒产量；独立柱不连线，不代表细分市场容量。','bar','万千升',[{'label':str(y),'v':D(a['production_wan_kl'])} for y,a in industry],[('v','原文年度水平')],['E09'],f"2024/2023相邻原值算术为{f(indnaive)}%，不同于原统计公布同比口径；两种算法须并存，不能用这个序列算公司细分份额。",'A05仅相邻原值算术。行业原公布同比与跨报告基数不同，旧双口径继续分别保留。'),
 chart('核心产品在2025明显放慢','茅台酒公司销量；非终端消费者销量。','line','万吨',[{'label':str(y),'v':Q(products[y][0])/10000} for y in range(2020,2025)]+[{'label':'2025后验','v':mtship25/10000}],[('v','茅台酒公司销量')],['E02','E08'],'2025销量接近持平，让未来增长更依赖价格/组合恢复或新承接，而不是自然延续两位数增量。')],
 ['高利润可能来自产品、渠道或成本，而非纯品牌','无同范围反事实，不能把利润率差全算品牌；教师包中的五家公司候选排名和旧挂牌价比不直接升为本项目Fact。'],['同规格净价弱化且销售成本上升','如果承接依赖持续降组合ASP、加费用并累成品，品牌“可扩张性”应下修；若净价稳、库存降、费用回落则上修。'],'交给第七次：将“核心竞争力未发生重大变化”拆成可检验机制，主动寻找与增长承接压力一致的反方证据。',matrix={'headers':['五步','当前回答','未解决的关键证据'],'rows':[['定边界','大陆高端酱香；高端白酒可替代','数字价格带、客户场景与兼容分母'],['分阶段','存量利润争夺的工作假说','细分需求与集中度面板'],['找矛盾','成熟供给承接与利润保留','终端动销、渠道库存'],['验逻辑','量价×成品库存×费用','固定规格实际成交与费用归属'],['防风险','三组指标联动反证','持续性而非单年方向']]},deliverables=['新版原五步表与品牌链已获P04增量认可；本章新综合判断与预测另为研究扩展稿。','完整行业缺口满足可操作交接，但未拿管理层自述或广义总量冒充细分市场独立Fact。'])

chapter('task07','07','第七次 · 叙事核验','第七次合同 / 一条具体叙事','“核心竞争力未变”，不等于经济效果未变','管理层列出的品质、品牌、工艺、环境、文化，能证明什么？',
 '最大可辩护表述是：公司维持了高毛利产品体系和长周期生产安排，品牌与时间资本是有解释力的候选机制；但五项标签不能打包证明未来定价权和扩张回报。即使能力载体仍在，需求环境改变也可能降低这些能力的经济兑现程度。',['E10','E07','E04','E05'],[
 block('把一句话改写成可反驳的经济命题','原文在2024年报第8、20—21页提出五项核心竞争力及“未发生重大变化”。需区分两层：公司仍具有这些安排或载体；这些安排仍能以相似净价、销售效率和资本回报转化为经济收益。前者存在，不自动证明后者稳定。','我的新见解是：最值得测试的不是“五个名词还在不在”，而是“同样的能力，面对变化后的需求和渠道，是否还能换回同样的净经济结果”。这把静态能力叙事转成了预测问题。',refs=['E10']),
 block('正反证据怎样一起改变判断','正面是高产品组单位收入和毛利、长生产贮存安排；挑战是2024费用增长、2025渠道内部毛利下滑、成品相对出货提高。它们不证明品牌消失，却足以限制“全面持续增强”的说法。','替代机制依次包括规格/渠道组合、供给投放、成本税费/会计分类、公司出货与最终消费的差异。下一步分别取得固定SKU净价、成熟量和配额、成本税费桥、终端及渠道面板，避免用同一份数据为所有标签背书。',refs=['E02','E04','E05','E07']),
 block('代理评级不能变成新的确定性','公司销量对“公司出货”是匹配变量，对“终端消费”只是边界代理；费用金额对“费用”是准确输入，对“品牌经济效果”仅能旁证。S0—S4评级描述目标距离，不把算式算对就一律升S1。','研发、专利、资产和推广可扩展投入或能力载体的可观察性，但仍需后续结果连接。预测可以基于假设先做；独立因果、持续期或终端指标缺口不能因此被抹掉。',refs=['E07','E10'])],[],
 ['能力未变，但外部需求和销售路径改变','这可能比“品牌突然失效”更符合当前证据：能力存在，边际兑现变难。应预测兑现程度而非简单给能力贴真/假标签。'],['固定SKU及渠道证据支持兑现恢复','如果同规格实际净价、终端量、渠道库存及可归属净贡献同步恢复，能力经济效果的怀疑应削弱；反向持续则加强。'],'把本章交给后续财务：检验量价恢复、费用效率、库存兑现和实体现金；将预测误差归回具体机制，而非只修改一个增长率。',matrix={'headers':['标签','当前可支持内容','独立经济效果与预测用途'],'rows':[['品质','公司自述质量安排','支付、复购贡献Unknown；不因研发增加自动提高预测价格'],['品牌','高单位收入、毛利与H04有限意见','候选解释；预测须同时给价格和量的压力路径'],['工艺','至少五年、跨年勾兑和半成品主体','前置供给约束；不能机械t+5映射'],['环境','存在原产地与自然条件叙事','独立成本/品质贡献与复制性Unknown'],['文化','存在文化体系叙事','场景、黏性和复购贡献Unknown']]},deliverables=['本章逐一回答原合同：经济机制、预期结果、支持/挑战、替代解释、最大可辩护表述与反证、财务交接。','原过程稿work/task07-narrative-audit.md及两份lec03受审成果冻结；此HTML不是替代P04权威终稿或新签署。'])

model={'years':[2026,2027,2028],'baseline':{'year':2025,'mt_volume':str(mtship25),'mt_asp':str(mtrev25/mtship25),'sr_volume':str(srship25),'sr_asp':str(srrev25/srship25),'gross_margin':ch25['combined_gross_margin'],'company_revenue':str(rev25),'other_revenue':str(other25),'net_profit':c25['net_profit_yuan'],'selling_expense':str(nums(raw('R2025-18')['value'])[1])},
 'scenarios':{
 'stress':{'label':'压力 · 承接继续走弱','mt_q':[-.03,0,.01],'mt_p':[-.06,-.03,0],'sr_q':[-.05,0,.02],'sr_p':[-.08,-.03,0],'gm_delta':[-.015,-.005,0],'selling_rate':[.052,.053,.05],'retention':[.6,.6,.6],'cash_ratio':[.65,.7,.75]},
 'base':{'label':'基准 · 缓慢消化修复','mt_q':[.01,.02,.03],'mt_p':[-.02,0,.01],'sr_q':[0,.03,.05],'sr_p':[-.04,-.01,0],'gm_delta':[-.005,0,.002],'selling_rate':[.045,.044,.043],'retention':[.6,.6,.6],'cash_ratio':[.72,.85,.94]},
 'recovery':{'label':'修复 · 量价与效率改善','mt_q':[.05,.06,.05],'mt_p':[.01,.02,.02],'sr_q':[.07,.08,.06],'sr_p':[0,.02,.02],'gm_delta':[.002,.002,.001],'selling_rate':[.041,.039,.038],'retention':[.6,.6,.6],'cash_ratio':[.94,1,1.05]}},
 'formula_note':'各年产品组销量Q=上年Q×(1+量增速)，公司组合ASP P=上年P×(1+ASP增速)；酒类收入=茅台酒Q×P+系列酒Q×P；公司营业收入=酒类收入+2025其他业务收入（固定）。酒类毛利率按年度pp变化；净利润桥=2025合并净利润+60%×[本年酒类毛利−2025酒类毛利−(本年销售费−2025销售费)]。其余税费、金融和未建模损益采用基期，60%是增量保留假设而非已核税率。CFO敏感性=条件净利润×设定合并转换率，不是实体经营现金或FCFF。',
 'assumption_note':'全部未来参数为Agent情景假设，不是管理层目标、历史Fact或概率估计。销量低增速和ASP压力以2025放缓、成品/出货上升及毛利/费用变化为方向锚，数值幅度人为设定。2024→2025酒类毛利下降0.7837pp、费用率增加0.9963pp为压力尺度参考；后续回升是条件路径而非均值回归定律。60%增量保留率固定，仅为把未建模税费和其余损益隔离出来的试算；需用完整利润表预测替代。CFO比率沿0.65—1.05试算，0.94参考2016—2025累计0.9414，不能表示未来金融现金已被预测。'}
forecast_results={k:ir.forecast(model,k) for k in model['scenarios']}
base26=forecast_results['base'][0];stress26=forecast_results['stress'][0];rec26=forecast_results['recovery'][0]
base28=forecast_results['base'][-1]
sens_asp=oneasp*D(ch25['combined_gross_margin'])*D('.6');sens_fee=onefee*D('.6')
chapter('forecast','08','预测 · 2026—2028','预测扩展 / Forecast · Agent假设','把判断落到可以检验的未来路径','未来三年，什么变化会令收入和利润上修或下修？',
 f"我的基准是缓慢消化，而非立即回到历史高增长。条件模型给出2026营业收入约{f(yi(base26['revenue']),1)}亿元，2028约{f(yi(base28['revenue']),1)}亿元；2026压力至修复路径约{f(yi(stress26['revenue']),1)}—{f(yi(rec26['revenue']),1)}亿元。这是参数条件下的区间，不是概率区间，更不是已敲定的业绩或估值。",['E04','E05','E06','E08'],[
 block('为什么选这个基准，而不是照搬历史增速','2025已经出现核心产品销量放缓、组合ASP承压、成品库存相对出货升高、费用率上升，因此基准先假设2026茅台酒量增1%、ASP降2%，系列酒量持平、ASP降4%；2027—2028仅作逐步恢复。这一方向比直接延续2024两位数增速更符合最新有效观测。','具体1%、-2%等不是统计识别出来的真参数，而是可审阅的研究设定：它们将“库存消化需要时间、价格仍有压力”的解释变成可检验结果。压力情景加深量价与费用负担，修复情景要求量价和费用同步改善；没有为情景指定概率。',refs=['E04','E05','E08']),
 block('利润预测使用桥接，主动暴露模型少了什么','模型以2025合并净利润为锚，按新增酒类毛利减新增销售费用，再保留60%形成条件净利润。60%不是税率Fact，只是未建模税费/损益的情景简化；金融收入、管理研发、投资与非经营净项等维持基期假设，若显著变化必须重建完整利润表。','CFO单独以条件净利润乘设定转换率作敏感性，不能从它推实体FCFF或可分配现金。当前没有用股价、股本、WACC等参数估目标价；这不妨碍先把经营前景量化。',refs=['E06','E08']),
 block('最有用的敏感度：价格与费用的小变化能否吃掉增长',f"在2025茅台酒收入基数上，组合ASP变动1%大约对应{f(yi(oneasp))}亿元收入；若沿基期酒类毛利率及60%增量保留假设，对条件利润约影响{f(yi(sens_asp))}亿元（未计收入变化导致的费用联动）。公司销售费用率提高1个百分点，在同样公司收入规模上多支出{f(yi(onefee))}亿元，对条件利润约影响{f(yi(sens_fee))}亿元。",f"若茅台酒销量只增1%，要维持该产品组收入不降，ASP最多约下降{f(-central_break_p*100)}%：1.01×(1+ASP变化)=1。基准ASP降2%就意味着单靠这点量增还不够。这个门槛是代数条件，不是市场价格预测。",refs=['E08'])],[],
 ['更快的库存兑现或更强的价格承接','如果成熟供给被更快接走、实际公司ASP稳定且费用率下降，应转向修复路径；只有产量增加不足以切换。'],['量价、库存与费用同时偏离基准','每次新报告按同口径比较实际与预测：先定位量、ASP、产品结构、毛利、费用或金融项中的误差，再更新机制。不能只把增长率调到贴合实际。'],'人机协作下一批优先提供或核查：后续同范围产品销量/收入、成品库存、销售费用、真实成交及终端/渠道库存。先补最能区分机制的数据，不重核已有144项原披露。',forecast=True,
 deliverables=['默认与所有场景精确结果、参数来源、公式和独立复算记录保存在work/research-atlas-20261025。','预测属于本次用户明确授权的研究扩展；旧前四合同的阶段性禁预测条款仍留在原文，不用于否定当前新增工作。'])

# Contract coverage and appendix source links are explicit rather than an implied completion rate.
contract_files=[]
for c in load('work/20261010-contract-map.json')['contracts']:
 rel=c.get('current_executed_copy',c['executed_copy']);dep(rel);contract_files.append({'name':c['file'],'path':rel,'sha256':sha(p/rel),'chapter':{'第一次':'task01','第二次':'task02','第三次':'task03','第四次':'task04'}.get(c['name'],'task05')})
for file in (p/'sources/library/补充材料3').glob('*合同*.md'):
 rel=file.relative_to(p).as_posix();dep(rel);id='lag' if '滞后' in file.name else 'channel' if '渠道' in file.name else 'cash' if '现金' in file.name else 'task06' if '第六' in file.name else 'task07' if '第七' in file.name else 'task05';contract_files.append({'name':file.name,'path':rel,'sha256':sha(file),'chapter':id})
src('E16','逐合同覆盖地图与本轮分析扩展',[],rel=None,note='原合同逐条执行状态与本图册的问题回答分开；本轮把阶段核验成果连接成研究意见，未假称原合同全部正式验收。')
for c in chapters:
 c['contract_refs']=[r for r in contract_files if r['chapter']==c['id']]
 c['deliverables']=c.get('deliverables',[])+[r['name']+' → 本章；原件/执行副本 '+r['path'] for r in c['contract_refs']]
 # JSON cannot contain Decimal values; retain exact values in derived ledger.
 for ch in c['charts']:
  for row in ch['rows']:
   for key,val in list(row.items()):
    if isinstance(val,D):row[key]=float(val)
analysis_rel='work/research-atlas-20261025/chart-analysis.json'
if (p/analysis_rel).is_file():
 annotations=load(analysis_rel);dep(analysis_rel)
 for chapter in chapters:
  for item in chapter['charts']:
   if item['title'] in annotations['charts']:item['analysis']=annotations['charts'][item['title']]
  if chapter.get('matrix') and chapter['id'] in annotations.get('matrices',{}):chapter['matrix']['analysis']=annotations['matrices'][chapter['id']]
spec={'schema_version':1,'company':'贵州茅台','security_code':'600519','date':'2026-10-25','title':'贵州茅台：变化、机制与未来','subtitle':'逐合同的证券投资分析研究图册。先回答问题，再用图表解释变化，最后将判断写进可修改、可复算的未来情景。',
 'snapshot_note':'本页为2026-10-25生成的离线研究快照。原披露Fact144项，独立域分列且不合计；新增分析为Interpretation，未来参数与结果为Forecast，均未自动人审或签署。工作台打开时重新校验源绑定；离线副本不会自动感知后续文件变化。',
 'chapters':chapters,'sources':sources,'authority':list(used.values()),'dependencies':list(deps.values()),'forecast':model,'forecast_results':forecast_results,'contract_coverage':contract_files,
 'fact_domain_counts':{k:len(v) for k,v in domains.items()},'new_human_confirmations':0,'new_signature_created':False}
out=stage/'company';out.mkdir(exist_ok=True)
def put(rel,text):f=out/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text,encoding='utf-8',newline='\n')
def jput(rel,value):put(rel,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
jput('work/research-atlas-20261025/report-spec.json',spec);jput('work/research-atlas-20261025/derived-calculations.json',derived);jput('work/research-atlas-20261025/forecast-results.json',{'state':'Forecast','model':model,'results':forecast_results})
jput('work/research-atlas-20261025/industry-dual-check.json',{'csv_sha256':sha(csvpath),'selected_rows':csv_extract,'state':'附件候选与Agent计算，不是新增人工Fact','raw_path_2025':str(ind24*(1+indnaive/100)),'reported_yoy_path_2025':str(ind24*(1+D(dualrow['reported_yoy_percent'])/100))})
jput('work/research-atlas-current.json',{'spec_path':'work/research-atlas-20261025/report-spec.json','state':'研究扩展稿，新增观点和Forecast待人工最终裁决','date':'2026-10-25'})
put('outputs/证券投资分析研究图册.html',ir.render(spec,source_url=lambda x:'../'+x))
for c in chapters:put('outputs/research-atlas/'+c['id']+'.html',ir.render(spec,c['id'],source_url=lambda x:'../../'+x))
put('outputs/research-atlas/README.md','# 逐合同研究图册\n\n2026-10-25。主入口：[综合图册](../证券投资分析研究图册.html)。\n\n'+'\n'.join('- ['+c['kicker']+'：'+c['title']+']('+c['id']+'.html)' for c in chapters)+'\n\n原始Fact权威不变。新观点和预测是待人工最终裁决的研究扩展稿，未转移旧P04等认可或旧签名。\n')
put('outputs/证券投资分析研究意见.md','# 贵州茅台：变化、机制与未来\n\n2026-10-25 · 研究扩展稿。\n\n'+ '\n\n'.join('## '+c['kicker']+'\n\n'+c['thesis']+'\n\n'+'\n\n'.join('### '+b['title']+'\n\n'+'\n\n'.join(b['paragraphs']) for b in c['blocks'])+'\n\n替代解释：'+c['alternative'][1]+'\n\n反证：'+c['falsifier'][1] for c in chapters)+'\n')
print(json.dumps({'chapters':len(chapters),'html_pages':len(chapters)+1,'charts':sum(len(x['charts']) for x in chapters),'used_authority_records':len(used),'dependencies':len(deps),'scenario_revenue_2026_yi':{k:f(yi(v[0]['revenue'])) for k,v in forecast_results.items()},'stage':str(out)},ensure_ascii=False))
