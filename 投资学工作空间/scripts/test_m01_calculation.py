"""Meaningful fail-closed tests for sales denominators and source bindings."""
from pathlib import Path
import json,shutil,sys,tempfile,types,unittest
from unittest.mock import patch
from calculate_m01_metrics import calculate
from review_store import ReviewStore

WORKSPACE=Path(__file__).resolve().parents[1]

class CalculationGuards(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.payload=json.loads((WORKSPACE/'work/m01-calculation-inputs.json').read_text(encoding='utf-8'))
  source=self.root/self.payload['pdf_path'];source.parent.mkdir(parents=True)
  shutil.copyfile(WORKSPACE/self.payload['pdf_path'],source)
  (self.root/'work').mkdir()
  self.rows=ReviewStore(WORKSPACE).facts()
  module=types.ModuleType('review_store')
  rows=self.rows
  module.ReviewStore=lambda root:types.SimpleNamespace(facts=lambda:rows)
  self.patch=patch.dict(sys.modules,{'review_store':module});self.patch.start()
 def tearDown(self):self.patch.stop();self.temp.cleanup()
 def execute(self):
  (self.root/'work/m01-calculation-inputs.json').write_text(json.dumps(self.payload),encoding='utf-8')
  return calculate(self.root)
 def test_valid_but_never_self_confirms(self):
  result=self.execute()
  self.assertTrue(result['results'])
  self.assertTrue(all(r['state']=='Unknown' for r in result['results']))
 def test_production_cannot_replace_sales(self):
  self.payload['products'][0]['sales_tonnes']='56271.99'
  with self.assertRaisesRegex(ValueError,'Sales/production'):self.execute()
 def test_changed_human_binding(self):
  self.payload['required_fact_bindings']['N2024-01']='different'
  with self.assertRaisesRegex(ValueError,'binding changed'):self.execute()
 def test_changed_channel_column(self):
  self.payload['channels'][0]['sales_tonnes_2024']='15634.95'
  with self.assertRaisesRegex(ValueError,'original columns'):self.execute()
 def test_changed_source(self):
  (self.root/self.payload['pdf_path']).write_bytes(b'changed-source')
  with self.assertRaisesRegex(ValueError,'Source PDF changed'):self.execute()
 def test_unmatched_wine_revenue(self):
  self.payload['wine']['revenue_yuan']='170899152276.34'
  with self.assertRaisesRegex(ValueError,'C06 Fact'):self.execute()

if __name__=='__main__':unittest.main()
