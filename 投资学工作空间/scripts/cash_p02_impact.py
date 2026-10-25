"""Assess unchanged reviewed support without expanding the user's old adoption."""
from pathlib import Path
import json
from cash_conclusion_review import sha,digest,semantic
def assess_p02_support(p,raw,groups,current):
    p=Path(p)
    try:
        a=json.loads((p/'evidence/cash-conclusion-content-review.json').read_text(encoding='utf-8'));m=json.loads((p/a['display_manifest']).read_text(encoding='utf-8'));payload=dict(m);fp=payload.pop('display_payload_sha256')
        assert a['actual_user_reply']=='认可P02两项判断' and a['actor']=='user' and a['channel']=='actual-user-chat' and a['adopted_ids']==['N06','N07'] and not a['new_signature_created'] and not a['contract_formally_closed']
        assert fp==digest(payload)==a['display_payload_sha256'] and sha(p/a['display_manifest'])==a['display_manifest_sha256'] and a['validator_sha256']==sha(p/'scripts/cash_conclusion_review.py')
        assert sha(p/m['displayed_calculations_path'])==m['displayed_calculations_sha256'] and sha(p/m['displayed_opinions_path'])==m['displayed_opinions_sha256']
        displayed=json.loads((p/m['displayed_calculations_path']).read_text(encoding='utf-8'));assert digest(semantic(displayed))==m['calculation_semantic_sha256']
        for x in m['input_authority_snapshot']:
            if x['domain']=='facts':assert raw[x['id']]['binding']==x['binding'] and raw[x['id']]['pdf_sha256']==x['pdf_sha256']
            else:assert digest(groups[x['id']])==x['validated_snapshot_sha256']
        old,new=semantic(displayed),semantic(current)
        # P02's numerical claims use the continuous ten years, 2007/2011
        # endpoints, classification, and FY2012 sensitivity. New intermediate
        # observations remain Agent analysis; they are not newly adopted.
        def scope(data):return {**{k:v for k,v in data.items() if k!='panel'},'panel':[x for x in data['panel'] if x['year'] in [2007,2011,2012] or 2016<=x['year']<=2025]}
        same=digest(scope(old))==digest(scope(new));full=digest(old)==digest(new)
        return {'status':'accepted-current' if full else 'accepted-original-scope-supplement-unreviewed' if same else 'needs-content-reassessment','judgment_type':'Interpretation','original_user_adoption_record_valid':True,'original_reviewed_support_unchanged':same,'full_calculation_package_matches_display':full,'new_supplement_human_adoption':False,'reviewer_name':None,'new_signature_created':False,'contract_formally_closed':False,'boundary':'保留本人对原版本的真实采纳；新增中间年运算是AgentCalculated，不自动扩展本人意见认可。支持范围若变化则另行重评；原严格校验器及其历史不改。'}
    except (AssertionError,KeyError,ValueError,OSError) as e:return {'status':'stale-source-or-record','original_user_adoption_record_valid':False,'reason':type(e).__name__+': '+str(e),'new_supplement_human_adoption':False}
