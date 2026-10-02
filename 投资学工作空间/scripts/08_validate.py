from common import *
import sys,re,hashlib,py_compile,importlib.util,os,asyncio
os.environ["IPYTHONDIR"]=str(W/"config/.ipython")
os.environ["JUPYTER_CONFIG_DIR"]=str(W/"config/.jupyter")
os.environ["JUPYTER_RUNTIME_DIR"]=str(W/"config/.jupyter-runtime")
os.environ["PYDEVD_DISABLE_FILE_VALIDATION"]="1"
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from workspace_utils import original_source_root, contract_intact
from review_store import ReviewStore
import pymupdf
from nbclient import NotebookClient
import nbformat
sys.stdout.reconfigure(encoding='utf-8')
checks=[]
def check(name,condition,details=''):
 checks.append({'name':name,'pass':bool(condition),'details':details})
 print(('PASS ' if condition else 'FAIL ')+name)
# Source integrity: original-tree hashes checked against the untouched outside originals.
inv=json.loads((W/'work/source-inventory.json').read_text(encoding='utf-8'))
changed=[]
source_root=original_source_root(W)
for item in inv['files']:
 p=source_root/item['path']
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:changed.append(item['path'])
check('全部51个源文件保持原始字节',not changed,str(changed))
for r in D['reports']:
 for kind in ['pdf','md']:
  p=W/r[kind];check(str(r['year'])+' '+kind+'规范副本SHA-256一致',hashlib.sha256(p.read_bytes()).hexdigest()==r[kind+'_sha256'])
# Independent extraction engine compared to stored candidates.
norm=lambda t:re.sub(r'\s+','',t)
docs={r['year']:pymupdf.open(W/r['pdf']) for r in D['reports']}
bad=[]
for r in D['structure']+D['full_structure']:
 n=r['pdf_pages'][0];t=norm(docs[r['year']][n-1].get_text())
 if not all(norm(r[k]) in t for k in ['revenue_raw','cost_raw']):bad.append(r['id'])
check('51条收入成本候选经独立PDF引擎匹配',not bad,str(bad))
for r in D['summary']:
 t=norm(docs[r['year']][r['pdf_pages'][0]-1].get_text());check(str(r['year'])+' '+r['metric']+'PDF原值匹配',norm(r['raw_current']) in t)
scope=json.loads((W/'work/scope-data.json').read_text(encoding='utf-8'))
check('12条口径候选均匹配2024原PDF',all(money(r[2]) in norm(docs[2024][r[3]-1].get_text()) for r in scope))
check('21组分项与合计一致',len(D['reconciliations'])==21 and all(r['pass'] for r in D['reconciliations']))
check('原始候选保留提取状态，本人核验独立登记',all(r['human_verification']=='待核验' and r['state']=='Unknown' for r in D['structure']+D['full_structure']+D['summary']))
check('2022原报和2023重述比较数分别保留',next(r for r in D['summary'] if r['year']==2022 and '股东' in r['metric'])['current']=='62716443738.27' and next(r for r in D['summary'] if r['year']==2023 and '股东' in r['metric'])['previous']=='62717467870.12')
# Contract texts must remain intact except the explicitly completed company field.
for task in (W/'tasks').glob('0[1-5]-*.md'):
 t=task.read_text(encoding='utf-8');m=re.search('合同来源：(.+?)；正文',t)
 p=W/m[1];original=p.read_text(encoding='utf-8').replace('- **研究公司**：','- **研究公司**：贵州茅台酒股份有限公司（600519）')
 check(task.name+'合同条款完整',contract_intact(t, original))
