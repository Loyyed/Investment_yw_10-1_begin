"""Independent adoption of the incremental annual-capital Interpretation."""
from pathlib import Path
import json,hashlib
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def semantic_scope(data):
    def strip(v):
        if isinstance(v,dict):return {k:strip(x) for k,x in v.items() if k not in {'date','code_sha256'}}
        if isinstance(v,list):return [strip(x) for x in v]
        return v
    return strip(data['annual_selected_capital_path'])
def current_p03_adoption(p):
    p=Path(p);ledger=p/'evidence/cash-path-content-review.json'
    if not ledger.exists():return {'status':'pending','judgment_type':'Interpretation','adopted_ids':[],'new_signature_created':False}
    try:
        a=json.loads(ledger.read_text(encoding='utf-8'));m=json.loads((p/a['display_manifest']).read_text(encoding='utf-8'));payload=dict(m);fp=payload.pop('display_payload_sha256')
        assert fp==digest(payload)==a['display_payload_sha256'] and sha(p/a['display_manifest'])==a['display_manifest_sha256']
        assert a['actual_user_reply']=='认可P03判断' and a['actor']=='user' and a['channel']=='actual-user-chat' and a['adopted_ids']==['N07-annual-path']
        assert a['validator_sha256']==sha(Path(__file__)) and not a['new_signature_created'] and not a['contract_formally_closed']
        assert sha(p/m['calculation_snapshot_path'])==m['calculation_snapshot_sha256'] and sha(p/m['opinion_snapshot_path'])==m['opinion_snapshot_sha256']
        current=json.loads((p/'work/cash-20261024/calculations.json').read_text(encoding='utf-8'));snapshot=json.loads((p/m['calculation_snapshot_path']).read_text(encoding='utf-8'))
        assert digest(semantic_scope(current))==m['calculation_semantic_sha256']==digest(semantic_scope(snapshot))
        from review_store import ReviewStore
        raw={x['id']:x for x in ReviewStore(p).facts()}
        for x in m['input_authority_snapshot']:assert raw[x['id']]['binding']==x['binding'] and raw[x['id']]['pdf_sha256']==x['pdf_sha256']
        return {'status':'accepted-current','judgment_type':'Interpretation','adopted_ids':a['adopted_ids'],'actual_user_reply':a['actual_user_reply'],'actor':'user','reviewer_name':None,'new_signature_created':False,'contract_formally_closed':False}
    except (AssertionError,KeyError,ValueError,OSError) as e:return {'status':'stale','judgment_type':'Interpretation','reason':type(e).__name__+': '+str(e),'new_signature_created':False}
