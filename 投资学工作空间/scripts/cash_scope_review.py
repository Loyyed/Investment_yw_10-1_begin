"""P01 method approval, kept distinct from economic classification and raw facts."""
from pathlib import Path
import json,hashlib
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def current_p01_adoption(project,raw=None,groups=None):
 p=Path(project);path=p/'evidence/cash-scope-review.json'
 if not path.exists():return {'status':'pending','method_approved':False,'economic_classification_complete':False}
 try:
  a=json.loads(path.read_text(encoding='utf-8'));m=json.loads((p/a['display_manifest']).read_text(encoding='utf-8'));payload=dict(m);fp=payload.pop('display_payload_sha256')
  assert fp==digest(payload)==a['display_payload_sha256'] and sha(p/a['display_manifest'])==a['display_manifest_sha256']
  assert a['actual_user_reply']=='我认可P01四项口径' and a['channel']=='actual-user-chat' and a['actor']=='user'
  assert a['approved_ids']==['P01-1','P01-2','P01-3','P01-4'] and not a['new_signature_created'] and not a['economic_classification_complete']
  assert a['validator_sha256']==sha(Path(__file__))
  for item in a['reviewed_context']:assert sha(p/item['path'])==item['sha256']
  assert sha(p/m['calculation_snapshot_path'])==m['calculation_snapshot_sha256']
  assert sha(p/a['reviewed_workbook_snapshot'])==m['spreadsheet_sha256']
  assert digest(m['input_authority_snapshot'])==m['input_authority_snapshot_sha256']
 except (AssertionError,KeyError,ValueError,OSError) as e:return {'status':'stale-record','method_approved':False,'economic_classification_complete':False,'reason':type(e).__name__+': '+str(e)}
 issues=[]
 try:
  if raw is None or groups is None:
   from review_store import ReviewStore
   store=ReviewStore(p)
   if raw is None:raw={x['id']:x for x in store.facts()}
   if groups is None:groups={x['id']:x for x in store.lec03_agent_facts()}
  for x in m['input_authority_snapshot']:
   if x['domain']=='facts':
    now=raw.get(x['id']);valid=now is not None and now['binding']==x['binding'] and now['pdf_sha256']==x['pdf_sha256']
   else:valid=x['id'] in groups and digest(groups[x['id']])==x['validated_snapshot_sha256']
   if not valid:issues.append(x['id'])
 except (KeyError,ValueError,OSError) as e:issues.append(type(e).__name__+': '+str(e))
 return {'status':'accepted-method-with-followups','method_approved':True,'reference_examples_status':'current' if not issues else 'stale-inputs','stale_reference_ids':issues,'economic_classification_complete':False,'new_raw_facts':0,'new_signature_created':False,'approved_ids':a['approved_ids'],'actual_user_reply':a['actual_user_reply'],'actor':'user','reviewer_name':None,'recorded_at':a['recorded_at'],'required_followups':a['required_followups'],'boundary':a['boundary']}
