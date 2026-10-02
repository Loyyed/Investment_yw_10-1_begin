from common import *
import sys,subprocess
sys.stdout.reconfigure(encoding='utf-8')
G='C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def run(*args):
 r=subprocess.run([G,*args],cwd=W,text=True,encoding='utf-8',capture_output=True,check=True)
 return r.stdout.strip()
def inventory():
 rows=[]; data=[]
 for p in sorted(W.rglob('*')):
  if not p.is_file() or '.git' in p.parts or 'review-ui-upgrade-backup' in p.parts or '__pycache__' in p.parts or any(x in p.parts for x in ['.ipython','.jupyter','.jupyter-runtime']):continue
  rel=p.relative_to(W).as_posix()
  if rel=='docs/generated-files.json':continue
  if rel.startswith('sources/annual_reports/'):why='规范原始年报／对应检索MD；按报告原样留存'
  elif rel.startswith('sources/original-tree/'):why='输入目录副本；保持出处、版本和原ZIP'
  elif rel.startswith('sources/unpacked/'):why='ZIP解包内容；按正文识别，保留原名及出处'
  elif rel.startswith('sources/course/'):why='课程与模板规范副本；按正文用途组织'
  elif rel.startswith('sources/toolkit/'):why='PDF转换工具参考；未安装或执行'
  elif rel.startswith('tasks/'):why='对应研究合同；保留原条款和签署空栏'
  elif rel.startswith('work/pdf-text/'):why='逐页全文缓存；可重建，只辅助定位'
  elif rel.startswith('work/'):why='实际过程、候选、冲突、修正或验证记录'
  elif rel.startswith('evidence/'):why='本人核验专用记录；未伪造Fact'
  elif rel.startswith('outputs/'):why='课件合同的阶段成果准备稿'
  elif rel.startswith('docs/images/pdf-'):why='原报告真实页面截图；页码在文件名'
  elif rel.startswith('docs/images/'):why='用程序绘制的说明图；辅助理解目录与研究逻辑'
  elif rel.startswith('docs/'):why='操作、核验、来源或全部文件说明'
  elif rel.startswith('scripts/'):why='本轮实际使用的可重运行脚本，保留实现与检查方法'
  elif rel.startswith('config/') or rel.startswith('.vscode'):why='环境及人工确认／编辑器配置'
  elif rel=='.gitignore' or rel=='.gitattributes':why='版本排除及文本二进制处理规则'
  elif rel=='research.ipynb':why='可执行研究笔记；数据浏览与合计检查'
  else:why='项目入口、运行器或总说明'
  rows.append([rel,why]); data.append({'path':rel,'purpose':why})
 data.append({'path':'docs/generated-files.json','purpose':'机器可读的全部生成文件位置与理由'})
 rows.append(['docs/generated-files.json','机器可读的全部生成文件位置与理由'])
 write('docs/generated-files.md','# 全部生成文件的位置与理由\n\n以下路径均相对本清单上级的工作空间根目录；目录完整保留在本地。原件51个和ZIP154成员另在work/source-inventory.json逐项登记。Git内部对象不逐个列入教学成果，.git保存提交和差异。scripts/__pycache__/为Python编译缓存；config/.ipython/、config/.jupyter/、config/.jupyter-runtime/为本地笔记运行配置及缓存，均按目录说明、不逐文件列入成果清单。\n\n'+table(['相对路径','为什么放在这里'],rows))
 write('docs/generated-files.json',json.dumps(data,ensure_ascii=False,indent=2))
 print('FILE INVENTORY',len(data),'files')

def git_save():
 run('config','--local','user.name','Investment Workbench Agent');run('config','--local','user.email','workbench@localhost.invalid');run('config','--local','core.quotepath','false');run('config','--local','core.autocrlf','false')
 groups=[('build(workspace): organize sources, contracts and reproducible environment',['.gitignore','.gitattributes','README.md','AGENTS.md','CLAUDE.md','sources/annual_reports','sources/course','sources/toolkit','sources/manifest.json','tasks','config','environment.yml','scripts','Git.cmd','运行检查.cmd','打开研究笔记.cmd','投资学工作空间.code-workspace','.vscode']),('research(task1): preserve PDF metric locations and candidate evidence',['outputs/first-analysis.md','work/notes.md','work/pending-checks.md','work/evidence-candidates.md','evidence']),('research(task2): distinguish wine revenue from full consolidated revenue',['outputs/revenue-structure-table.md','work/revenue-structure-extraction.md','work/structured-data.json','work/source-inventory.json','work/reading-index.json']),('research(task3): retain scope conflicts and excluded metric candidates',['outputs/metric-scope-decision.md','work/metric-scope-candidates.md','work/scope-adjudication.md','work/scope-data.json']),('research(task4): gate comparable changes on human review',['outputs/change-verification-record.md','work/change-verification.md','work/change-recalculation.json'])]
 for message,paths in groups:
  run('add','--',*paths);run('diff','--cached','--check','--','.',':!sources')
  if run('diff','--cached','--name-only'):print(run('commit','-m',message))
 run('add','-A');run('diff','--cached','--check','--','.',':!sources')
 if run('diff','--cached','--name-only'):print(run('commit','-m','research(lec03): add mechanism hypotheses, notebook and illustrated documentation'))
 fsck=run('fsck','--full');history=run('log','--date=iso-strict','--format=%h | %ad | %s')
 write('docs/git-history.md','# Git版本记录\n\n分支main；本地仓库，没有远程配置。作者Investment Workbench Agent明确表示自动化生成历史。按逻辑成果分组提交，不声称学生已进行对应人工核验。\n\n'+table(['历史提交'],[[line] for line in history.splitlines()])+'\nGit fsck --full：通过。此表记录本轮成果提交；其自身的保存提交可用Git.cmd log查看。')
 inventory();run('add','docs/git-history.md','docs/generated-files.md','docs/generated-files.json');run('diff','--cached','--check','--','.',':!sources')
 if run('diff','--cached','--name-only'):print(run('commit','-m','docs(workspace): record git integrity and exhaustive file locations'))
 print('FINAL STATUS',run('status','--porcelain'))
 print('FINAL HEAD',run('rev-parse','--short','HEAD'))
 print('FINAL FSCK',run('fsck','--full') or 'OK')
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='git':git_save()
 else:inventory()
