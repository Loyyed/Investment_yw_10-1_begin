from common import *
from workspace_utils import guard_generated_writes
guard_generated_writes(W, "09_documentation.py")
import html,sys
sys.stdout.reconfigure(encoding='utf-8')
intro='''# 投资学工作空间

贵州茅台（600519），指定2020—2024年年报，2026秋金融专硕投资学任务。建立日期2026-10-02。

资料与自动化研究准备已完成；学生本人PDF核验、口径裁决、证据Fact升级与合同签署尚待完成。人名和签署日期留空，按用户要求以后统一填写。

[带图片的工作流程与文件说明](工作流程与文件说明.md) · [本地工作台](工作台.html) · [任务进度](docs/task-status.md) · [本人核验入口](docs/human-review-guide.md) · [全部文件位置](docs/generated-files.md)

![工作台构成](docs/images/workspace-structure.png)

| 位置 | 内容与用途 |
| --- | --- |
| sources/annual_reports/ | 五份原PDF与五份检索MD；保持原样，SHA-256见manifest.json |
| sources/course/ | 按正文用途整理的Lec01—03课件、附件、模板与原图片，副本原字节不变 |
| sources/toolkit/ | MinerU工具参考源码与说明；只读取，不安装或调用API |
| sources/original-tree/、sources/unpacked/ | 原目录副本与六个ZIP解包结果，保留出处；重复内容不重复进Git |
| tasks/ | 00本次执行说明、01—04合同和05Lec03合同 |
| work/ | 原页全文、检索、候选、口径冲突、修正、Unknown、计算与检查 |
| evidence/ | 本人核验后的证据日志及人工表；当前未假造Fact |
| outputs/ | 六份合同成果准备稿与课件补充成果 |
| docs/ | 图片、核验指南、资料用途、运行与Git说明、文件清单 |
| scripts/ | 实际使用的解包、提取、生成、核验和计算脚本 |
| config/ | Python版本、依赖锁定及本人可比性确认配置 |
| .git/ | 本地版本库，无远程服务，无Token |

常用成果：[第一次定位](outputs/first-analysis.md)、[收入结构](outputs/revenue-structure-table.md)、[口径卡](outputs/metric-scope-decision.md)、[变化记录准备](outputs/change-verification-record.md)、[Lec03矩阵](outputs/lec03-evidence-matrix.md)、[Lec03五项成果](outputs/lec03-stage-deliverables.md)。

运行环境为本机D:/Anaconda/python.exe。双击“打开研究笔记.cmd”使用已有JupyterLab；双击“运行检查.cmd”执行验证。也可以用支持Python的编辑器打开投资学工作空间.code-workspace。详细说明见docs/run-guide.md。
'''
write('README.md',intro)
write('docs/task-status.md','# 任务与验收状态\n\n'+table(['任务','已完成的自动化工作','成果位置','本人仍需完成'],[['第一次','PDF63—64页收入和利润归属定位；交叉位置保留','outputs/first-analysis.md','两条原文核验及Fact登记'],['第二次','51条收入成本候选，21组合计检查','outputs/revenue-structure-table.md','至少一条本人核验；最终逐行确认范围'],['第三次','12条候选；收入/利润两组冲突；真实Agent修正保留','outputs/metric-scope-decision.md','本人采用/排除裁决及实际修正记录'],['第四次','可比性材料、公式代入、披露变动率及阻断程序','outputs/change-verification-record.md','本人确认可比性后执行复算并核验'],['Lec03','六条矩阵、问题清单、经济逻辑图、优势证据表、两条人工核验准备','outputs/lec03-evidence-matrix.md；lec03-stage-deliverables.md','本人选择机制与核验：至少一Fact及一Unknown'],['课件补充','产品结构A、披露地图、组件选择、反方质询','outputs/lec01-decision-card.md等','按个人实际过程改写Exit Ticket及小组裁决']])+'\n合同正式关闭：尚未。执行人、复核人和签署日期按用户要求留空；仅填姓名不等于已经核验。材料未含第五次及更后续独立合同，不能凭“等”虚构任务内容。')
write('docs/human-review-guide.md', '''# 本人核验与提交入口

自动化准备已完成，但课程将学生本人核验作为验收条件。依据源文件“第一次任务合同”第六节、第二次合同第六节、第三次合同第六节、第四次合同使用边界及Lec03合同第六节；条款副本均在tasks。用户已要求人名与签署以后填写。

1. 先打开[第一次结果](../outputs/first-analysis.md)，回[2024原PDF](../sources/annual_reports/pdf/600519_2024_贵州茅台_贵州茅台2024年年度报告_2025-04-03.pdf#page=63)核对63页营业收入和64页归母净利润，检查单位、本期列、合并主体。5页和108页提供交叉披露。
2. 第二次选择2024年108页N组：商品类型有茅台酒、其他系列酒、其他业务三行；地区与渠道各两行。9页R组是酒类，不混用。确认后在[候选账本](../work/evidence-candidates.md)记录真实核验过程，再移入[证据日志](../evidence/evidence-log.md)。
3. 阅读[口径卡](../outputs/metric-scope-decision.md)，按研究用途选择C01/C03/C02，保留被排除候选；在[裁决底稿](../work/scope-adjudication.md)记录个人实际修正过程，不能抄成自己已经发生的错误。
4. 第四次先确认七项可比性：版本、期间、单位币种、报表主体、合并范围、指标定义、无重述。2024年85页会计变更，120—121页合并范围；收入和归母比较值在63—64页。全部确认后填写[human-review.json](../config/human-review.json)的对应布尔值并运行复算脚本。不要把2023比较列中的2022重述利润与2022原报数混算。
5. Lec03使用[本人核验表](../evidence/human-review-forms.md)：H01确认C01候选；H02核对公司品牌自评后保留缺证Unknown。再自己选取机制、替代解释与反证，更新矩阵正式Fact栏。
6. 填各合同执行人、复核人、签署日期，重新核对所有验收项。将正式Fact、Unknown和变化记录分开后保存新Git提交。

证据升级规则：只有本人完成回到PDF的核验，填写核验人、日期、精确位置、期间、口径和支持边界，才能从work复制到evidence并改Fact。程序不会自动替你完成此步骤。
''')
write('docs/run-guide.md', '''# 环境、复现与Git使用

实际环境：D:/Anaconda/python.exe，Python3.12.4；依赖具体版本见config/dependencies.json。D:/Py是另一个Python，不作为本项目执行环境。环境文件environment.yml用于未来复建，本次未创建额外conda环境或修改全局包。

在本目录的cmd中运行：

~~~cmd
D:/Anaconda/python.exe scripts/03_extract.py
D:/Anaconda/python.exe scripts/08_validate.py
D:/Anaconda/python.exe -m jupyter lab research.ipynb
~~~

前两命令为抽取和检查，第三命令打开本机JupyterLab。Notebook可以读取51条结构候选及21组核对记录；运行不意味着人工核验完成。Notebook实际内核执行副本在work/notebook-executed.ipynb。

正式变化复算：本人完成七项核验后改config/human-review.json对应值，再运行scripts/07_compute_changes.py。缺确认、零基数或明确重述/口径变化必须保持阻断。2022重述不能仅用“no_restatement=true”绕过；应先另建同口径调整记录，当前脚本只服务2024对2023。

重建顺序为00清点解包→01全文读取→03结构提取→04原页渲染→05建立目录合同→06/06b成果→07b图片笔记→09文档。原件一直保持不变。已有人工修改后不要直接重跑05、06、06b、09，会覆盖这些生成文件；先git status/diff和保存版本，在副本重建。human-review.json已防止生成脚本覆盖，但其他人工修改仍需版本保护。

本地工作台.html可由你在浏览器打开，Markdown链接可用编辑器阅读。内置浏览器安全策略拒绝本地file://页面，本轮只验证HTML链接、结构和图片，未验证其浏览器渲染。

Git可执行文件：C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe。系统未将Git加入公共PATH时，可运行本目录Git.cmd代理入口，例如：

~~~cmd
Git.cmd status
Git.cmd diff
Git.cmd log --oneline
Git.cmd add outputs evidence work tasks
Git.cmd diff --staged
Git.cmd commit -m "verify annual report evidence"
~~~

使用项目本地作者身份Investment Workbench Agent / workbench@localhost.invalid保存本轮Agent生成记录；可以在本仓库修改user.name/user.email为你真实身份，不影响全局。没有远程仓库，本地init/add/commit/log/diff/fsck可用；未测试push或GitHub登录。

sources/annual_reports、course、toolkit规范副本和核心产物进Git。原目录副本、重复解包、可重提的PDF全文、Notebook执行缓存、机器环境信息不重复进Git；它们仍保存在本地且清单可追溯。PNG与PDF作为二进制记录，敏感token/env/key排除。
''')
write('Git.cmd','@echo off\ncd /d "%~dp0"\n"C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe" %*\n')
coverage=[]
for x in json.loads((W/'work/reading-index.json').read_text(encoding='utf-8')):
 role='五年年报全文提取及任务相关经营、财务附注深度定位' if x.get('pages') else '全文读取；标题/章节索引，按合同和研究用途分析'
 if 'mineru-pdf-converter' in x['file']:role='全文读取工具代码/说明，不执行；用途为PDF转换与API请求'
 coverage.append([x['file'],x.get('pages','文本'),x['chars'],role])