review_store=ReviewStore(W)
review_store.sync()
valid_facts=review_store.facts()
check('人工确认机器视图与有效Fact一致', len(json.loads((W/'evidence/confirmed-facts.json').read_text(encoding='utf-8'))['facts'])==len(valid_facts))
required=['人工核验入口.cmd','scripts/review_store.py','scripts/review_ui.py','README.md','CLAUDE.md','AGENTS.md','outputs/first-analysis.md','outputs/revenue-structure-table.md','outputs/metric-scope-decision.md','outputs/change-verification-record.md','outputs/lec03-evidence-matrix.md','outputs/lec03-stage-deliverables.md','work/notes.md','work/pending-checks.md','evidence/evidence-log.md','research.ipynb','工作流程与文件说明.md']
check('必需交付文件存在',all((W/p).is_file() and (W/p).stat().st_size>0 for p in required))
# Validate generated Markdown links only. Source snapshots keep original historical links.
broken=[]
for p in [W/'README.md',W/'工作流程与文件说明.md']+list((W/'outputs').glob('*.md'))+list((W/'docs').glob('*.md'))+list((W/'evidence').glob('*.md')):
 if not p.exists():continue
 text=p.read_text(encoding='utf-8')
 for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
  if link.startswith(('http:','https:','#','mailto:')):continue
  target=link.strip('<>').split('#')[0]
  if not (p.parent/target).exists():broken.append(str(p.relative_to(W))+' -> '+link)
check('所有生成Markdown文件链接可定位',not broken,str(broken))
# Static checks do not claim a browser render (local file navigation was denied).
from html.parser import HTMLParser
from urllib.parse import unquote
class LocalLinks(HTMLParser):
 def __init__(self): super().__init__(); self.links=[]; self.scripts=0
 def handle_starttag(self,tag,attrs):
  if tag=='script':self.scripts+=1
  for key,value in attrs:
   if key in ('href','src') and value:self.links.append(value)
html_parser=LocalLinks();html_parser.feed((W/'工作台.html').read_text(encoding='utf-8'))
html_bad=[u for u in html_parser.links if not u.startswith('#') and (u.startswith(('http:','https:','javascript:')) or not (W/unquote(u.split('#')[0])).exists())]
check('本地HTML入口链接及图片可定位',not html_bad,str(html_bad)+'；浏览器渲染未验证')
check('本地HTML无需外部脚本或网络资源',html_parser.scripts==0 and not any(u.startswith(('http:','https:','//')) for u in html_parser.links))
for p in (W/'scripts').glob('*.py'):py_compile.compile(str(p),doraise=True)
check('Python脚本语法全部通过',True)
spec=importlib.util.spec_from_file_location('changes',W/'scripts/07_compute_changes.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
yes={k:True for k in ['report_version','periods','unit_currency','reporting_entity','consolidation_scope','metric_definition','no_restatement']}
check('公式与舍入测试（合成数据）',mod.verified_change('115.715','100',yes)==Decimal('15.72'))
blocked=0
for c,p,flags in [('20','0',yes),('20','10',{**yes,'no_restatement':False}),('20','10',{**yes,'unit_currency':False}),('20','10',{**yes,'consolidation_scope':False})]:
 try:mod.verified_change(c,p,flags)
 except ValueError:blocked+=1
check('零基数／重述／单位／合并范围阻断',blocked==4)
nb=nbformat.read(W/'research.ipynb',as_version=4)
client=NotebookClient(nb,timeout=60,kernel_name='python3',resources={'metadata':{'path':str(W)}})
try:
 client.execute(); nbformat.write(nb,W/'work/notebook-executed.ipynb')
 outputs=''.join(o.get('text','') for c in nb.cells for o in c.get('outputs',[]))
 check('Notebook通过真实Jupyter内核执行',True,outputs[:700])
except Exception as e:check('Notebook通过真实Jupyter内核执行',False,str(e))
result={'date':'2026-10-02','checks':checks,'passed':sum(r['pass'] for r in checks),'failed':sum(not r['pass'] for r in checks),'human_reviewed_fact_count':len(valid_facts),'human_verification_complete':False}
write('work/validation-results.json',json.dumps(result,ensure_ascii=False,indent=2))
write('docs/verification-report.md','# 自动检查记录\n\n执行日期2026-10-02；'+str(result['passed'])+'项通过，'+str(result['failed'])+'项失败。当前有效人工Fact：'+str(len(valid_facts))+'条；合同签署与正式验收另行确认。HTML浏览器渲染未验证。\n\n'+table(['检查','结果','说明'],[[c['name'],'通过' if c['pass'] else '失败',c['details']] for c in checks]))
print('RESULT',result['passed'],'passed,',result['failed'],'failed')
raise SystemExit(1 if result['failed'] else 0)
