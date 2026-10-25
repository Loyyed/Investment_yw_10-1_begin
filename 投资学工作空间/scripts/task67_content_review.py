"""Validate version-specific Task06/07 content adoption, not facts/signatures."""
from pathlib import Path
import hashlib,json
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def current_p04_adoption(p):
    p=Path(p);ledger=p/'evidence/task67-content-review.json'
    if not ledger.exists():return {'status':'pending','review_type':'version-specific-content','adopted_ids':[],'new_signature_created':False}
    try:
        a=json.loads(ledger.read_text(encoding='utf-8'));m=json.loads((p/a['display_manifest']).read_text(encoding='utf-8'));payload=dict(m);fp=payload.pop('display_payload_sha256')
        assert fp==digest(payload)==a['display_payload_sha256'] and sha(p/a['display_manifest'])==a['display_manifest_sha256']
        assert a['channel']=='actual-user-chat' and a['actor']=='user' and a['actual_user_reply']=='认可P04两项内容' and a['adopted_ids']==['T06-v20261021','T07-v20261021']
        assert a['validator_sha256']==sha(Path(__file__)) and not a['new_signature_created'] and not a['contracts_formally_closed'] and not a['new_human_fact_events']
        for x in m['bound_artifacts']:assert sha(p/x['path'])==x['sha256']
        from review_store import ReviewStore
        s=ReviewStore(p);domains={'facts':{x['id']:x for x in s.facts()},'m01_disclosure_facts':{x['id']:x for x in s.m01_disclosure_facts()},'lec03_agent_facts':{x['id']:x for x in s.lec03_agent_facts()}}
        for x in m['input_authority']:
            now=domains[x['domain']][x['id']]
            if x['domain']=='facts':assert now['binding']==x['binding'] and now['pdf_sha256']==x['pdf_sha256']
            else:assert digest(now)==x['validated_snapshot_sha256']
        return {'status':'accepted-current','review_type':'version-specific-content','adopted_ids':a['adopted_ids'],'actual_user_reply':a['actual_user_reply'],'actor':'user','reviewer_name':None,'new_signature_created':False,'contracts_formally_closed':False,'strict_new_visit_clause_resolved':False}
    except (AssertionError,KeyError,ValueError,OSError) as e:return {'status':'stale','review_type':'version-specific-content','reason':type(e).__name__+': '+str(e),'new_signature_created':False}
