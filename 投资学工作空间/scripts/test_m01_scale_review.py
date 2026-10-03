from pathlib import Path
from contextlib import nullcontext
import copy,json,shutil,sys,tempfile,types,unittest
from unittest.mock import patch
from review_store import ReviewStore
from calculate_m01_scale import calculate
from m01_scale_review import M01ScaleReview
W=Path(__file__).resolve().parents[1]
class CostConfirmationGuards(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.raw=copy.deepcopy(ReviewStore(W).facts());self.metrics=copy.deepcopy(ReviewStore(W).m01_metric_facts())
  inputs=json.loads((W/'work/m01-scale-inputs.json').read_text(encoding='utf-8'))
  paths=['work/m01-scale-inputs.json','work/m01-scale-results.json','sources/manifest.json',
   'scripts/calculate_m01_scale.py','scripts/m01_metric_review.py','scripts/m01_scale_review.py']+[r['pdf'] for r in inputs['reports']]
  for relative in paths:
   target=self.root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(W/relative,target)
  (self.root/'evidence').mkdir();outer=self
  class Review:
   def __init__(self,root):pass
   def facts(self):return outer.raw
   def m01_metric_facts(self):return outer.metrics
   def _locked(self):return nullcontext()
   @staticmethod
   def _atomic_text(path,text):Path(path).write_text(text,encoding='utf-8')
  module=types.ModuleType('review_store');module.ReviewStore=Review
  self.patch=patch.dict(sys.modules,{'review_store':module});self.patch.start()
  self.store=M01ScaleReview(self.root)
 def tearDown(self):self.patch.stop();self.temp.cleanup()
 def confirm(self):return self.store.confirm('核验完毕','核对成本分析2—4节原数和算术，不确认估算假设','reviewed-sha','4832eb6')
 def mutate(self,relative,fn):
  path=self.root/relative;data=json.loads(path.read_text(encoding='utf-8'));fn(data);path.write_text(json.dumps(data),encoding='utf-8')
 def test_confirm_idempotent_and_separate_groups(self):
  self.assertEqual(len(self.confirm()),3);self.confirm()
  self.assertEqual(len(json.loads(self.store.path.read_text(encoding='utf-8'))['events']),1)
  self.assertEqual({r['id'] for r in self.store.facts()},{'M01-K01','M01-K02','M01-K03'})
 def test_production_truth_and_assumptions_never_promoted(self):
  self.confirm();result=self.store.annotate(calculate(self.root))
  self.assertEqual(result['production_bridge']['state'],'Unknown')
  self.assertEqual(result['production_bridge']['arithmetic_state'],'Fact')
  self.assertTrue(all(r['state']=='Unknown' for r in result['production_bridge']['assumptions']))
  self.assertTrue(all(r['field_states']['inventory_bridge_production_input_yuan']=='Unknown' for r in result['years']))
  self.assertTrue(all(r['state']=='Fact' for r in result['products']))
 def test_calculation_without_confirmation_stays_unknown(self):
  self.assertFalse(self.store.facts())
  self.assertTrue(all(r['state']=='Unknown' for r in self.store.annotate(calculate(self.root))['products']))
 def test_result_formula_or_assumption_tampering_invalidates(self):
  self.confirm();path=self.root/'work/m01-scale-results.json';before=path.read_bytes()
  changes=[lambda d:d['products'][0].update(unit_cost_change_percent='999'),
   lambda d:d['production_bridge'].update(formula='wrong'),
   lambda d:d['production_bridge']['assumptions'][0].update(state='Fact')]
  for fn in changes:
   path.write_bytes(before);self.mutate('work/m01-scale-results.json',fn);self.assertFalse(self.store.facts())
 def test_pdf_change_invalidates_and_keeps_history(self):
  self.confirm();history=self.store.path.read_bytes()
  source=json.loads((self.root/'work/m01-scale-inputs.json').read_text(encoding='utf-8'))['reports'][0]['pdf']
  (self.root/source).write_bytes(b'changed')
  self.assertFalse(self.store.facts());self.assertEqual(self.store.path.read_bytes(),history)
 def test_input_or_source_fact_change_invalidates(self):
  self.confirm();self.metrics[0]['confirmation_key']='changed'
  self.assertFalse(self.store.facts())
 def test_code_change_invalidates(self):
  self.confirm();path=self.root/'scripts/calculate_m01_scale.py';path.write_bytes(path.read_bytes()+b'\n# changed\n')
  self.assertFalse(self.store.facts())
 def test_missing_or_changed_chat_event_invalidates(self):
  self.confirm();before=self.store.path.read_bytes()
  self.mutate('evidence/m01-scale-review.json',lambda d:d['events'][0].update(statement_original='different'))
  self.assertFalse(self.store.facts());self.store.path.write_bytes(before)
  self.mutate('evidence/m01-scale-review.json',lambda d:d.update(events=[]));self.assertFalse(self.store.facts())
if __name__=='__main__':unittest.main()
