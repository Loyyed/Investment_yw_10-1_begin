from pathlib import Path
import json,hashlib
from review_store import ReviewStore
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def current_lec05_review(workspace):
 w=Path(workspace);data=json.loads((w/'evidence/lec05-content-review.json').read_text(encoding='utf8'));s=ReviewStore(w);facts={x['id']:x for x in s.facts()};ds={x['id']:x for x in s.m01_disclosure_facts()};out=[]
 for r in data['records']:
  errors=[]
  for id,b in r['facts_bindings'].items():
   if id not in facts or facts[id]['state']!='Fact' or facts[id]['binding']!=b:errors.append(id+' binding changed')
  if ds.get(r['disclosure']['id'])!=r['disclosure']:errors.append('disclosure changed')
  if digest(w/r['model_path'])!=r['model_sha256']:errors.append('model changed')
  if digest(w/r['source_manifest_path'])!=r['source_manifest_sha256']:errors.append('source manifest changed')
  manifest=json.loads((w/r['source_manifest_path']).read_text(encoding='utf8'))
  for x in manifest:
   p=w.parent/'课件与任务文件/补充材料4'/x['file']
   if digest(p)!=x['sha256']:errors.append(x['file']+' changed')
  if digest(w/'work/lec05-depth-20261028'/ (r['batch_id']+'.json'))!=r['batch_file_sha256']:errors.append('display batch changed')
  out.append(dict(batch_id=r['batch_id'],state='provisionally-current' if not errors else 'stale-awaiting-review',actual_reply=r['actual_user_reply'],item_count=6,errors=errors))
 return out
if __name__=='__main__':
 print(json.dumps(current_lec05_review(Path(__file__).resolve().parents[1]),ensure_ascii=False,indent=2))
