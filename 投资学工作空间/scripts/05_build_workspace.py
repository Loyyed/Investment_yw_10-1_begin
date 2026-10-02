from pathlib import Path
import json,shutil,sys,importlib.metadata
sys.stdout.reconfigure(encoding='utf-8')
W=Path(__file__).resolve().parents[1]
from workspace_utils import guard_generated_writes
guard_generated_writes(W, "05_build_workspace.py")
D=json.loads((W/'work/structured-data.json').read_text(encoding='utf-8'))
IDX=json.loads((W/'work/reading-index.json').read_text(encoding='utf-8'))
def write(p,t):
 f=W/p; f.parent.mkdir(parents=True,exist_ok=True); f.write_text(t.strip()+'\n',encoding='utf-8')
def table(headers,rows):
 def c(x):return str(x).replace('|','／').replace('\n','；')
 return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(c(x) for x in row)+' |' for row in rows)+'\n'
cat=[]
for item in IDX:
 if 'sections' not in item or 'annual_reports' in item['file']:continue
 p=W/item['file']; name=p.name
 if '贵州茅台年报_' in str(p) or 'MinerU' in name:continue
 if 'mineru-pdf-converter' in str(p):folder='toolkit/mineru-reference'
 elif 'Lec03课件' in str(p) or 'lec03' in name.lower():folder='course/lec03'
 elif '03_学生材料(2)' in str(p) or 'lec02' in name or '第02' in name:folder='course/lec02'
 elif '03_学生材料' in str(p) or 'Lec_01' in name or 'Appendix_' in name:folder='course/lec01'
 else:folder='course/project-reference'
 if '年报研究工作台模板' in str(p): folder+='/'+'/'.join(p.parts[p.parts.index('年报研究工作台模板'):-1])
 elif 'scripts' in p.parts:folder+='/scripts'
 elif 'references' in p.parts:folder+='/references'
 target=W/'sources'/folder/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,target)
 role='原课件与协作方法'
 if '合同' in name or '任务' in name:role='任务边界、字段与交付要求'
 elif 'toolkit' in folder:role='PDF转换工具参考；已具备PDF/MD，不安装或调用API'
 elif p.suffix=='.svg':role='课件结构与流程图'
 cat.append([target.relative_to(W).as_posix(),p.relative_to(W).as_posix(),item['sha256'],role])
write('docs/material-catalog.md','# 资料内容与用途登记\n\n原名按原样保留，按正文和用途分类；ZIP成员按编码解码，源压缩包不改动。\n\n'+table(['规范副本','原始或解包位置','SHA-256','用途'],cat)+'''\n资料缺口：学生清单中的“lec03_专业读本”实际发放名为“lec03_摘要读本”，正文标题为专业读本。原课件引用教师Mac路径、Wiki、课程蓝图以及Lec04—05完整课件，未包含在当前资料中；只登记缺失，不补造。两份Lec02版本分别保留。\n\n[实际专业读本](../sources/original-tree/学生用/lec03_摘要读本_商业模式、行业竞争与竞争优势.md)\n[Lec03主课件](../sources/course/lec03/lec03_商业模式、行业竞争与竞争优势.md)\n[附件2](../sources/course/lec03/Append2_lec03.md)\n\n完整成员清单见work/source-inventory.json；__MACOSX、._*和.DS_Store为Apple元数据，仅登记不作为课程内容。全文读取索引见work/reading-index.json。\n''')
base=W/'sources/unpacked/03_学生材料(2)/03_学生材料/年报研究工作台模板/tasks'
contracts=[(base/'第一次任务合同.md','01-first-task.md','仅2024年PDF；定位收入和归母净利润'),(W/'sources/original-tree/学生用/第二次任务合同_年报收入信息结构化提取.md','02-revenue-extraction.md','2024年PDF和对应MD为主；指定2020—2023年补充定位'),(W/'sources/original-tree/学生用/第三次任务合同_年报指标口径识别.md','03-metric-scope.md','2024年PDF及第二次成果；收入、利润两组口径冲突'),(W/'sources/original-tree/学生用/第四次任务合同_年报指标变化核验.md','04-change-verification.md','2024年PDF中的本期及2023年比较列'),(W/'sources/original-tree/学生用/Lec03任务合同_商业模式与竞争优势证据表.md','05-lec03-business-model.md','指定五份年报和Lec03课件；不新增外部行业资料')]
for src,name,bound in contracts:
 t=src.read_text(encoding='utf-8').replace('- **研究公司**：','- **研究公司**：贵州茅台酒股份有限公司（600519）')
 t+='\n\n---\n\n## 本工作空间执行说明\n\n公司：贵州茅台（600519）；执行日期2026-10-02。\n材料：'+bound+'。\n合同来源：'+src.relative_to(W).as_posix()+'；正文条款完整保留。\n执行人：__________；复核人：__________；签署日期：__________。\n状态：自动化定位、整理和检查已完成；人工核验未完成，合同尚未正式关闭。\n人工入口：docs/human-review-guide.md。\n'
 write('tasks/'+name,t)
