"""Validate the user's G6 Interpretation adoption separately from raw Fact authority."""
from pathlib import Path
import json,hashlib

def digest(value):
 return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def semantic_calculation(data):
 # Presentation dates, code/output hashes may change when showing adoption status.
 return {key:value for key,value in data.items() if key not in {'date','code_sha256','generated_output_sha256'}}

def current_g6_adoption(project):
 project=Path(project);ledger=project/'evidence/lag-g6-content-review.json'
 if not ledger.exists():return {'status':'pending','judgment_type':'Interpretation','reason':'No actual content adoption recorded'}
 try:
  record=json.loads(ledger.read_text(encoding='utf-8'));manifest_path=project/record['display_manifest'];manifest=json.loads(manifest_path.read_text(encoding='utf-8'));payload=dict(manifest);fp=payload.pop('display_payload_sha256')
  assert fp==digest(payload)==record['display_payload_sha256'];assert sha(manifest_path)==record['display_manifest_sha256']
  assert record['actual_user_reply']=='认可G6两项判断' and record['channel']=='actual-user-chat'
  assert record['adopted_ids']==['G6-N02','G6-N05'] and not record['new_signature_created']
  assert sha(Path(__file__))==record['validator_sha256']
  from review_store import ReviewStore
  store=ReviewStore(project);raw={x['id']:x for x in store.facts()};groups={x['id']:x for x in store.lec03_agent_facts()}
  assert digest(manifest['input_authority_snapshot'])==manifest['input_authority_snapshot_sha256']
  for item in manifest['input_authority_snapshot'].values():
   if item['domain']=='facts':
    now=raw[item['id']];assert now['binding']==item['binding'] and now['pdf_sha256']==item['pdf_sha256']
   else:
    now=groups[item['id']];expected=item.get('validated_snapshot_sha256') or item.get('validated_group_snapshot_sha256');assert digest(now)==expected
  for name,item in record['calculation_bindings'].items():
   displayed=project/item['displayed_snapshot_path'];current=project/item['current_path']
   assert sha(displayed)==manifest['calculation_artifacts'][name]
   previous=json.loads(displayed.read_text(encoding='utf-8'));now=json.loads(current.read_text(encoding='utf-8'))
   assert digest(semantic_calculation(previous))==item['semantic_sha256']==digest(semantic_calculation(now))
  return {'status':'accepted-current','judgment_type':'Interpretation','adopted_ids':record['adopted_ids'],'actual_user_reply':record['actual_user_reply'],'actor':record['actor'],'reviewer_name':record['reviewer_name'],'recorded_at':record['recorded_at'],'display_payload_sha256':fp,'new_signature_created':False,'boundary':record['boundary']}
 except (AssertionError,KeyError,ValueError,OSError) as error:
  return {'status':'stale','judgment_type':'Interpretation','reason':type(error).__name__+': '+str(error),'new_signature_created':False}
