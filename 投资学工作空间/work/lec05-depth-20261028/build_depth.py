from pathlib import Path
from decimal import Decimal as D,getcontext
import json,hashlib,sys,re,html,subprocess,time,ast,os
getcontext().prec=48
R=Path('D:/投资学');W=R/'投资学工作空间';B=R/'课件与任务文件/补充材料4';O=W/'outputs';C=O/'02_Lec05叙事与估值';P=W/'work/lec05-depth-20261028'
P.mkdir(parents=True,exist_ok=True)
if (W/'evidence/lec05-content-review.json').exists():raise RuntimeError('已存在真实人审记录；停止覆盖。请编辑当前文档/图册缓存并校验批次语义，不重跑一次性作者程序。')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,t):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding='utf8')
def js(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def git(*a):
 for i in range(20):
  r=subprocess.run(['git','-C',str(R),*a],capture_output=True,text=True,encoding='utf8')
  if 'index.lock' not in r.stderr:break
  time.sleep(.3)
 if r.returncode:raise RuntimeError(r.stderr)
 return r.stdout.strip()
assert git('remote','get-url','origin')=='git@github.com:Loyyed/Investment_yw_10-1_begin.git'
assert not git('diff','--cached','--name-only')
sys.path[:0]=[str(W/'scripts'),str(R/'投资学公司分析通用工作台')]
from review_store import ReviewStore
from companybench import insight
store=ReviewStore(W);F={x['id']:x for x in store.facts()};dis={x['id']:x for x in store.m01_disclosure_facts()}
spec=json.loads((W/'work/t5-forecast-20261027/report-spec.json').read_text(encoding='utf8'))
authority=insight.validate_current(W,spec);assert authority['status']=='current'
diagnostics=json.loads(subprocess.check_output([sys.executable,'-B','-X','utf8',str(W/'work/t5-forecast-20261027/calculate_depth.py')],encoding='utf8'))
assert diagnostics==json.loads((W/'work/t5-forecast-20261027/diagnostics.json').read_text(encoding='utf8'))
protected={str(p):sha(p) for d in [W/'sources',W/'evidence',O/'01_路演与讲稿'] for p in d.rglob('*') if p.is_file()}
protected.update({str(W/x['path']):sha(W/x['path']) for x in spec['dependencies']})
protected[str(W/'work/t5-forecast-20261027/report-spec.json')]=sha(W/'work/t5-forecast-20261027/report-spec.json')
manifest=[dict(file=p.name,sha256=sha(p),lines=len(p.read_text(encoding='utf8').splitlines())) for p in B.glob('*.md')]
js(P/'reading-manifest.json',manifest)
ids=['R2024-07','R2024-11','R2024-13','R2022-10','R2016-05','R2025-01','R2025-17','R2025-18','R2025-21','R2012-01']
assert all(F[k]['state']=='Fact' for k in ids) and dis['M01-D02']['state']=='Fact'
js(P/'source-bindings.json',dict(authority=authority,facts=[F[k] for k in ids],disclosures=[dis['M01-D02']],meaning='只读API校验快照，原ReviewStore仍权威'))
# Existing authoring renderer has no runtime side effects when extracting only its pure helpers.
source=(W/'work/lec05-20261028/implementation/implement.py').read_text(encoding='utf8')
module=ast.parse(source);env={'html':html,'re':re}
for node in module.body:
 if isinstance(node,ast.FunctionDef) and node.name in ['inline','render','page']:exec(compile(ast.Module(body=[node],type_ignores=[]),'helpers','exec'),env)
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CSS' for t in node.targets):exec(compile(ast.Module(body=[node],type_ignores=[]),'helpers','exec'),env)
render=env['render'];page=env['page']
# Requirements are located by original line, not inferred from prior summaries.
coverage=[]
for p in sorted(B.glob('*任务合同*.md')):
 task=re.search(r'合同(\d+)',p.name)[1]
 for no,line in enumerate(p.read_text(encoding='utf8').splitlines(),1):
  if line.startswith('- [ ]'):
   coverage.append(dict(id=f'L05-{task}-A{1+len([x for x in coverage if x["task"]==task])}',task=task,source=p.name,line=no,requirement=line[6:],delivery=f'Lec05_任务{task}.md',state='Agent已覆盖；人工判断/签署独立待审'))
assert len(coverage)==18
# Mandatory text is retained and extended in the current documents; no extra outputs copies.
t1=(C/'Lec05_任务01.md').read_text(encoding='utf8')
t1=t1.replace('公司自述：本轮不新增管理层引文，使用R2022-10的已核渠道定义作范围依据，定义不冒充竞争优势主张。','公司自述：M01-D02已核公司披露原话为“主要是本期销量增加及茅台酒主要产品销售价格调整。”（2024年报第8页，收入变动说明，公开日2025-04-03）。原话只证明公司这样解释，不能认定各原因的独立贡献；R2022-10另提供渠道定义。')
t1+='''
## 深化：让叙事真正约束参数

公司收入增长的披露解释只是一条起点：数量变化可能来自供给、计划投放、经销商补货或终端承接；公司实现ASP可能来自同规格出厂价格、产品组合或渠道组合。公司解释、市场预期、研究者命题三个层次分别保留。市场叙事未纳入，不推测市场已经给予怎样的溢价。

| 检查 | 收入 | 成本费用 | 资本及现金 | 研究含义 |
| --- | --- | --- | --- | --- |
| Possible | 可售供给、总量与渠道服务容量允许吗 | 能否承担相应服务 | 建设和库存需要提前多久投入 | 满足物理条件只是可能，不等于较可能 |
| Plausible | 客户为何改变购买路径，竞争者会怎样反应 | 平台/配送替代谁原先承担的工作 | 回款、退货和库存责任由谁承担 | 合理机制须与替代解释并列 |
| Probable | 已有收入结构证据，缺同SKU量价和终端样本 | 缺渠道完整费用 | 缺渠道资本占用 | 不赋予概率，也不将结构恒等式当实证净收益 |

反向检查一个参数：ASP受支付意愿、渠道数量份额、产品组合和折扣共同决定；先把这些因素落实到各格Q×P，再汇总收入，不能分别给“品牌”“直销”各加一个增速。若同品净价下降，即使直销比例上升，ASP也可能下降；不能把这些方向都预设为利好。

研究优先级（Agent建议）：先补同SKU渠道数量、实现净价和可归属履约费用，再讨论净价值。没有行业分母时不算份额；没有金融/实体范围桥时不拼正式FCFF。品牌维护的广告分项不是全部渠道成本，不能拿它单独证明渠道扩张费用很低。
'''
t2=(C/'Lec05_任务02.md').read_text(encoding='utf8')
t2=t2.replace('收入（万元）=100万件×ASP元/件÷1万元=100×ASP','收入（万元）=(100×10⁴件)×ASP元/件÷10⁴元=100×ASP')
t2+='''
## 历史起点、分析调整与信息窗口

| 层次 | 实际处理 | 边界 |
| --- | --- | --- |
| 报告数字 | 2024直销收入748.4332703079亿元，2025直销845.4303185463亿元，来源R2024-07/R2025-17 | 两渠道主营披露；不是同SKU净价或终端购买量 |
| 分析数字 | 两者差96.9970482384亿元；原渠道研究显示平台减少、其余直销增加 | 算术不识别渠道政策因果；其余直销差额不命名新增需求 |
| 预测数字 | 当前t−5按基酒参照、成熟修正、库存额外调整、计划投放、承接得销量，再乘组ASP | 修正系数与ASP路径为Forecast，不是原披露 |
| 正常化调整 | 本任务没有新增可证的金额剔除，也不随意删除低利润年份 | 未执行调整不能声称已经获得正常化盈利 |
| 信息边界 | 截止2026-10-27；2024年报公开2025-04-03 | 其他记录发布日期待核者，不据其声称更早时点已知；旧Fact值与可获时间分别管理 |

真实收入可写R=Σ产品Σ渠道 Q(p,c)×P(p,c)。目前没有完整交叉表，故采用已披露产品组Q×ASP作有限研究，不用收入占比代替数量占比，也不能把产品维度和渠道维度相加。

## 当前t−5模型的四项一致性复核（研究延伸，不改原模型）

| 关系 | 当前处理 | 未满足的部分与下一步 |
| --- | --- | --- |
| 量价收入 | 基酒年度尺度生成条件销量；产品组ASP滚动；两组收入加其他收入 | 同SKU量价与渠道交叉矩阵未齐；不再叠加直销增长 |
| 增长与投入 | 分列成熟、投放、承接；原费用路径仍保留 | 尚无逐项目资本支付、分龄库存状态及成熟映射，不能判断增长现金代价已完整 |
| 范围与期间 | 历史合并、产品组、酒类主营分别注明 | 合并利润/CFO敏感性不升格为酒类实体利润/FCFF |
| 风险与假设 | 三情景无概率；ASP、费用、承接方向共同讨论 | 60%增量保留和现金比率未独立识别，不能称完整利润税费桥；也不因缺资料任意提高WACC |

本轮不改路演依赖的模型和数值。基准2026茅台酒投放97%、承接98%、ASP变动−2%；系列酒投放95%、承接96%、ASP变动−4%；销售费率4.5%。它们是一组情景设定，不能称已经从历史唯一估计。2027—2028承接改善与系列酒供给映射需要单独验证，不自动兑现。

## 延伸：投入时序与路径质量

教学原路径在三年分别多250、500、250万元收入，累计多1000万元。这只计算未折现的收入差，不称现金或价值差。延迟路径第三年加速部分来自较低基数和当年更大的份额增量；不能单用增长率给路径排序。

若建设投入在第0年已经支付，渠道收入到第2—3年才兑现，延迟可能延长资金占用。当前无费用和投资金额，故只给因果路径：建设/获客提前→服务容量逐步形成→渠道数量改变→确认收入→费用及库存回款→现金。不能把延迟的影响统一处理为“终值不变所以价值不变”。

参数修正规则：先区分实际偏差来自供给、投放、承接、同品净价、组合还是费用；一次修改对应变量，保留原假设与误差归因，不为了贴近新结果同时任意调所有系数。
'''
t3=(C/'Lec05_任务03.md').read_text(encoding='utf8')
t3+='''
## 补足现金流、权利与资产范围的检查

| 项目 | 本组的处理原则 | 真实研究仍需补齐 |
| --- | --- | --- |
| FCFF | 同业务EBIT×(1−经营税率)+折旧摊销−资本开支−非现金经营营运资本增加 | 营业利润不直接等于经营EBIT；税率、资本及金融抵销需匹配 |
| FCFE | 同普通股范围净利润+折旧摊销−资本开支−营运资本增加+净新增债务 | 不从归母净利直接扣全合并资本开支；不重复扣利息或股利 |
| DDM | 折现预计实际分红，匹配股权成本 | 分红政策和可分配能力不同；当前股利为0不自动代表价值0 |
| 经营存货、厂房、土地 | 贡献已进入经营预测时，不再整体加账面价值 | 闲置非经营资产须另估并排除重复 |
| 品牌及技术 | 经价格、利润率或优势持续期进入预测，不额外加品牌溢价 | 贡献需证据，不能将五项管理层主张变成五笔资产加回 |
| 应付账款、合同负债 | 通常经经营营运资本影响现金，不全当融资债务再扣 | 结合实际业务及附注判断 |
| 租赁及其他权利 | 租金/现金流/租赁债务配套处理 | 避免现金已扣全部租金又扣同笔付款现值 |
| 少数权益 | 100%子公司现金已入价值才扣匹配少数权益价值 | 仅按持股份额预测则不再扣；账面余额不自动等于价值 |

借入资金增加现金和债务，不是经营创造价值。FCFF不混入借还本金；FCFE考虑债务融资。币种、名义/实际、税前/税后及现金流发生时点也须一致，不能只检查折现率的名字。

## 两册讲义的延伸学习（与合同必交分列）

平台：净额佣金收入=同口径GMV×有效抽成率，GMV不是平台收入；广告和自营另列。提高抽成可能反过来减少交易与商户留存，不能独立取两个最优值。本段是方法迁移，不把i茅台机械当净佣金平台。

品牌：消费者支付意愿和上市公司实际收入归属不同。法拉利2015历史案例只启发“数量—稀缺性—投入”的权衡，不借其当时表现证明茅台当前机制，也不补造该公司的当前数字。

轻资产：少厂房不等于无研发、获客和服务投入。研发若已费用化，现金流不再完整扣一次；若作分析资本化，应同时调整利润、资本和摊销。本组不实际执行研发资本化。

风险：讲义的独立教学例中，70%×1000+30%×600=880万元预期FCFF；按10%折现得800万元。只把1000按12%折现得892.8571万元，未体现订单流失；若资本成本另有依据升至12%，应以880÷1.12=785.7143万元。概率与资本成本均来自讲义设定，不用于茅台，不与合同220万元或1500万元两例串联。

价值与价格：市场EV的组成与DCF估计的经营价值先列口径；没有当日价格与可核市场预期时，不比较高估低估。本组不要求完整DCF、终值、相对或反向估值；它们保留为后续独立研究，不用“未来研究”掩盖本组三项任务的实际缺口。
'''
for i,t in enumerate([t1,t2,t3],1):write(C/f'Lec05_任务0{i}.md',t)
# Calculation derivations, not new company facts.
calc=json.loads((W/'work/lec05-20261028/calculations.json').read_text(encoding='utf8'))
rows=calc['revenue_paths'];orig=[D(x['revenue_10k_yuan']) for x in rows[:4]];delay=[D(x['revenue_10k_yuan']) for x in rows[4:]]
gaps=[a-b for a,b in zip(orig,delay)];assert gaps==[D(0),D(250),D(500),D(250)] and sum(gaps)==1000
ext=dict(type='Teaching/AgentCalculated',revenue_gaps_10k=list(map(str,gaps)),cumulative_gap_10k=str(sum(gaps)),share_vs_revenue_share={'quantity_share':'.20','revenue_share':str(D('.2')*150/(D('.8')*100+D('.2')*150))},pv={'contract_fcff':str(D(220)/D('1.1')),'wrong_fcff_discount':str(D(220)/D('1.12')),'lecture_fcfe':str(D(112)/D('1.12'))},risk_example={'expected_fcff':str(D('.7')*1000+D('.3')*600),'correct_pv':'800','unsupported_rate_only_pv':str(D(1000)/D('1.12')),'both_justified_pv':str(D(880)/D('1.12'))},unchanged_model_sha256=sha(W/'work/t5-forecast-20261027/report-spec.json'))
js(P/'extended-calculations.json',ext)
e=lambda x:html.escape(str(x),quote=True)
def table(headers,rows):return '<div class="v2-table"><table><thead><tr>'+''.join('<th>'+e(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+e(x)+'</td>' for x in r)+'</tr>' for r in rows)+'</tbody></table></div>'
def paras(ps):return ''.join('<p>'+e(p)+'</p>' for p in ps)
def graph(title,labels,values,unit,colors=None):
 width=820;height=360;top=45;bottom=285;vmin=min(0,min(values));vmax=max(values)*1.12 if max(values)>0 else 0;span=vmax-vmin or 1
 yy=lambda v:bottom-(v-vmin)/span*(bottom-top)
 body=f'<svg class="vis-svg" viewBox="0 0 {width} {height}" role="img" aria-label="{e(title)}"><title>{e(title)}（{e(unit)}）</title><line x1="60" y1="{yy(0)}" x2="790" y2="{yy(0)}" stroke="#9bb9b1"/>'
 for i,(label,v) in enumerate(zip(labels,values)):
  x=85+i*700/len(values);bw=min(100,520/len(values));y=min(yy(0),yy(v));h=abs(yy(v)-yy(0))
  color=(colors[i] if colors else '#167d8d')
  body+=f'<rect x="{x}" y="{y}" width="{bw}" height="{max(h,1)}" rx="3" fill="{color}"/><text x="{x+bw/2}" y="{yy(v)-12 if v>=0 else yy(v)+20}" text-anchor="middle" class="value">{v:,.2f}</text><text x="{x+bw/2}" y="330" text-anchor="middle" class="tick">{e(label)}</text>'
 return body+'</svg>'
def linechart():
 svg='<svg class="vis-svg" viewBox="0 0 820 380" role="img" aria-label="两条教学收入路径"><title>原路径与延迟路径（万元）</title>'
 for val in [11000,11500,12000,12500]:
  y=300-(val-11000)*.16;svg+=f'<line x1="75" x2="775" y1="{y}" y2="{y}" stroke="#d9e4df"/><text x="5" y="{y+5}" class="tick">{val}</text>'
 for vals,color,off in [(orig,'#167d8d',-14),(delay,'#b27a2f',24)]:
  points=[]
  for i,v in enumerate(vals):
   x=100+210*i;y=300-float(v-11000)*.16;points.append(f'{x},{y}')
   svg+=f'<circle cx="{x}" cy="{y}" r="5" fill="{color}"/><text x="{x}" y="{y+off}" text-anchor="middle" class="value">{v:.0f}</text>'
  svg+=f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="3"/>'
 for i in range(4):svg+=f'<text x="{100+210*i}" y="360" text-anchor="middle" class="tick">第{i}年</text>'
 return svg+'</svg>'
def flow(labels):
 return '<div class="flow">'+''.join('<div><small>'+str(i+1).zfill(2)+'</small><strong>'+e(t[0])+'</strong><p>'+e(t[1])+'</p></div>' for i,t in enumerate(labels))+'</div>'
def fig(id,title,svg,reading,why,limits,source):
 return '<figure id="'+id+'"><figcaption><div class="eyebrow">LEC05 · '+id.upper()+'</div><h3>'+title+'</h3></figcaption>'+svg+'<p class="chart-reading"><strong>怎么看：</strong>'+reading+'</p><details><summary>推理、替代解释与来源批注</summary>'+paras([why,limits,source])+'</details></figure>'
def answer(q,a,source):
 return '<article class="contract-answer"><h4>'+e(q)+'</h4>'+paras([a])+'<details><summary>依据与支持边界</summary>'+paras([source])+'</details></article>'
def head(id,kicker,title,q,verdict):
 return '<article class="lec05-unit" id="'+id+'"><header class="chapter-head"><div class="eyebrow">'+kicker+'</div><h2>'+title+'</h2><p class="question">'+q+'</p><div class="verdict"><span>本轮工作判断 · 待本人审阅</span><p>'+verdict+'</p></div></header>'
def reason(title,items):return '<article class="depth-reason"><h3>'+title+'</h3><ol>'+''.join('<li>'+e(x)+'</li>' for x in items)+'</ol></article>'
# Native atlas figures and reasoning reuse existing CSS/classes; no external assets.
part1=head('lec05-task01','Lec05合同01 / 叙事与参数','公司收入增加，为什么不能只讲成品牌或直销成功？','公司自述、历史结果和未来假设怎样连接？','保留渠道迁移可能提高公司确认收入的条件命题；不据此断言新增终端需求或净价值。先解释量、价、组合与新增责任，再判断未来。')
part1+=reason('把命题推出来',['M01-D02核实公司将收入变动解释为销量和主要产品价格调整；这只确认自述，不识别各项独立因果。','R2022-10确认直销包含自营与i茅台；不能把平台与直销再加总。','R2024-07和R2025-17显示主营直销确认收入增加；收入份额不是数量份额，ASP还受产品/渠道组合影响。','可能拿回价差，也可能承接原由经销商承担的配送、库存和服务；净贡献须追踪新增责任。','优先收窄为可检验的条件研究主张；未核同SKU净价、终端动销和归属费用前，不赋予成功概率。'])
part1+=flow([('公司说什么','销量与主要产品价格调整'),('事实能支持什么','渠道定义与确认收入'),('研究怎样解释','份额迁移、组合或净价'),('未来怎样检验','Q、P、费用和资本共同约束')])
direct24=D('74843327030.79')/D(1e8);direct25=D('84543031854.63')/D(1e8)
part1+='<div class="chart-grid">'+fig('l05-f1','确认收入增加，不等于新增终端需求',graph('两年主营直销收入',['2024','2025'],[float(direct24),float(direct25)],'亿元'),'主营直销由748.43增至845.43亿元，算术增96.9970亿元。','两年已核原数可描述确认金额；应继续检查净价、数量、组合与客户跨渠道迁移。','不能据此判断同品提价、数字平台因果或消费者购买量；不同口径数据不相加。','R2024-07，2024年报9/17页；R2025-17，2025年报10页；当前绑定见本章来源表。')+fig('l05-f2','结构帮助可以被渠道内部变化抵消',graph('2025固定规模毛利率效应金额',['结构效应','内部效应','合计'],[float(D(diagnostics['margin_static_yi'][k])) for k in ['structure','internal','total']],'亿元',['#167d8d','#b27a2f','#183d42']),'原分解折算约+6.64、−19.87、−13.23亿元，后两者说明只看份额会漏掉反向变化。','使用既有诊断固定收入规模折算率效应；中点分解保持描述性恒等式。','不是实际政策净利润、渠道归属利润或因果；未扣完整费用与资本。','原渠道计算及本次重新执行calculate_depth.py，与既有diagnostics.json一致。')+'</div>'
part1+=table(['叙事→参数','收入增长','利润率/费用','再投资','风险/持续期'],[['渠道迁移','数量份额和ASP','履约与营销责任','库存/结算及建设','服务能力与承接'],['品牌支付意愿','同品净价与需求','维护支出','渠道维护投入','竞争、替代与持续性'],['长周期供给','成熟与投放','储存损耗/组合','提前资本与库存','供给与需求错配']])
part1+=answer('3P到底判到哪一步？','Possible检查供给和实施时间；Plausible检查客户选择、竞争反应与新增责任；Probable现有证据尚不足以给未来净贡献提高赋概率。满足前两项不自动通过第三项。','Part1 §1.3/2.2；为Interpretation/Forecast。')
part1+=answer('一个参数能否只靠一条叙事？','ASP同时受支付意愿、产品组合、渠道数量结构和折扣影响。先逐格Q×P再加总，避免品牌增速与直销增速重复叠加；同SKU折扣可以抵消渠道上移。','合同01步骤4；Part1 §2.2—2.3。')
part1+='</article>'
part2=head('lec05-task02','Lec05合同02 / 历史起点与路径','同样方向，兑现早晚和基数会改变研究判断','如何同时看收入水平、增长率和投入？','教学延迟路径第三年增速更高，收入仍较低；真实模型还须检查ASP、供给、费用与资本是否同属一组经营条件。')
part2+=reason('从原数到预测，缺哪一步都不能跳过',['报告数：收入与销量必须同产品、渠道、期间，披露日与经营年份分开。','分析数：如有一次性或周期调整须保留原数和桥接，本任务没有新增有证据的金额剔除。','未来参数：原t−5供给锚不等于可售库存；成熟、投放、承接与ASP仍是条件设定。','教学两路径总量100万件、渠道价格100/150元均不变；收入增量完全来自数量结构。','资本支付可能早于服务与收入形成；没有费用及投资金额，只计算收入差，不把它升级为现金流差。'])
part2+='<div class="chart-grid">'+fig('l05-f3','收入水平：延迟路径三年均未追上',linechart(),'青色原路径，金色延迟路径；各年差0/250/500/250万元。','第3年增长更快不足以弥补前期差距；三年累计收入差1000万元。','全为合同02教学假设；累计差未折现，不是价值差。','合同02教学输入及教学计算.csv；一年公式及增速解释本人已确认，不扩其范围。')+fig('l05-f4','增长率：比较基期和当年结构变化',graph('第3年收入增长率',['原路径','延迟路径'],[float((orig[3]/orig[2]-1)*100),float((delay[3]/delay[2]-1)*100)],'%'),'2.08%与4.35%都从各自上年收入计算。','延迟路径第3年份额提高10pp，原路径提高5pp；基数也更低。','增速差不能证明路径价值更优，也不证明真实公司需求更强。','合同02；前次真实聊天确认仅教学第1年及第3年解释。')+'</div>'
part2+=table(['期间','基期','第1年','第2年','第3年'],[['原路径收入/万元',*map(str,orig)],['延迟收入/万元',*map(str,delay)],['差额/万元',*map(str,gaps)],['原直销数量占比','20%','30%','40%','45%'],['延迟数量占比','20%','25%','30%','40%']])
part2+='<div class="chart-grid">'+fig('l05-f5','同一个占比，分子不同就不能替换',graph('教学基期直销份额',['数量占比','收入占比'],[20,float(D('.2')*150/110*100)],'%'),'相同基期20%的数量，以较高单价销售，对应收入占比27.27%。','收入份额=s×Pd/[(1−s)Pw+sPd]；没有渠道价格关系不能倒算数量份额。','此为额外教学推导，不是茅台份额估计；不能用27.27%填真实模型。','合同02教学总量与价格设定，extended-calculations.json。')+fig('l05-f6','风险先进入经营结果，再判断资本成本',graph('讲义独立单笔现金现值',['只续约10%','概率加权10%','仅调率12%','两者有据12%'],[float(D(1000)/D('1.1')),800,float(D(1000)/D('1.12')),float(D(880)/D('1.12'))],'万元'),'续约/流失70%/30%，现金1000/600，先得期望880，再折现。','800万元已反映给定经营损失；仅调率未表达客户流失；若资本成本另有依据变化，两者均可调整。','概率与WACC来自讲义，不用来识别茅台风险；不把所有不确定性都塞进WACC。','Part1 §2.2独立教学例，不与合同03的220/1500串联。')+'</div>'
bs=spec['forecast']['scenarios']['base']
part2+=table(['四项一致性','当前模型怎样处理','仍缺什么'],[['量价','2026基准茅台投放97%/承接98%/ASP−2%；系列95%/96%/−4%','渠道/SKU交叉量价未齐'],['增长与投入','基酒锚、成熟、投放与承接逐层列示','分龄库存、逐项目支付及成熟映射'],['范围与期间','产品收入与合并利润/CFO分别标明','金融/实体抵销与经营税费桥'],['风险与假设','三种条件场景，无概率；销售费率4.5%','60%保留与现金比率未独立识别，不是完整FCFF']])
part2+=answer('为什么不能再乘1.03？','Q×渠道价格及数量结构已计入渠道作用，再以直销提高加3%重复计算同一效应。独立新因素须落实到独立变量，不把同一句叙事加两遍。','合同02问题4；Part1 §3.4。')
part2+=answer('真实预测为何不能一张教学表就算完？','需补同SKU净价/数量、终端购买和渠道库存，以及服务费用、回款、建设投资。现有证据允许方向与条件判断，但不证明参数已经独立估计。','R2016-05、R2022-10；原t−5参数及结果保留，不改路演依赖。')
part2+='</article>'
part3=head('lec05-task03','Lec05合同03 / 归属与估值范围','能产生现金，和现金属于谁，是两道问题','经营资产价值如何成为普通股每股价值？','按给定条件，教学B得1315万元普通股价值、13.15元/股；真实公司尚缺实体现金、金融抵销与权利归属，不能照搬教学数字形成目标价。')
part3+=reason('先明确索取权，再做加减',['DDM折现预计股利，FCFE折现股权分配能力，二者配股权资本成本；FCFF为全体资本现金，配WACC。','合同03练习A：220÷1.10=200，只是一年后一笔FCFF的现值，不是完整经营价值。','练习B经营价值1500完全独立；经营现金70已在其中，剩余110才按题设单独加回。','加金融投资60，扣债务280及少数权益75，得到1315；万元除万股=元每股。','真实金融业务与酒类范围不能任意分摊；账面现金、少数权益和市场EV都须先核组成与价值口径。'])
part3+='<div class="chart-grid">'+fig('l05-f7','同一笔FCFF不能随意改用股权成本',graph('合同03单笔220万元现值',['WACC 10%','错用Ke 12%'],[200,float(D(220)/D('1.12'))],'万元'),'正确归属得到200；196.43虽可算出，但折现率索取权不匹配。','匹配还包括币种、名义实际、税前税后与发生时间；结果接近不证明口径正确。','仅单笔现值，不含其他年或终值。','合同03练习A；全部教学设定。')+fig('l05-f8','经营价值不全部归普通股股东',graph('独立教学B桥接',['经营价值','富余现金','金融投资','债务','少数权益','普通股'],[1500,110,60,-280,-75,1315],'万元',['#183d42','#167d8d','#167d8d','#b27a2f','#b27a2f','#183d42']),'1500+110+60−280−75=1315，再除100万股=13.15元。','现金总180中70用于经营已包含；净债务170验证1500+60−170−75=1315。','这是逐项加减柱状比较，非累计高度；全部现金加回高估0.70元/股，问题在范围。','合同03练习B完整题设；与A独立。')+'</div>'
part3+=flow([('先选范围','酒类实体与金融业务分开识别'),('再识别现金','经营必需、受限、富余与收益'),('再核权利','100%子公司现金对应少数权益'),('最后算每股','资料不齐先暂停真实目标价')])
part3+=table(['路径','现金流','折现率','首先得到'],[['DDM','普通股预期股利','Ke','普通股价值'],['FCFE','同普通股范围、再投资与净债务融资后现金','Ke','对应普通股价值'],['FCFF','经营税后、再投资后全体资本现金','WACC','经营资产价值']])
part3+=answer('合并CFO为何不能当酒类FCFF？','R2025-21的合并净利润853.1032、CFO615.2220亿元只说明合并流量。金融业务相关资金变动、税费、营运资本及经营资本支出均须匹配；2012已合并财务公司，不按收入比例机械剥离。','R2025-21、R2012-01当前Fact；实体FCFF仍Unknown。')
part3+=answer('哪些项目最容易重复计值？','已支持预测的存货/厂房、已经进入价量和利润率的品牌、经营营运资本中的应付与合同负债，不能再次整体加回或当融资债务扣除；租赁及少数权益按是否已进入现金流判断。','Part2 §4.2—4.6；具体公司调整须来源，不仅看科目名。')
part3+=answer('现在选择怎样的真实研究范围？','Agent建议先搭酒类经营业务现金及资本桥，再识别财务公司权益与内部抵销；关键数据未齐，暂停真实每股数值。另一路可以整体股权口径研究，但也须一致的现金与权利范围，不能把范围选择当唯一正确答案。','待本人选择并审阅；不改变旧事实，不冒称已完成真实估值。')
part3+='</article>'
sources='<article id="lec05-sources"><h3>本章来源、版本与支持边界</h3>'
sources+=table(['来源ID','定位','作用与限制'],[['M01-D02','2024年报第8页；2025-04-03公开','已核公司自述，仅证明其这样解释'],['R2024-07/R2025-17','2024年报9/17页；2025年报10页','主营渠道收入成本，不是同SKU或终端动销'],['R2022-10','2022年报15页','直销含自营+i茅台，定义非效率因果'],['R2016-05/R2025-01','2016年报12—13页；2025年报16页','工艺与产销量；非固定五年转化'],['R2025-21/R2012-01','2025年报62/65页；2012物理67页','合并现金与范围，不是酒类FCFF'],['Part1/Part2','新增讲义§1.1—4.6','方法与教学假设，不证明公司当前事实']])
sources+='<details><summary>逐项回到本地原件与当前绑定</summary>'
for k in ids:
 x=F[k];sources+='<p><strong>'+k+'</strong> '+e(x['location'])+'；'+e(x['period'])+'；<a href="../'+e(x['pdf_path'])+'">原PDF</a>；当前绑定 '+e(x['binding'])+'</p>'
sources+='</details><p>非2024记录的原始公开日仍有待核项；保留旧原数Fact，同时不凭其构造更早已知信息集。核验有效性由API维护，快照不替代账本。</p></article>'
chapter='<section id="lec05" class="chapter"><div class="eyebrow">补充材料4 · 完整执行与研究延伸</div><h2>从叙事到预测，再到现金与权利</h2><p>原章简版已修订。下面按三合同展开8幅图、逐步推理、替代解释、来源批注与人机审阅；原14章及原t−5模型保留。教学结果、真实事实、研究判断和签署分别管理。</p><div class="toolbar"><a href="#lec05-task01">合同01：叙事</a><a href="#lec05-task02">合同02：路径</a><a href="#lec05-task03">合同03：归属</a><a href="#lec05-sources">来源</a></div>'+part1+part2+part3+sources+'<p><a href="02_Lec05叙事与估值/人机核对与验收.md">分批审阅清单与逐条验收</a></p></section>'
write(W/'work/lec05-20261028/atlas-chapter.html',chapter)
atlaspath=O/'证券投资分析研究图册_V2.2.html';old=atlaspath.read_text(encoding='utf8')
start=old.index('<section id="lec05"');end=old.index('</section>',start)+len('</section>')
assert old[start:end].count('<section')==1
new=old[:start]+chapter+old[end:]
assert new[:start]==old[:start] and new.endswith(old[end:])
write(atlaspath,new)
# Per-task HTML uses the exact atlas CSS and native chapter contents.
style=re.search(r'<style>(.*?)</style>',old,re.S)[1]
nativecss=style+'\n.lec05-unit{padding:32px 0 50px;border-bottom:1px solid var(--line)}.lec05-unit h2{font-size:29px}.lec05-unit .flow{margin:24px 0} .lec05-unit figure{align-self:start} .lec05-unit .chart-grid{align-items:start}.lec05-unit .depth-reason li{margin:12px 0} @media(max-width:720px){.lec05-unit h2{font-size:24px}}'
# Scope the added rules in both the main atlas and standalone task pages.
write(atlaspath,new.replace('</head>','<style>'+nativecss[len(style):]+'</style></head>',1))
for i,body in enumerate([part1,part2,part3],1):
 full='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lec05任务0'+str(i)+'</title><style>'+nativecss+' main{margin-left:0;max-width:1250px;margin:auto}</style></head><body><main><p><a href="../证券投资分析研究图册_V2.2.html#lec05">返回完整图册</a> · <a href="index.html">课程成果入口</a></p>'+body+'<details><summary>完整提交文档（含规定字数判断与补足内容）</summary>'+render([t1,t2,t3][i-1])+'</details></main></body></html>'
 write(C/f'Lec05_任务0{i}.html',full)
# Freeze review payloads. Prior confirmed teaching material remains valid, not re-requested.
batches=[
 dict(id='L05-R1',topic='研究命题与参数边界',items=[
 ('R1-01','公司自述只确认其说过销量/价格解释，不把原因自述当独立因果；市场叙事未纳入。','M01-D02；任务01'),
 ('R1-02','保留渠道迁移可能提高确认收入的条件命题，不据此认定新增终端需求或净贡献。','R2024-07/R2025-17及费用资本Unknown'),
 ('R1-03','ASP由同品净价、产品组合、渠道数量结构与折扣共同决定，不单靠品牌或直销判断。','Part1 §2.2—2.3'),
 ('R1-04','3P前两项是条件检验，当前证据不足以给未来净贡献改善赋概率。','任务01研究判断'),
 ('R1-05','t−5系数与后两年修复仍为条件设定，60%保留/现金比率不构成完整实体FCFF。','当前原模型SHA与任务02一致性表'),
 ('R1-06','净贡献研究优先补同SKU量价、渠道费用与资本责任；新证据按变量修正，不任意同时调所有参数。','任务01—02延伸')]),
 dict(id='L05-R2',topic='剩余教学计算与归属口径',items=[
 ('R2-01','八行路径表及三年收入差250/500/250、累计1000万元；累计未折现且不是现金差。','原合同02与extended-calculations.json'),
 ('R2-02','同教学基期直销数量占比20%，收入占比27.2727%；收入份额不能替代数量份额。','额外教学推导，非公司预测'),
 ('R2-03','220万元FCFF按10%折现200万元，只是一笔现值；不与独立1500万元例串联。','合同03练习A'),
 ('R2-04','独立B：1500+110+60−280−75=1315万元；每股13.15元；多加经营现金70高估0.70元/股；净债务170。','合同03练习B'),
 ('R2-05','讲义独立风险例：期望880，10%现值800；仅提高折现率不替代经营损失测算。','Part1 §2.2，非公司概率')]),
 dict(id='L05-R3',topic='真实估值范围与最终取舍',items=[
 ('R3-01','先研究酒类经营现金与资本，再识别财务公司权益和内部抵销，是建议路径而非已完成拆分。','任务03练习C'),
 ('R3-02','合并CFO不是酒类FCFF；经营现金、受限现金、金融资金不直接全加回。','R2025-21/R2012-01'),
 ('R3-03','已进入经营价值的存货、品牌等不重复加；少数权益仅在100%子公司现金已纳入时扣除。','Part2 §4.4—4.6'),
 ('R3-04','关键实体现金与权利资料未齐，暂停真实每股价值；不补目标价、WACC或终值来假装完成。','合同03范围要求'),
 ('R3-05','平台GMV/净佣金、轻资产必要投入和品牌稀缺性权衡仅为方法延伸，不转移成茅台Fact。','两册讲义学习延伸')])]
for b in batches:
 b['version']=1;b['state']='awaiting-actual-user-review';b['source_binding_sha256']=sha(P/'source-bindings.json');b['model_sha256']=sha(W/'work/t5-forecast-20261027/report-spec.json')
 b['display_payload_sha256']=hashlib.sha256(json.dumps(b,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
 js(P/(b['id']+'.json'),b)
# Correct the prior overly broad completion claim explicitly.
audit='''# 补充材料4逐条审计、修正与人机审阅

2026-10-28。本次核查结论：上轮Agent把简版文字/算术覆盖表述成充分完成，结论过宽。旧成果与旧提交保留在Git历史，不在outputs另存副本。本次不改路演讲稿、原Fact、旧采纳或签署。

## 实际修正

| 项目 | 上轮不足 | 本次改进 | 仍须本人完成 |
| --- | --- | --- | --- |
| 公司叙事 | 以渠道定义代替充分的自述层展开 | 增M01-D02已核原话、上下文及支持边界 | 裁定研究解释 |
| 讲义学习 | 主要覆盖三合同最简答案 | 补历史调整、正常化、风险分解及平台/品牌/轻资产迁移 | 审阅适用性 |
| 路径质量 | 只有两路径表和两简图 | 八图、收入水平/增速/份额定义、时序及t−5四项一致性 | 审阅条件假设 |
| 现金归属 | 正确加减但未系统展开 | 补FCFF/FCFE、资产/债务/少数权益及双重计算 | 真实范围选择 |
| 图册范式 | 独立简版，与旧章脱节 | 沿用旧CSS、结论/推理/图注/替代/来源/逐问结构 | 评价是否可接受 |
| 完成状态 | 文件生成容易被理解为全部验收 | 原稿待教师审核；Agent执行、本人裁决、签署分开 | 不伪造教师审核或签名 |

## 合同原验收条目逐行对照

'''
audit+='| 编号 | 原稿与行号 | 原要求 | 当前对应 | 状态 |\n| --- | --- | --- | --- | --- |\n'
for x in coverage:audit+=f"| {x['id']} | {x['source']}:{x['line']} | {x['requirement']} | [{x['delivery']}]({x['delivery']}) | {x['state']} |\n"
audit+='''
步骤补核：合同01可检验命题/三层叙事/至少两证据/3P/多对多/200—300字均对应任务01；合同02两真实证据/八行计算/五题回答/一年亲查分别对应任务02及原确认；合同03 A/B/C、两种列式、150—250字对应任务03。完整DCF、终值、相对和反向估值不属本组必交。真实数据缺口不妨碍完整教学计算，也不允许编造真实数字。

## 已有确认，不重复请审

本人原答复“确认教学计算与解释”仅覆盖当时展示的延迟路径第1年及第3年增速/水平解释，记录保持work/lec05-20261028/validation.json。本轮不新增原数Fact，不要求重复核144条有效原数。其余研究意见此前未收到明确认可，不冒称已采纳。

## 分批审阅

请逐批答“本批全部认可”，或列出需要修改/待定的编号并明确其余认可。计算、研究解释、范围选择与正式签署分别记录，不把一次答复扩成全部通过。新版本或来源语义变化后重新绑定展示，旧答复只对原范围有效。
'''
for b in batches:
 audit+='\n### '+b['id']+' · '+b['topic']+'\n\n| 编号 | 待审内容 | 依据 |\n| --- | --- | --- |\n'
 for id,t,src in b['items']:audit+='| '+id+' | '+t+' | '+src+' |\n'
audit+='\n## 正式关口\n\n执行记录：Agent，2026-10-28。本人核验/研究采纳按真实回复写独立记录；本轮学生身份与签署、复核或“未复核”需实际指定。未发生教师批准、独立复核或合同正式关闭。签署不是研究内容认可的替代。\n'
write(C/'人机核对与验收.md',audit)
index='<h1>Lec05：完整执行与批量审阅</h1><p>本轮对简版作逐条审计和深化；三项任务、两册学习延伸和8幅原范式图已接入当前图册。人工关口尚未代替完成。</p><div class="flow">'+''.join('<div><strong><a href="Lec05_任务0'+str(i)+'.html">任务0'+str(i)+'</a></strong><p>'+x+'</p></div>' for i,x in enumerate(['叙事与参数','历史起点和收入路径','现金归属与价值范围'],1))+'</div><p><a href="../证券投资分析研究图册_V2.2.html#lec05">读完整图册新增内容</a> · <a href="人机核对与验收.md">逐条审计与3批审阅</a> · <a href="教学计算.csv">教学原计算</a></p><details open><summary>本轮重点修正</summary><p>原版只完成简答，缺少完整推理、讲义方法与模型衔接。新增内容明确区分必交、延伸、Unknown及人工裁决；教学一年原确认不扩张。</p></details>'
write(C/'index.html',page('Lec05完整执行与审阅',index))
js(P/'coverage.json',coverage)
write(W/'docs/20261028-lec05-depth-audit.md',audit.replace('](Lec05_','](../outputs/02_Lec05叙事与估值/Lec05_'))
# Rebuild integration idempotently with an HTML-aware section-depth locator.
integrator=r'''from pathlib import Path
from html.parser import HTMLParser
W=Path(__file__).resolve().parents[1];p=W/'outputs/证券投资分析研究图册_V2.2.html'
t=p.read_text(encoding='utf8')
class Locator(HTMLParser):
 def __init__(self,text):
  super().__init__(convert_charrefs=False);self.text=text;self.lines=[0];self.depth=0;self.start=None;self.end=None
  for i,c in enumerate(text):
   if c=='\n':self.lines.append(i+1)
 def pos(self):a,b=self.getpos();return self.lines[a-1]+b
 def handle_starttag(self,tag,attrs):
  if tag=='section':
   if dict(attrs).get('id')=='lec05' and self.start is None:self.start=self.pos();self.depth=1
   elif self.depth:self.depth+=1
 def handle_endtag(self,tag):
  if tag=='section' and self.depth:
   self.depth-=1
   if not self.depth:self.end=self.pos()+len('</section>')
loc=Locator(t);loc.feed(t)
c=(W/'work/lec05-20261028/atlas-chapter.html').read_text(encoding='utf8')
if loc.start is not None:t=t[:loc.start]+c+t[loc.end:]
else:t=t.replace('</main>',c+'</main>',1)
if 'href="#lec05"' not in t:t=t.replace('</nav>','<a href="#lec05">Lec05 · 完整任务与延伸</a></nav>',1)
p.write_text(t,encoding='utf8')
'''
write(W/'scripts/integrate_lec05_atlas.py',integrator)
# Native styles for added units are included in section, so later integration survives a full rebuild.
chapter='<style>.lec05-unit{padding:32px 0 50px;border-bottom:1px solid var(--line)}.lec05-unit h2{font-size:29px}.lec05-unit .chart-grid{align-items:start}.lec05-unit .depth-reason li{margin:12px 0}</style>'+chapter
# Keep chapter cache starting with section for locator idempotency; style is nested inside it.
chapter=chapter[chapter.index('<section'):]
chapter=chapter.replace('<section id="lec05" class="chapter">','<section id="lec05" class="chapter"><style>.lec05-unit{padding:32px 0 50px;border-bottom:1px solid var(--line)}.lec05-unit h2{font-size:29px}.lec05-unit .chart-grid{align-items:start}.lec05-unit .depth-reason li{margin:12px 0}</style>',1)
write(W/'work/lec05-20261028/atlas-chapter.html',chapter)
subprocess.run([sys.executable,'-B',str(W/'scripts/integrate_lec05_atlas.py')],check=True)
once=sha(atlaspath);subprocess.run([sys.executable,'-B',str(W/'scripts/integrate_lec05_atlas.py')],check=True);assert once==sha(atlaspath)
for p,h in protected.items():assert sha(Path(p))==h,p
assert insight.validate_current(W,spec)==authority
assert all(sha(B/x['file'])==x['sha256'] for x in manifest)
cur=R/'会话交接/CURRENT.md'
write(cur,cur.read_text(encoding='utf8')+'\n\n## 2026-10-28补充材料4深化返工\n\n本人指出简版不充分，允许完成全部任务并延伸。已逐条复核18项原合同验收及各执行步骤，补两册方法、历史起点/风险/平台品牌轻资产延伸、t−5参数一致性，图册新增章按原范式重做3单元8图，三份任务文档同步深化。原模型、原14章实质内容、路演讲稿、Fact和旧采纳保持；修正账本outputs/02_Lec05叙事与估值/人机核对与验收.md。Agent覆盖不代表人审/签署完成。下一步L05-R1六项研究判断→R2剩余教学五项→R3范围五项；批次版本/展示指纹在work/lec05-depth-20261028，不扩原一年教学确认。所有新增成果只保留当前版，Git保留简版历史；逐次提交push。\n')
subprocess.run([sys.executable,'-B',str(W/'scripts/organize_outputs.py')],check=True)
js(P/'validation.json',dict(authority=authority,protected_files=len(protected),protected_unchanged=True,contracts_acceptance_items=len(coverage),teaching_extensions_checked=True,figures=8,source_files_unchanged=True,integration_idempotent=True,batches=[b['id'] for b in batches],new_fact=0,new_adoption=0,new_signature=0))
write(P/'build_depth.py',Path(__file__).read_text(encoding='utf8'))
print(json.dumps(dict(status='built',authority=authority,protected=len(protected),figures=8,review_batches=[b['id'] for b in batches]),ensure_ascii=False))
