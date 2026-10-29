from pathlib import Path
import json,shutil,re,hashlib,sys
sys.stdout.reconfigure(encoding='utf-8');r=Path(__file__).parent;w=Path('D:/投资学/投资学工作空间');b=Path('D:/投资学/投资学公司分析通用工作台');out=w/'work/deep-study-20261029';od=w/'outputs/04_研究深化'
def copy(src,dst):
 if Path(src).resolve()!=Path(dst).resolve():shutil.copy2(src,dst)
def put(p,s):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(s,encoding='utf-8')
kb=json.loads((r/'knowledge.json').read_text(encoding='utf-8'))
cards='\n'.join('### '+c['id']+' '+c['title']+'\n\n'+c['method']+'\n\n边界：'+c['stop']+'\n\n出处：'+c['source']+'；PDF物理页'+str(c['pdf_physical_pages'])+'。\n' for c in kb['cards'])
learning=(r/'learning.md').read_text(encoding='utf-8').replace('KNOWLEDGE_CARDS',cards)
put(od/'学习与方法知识库.md',learning)
put(out/'source-reading-coverage.json',json.dumps({'book':'博迪投资学.pdf','book_total_pages':801,'usable_text_pages':0,'ocr_single_pages':164,'whole_book_deep_read':False,'key_sections':[9,11,12,17,18,19,28],'web_readable':[1,2,4,5,6,7],'web_pending':[3]},ensure_ascii=False,indent=2))
shutil.copy2(r/'web-access.json',out/'web-access.json')
put(out/'修正与冲突.md','''# 本轮修正、冲突与未决

2026-10-29。旧原件、真实审阅与签署保留，本轮未新增人工确认。

| 编号 | 旧位置/表述 | 本轮检查与处理 | 影响/状态 |
| --- | --- | --- | --- |
| U01 | 参考雪球394604887的2025CFO895亿 | 原ReviewStore R2025-21及本地年报615.22亿；保留原文冲突，不挪用 | 改用原权威；网页统计不入Fact |
| U02 | 参考网页的Q1转正→周期底部 | 官方H1−Q1算Q2收入−5.14%、归母−6.90% | 底部断言证据不足，新Interpretation |
| U03 | 平台增长→全公司需求增长 | H1平台+295.03、其余直销−175.51、批发−106.46，主营+13.06 | 明确路径迁移，终端需求Unknown |
| U04 | 2025销售费率升高外推2026 | H1销售费用32.06低于32.60亿，缓冲而非继续增加 | 修正跨期叙事，成本及税费仍压利润 |
| U05 | 草稿曾写两金融行贡献超过100% | 实算571?不得凭近似：精确贡献占575.7168908773亿总增量99.3646%，原稿更正；其余净影响3.6579048602亿 | 真实自查修正，最终稿99.36%，不隐藏失误 |
| U06 | 扫描书文字提取空值 | 801页无文字层，改中文OCR；首次WinRT类型加载失败、空缓存已重建 | OCR不是已读全书；实际精读页码另列 |
| U07 | GitHub参考初次乱码 | 明确UTF-8解码，原响应SHA不变 | 阅读副本已修复 |
| U08 | 旧图册预测导图仍有“核心量+1%”文字 | 当前t−5计算已非自由量增，图册展示作局部文字修正并加新资料入口；源spec旧版本保留 | 重建旧图册后须再跑本轮展示修正，公式/参数不改 |
| U09 | 今日头条HTTP200正文空 | 网页工具、原生请求、精确ID搜索均未取得正文 | 未读；待正文，不凭题目补内容 |
| U10 | 网页利润DCF/低国债率/近零风险 | 第18章FCFF/FCFE与风险折现匹配，工具增加资格停止 | 不能据网页给目标价或仓位 |

注：U05保留草稿错误与精确重算结果；不把修正文案说成原披露修正。新公告身份ExternalSourceChecked，真实核查者Agent，不写旧人工域。
'''.replace('实算571?不得凭近似：',''))
# Add current-source banner and remove one stale label in the current atlas display only.
for p in [w/'outputs/证券投资分析研究图册_V2.2.html']:
 if p.exists():
  s=p.read_text(encoding='utf-8');s=s.replace('基准核心量+1%、ASP−2%','2026条件核心销量49,459.30吨；ASP−2%')
  if 'deep-study-20261029' not in s:
   s=re.sub(r'(<body[^>]*>)',lambda m:m[0]+'<aside id="deep-study-20261029" style="padding:18px;background:#f3e9ca;color:#173d37">2026-10-29新增官方半年资料：本图册模型仍为2025锚定条件情景；当前经营判断请连同<a href="04_研究深化/增长质量与价值兑现.html">增长质量与价值兑现</a>阅读，旧预测与旧认可不自动更新。</aside>',s,count=1)
  put(p,s)
