"""Source-bound cost review; a conditional arithmetic Fact is never a cost proof."""
from pathlib import Path
import copy,json
from m01_metric_review import M01MetricReview,digest,sha

META={'state','note','confirmed_at','confirmation_key','field_states','arithmetic_fact_id'}
BRIDGE_FIELDS={'inventory_bridge_production_input_yuan','bridge_per_reported_base_wine_tonne'}
def normalized(payload):
 value=copy.deepcopy(payload)
 value.pop('status',None)
 for group in ['products','years','cost_components']:
  value[group]=[{k:v for k,v in row.items() if k not in META} for row in value[group]]
 value['mix_decomposition']={k:v for k,v in value['mix_decomposition'].items() if k not in META}
 # State and assumptions of the production estimate itself stay sealed as Unknown.
 for key in ['arithmetic_state','arithmetic_fact_id','confirmed_at','confirmation_key']:
  value['production_bridge'].pop(key,None)
 return value

def groups(current):
 common={'state_boundary':'统计核验不证明规模机制、品牌因果或持续性'}
 return {
  'M01-K01':{'label':'2023—2024单位销售成本、产销量、毛利与组合拆分',
   'evidence_type':'verified-cost-statistics','products':current['products'],
   'years':[{k:v for k,v in r.items() if k not in BRIDGE_FIELDS and not k.startswith('productive_inventory_')} for r in current['years']],
   'aggregate_change_percent':{k:v for k,v in current['aggregate_change_percent'].items() if k not in BRIDGE_FIELDS},
   'mix_decomposition':current['mix_decomposition'],
   'support_boundary':'仅支持所列两期公司销售口径统计量及大类组合拆分；不是准确单位生产成本',**common},
  'M01-K02':{'label':'酒类营业成本的材料、人工、制造费用等构成',
   'evidence_type':'verified-cost-components','cost_components':current['cost_components'],
   'support_boundary':'仅支持已结转营业成本的生产相关构成及每销售吨计算；不是当年新投入生产分项',**common},
  'M01-K03':{'label':'存货桥接原数、给定公式的附条件算术结果',
   'evidence_type':'conditional-arithmetic-only',
   'years':[{k:v for k,v in r.items() if k in BRIDGE_FIELDS or k.startswith('productive_inventory_') or k in ['year','cost_yuan','production_tonnes']} for r in current['years']],
   'bridge':current['production_bridge'],
   'aggregate_change_percent':{k:v for k,v in current['aggregate_change_percent'].items() if k in BRIDGE_FIELDS},
   'production_cost_proof_state':'Unknown',
   'support_boundary':'仅确认原数和附条件算术；实际生产投入、准确单位制造成本与全部桥接假设仍Unknown',**common}}

class M01ScaleReview(M01MetricReview):
 def __init__(self,workspace):
  super().__init__(workspace)
  self.path=self.workspace/'evidence/m01-scale-review.json'
 def _validated(self,payload=None):
  from calculate_m01_scale import calculate
  root=self.workspace
  code={name:sha(root/'scripts'/name) for name in ['calculate_m01_scale.py','m01_metric_review.py','m01_scale_review.py']}
  current=calculate(root)
  if payload is None:payload=json.loads((root/'work/m01-scale-results.json').read_text(encoding='utf-8'))
  expected=normalized(current)
  if expected['production_bridge']['state']!='Unknown' or any(a['state']!='Unknown' for a in expected['production_bridge']['assumptions']):
   raise ValueError('Unproved production assumptions cannot be promoted by arithmetic review')
  if normalized(payload)!=expected:raise ValueError('Reviewed scale inputs, results, formula or Unknown assumptions differ from recomputation')
  if code!={name:sha(root/'scripts'/name) for name in code}:raise ValueError('Cost review code changed during validation')
  binding={'calculation':expected,'code_sha256':code}
  return binding,groups(expected)
 def records(self,payload=None):
  rows=super().records(payload)
  for row in rows:
   row['evidence_type']=row['calculation']['evidence_type']
   row['support_boundary']=row['calculation']['support_boundary']
   if row['id']=='M01-K03':row['production_cost_proof_state']='Unknown'
  return rows
 def export(self):
  value=super().export();value['authority']='evidence/m01-scale-review.json'
  value['qualification']='M01-K03 is conditional arithmetic only; production-cost proof and bridge assumptions remain Unknown.'
  return value
 def annotate(self,payload):
  result=copy.deepcopy(payload)
  facts={r['id']:r for r in self.records(result) if r['state']=='Fact'}
  for group,identifier in [('products','M01-K01'),('cost_components','M01-K02')]:
   for row in result[group]:
    row['state']='Fact' if identifier in facts else 'Unknown'
    row['note']='本人聊天确认当前输入、单位与结果；'+groups(normalized(payload))[identifier]['support_boundary'] if identifier in facts else '尚无当前有效的本人成本计算核验'
  result['mix_decomposition']['state']='Fact' if 'M01-K01' in facts else 'Unknown'
  for row in result['years']:
   row.pop('state',None)
   row['field_states']={key:('Unknown' if key in BRIDGE_FIELDS else 'Fact' if ('M01-K03' if key.startswith('productive_inventory_') else 'M01-K01') in facts else 'Unknown') for key in row if key!='year' and key not in META}
   if 'M01-K03' in facts:row['arithmetic_fact_id']='M01-K03'
  bridge=result['production_bridge']
  bridge['state']='Unknown'
  bridge['arithmetic_state']='Fact' if 'M01-K03' in facts else 'Unknown'
  if 'M01-K03' in facts:bridge['arithmetic_fact_id']='M01-K03'
  else:bridge.pop('arithmetic_fact_id',None)
  result['status']='human-confirmed-statistics-and-conditional-arithmetic' if len(facts)==3 else 'calculated-awaiting-human-verification'
  return result
