"""Read only source-bound, explicitly quoted human reviews of company disclosures."""
from pathlib import Path
import hashlib,json,re

def digest(value):
 return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()

class M01DisclosureReview:
 def __init__(self,workspace):
  self.root=Path(workspace).resolve()
  self.path=self.root/'evidence/m01-disclosure-review.json'

 def records(self):
  if not self.path.exists():return []
  ledger=json.loads(self.path.read_text(encoding='utf-8'))
  if ledger.get('schema_version')!=1 or not isinstance(ledger.get('records'),list):raise ValueError('Invalid disclosure review ledger')
  output=[]
  normalize=lambda text:re.sub(r'\s+','',text)
  for saved in ledger['records']:
   row=dict(saved);reason=''
   try:
    source=(self.root/row['pdf_path']).resolve()
    if not source.is_relative_to(self.root/'sources/annual_reports/pdf'):raise ValueError('Source path outside annual reports')
    manifest=json.loads((self.root/'sources/manifest.json').read_text(encoding='utf-8'))
    version=next(r for r in manifest if r['year']==2024)
    if row['pdf_path']!=version['pdf'] or row['pdf_sha256']!=version['pdf_sha256']:
     raise ValueError('Annual report version changed')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=row['pdf_sha256']:raise ValueError('Source PDF changed or missing')
    if row.get('kind')!='company-self-disclosure' or row.get('page')!=8 or row.get('submitted_state')!='Fact':
     raise ValueError('Disclosure review boundary changed')
    if normalize(row['review_excerpt']) not in normalize(ledger['user_response']):
     raise ValueError('User response no longer contains the reviewed disclosure')
    if not any(event.get('type')=='chat-disclosure-review'
      and event.get('response_digest')==digest(ledger['user_response'])
      and any(digest(previous)==digest(saved) for previous in event.get('records',[]))
      for event in ledger.get('events',[])):
     raise ValueError('Record lacks matching real chat review history')
   except (OSError,ValueError,TypeError,KeyError,StopIteration) as error:reason=type(error).__name__+': '+str(error)
   row.update(state='Unknown' if reason else 'Fact',stale_reason=reason)
   output.append(row)
  return output

 def facts(self):return [r for r in self.records() if r['state']=='Fact']
