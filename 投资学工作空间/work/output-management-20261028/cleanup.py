from pathlib import Path
import hashlib,json,subprocess,sys,re,html,time,os
from urllib.parse import unquote
R=Path('D:/投资学');W=R/'投资学工作空间';O=W/'outputs';P=W/'work/output-management-20261028'
P.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,t):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding='utf8')
def js(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def git(*a):
 for attempt in range(20):
  r=subprocess.run(['git','-C',str(R),*a],capture_output=True,text=True,encoding='utf8')
  if 'index.lock' not in r.stderr:break
  time.sleep(.3)
 if r.returncode:raise RuntimeError(str(a)+'\n'+r.stderr)
 return r.stdout.strip()
def push():
 git('push','origin','main')
 h=git('rev-parse','HEAD');assert git('ls-remote','origin','refs/heads/main').split()[0]==h
 return h
assert git('remote','get-url','origin')=='git@github.com:Loyyed/Investment_yw_10-1_begin.git'
assert git('branch','--show-current')=='main' and not git('diff','--cached','--name-only')
before={p.relative_to(O).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in O.rglob('*') if p.is_file()}
remove_dirs=['research-atlas','research-atlas-v2']
remove_names=['研究结论与合同回答_V2.1.html','研究结论与合同回答_V2.1.md','证券投资分析研究图册_V2.0.html','证券投资分析研究图册_V2.1.html','投资研究系统_V2.0_总入口.html','投资分析系统与茅台研究_路演V2.0.html','投资分析系统与茅台研究_逐页讲稿V2.0.md']
gone=[p for d in remove_dirs for p in (O/d).rglob('*') if p.is_file()]+[O/n for n in remove_names]
moves={}
for n in ['投资分析系统与茅台研究_任务框架与经验V2.0.html','投资分析系统与茅台研究_任务框架与经验V2.0.md']:
 moves[O/n]=O/'03_方法与图表'/n
for p in (O/'images').iterdir():
 if p.is_file():moves[p]=O/'03_方法与图表/images'/p.name
moves[O/'research-atlas/visual-gallery.html']=O/'03_方法与图表/图表图库.html'
def outpath(p):assert p.resolve().is_relative_to(O.resolve()) and not p.is_symlink();return p
for p in gone+list(moves):outpath(p)
# Preserve all frozen/authority-bound materials and every roadshow byte.
excluded=set(gone)|set(moves)|{O/'00_从这里开始.html',O/'README.md',O/'文件目录.json',O/'全任务合同核查与覆盖清单.html',O/'全任务合同核查与覆盖清单.md'}
protected={str(p):sha(p) for root in [W/'sources',W/'evidence',O] for p in root.rglob('*') if p.is_file() and p not in excluded}
sys.path[:0]=[str(W/'scripts'),str(R/'投资学公司分析通用工作台')]
from review_store import ReviewStore
from companybench import insight
store=ReviewStore(W);domain={n:len(getattr(store,n)()) for n in ['facts','change_facts','lec03_agent_facts','m01_metric_facts','m01_scale_facts','m01_disclosure_facts']}
spec=json.loads((W/'work/t5-forecast-20261027/report-spec.json').read_text(encoding='utf8'))
authority_before=insight.validate_current(W,spec)
js(P/'plan.json',dict(repository='Loyyed/Investment_yw_10-1_begin',branch='main',remove=[p.relative_to(O).as_posix() for p in gone],move={p.relative_to(O).as_posix():q.relative_to(O).as_posix() for p,q in moves.items()},roadshow='exclude all files',original_files='exclude all files'))
# Exact original bytes are saved in the same already-authorized remote before deletion.
historical=sorted(set(gone)|set(moves))
for p in historical:
 blob=git('hash-object','-w','--no-filters',str(p))
 git('update-index','--add','--cacheinfo','100644',blob,p.relative_to(R).as_posix())
if git('diff','--cached','--name-only'):git('commit','-m','保存分章冗余清理前的输出原字节')
history=push()
for p in historical:assert git('rev-parse',history+':'+p.relative_to(R).as_posix())==git('hash-object','--no-filters',str(p))
mapping={**moves}
anchor=lambda p: 'overview' if p.stem in ['overview','visual-gallery'] else p.stem
for p in gone:
 if p in moves:continue
 if p.parent.name.startswith('research-atlas'):mapping[p]=O/('证券投资分析研究图册_V2.2.html#'+anchor(p))
for n in remove_names:
 if '图册' in n:target='证券投资分析研究图册_V2.2.html'
 elif '合同回答' in n:target='研究结论与合同回答_V2.2'+Path(n).suffix
 elif '路演' in n:target='01_路演与讲稿/投资分析系统与茅台研究_首次听众路演V2.5.html'
 elif '逐页讲稿' in n:target='01_路演与讲稿/投资分析系统与茅台研究_首次听众逐页讲稿V2.5.md'
 else:target='00_从这里开始.html'
 mapping[O/n]=O/target
def url(raw,origin,dest):
 if not raw or raw.startswith(('#','/','?')) or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',raw):return raw
 parts=re.split('([?#])',html.unescape(unquote(raw)),maxsplit=1);src=(origin/parts[0]).resolve();tail=''.join(parts[1:])
 target=mapping.get(src,src)
 # Path containing the deliberate anchor is normalized only at serialization.
 rel=Path(os.path.relpath(target,dest)).as_posix()
 return rel+(tail if '#' not in rel else '')
def rebase(t,src,dst,kind):
 if kind=='.html':
  return re.sub(r"""((?:href|src)\s*=\s*["'])([^"']+)(["'])""",lambda m:m[1]+html.escape(url(m[2],src,dst),quote=True)+m[3],t)
 if kind=='.md':return re.sub(r'(\]\()([^)]+)(\))',lambda m:m[1]+url(m[2],src,dst)+m[3],t)
 return t
# Rebase only the movable method documents; immutable source-bound files keep all bytes.
for p,q in moves.items():
 assert not q.exists()
 if p.suffix in ['.html','.md']:write(q,rebase(p.read_text(encoding='utf8'),p.parent,q.parent,p.suffix))
 else:q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
for n in ['全任务合同核查与覆盖清单.html','全任务合同核查与覆盖清单.md']:
 p=O/n;write(p,rebase(p.read_text(encoding='utf8'),O,O,p.suffix))
for p in sorted(set(gone)|set(moves)):
 outpath(p).unlink()
for d in [*(O/x for x in remove_dirs),O/'images']:
 if d.exists():
  for child in sorted(d.rglob('*'),key=lambda p:len(p.parts),reverse=True):
   if child.is_dir():outpath(child).rmdir()
  outpath(d).rmdir()
# Catalog and primary portal offer current outputs by purpose; no history copies.
organizer=r'''"""Maintain current output navigation. Never copy history into outputs."""
from pathlib import Path
import json,hashlib,html
W=Path(__file__).resolve().parents[1];O=W/'outputs'
def category(p):
 if p.startswith('01_路演与讲稿/'):return '路演与讲稿'
 if p.startswith('02_Lec05'):return 'Lec05新成果'
 if p.startswith('03_方法与图表/'):return '方法与图表'
 if p.endswith(('.xlsx','.csv','.json')):return '复算与数据'
 if p.endswith('.md') and p!='README.md':return '专题与核验'
 return '当前综合成果'
rows=[dict(path=p.relative_to(O).as_posix(),category=category(p.relative_to(O).as_posix()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['文件目录.json','00_从这里开始.html']]
def a(p,t):return '<a href="'+html.escape(p,quote=True)+'">'+html.escape(t)+'</a>'
css='body{font:17px/1.9 Microsoft YaHei,sans-serif;background:#f3f5f0;color:#173f38;margin:0}main{max-width:1100px;margin:auto;padding:40px 24px}h1{font-size:36px}a{color:#126b61}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}.cards a{background:white;border:1px solid #becfc2;border-radius:10px;padding:22px;display:block;text-decoration:none;font-size:21px}details{margin:20px 0;padding:20px;background:white;border:1px solid #ccd8cc;border-radius:10px}summary{cursor:pointer;font-size:21px}li{overflow-wrap:anywhere}'
main=[('01_路演与讲稿/投资分析系统与茅台研究_首次听众路演V2.5.html','路演 V2.5'),('01_路演与讲稿/投资分析系统与茅台研究_首次听众讲稿V2.5.html','配套讲稿'),('证券投资分析研究图册_V2.2.html','当前研究图册'),('研究结论与合同回答_V2.2.html','综合研究与合同回答'),('02_Lec05叙事与估值/index.html','Lec05三项成果'),('全任务合同核查与覆盖清单.html','原合同覆盖清单')]
body='<h1>投资研究成果</h1><p>先选当前成果，再按用途查找专题。历史版本保存在GitHub，不放在本目录。</p><div class="cards">'+''.join(a(p,t) for p,t in main)+'</div>'
for cat in ['方法与图表','专题与核验','复算与数据','当前综合成果']:
 items=[r for r in rows if r['category']==cat and not r['path'].endswith(('.png','.svg'))]
 body+='<details><summary>'+cat+' · '+str(len(items))+'</summary><ul>'+''.join('<li>'+a(r['path'],Path(r['path']).name)+'</li>' for r in items)+'</ul></details>'
body+='<p>'+a('../docs/20261028-output-policy.md','目录规则与历史恢复')+' · '+a('文件目录.json','全部文件与指纹')+'</p>'
(O/'00_从这里开始.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>投资研究成果</title><style>'+css+'</style><main>'+body+'</main></html>',encoding='utf8')
portal=O/'00_从这里开始.html';rows.append(dict(path=portal.name,category='当前综合成果',bytes=portal.stat().st_size,sha256=hashlib.sha256(portal.read_bytes()).hexdigest()))
(O/'文件目录.json').write_text(json.dumps(dict(date='2026-10-28',policy='current outputs only; history in GitHub; no physical backups',files=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
'''
write(W/'scripts/organize_outputs.py',organizer)
write(O/'README.md',"""# 当前成果

打开 [00_从这里开始.html](00_从这里开始.html)，按当前研究、课程成果、方法图表、专题核验、复算数据查找。

- 01_路演与讲稿：保留原字节，本轮未改。
- 02_Lec05叙事与估值：本轮三项课程成果。
- 03_方法与图表：框架说明、图表图库与配套图片。
- 根目录专题与核验稿保留原路径及字节，避免来源/审阅绑定失效。
- 完整图册只保留当前版本；重复分章目录与无用旧入口已撤下。
- 历史只保存在GitHub，不在outputs建立archive、备份、历史副本。
- 修改成果后检查引用与保护文件，提交并push同一公司远端。目录更新运行scripts/organize_outputs.py；图册重建后须接回Lec05章。
""")
assert all(Path(p).is_file() and sha(Path(p))==v for p,v in protected.items()),'保护文件变化'
assert {n:len(getattr(store,n)()) for n in domain}==domain
assert insight.validate_current(W,spec)==authority_before
# Verify local references for every remaining output; never repair immutable material blindly.
def check_links():
 missing=[];count=0
 for p in O.rglob('*'):
  if p.suffix not in ['.html','.md']:continue
  t=p.read_text(encoding='utf8')
  refs=[m[1] for m in re.finditer(r"""(?:href|src)\s*=\s*["']([^"']+)["']""",t)] if p.suffix=='.html' else re.findall(r'\]\(([^)]+)\)',t)
  for raw in refs:
   if raw.startswith(('#','/','?')) or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',raw):continue
   rel=re.split('[?#]',html.unescape(unquote(raw)),maxsplit=1)[0]
   if not rel:continue
   count+=1
   if not (p.parent/rel).exists():missing.append(dict(file=p.relative_to(O).as_posix(),target=raw))
 return count,missing
write(W/'docs/20261028-output-policy.md',f"""# outputs当前成果管理

2026-10-28。用户要求历史依靠GitHub，不在outputs做物理备份，并排除01_路演与讲稿。

保留当前完整图册、综合报告、课程成果、复算数据及来源绑定专题。两个重复分章目录已合并到当前总图册；图表图库、框架说明及图片集中到03_方法与图表。清理前原字节已提交并核验GitHub：{history}。历史恢复使用git show 提交:原路径，恢复目标选临时工作目录，不写回outputs充当备份。

根目录部分专题被核验/内容审阅绑定，所以保留原路径和字节；统一入口已按用途归类。旧日期不自动表示历史废稿，已采纳展示或唯一底稿不会仅按文件日期删除。

后续发布同一origin（Loyyed/Investment_yw_10-1_begin/main）；每次修改后提交并push。新生成器不得再制造重复分章、archive或历史副本；导航用scripts/organize_outputs.py更新，不调用路演生成器。

无新Fact、内容采纳、签署。详细变更清单、校验与发布回执在work/output-management-20261028。
""")
cur=R/'会话交接/CURRENT.md'
write(cur,cur.read_text(encoding='utf8')+f'\n\n## 2026-10-28二次输出精简\n\n按本人再次要求，完整重复分章目录已撤下，旧入口撤下，方法图表集中到outputs/03_方法与图表；当前入口按用途分类。历史原字节已在GitHub提交{history}核验，outputs不保留物理历史。01_路演与讲稿与原核验/采纳绑定文件保持字节；事实/来源动态验证通过。方法说明docs/20261028-output-policy.md，清单与回执work/output-management-20261028；以后每次修改提交并push同一公司远端，不创建outputs历史备份。\n')
subprocess.run([sys.executable,'-B',str(W/'scripts/organize_outputs.py')],check=True)
count,missing=check_links();js(P/'link-check.json',dict(checked=count,missing=missing))
assert not missing,missing
after={p.relative_to(O).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in O.rglob('*') if p.is_file()}
stats=dict(before_files=len(before),after_files=len(after),before_bytes=sum(x['bytes'] for x in before.values()),after_bytes=sum(x['bytes'] for x in after.values()),history_commit=history,protected_files=len(protected),roadshow_unchanged=True,fact_domains=domain,authority_unchanged=True,local_links_checked=count,missing_links=0)
js(P/'validation.json',stats)
# Persist the exact operation source for review, never in outputs.
write(P/'cleanup.py',Path(__file__).read_text(encoding='utf8'))
paths=set(gone)|set(moves)|set(moves.values())|{O/'README.md',O/'00_从这里开始.html',O/'文件目录.json',O/'全任务合同核查与覆盖清单.html',O/'全任务合同核查与覆盖清单.md',W/'scripts/organize_outputs.py',W/'docs/20261028-output-policy.md',cur}
paths|={P/'plan.json',P/'validation.json',P/'link-check.json',P/'cleanup.py'}
assert all(not p.is_relative_to(O/'01_路演与讲稿') for p in paths)
git('add','-A','--',*[p.relative_to(R).as_posix() for p in sorted(paths)])
assert set(git('diff','--cached','--name-only').splitlines())<=set(p.relative_to(R).as_posix() for p in paths)
git('commit','-m','合并重复图册分章与旧入口，集中方法图表并规范输出目录')
commit=push()
js(P/'publication-receipt.json',dict(repository='https://github.com/Loyyed/Investment_yw_10-1_begin',branch='main',commit=commit,remote_verified=True,history_commit=history,paths=git('show','--format=','--name-only',commit).splitlines()))
print(json.dumps(dict(stats=stats,commit=commit),ensure_ascii=False))