write('docs/reading-coverage.md','# 阅读与分析覆盖说明\n\n所有原件均已字节读取，原PDF五份657页全文提取，53份唯一文本资产全文解析。关键任务合同、相关课件与年报表格另作内容分析和定位；不声称每条员工名单或每项无关附注都进行了财务审计。重复内容不重复分析；Apple元数据仅登记。\n\n'+table(['来源','页数或类型','读取字符数','处理方式'],coverage))
write('工作流程与文件说明.md', '''# 投资学工作空间：工作流程、成果与存放说明

工作空间位于 **本说明所在的工作空间根目录**，建立日期2026-10-02。原目录保持不变，所有新成果在此目录中。

已完成六个压缩包的解包与内容识别、指定五年年报读取、工作台与本地Git建立，以及前四次和Lec03合同要求的自动化准备。人员、签署与学生本人核验由你以后统一完成；当前成果是完整的可审阅准备稿，尚不能宣称课程任务已正式验收关闭。

## 工作流程与采用的材料

![工作流程](docs/images/workflow.png)

先登记原件及ZIP成员，再按正文标题和用途识别，而不是只看文件名。原目录51个文件均读取并计算SHA-256；六个ZIP共154个成员登记，Apple元数据另列。解包找到第一次合同、工作台模板、课件、读本、SVG图片和MinerU工具。五份年报PDF共657页全文提取，53份唯一文本资产形成章节索引，任务相关课件、合同与年报经营/财务披露进一步分析。

这门课要求的研究链是“定位 → 结构化提取 → 口径识别 → 变化核验 → 商业模式命题”。它强调版本、期间、单位、主体、原文定位、Unknown、反证和责任，不能用一篇流畅报告代替。实际阅读覆盖见[覆盖说明](docs/reading-coverage.md)，每份资料用途见[内容登记](docs/material-catalog.md)。

## 工作台为什么这样组织

![实际工作空间构成图](docs/images/workspace-structure.png)

sources保留依据，tasks明确本次要求，work保留候选与修正，evidence仅放本人核验的证据，outputs放阶段成果。docs解释接手方法，scripts与Notebook支持复现，.git保留版本。这样能从任一结论回到原材料，也能知道哪些是自动化输出、哪些由本人裁决。

原目录副本与解包结果在sources/original-tree和sources/unpacked保留；供执行的年报在sources/annual_reports，课程副本在sources/course，工具参考在sources/toolkit。规范副本保持原字节并登记哈希；重复副本不重复进入Git。

## 各次任务成果

| 合同 | 已完成内容 | 存放位置与理由 |
| --- | --- | --- |
| 第一次 | 合并利润表收入63页、归母利润64页；版本、单位、主体与交叉位置 | [first-analysis.md](outputs/first-analysis.md)；检索过程在work/notes.md，候选不冒充Fact |
| 第二次 | 35条五年酒类收入成本记录，加16条2023—2024合并附注记录；21组合计匹配 | [revenue-structure-table.md](outputs/revenue-structure-table.md)；原字段与来源另存work/structured-data.json |
| 第三次 | 12条口径候选；收入及利润两组冲突；采用与排除理由；真实修正 | [metric-scope-decision.md](outputs/metric-scope-decision.md)；保留work/scope-adjudication.md供本人裁决 |
| 第四次 | 两期原值、版本与可比性定位、公式代入、年报披露比例、停止条件 | [change-verification-record.md](outputs/change-verification-record.md)；本人确认后才正式复算，未强行计算 |
| Lec03 | 六条叙事变量矩阵、业务行业问题、经济逻辑图、优势证据要求、两项本人核验准备 | [矩阵](outputs/lec03-evidence-matrix.md)与[五项成果](outputs/lec03-stage-deliverables.md) |
| 课件补充 | 选题A产品结构、披露地图、组件选择、反方质询和个人提交提示 | outputs/lec01-decision-card.md、lec02-disclosure-map.md、lec02-component-choice.md、red-team-review.md |

全套合同原条款保留在tasks/01—05文件，追加工作空间执行说明。没有收到第五次及更后续独立合同，也没有Lec04—05完整材料；不能用自编要求冒充已发作业，后续验证问题已明确登记。

## 实际发现与修正

2024年9页经营分析分解的是酒类主营业务170,611,838,052.02元，108页合并附注的营业收入170,899,152,276.34元还含其他业务。地区和渠道分解也不同。于是保留两组而不是改掉原记录或硬凑合计。集团营业总收入还另含利息收入，与营业收入不能互换；母公司单体和归母盈利也分别保留。

![原年报108页实际截图](docs/images/pdf-2024-p108.png)

2022年原报归母净利润62,716,443,738.27元，与2023报告2022比较数62,717,467,870.12元不同。2023年86页解释第16号追溯调整是相关披露，保留版本冲突并停止混算。对品牌、渠道、行业阶段和现金转换，只生成有替代解释及反证的候选机制，不宣称护城河已证实。

![商业模式逻辑图](docs/images/business-model.png)

## 环境、Git与验证

使用已有D:/Anaconda/python.exe及本机依赖，未下载插件、未安装包、未修改全局环境。默认PowerShell有CET启动兼容问题，实际执行使用cmd。工作空间提供打开研究笔记.cmd、运行检查.cmd、Git.cmd及编辑器工作空间文件，详情见[运行指南](docs/run-guide.md)。

本地Git已建立，按资料工作台、各次研究和最终说明保存有意义的版本；提交作者明确为Agent生成记录。原文PDF、规范课件和研究成果进入版本库；冗余解包、全文缓存及本地环境文件留在本机清单中。没有连接远程仓库或执行发布。版本记录见[Git记录](docs/git-history.md)。

实际检查包括原件哈希、规范副本哈希、第二种PDF引擎的数值匹配、21组合计、合同条款完整性、文件链接、脚本语法、零基数/重述/单位/合并范围阻断、真实Jupyter内核执行及Git完整性。结果见[检查报告](docs/verification-report.md)。这些检查保证准备稿可追溯与可运行，不替代本人证据核验。

内置浏览器的安全策略拒绝打开本地file://工作台页面，因此HTML浏览器预览未验证；HTML链接与图片做静态检查，说明图片与原PDF截图已作图像检查。

## 所有生成文件在哪里

scripts/__pycache__/存放Python编译缓存，config/.ipython/、config/.jupyter/、config/.jupyter-runtime/存放本地笔记运行配置和缓存；.git内部对象保存版本。这些运行目录按用途说明，不逐个列入研究成果清单。

最常用入口是README.md、工作台.html与本说明；合同在tasks，阶段成果在outputs，详细候选和日志在work，人工表和已确认账本在evidence，图片在docs/images，程序在scripts，环境在config，Notebook在根目录research.ipynb。完整逐文件位置与用途见[全部文件清单](docs/generated-files.md)，源资料副本对照见material-catalog.md和work/source-inventory.json。

## 你以后统一填写的事项

人员与签署栏保持空白。课件明确要求本人回到PDF核验，故Fact已签认数量仍为0；63条证据候选已准备，第四次计算在七项可比性未人工确认前停止。先按[本人核验指南](docs/human-review-guide.md)完成实际核验、口径取舍和公式复算，再登记证据与签署合同。Unknown保留缺证或不可比内容，不必为追求“全部完成”补造事实。
''')
# Local dashboard: standalone file, no network or package dependencies.
cards=[('第一次：定位','outputs/first-analysis.md'),('第二次：结构提取','outputs/revenue-structure-table.md'),('第三次：口径卡','outputs/metric-scope-decision.md'),('第四次：变化准备','outputs/change-verification-record.md'),('Lec03：证据矩阵','outputs/lec03-evidence-matrix.md'),('Lec03：五项成果','outputs/lec03-stage-deliverables.md')]
content=''.join('<a class="card" href="'+p+'"><span>准备稿 · 待本人核验</span><h2>'+t+'</h2><p>'+p+'</p></a>' for t,p in cards)
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>投资学工作台</title><style>body{margin:0;background:#f4f7fb;color:#1b344e;font:17px Microsoft YaHei,sans-serif}main{max-width:1150px;margin:48px auto;padding:0 26px}h1{font-size:40px}header p{color:#587087}.metrics,.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:28px 0}.card,.stat{background:white;border:1px solid #d8e3ed;border-radius:16px;padding:25px;text-decoration:none;color:inherit}.card span{font-size:14px;color:#a06c27}.card h2{font-size:23px}.card p{font-size:14px;color:#587087;overflow-wrap:anywhere}.stat strong{display:block;font-size:32px}.notice{border-left:5px solid #c39136;background:#fff5df;padding:20px;line-height:1.8}nav{display:flex;gap:22px;flex-wrap:wrap;margin:25px 0}nav a{color:#236d9d}img{width:100%;border-radius:16px}footer{color:#587087;margin:30px 0}@media(max-width:700px){.metrics,.grid{grid-template-columns:1fr}}</style><main><header><p>600519 · 贵州茅台 · 2020—2024年指定资料</p><h1>投资学工作台</h1><p>资料、任务、过程、证据与版本在同一工作空间。建立日期2026-10-02。</p></header><div class="metrics"><div class="stat"><strong>657页</strong>五份PDF全文读取</div><div class="stat"><strong>51条</strong>收入与成本候选</div><div class="stat"><strong>21组</strong>同口径分项合计匹配</div></div><div class="notice">自动化准备与检查已完成。人员、签署及学生本人核验留待填写；已人工签认Fact为0条。第四次正式计算须先完成人工可比性确认。</div><nav><a href="工作流程与文件说明.md">带图片工作说明</a><a href="docs/human-review-guide.md">本人核验指南</a><a href="docs/material-catalog.md">资料内容索引</a><a href="docs/generated-files.md">全部文件位置</a><a href="docs/verification-report.md">检查记录</a><a href="research.ipynb">研究Notebook</a></nav><div class="grid">'''+content+'''</div><img src="docs/images/workspace-structure.png" alt="工作空间构成"><footer>完全本地，无外部依赖；源报告保留原样。Markdown链接可用编辑器阅读，PDF从sources目录打开。</footer></main></html>'''
write('工作台.html',page)
print('README, local dashboard and illustrated workflow documentation generated')
