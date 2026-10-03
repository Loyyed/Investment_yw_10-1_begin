from pathlib import Path
from contextlib import nullcontext
import copy,json,shutil,sys,tempfile,types,unittest
from unittest.mock import patch
from calculate_m01_metrics import calculate
from review_store import ReviewStore
from m01_metric_review import M01MetricReview
W=Path(__file__).resolve().parents[1]

class HumanMetricGuards(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.facts=ReviewStore(W).facts()
  payload=json.loads((W/'work/m01-calculation-inputs.json').read_text(encoding='utf-8'))
  for relative in ['work/m01-calculation-inputs.json','work/m01-calculated-metrics.json',
    'sources/manifest.json','scripts/calculate_m01_metrics.py',payload['pdf_path']]:
   target=self.root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(W/relative,target)
  (self.root/'evidence').mkdir()
  outer=self
  class Review:
   def __init__(self,root):pass
   def facts(self):return outer.facts
   def _locked(self):return nullcontext()
   @staticmethod
   def _atomic_text(path,text):Path(path).write_text(text,encoding='utf-8')
  module=types.ModuleType('review_store');module.ReviewStore=Review
  self.patch=patch.dict(sys.modules,{'review_store':module});self.patch.start()
  self.store=M01MetricReview(self.root)
 def tearDown(self):self.patch.stop();self.temp.cleanup()
 def confirm(self):
  return self.store.confirm('核对输入、单位和结果通过','回复所列M01输入、单位和结果', 'reviewed-table-sha','reviewed-commit')
 def mutate_json(self,relative,fn):
  path=self.root/relative;data=json.loads(path.read_text(encoding='utf-8'));fn(data);path.write_text(json.dumps(data),encoding='utf-8')
 def test_explicit_confirmation_idempotent(self):
  self.assertEqual(len(self.confirm()),15);self.assertEqual(len(self.confirm()),15)
  ledger=json.loads(self.store.path.read_text(encoding='utf-8'))
  self.assertEqual(len(ledger['events']),1);self.assertEqual(len(self.store.facts()),15)
 def test_recomputation_retains_valid_review(self):
  self.confirm();current=self.store.annotate(calculate(self.root))
  self.assertEqual(current['status'],'human-confirmed')
  self.assertTrue(all(r['state']=='Fact' for r in current['results']))
 def test_calculation_cannot_self_confirm(self):
  current=self.store.annotate(calculate(self.root))
  self.assertTrue(all(r['state']=='Unknown' for r in current['results']))
 def test_pdf_changes_invalidate_but_keep_history(self):
  self.confirm();history=self.store.path.read_bytes()
  source=json.loads((self.root/'work/m01-calculation-inputs.json').read_text(encoding='utf-8'))['pdf_path']
  (self.root/source).write_bytes(b'changed')
  self.assertFalse(self.store.facts());self.assertEqual(self.store.path.read_bytes(),history)
 def test_changed_inputs_invalidate(self):
  self.confirm()
  self.mutate_json('work/m01-calculation-inputs.json',lambda d:d['products'][0].update(sales_tonnes='56271.99'))
  self.assertFalse(self.store.facts())
 def test_original_fact_withdrawal_invalidates(self):
  self.confirm();self.facts[:]=[r for r in self.facts if r['id']!='N2024-01']
  self.assertFalse(self.store.facts())
 def test_saved_result_formula_or_unit_tampering(self):
  self.confirm();path=self.root/'work/m01-calculated-metrics.json';original=path.read_bytes()
  for field,value in [('value','999'),('formula','revenue_yuan/production_tonnes'),('unit','元/瓶')]:
   with self.subTest(field=field):
    path.write_bytes(original)
    self.mutate_json('work/m01-calculated-metrics.json',lambda d:d['results'][0].update({field:value}))
    self.assertFalse(self.store.facts())
 def test_changed_code_or_manifest_invalidates(self):
  self.confirm();code=self.root/'scripts/calculate_m01_metrics.py';before=code.read_bytes()
  code.write_bytes(before+b'\n# changed\n');self.assertFalse(self.store.facts());code.write_bytes(before)
  self.mutate_json('sources/manifest.json',lambda d:d.clear());self.assertFalse(self.store.facts())
 def test_missing_event_or_altered_response_invalidates(self):
  self.confirm();before=self.store.path.read_bytes()
  self.mutate_json('evidence/m01-metric-review.json',lambda d:d['events'][0].update(statement_original='different'))
  self.assertFalse(self.store.facts());self.store.path.write_bytes(before)
  self.mutate_json('evidence/m01-metric-review.json',lambda d:d.update(events=[]))
  self.assertFalse(self.store.facts())

if __name__=='__main__':unittest.main()