write('tasks/00-execution-mandate.md', '''# 本次执行合同

目标：按发放资料建立可接手的投资学工作台，完成定位、结构化提取、口径识别、变化核验准备和商业模式命题准备。
场景：2026秋金融专硕投资学作业；贵州茅台600519。用户授权使用本机软件和创建工作空间，签名及人员信息由用户以后统一填写。
材料：教师指定2020—2024年PDF、MD、课件和任务合同。第一次只读2024PDF；MD只作后续检索。信息集限定发放报告，不引入2026年行情、新闻或期后公告。文件名披露日期仅作版本标签，未外部核实。
过程：记录SHA-256、PDF及报告页码、原指标名称、单位、期间、主体、口径、来源和Unknown。自动核对不替代人工核验。
成果：合同指定六份阶段输出，另补齐课件要求的披露地图、红队问题、Decision Card准备稿及带图片说明。未安装或连接Claude、MinerU或外部服务。
验收：原材料未改、目录齐全、51条收入成本候选与15条主指标可回PDF，21组合计匹配，Git版本和差异可读。学生本人核验、口径选择及签署由本人承担。
''')
rules='''# 项目协作规则

- 执行前读取README.md、CLAUDE.md和当前tasks合同。
- sources保持原样；不得修改原文，不把摘要当成来源。工作空间外原件不动。
- 自动检索、提取、核对写work。只有学生本人回PDF核验并取得证据编号后才写evidence/evidence-log.md并标Fact。
- 分开标Fact、Interpretation、Forecast、Decision、Unknown；机器核对不等于人工核验。
- 不访问合同外网页或数据库，不混入期后信息，不作买卖建议。
- 变化计算读取config/human-review.json；可比性字段未全部人工确认就停止。零基数、定义/合并范围/单位/币种变化或重述立即停止。
- 保留被排除候选、真实修正和Unknown；不得伪造学生错误、核验、签名或独立审阅。
- 新产物只写本工作空间；先看差异再保存Git版本，不作强制回滚。
'''
write('AGENTS.md',rules);write('CLAUDE.md',rules+'\n这些规则适用于任何Agent，目录用途见README.md。')
write('.gitignore','''__pycache__/
*.py[cod]
.ipynb_checkpoints/
.venv/
.env
.env.*
*.token
*.key
.DS_Store
__MACOSX/
sources/original-tree/
sources/unpacked/
work/pdf-text/
work/notebook-executed.ipynb
config/environment-*.json
work/review-ui-upgrade-backup/
evidence/.review-state.lock
.claude/settings.local.json
config/.ipython/
config/.jupyter/
config/.jupyter-runtime/
''')
write('.gitattributes','* text=auto\n*.md text eol=lf\n*.py text eol=lf\n*.json text eol=lf\n*.cmd text eol=crlf\n*.pdf binary\n*.png binary')
review={'execute_person':'','review_person':'','review_date':'','human_confirmation':{k:False for k in ['report_version','periods','unit_currency','reporting_entity','consolidation_scope','metric_definition','no_restatement']},'confirmed_evidence_ids':[],'note':'本人完成PDF核验后才能改为true；Agent不代填人名和签名。'}
if not (W/'config/human-review.json').exists(): write('config/human-review.json',json.dumps(review,ensure_ascii=False,indent=2))
settings={'python.defaultInterpreterPath':'D:/Anaconda/python.exe','files.encoding':'utf8','files.autoSave':'afterDelay','editor.wordWrap':'on'}
write('.vscode/settings.json',json.dumps(settings,ensure_ascii=False,indent=2));write('投资学工作空间.code-workspace',json.dumps({'folders':[{'path':'.'}],'settings':settings},ensure_ascii=False,indent=2))
versions={n:importlib.metadata.version(n) for n in ['numpy','pandas','matplotlib','pypdf','pdfplumber','pypdfium2','PyMuPDF','nbformat','nbclient','jupyterlab','jupyter_client','ipykernel','pillow']}
write('config/dependencies.json',json.dumps(versions,ensure_ascii=False,indent=2))
write('environment.yml','name: investments-workbench\nchannels:\n  - defaults\ndependencies:\n  - python=3.12\n  - pip\n  - pip:\n'+''.join('    - '+k+'=='+v+'\n' for k,v in versions.items()))
write('打开研究笔记.cmd','@echo off\ncd /d "%~dp0"\nset "IPYTHONDIR=%~dp0config\\.ipython"\nset "JUPYTER_CONFIG_DIR=%~dp0config\\.jupyter"\nset "JUPYTER_RUNTIME_DIR=%~dp0config\\.jupyter-runtime"\n"D:/Anaconda/python.exe" -m jupyter lab research.ipynb\n')
write('运行检查.cmd','@echo off\ncd /d "%~dp0"\n"D:/Anaconda/python.exe" scripts/08_validate.py\npause\n')
write('sources/manifest.json',json.dumps(D['reports'],ensure_ascii=False,indent=2))
print('Workspace infrastructure, source catalog and five contracts generated')
