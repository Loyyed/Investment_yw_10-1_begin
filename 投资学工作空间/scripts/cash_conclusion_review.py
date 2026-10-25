"""Separate cash-contract Interpretation adoption from raw confirmation/signatures."""
from pathlib import Path
import hashlib,json
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def semantic(data):
    def strip(v):
        if isinstance(v,dict):return {k:strip(x) for k,x in v.items() if k not in {'code_sha256','date','generated_output_sha256'}}
        if isinstance(v,list):return [strip(x) for x in v]
        return v
    proxy=data['selected_capital_proxy_diagnostics']
    return strip({'panel':data['panel'],'continuous_2016_2025_diagnostics':data['continuous_2016_2025_diagnostics'],'cash_reconciliation_2025':data['cash_reconciliation_2025'],'proxy_panel':proxy['panel'],'window':proxy['window_diagnostic'],'classification':proxy['classification_and_profit_details'],'fy2012_sensitivity':data['fy2012_sensitivity']})
def current_cash_conclusion_adoption(p):
    p=Path(p);ledger=p/'evidence/cash-conclusion-content-review.json'
    if not ledger.exists():return {'status':'pending','judgment_type':'Interpretation','adopted_ids':[],'new_signature_created':False}
    try:
        a=json.loads(ledger.read_text(encoding='utf-8'));m=json.loads((p/a['display_manifest']).read_text(encoding='utf-8'));payload=dict(m);fp=payload.pop('display_payload_sha256')
        assert fp==digest(payload)==a['display_payload_sha256'] and sha(p/a['display_manifest'])==a['display_manifest_sha256']
        assert a['channel']=='actual-user-chat' and a['actor']=='user' and a['actual_user_reply']=='认可P02两项判断'
        assert a['adopted_ids']==['N06','N07'] and not a['new_signature_created'] and not a['contract_formally_closed']
        assert a['validator_sha256']==sha(Path(__file__))
        assert sha(p/m['displayed_calculations_path'])==m['displayed_calculations_sha256'] and sha(p/m['displayed_opinions_path'])==m['displayed_opinions_sha256']
        snapshot=json.loads((p/m['displayed_calculations_path']).read_text(encoding='utf-8'));current=json.loads((p/'work/cash-20261024/calculations.json').read_text(encoding='utf-8'))
        assert digest(semantic(snapshot))==m['calculation_semantic_sha256']==digest(semantic(current))
        from review_store import ReviewStore
        s=ReviewStore(p);raw={x['id']:x for x in s.facts()};groups={x['id']:x for x in s.lec03_agent_facts()}
        for x in m['input_authority_snapshot']:
            if x['domain']=='facts':assert raw[x['id']]['binding']==x['binding'] and raw[x['id']]['pdf_sha256']==x['pdf_sha256']
            else:assert digest(groups[x['id']])==x['validated_snapshot_sha256']
        return {'status':'accepted-current','judgment_type':'Interpretation','adopted_ids':a['adopted_ids'],'actual_user_reply':a['actual_user_reply'],'actor':'user','reviewer_name':None,'new_signature_created':False,'contract_formally_closed':False}
    except (KeyError,ValueError,AssertionError,OSError) as e:return {'status':'stale','judgment_type':'Interpretation','reason':type(e).__name__+': '+str(e),'new_signature_created':False}
