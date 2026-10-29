from pathlib import Path
import json,hashlib,shutil,sys,re,subprocess
sys.stdout.reconfigure(encoding='utf-8');r=Path(__file__).parent;top=Path('D:/投资学');w=top/'投资学工作空间';b=top/'投资学公司分析通用工作台';out=w/'work/deep-study-20261029';od=w/'outputs/04_研究深化'
def put(p,s):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(s,encoding='utf-8')
# Preserve old notes in-place under newest concise node.
p=top/'会话交接/CURRENT.md';s=p.read_text(encoding='utf-8');header='''> 2026-10-29研究深化：本人新增授权可突破原来源限制，从可信来源广泛取数/学习并逐项标出处；原人工Fact规则不改。当前新增入口：投资学工作空间/outputs/04_研究深化/增长质量与价值兑现.html，已接统一入口及当前图册。2020—2025五组收入桥；官方2026H1/Q1与2025H1对照，平台+295.03亿但主营只+13.06亿；Q2收入−5.14%、归母−6.90%；CFO金融两行贡献约99.36%。新判断为Interpretation，外部原数ExternalSourceChecked/Agent，无新人工确认、采纳或签署。
>
> 知识库20卡已接通用工作台侧栏/knowledge，支持检索、精确收入桥与估值资格检查。学习覆盖与七网页辨析在同目录学习与方法知识库.md。书为801页扫描版，164页单页OCR仅作索引，关键章节精读；不宣称全书读完。今日头条正文未取得，其余六网页可读。新公告原PDF仅本地。核验144/2/15/3/3/16分域与旧56依赖当前有效；保护账本未改。9新测试+9方法+22工作流通过，实际浏览器桌面/手机与检索通过。
>
> 当前模型仍为2025锚定t−5情景，未用新半年信息回填历史命中；旧全年目标所需2026H2收入826.88亿、同比门槛4.08%。新报告与旧图册/路演并列看，原受审P04等冻结。原图册局部残留“量+1%”展示已改为条件销量，重建旧图册后运行本轮finalize展示修正；原spec/参数保持。下步优先固定SKU净价/销售吨数、代售责任与渠道库存，再更新ASP/费用/实体现金；不重复核有效旧数。底稿与修正在work/deep-study-20261029；本轮两仓成果发布回执同目录另记，发布前不称已推送。

'''
if not s.startswith('> 2026-10-29研究深化'):put(p,header+s)
p=b/'会话交接/CURRENT.md';s=p.read_text(encoding='utf-8');head='''> 2026-10-29：新增companybench.research_depth、20卡knowledge.json、侧栏/knowledge搜索、CLI精确收入桥和估值资格检查。纯方法无公司参数/数据/授权，core.py不改。Fraction内部精确运算，ASP/结构解释有边界；现金流索取权、再投资、范围、时点或折现不闭合则停止正式估值。9新概念/边界+9方法+22工作流通过，真实浏览器20卡/关键词搜索/侧栏入口及手机无页面横溢。说明docs/2026-10-29-研究深化与知识库.md；本轮Git发布状态见公司回执，不提前宣称成功。

'''
if not s.startswith('> 2026-10-29：新增companybench.research_depth'):put(p,head+s)
put(od/'研究更新_口头汇报与答辩.md','''# 研究更新口头汇报与答辩

2026-10-29；配合增长质量与价值兑现.html使用。旧路演仍是原信息集成果，本页为取得2026半年公告后的新解释，不继承旧人审。

我现在更关心的，是茅台怎样把供给和品牌转成有质量的增收。2025年酒类增量−18.37亿元，分解后总销量项+36.27亿、产品结构−16.06亿、组内ASP−38.58亿。这意味着量并非没有增长，但交付结构和单位收入没有保住；系列酒的单位收入压力更大。

新半年资料又把问题推进一步。2026H1平台增收295.03亿，主营只净增13.06亿，其余直销减少175.51亿、批发减少106.46亿。增长正在集中到平台，不能把平台曲线当全市场需求曲线。我们还没有客户或终端开瓶迁移的直接证据。

利润端的反证比一句“高毛利”更重要。H1合并营业毛利率由91.30%降至89.56%，销售费用虽下降，却没抵消成本和税金压力。Q2收入同比−5.14%、归母−6.90%，说明一季度转正不足以宣布底部确认。

现金不是同一条故事。H1集团CFO反弹，两个明确金融报表行解释了约99.36%的同比增量。这不是在否定现金真实，而是在辨认它来自哪类经营。剩余也不能直接命名实体CFO。

我的工作判断是：盈利基础仍强，但新的渠道和价格体系是否提高最终价值，需要逐项验证。上修应看到同SKU净价、库存周转、后续季度利润与归属净贡献一起改善；仅扩产、用户增加或平台放量还不够。

问：既然7月又提价，为什么不立刻调高全组ASP？答：公告只覆盖特定SKU/渠道/月份；实际销量、含税口径、折扣、产品组合和税费必须接上，不能每瓶涨幅乘全部吨数。

问：为什么还不给目标价？答：现有集团现金、实体再投资与金融资金未闭合。正式FCFF、权益折现和超额现金不能靠假设换名称。可以先算达成旧2026收入基准所需H2同比约4.08%的经营门槛，再观察兑现。

所有金额与计算、原公告URL/页码/SHA见同目录研究报告及work/deep-study-20261029/external-source-register.json。新数据由Agent核查，未经新增人工确认；旧签署保留。
''')
# Record checks; publication allowlist excludes all raw payloads/OCR/web full text.
v=json.loads((out/'validation.json').read_text(encoding='utf-8'));v.update({'test_results':{'research_depth':9,'methods':9,'workflow':22},'browser':{'knowledge_cards':20,'income_query_visible':7,'sidebar_link':1,'report_tables':8,'report_sections':13,'desktop':[1440,1000],'mobile':[390,844],'mobile_document_width':390},'notes':'三模块名称导入曾失败，改用unittest discover实际通过；图表比例及现金文字已经修正。'})
put(out/'validation.json',json.dumps(v,ensure_ascii=False,indent=2))
# Include source fingerprints, not copyrighted source bytes.
coverage=json.loads((out/'source-reading-coverage.json').read_text(encoding='utf-8'));coverage['book_sha256']=hashlib.sha256((top/'课件与任务文件/补充材料5/博迪投资学.pdf').read_bytes()).hexdigest();put(out/'source-reading-coverage.json',json.dumps(coverage,ensure_ascii=False,indent=2))
# Fix precise target reference for future reproduction; no rounding before final report display.
p=r/'build_upgrade.py';s=p.read_text(encoding='utf-8').replace("target=D('173390825146.1598')", "target=D(spec['forecast_results']['base'][0]['revenue'])");put(p,s);shutil.copy2(p,out/'implementation/build_upgrade.py')
for p in [b/'companybench/research_depth.py',r/'handover_publish_prep.py']:shutil.copy2(p,out/'implementation'/p.name)
# Published metadata includes source titles/URLs but no full reference article text.
files=['会话交接/CURRENT.md','投资学工作空间/outputs/00_从这里开始.html','投资学工作空间/outputs/证券投资分析研究图册_V2.2.html']
files += [str(p.relative_to(top)).replace(chr(92),'/') for p in od.iterdir() if p.is_file()]
files += [str(p.relative_to(top)).replace(chr(92),'/') for p in out.iterdir() if p.is_file()]
files += [str(p.relative_to(top)).replace(chr(92),'/') for p in (out/'implementation').iterdir() if p.is_file()]
bench=['README.md','会话交接/CURRENT.md','companybench/research_depth.py','companybench/knowledge.json','companybench/portal.py','companybench/ui.html','tests/test_research_depth.py','docs/2026-10-29-研究深化与知识库.md']
scope={'company':sorted(set(files)),'toolkit':bench}
put(r/'publication-scope.json',json.dumps(scope,ensure_ascii=False,indent=2));put(out/'publication-scope.json',json.dumps(scope,ensure_ascii=False,indent=2))
print('publication scope',len(scope['company']),len(bench))