# Copy only original authoring inputs/code; full third-party text and PDFs stay ignored.
impl=out/'implementation';impl.mkdir(exist_ok=True)
for name in ['web-access.json','build_upgrade.py','report-template.md','learning.md','finalize.py','tests_depth.py','research_depth.py','knowledge.json']:copy(r/name,impl/name)
put(impl/'README.md','本轮原作者程序。主空间ReviewStore及原报告须在本地有效。build_upgrade.py从本目录official原始PDF的页缓存读取；原件不随Git发布，按上级external-source-register.json的URL取回、校验SHA后用PyMuPDF逐页提取再运行。运行build_upgrade.py后运行finalize.py。临时OCR/网页全文与QA仅本地。重跑不写人工核验；新的实际人工修改发生后先比较差异，不直接覆盖成果。\n')
# Generic module source warning repaired without changing runtime expression.
p=b/'companybench/research_depth.py';s=p.read_text(encoding='utf-8');s=s.replace('split(/'+chr(92)+'s+/)','split(/'+chr(92)+chr(92)+'s+/)');put(p,s)
copy(r/'tests_depth.py',b/'tests/test_research_depth.py')
put(b/'docs/2026-10-29-研究深化与知识库.md','''# 研究深化与可检索知识库

2026-10-29。侧栏新增“研究方法知识库”，不选公司也可打开/knowledge，按问题/术语检索20张卡。每卡含方法、来源、原PDF物理页与停止条件。不声称已精读整本801页教材；详见公司学习记录。

python -m companybench.research_depth knowledge --query 收入

python -m companybench.research_depth bridge --input 输入.json

输入包含before/after；每期产品名映射到revenue、quantity十进制字符串，产品集合、单位与范围须先对齐。输出总量→产品结构→组内ASP桥与逐产品量/ASP/交互项，Fraction精确运算、十进制展示40位，residual为精确运算结果。两种展示不能相加。缺失、零量、非有限数、浮点与新退出类别拒绝，避免制造均价或补零。

python -m companybench.research_depth valuation-audit --input 估值定义.json

basis取FCFF/FCFE/Dividend，discount_basis对应WACC或CostOfEquity；另需cashflow_defined、reinvestment_defined、financial_scope_defined、asof_defined均为true及r/g字符串。检查只判定义是否通过，不估计公司价值、不产生Fact。无风险率直接当权益折现、营运变动重复扣减均停止。

公司数值、授权和参数未注入通用代码。core.py与核验账本不改。9项概念/边界测试及实际浏览器搜索、桌面/手机阅读检查通过；原有工作流测试另记验证。方法不代真实审阅或签署。
''')
p=b/'README.md';s=p.read_text(encoding='utf-8')
if '2026-10-29-研究深化与知识库.md' not in s:put(p,s+'\n\n研究深化升级：侧栏可搜索方法知识库，支持精确收入桥与估值资格检查，见[操作说明](docs/2026-10-29-研究深化与知识库.md)。\n')
print('learning, conflicts, documentation and toolkit tests installed')
