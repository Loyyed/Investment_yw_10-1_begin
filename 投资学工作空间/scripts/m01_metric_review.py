"""Explicit human review of M01 metrics, separate from PDF-window authority."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import copy,hashlib,json

def digest(value):
 return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def normalized(payload):
 fields=['input_digest','pdf_path','pdf_sha256','required_fact_bindings','checks','support_boundary']
 result={k:copy.deepcopy(payload[k]) for k in fields}
 result['results']=[{k:copy.deepcopy(v) for k,v in row.items() if k not in ['state','note','confirmed_at','confirmation_key']}
                    for row in payload['results']]
 result['page15_direct_averages']=[{k:v for k,v in row.items() if k not in ['state','note','confirmed_at','confirmation_key']}
                                  for row in payload['page15_direct_averages']]
 return result

class M01MetricReview:
 def __init__(self,workspace):
  self.workspace=Path(workspace).resolve()
  self.path=self.workspace/'evidence/m01-metric-review.json'
 def _read(self):
  if not self.path.exists():return {'schema_version':1,'records':{},'events':[]}
  value=json.loads(self.path.read_text(encoding='utf-8'))
  if value.get('schema_version')!=1 or not isinstance(value.get('records'),dict) or not isinstance(value.get('events'),list):
   raise ValueError('Invalid M01 metric review ledger')
  return value
 def _validated(self,payload=None):
  from calculate_m01_metrics import calculate
  root=self.workspace
  code_sha=sha(root/'scripts/calculate_m01_metrics.py')
  current=calculate(root)
  manifest=json.loads((root/'sources/manifest.json').read_text(encoding='utf-8'))
  version=next(r for r in manifest if r['year']==2024)
  if (current['pdf_path'],current['pdf_sha256'])!=(version['pdf'],version['pdf_sha256']):
   raise ValueError('M01 annual-report version no longer matches manifest')
  if payload is None:payload=json.loads((root/'work/m01-calculated-metrics.json').read_text(encoding='utf-8'))
  expected=normalized(current)
  if normalized(payload)!=expected:raise ValueError('Saved M01 result, input, formula or unit differs from source recomputation')
  if code_sha!=sha(root/'scripts/calculate_m01_metrics.py'):raise ValueError('Calculation code changed during validation')
  binding={'calculation':expected,'calculation_code_sha256':code_sha}
  return binding,{r['id']:r for r in expected['results']}
 def records(self,payload=None):
  ledger=self._read()
  if not ledger['records']:return []
  try:
   binding,expected=self._validated(payload);failure=''
  except (OSError,ValueError,KeyError,TypeError,AttributeError,StopIteration) as error:
   failure=type(error).__name__+': '+str(error)
  output=[]
  for identifier,saved in ledger['records'].items():
   row=copy.deepcopy(saved);reason=failure
   if not reason:
    if row.get('submitted_state')!='Fact':reason='Metric is not currently submitted as Fact'
    elif row.get('binding_digest')!=digest(binding):reason='Source, inputs, original Facts or calculation code changed'
    elif identifier not in expected or row.get('calculation')!=expected[identifier]:reason='Confirmed metric no longer matches formula/result'
    elif not any(event.get('type')=='chat-m01-metric-confirmation'
      and event.get('binding')==binding
      and event.get('confirmation_key')==row.get('confirmation_key')
      and event.get('statement_original')==row.get('statement_original')
      and event.get('confirmation_context')==row.get('confirmation_context')
      and any(digest(previous)==digest(saved) for previous in event.get('records',[]))
      for event in ledger['events']):reason='No matching explicit human chat confirmation event'
   row.update(state='Unknown' if reason else 'Fact',stale_reason=reason)
   output.append(row)
  return output
 def facts(self):return [r for r in self.records() if r['state']=='Fact']
 def export(self):
  records=self.records()
  return {'schema_version':1,'authority':'evidence/m01-metric-review.json',
   'counts':{'Fact':sum(r['state']=='Fact' for r in records),'Unknown':sum(r['state']=='Unknown' for r in records)},
   'facts':[r for r in records if r['state']=='Fact']}
 def confirm(self,statement,context,reviewed_artifact_sha256,reviewed_commit,actor='',client_date='2026-10-03'):
  if not statement.strip() or not context.strip():raise ValueError('Actual statement and context required')
  from review_store import ReviewStore
  review=ReviewStore(self.workspace)
  with review._locked():
   binding,expected=self._validated();ledger=self._read()
   key=digest({'statement':statement,'context':context,'binding':binding,
               'reviewed_artifact_sha256':reviewed_artifact_sha256,'reviewed_commit':reviewed_commit})
   current=self.records()
   if len(current)==len(expected) and all(r['state']=='Fact' and r['confirmation_key']==key for r in current):return current
   now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
   rows={identifier:{'id':identifier,'calculation':copy.deepcopy(calculation),'binding_digest':digest(binding),
    'submitted_state':'Fact','confirmed_at':now,'actor':actor,'client_date':client_date,
    'statement_original':statement,'confirmation_context':context,'confirmation_key':key,
    'reviewed_commit':reviewed_commit,'reviewed_artifact_sha256':reviewed_artifact_sha256,
    'support_boundary':'仅支持所列公司口径统计量及对应计算结果；不证明品牌因果、终端动销或可持续定价权'}
    for identifier,calculation in expected.items()}
   if self._validated()[0]!=binding:raise ValueError('Source changed while confirming')
   ledger['records'].update(rows);ledger['updated_at']=now
   ledger['events'].append({'type':'chat-m01-metric-confirmation','sequence':len(ledger['events'])+1,
    'confirmed_at':now,'actor':actor,'client_date':client_date,'statement_original':statement,
    'confirmation_context':context,'confirmation_key':key,'binding':binding,
    'reviewed_commit':reviewed_commit,'reviewed_artifact_sha256':reviewed_artifact_sha256,
    'records':copy.deepcopy(list(rows.values()))})
   review._atomic_text(self.path,json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
   return self.records()
 def annotate(self,payload):
  result=copy.deepcopy(payload)
  current={r['id']:r for r in self.records(result) if r['state']=='Fact'}
  for row in result['results']:
   record=current.get(row['id'])
   row['state']='Fact' if record else 'Unknown'
   row['note']='本人明确聊天核验输入、单位和结果；仅支持该统计量' if record else '未有当前有效的本人计算核验'
   if record:row.update(confirmed_at=record['confirmed_at'],confirmation_key=record['confirmation_key'])
   else:
    row.pop('confirmed_at',None);row.pop('confirmation_key',None)
  for index,row in enumerate(result['page15_direct_averages'],1):
   record=current.get('M01-A0'+str(index))
   row['state']='Fact' if record else 'Unknown'
   row['note']='第15页展示精度的直接均价视图，不另计Fact编号' if record else '待本人核验'
  result['status']='human-confirmed' if len(current)==len(result['results']) else 'calculated-awaiting-human-verification'
  return result
