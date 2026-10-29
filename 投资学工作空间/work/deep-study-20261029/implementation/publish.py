from pathlib import Path
import subprocess,json,hashlib,sys
sys.stdout.reconfigure(encoding='utf-8');r=Path(__file__).parent;top=Path('D:/投资学');b=top/'投资学公司分析通用工作台';out=top/'投资学工作空间/work/deep-study-20261029'
scope=json.loads((out/'publication-scope.json').read_text(encoding='utf-8'))
def git(repo,*args):
 q=subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True,encoding='utf-8');
 if q.returncode:raise RuntimeError(q.stderr or q.stdout)
 return q.stdout.strip()
repos=[('company',top,'Investment_yw_10-1_begin'),('toolkit',b,'Investment_yw_finaltask')]
action=sys.argv[1]
if action=='review':
 scope['company']=sorted(set(scope['company']+['投资学工作空间/work/deep-study-20261029/publication-scope.json']))
 (out/'publication-scope.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2),encoding='utf-8')
 review={}
 for key,repo,expected in repos:
  remote=git(repo,'remote','get-url','origin');assert expected in remote and 'Loyyed' in remote
  assert git(repo,'branch','--show-current')=='main'
  assert not git(repo,'diff','--cached','--name-only'),'已有暂存内容，停止混入'
  files=scope[key];review[key]=[{'path':p,'sha256':hashlib.sha256((repo/p).read_bytes()).hexdigest(),'bytes':(repo/p).stat().st_size} for p in files]
  assert all(not p.endswith(('.pdf','.zip','.png')) for p in files)
  print(key,'branch main','expected remote',expected,'files',len(files))
  print(git(repo,'diff','--stat','--',*files))
  print('new files',json.dumps([p for p in files if not git(repo,'ls-files','--',p)],ensure_ascii=False))
 (out/'publication-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
elif action=='stage':
 review=json.loads((out/'publication-review.json').read_text(encoding='utf-8'))
 for key,repo,_ in repos:
  for f in review[key]:assert hashlib.sha256((repo/f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
  existing=set(filter(None,git(repo,'diff','--cached','--name-only','-z').split(chr(0))))
  assert not existing or existing==set(scope[key])
  git(repo,'add','-f','--',*scope[key])
  print(key,git(repo,'diff','--cached','--stat'))
  git(repo,'-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check')
  names=git(repo,'diff','--cached','--name-only','-z').split(chr(0));assert set(filter(None,names))==set(scope[key])
  print('staged scope and whitespace verified')
elif action=='push':
 review=json.loads((out/'publication-review.json').read_text(encoding='utf-8'));receipt={}
 for key,repo,expected in repos:
  for f in review[key]:assert hashlib.sha256((repo/f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
  staged=set(filter(None,git(repo,'diff','--cached','--name-only','-z').split(chr(0))));assert staged==set(scope[key])
  print(git(repo,'commit','-m','深化收入与价值兑现研究，接入可检索方法知识库'))
  print(git(repo,'push','origin','main'))
  head=git(repo,'rev-parse','HEAD');remote=git(repo,'ls-remote','origin','refs/heads/main').split()[0];assert head==remote
  receipt[key]={'commit':head,'remote_head':remote,'remote':'https://github.com/Loyyed/'+expected,'files':len(scope[key]),'raw_sources_uploaded':False};print(key,head)
 (out/'publication-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
else:raise ValueError(action)
