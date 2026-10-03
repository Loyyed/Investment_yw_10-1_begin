from decimal import Decimal
from pathlib import Path
import copy,json,sys,unittest
from calculate_m01_scale import calculate,divide
W=Path(__file__).resolve().parents[1]
class ScaleAnalysisGuards(unittest.TestCase):
 def setUp(self):self.inputs=json.loads((W/'work/m01-scale-inputs.json').read_text(encoding='utf-8'))
 def test_production_cannot_replace_selling_denominator(self):
  self.inputs['years'][0]['products'][0]['sales_tonnes']='57204.11'
  with self.assertRaisesRegex(ValueError,'columns differ'):calculate(W,self.inputs)
 def test_source_version_cannot_be_changed(self):
  self.inputs['reports'][0]['pdf_sha256']='different'
  with self.assertRaisesRegex(ValueError,'version changed'):calculate(W,self.inputs)
 def test_inventory_columns_cannot_be_reversed(self):
  self.inputs['years'][0]['inventory_gross']['在产品'].reverse()
  with self.assertRaisesRegex(ValueError,'Inventory gross'):calculate(W,self.inputs)
 def test_cost_component_cannot_be_invented(self):
  self.inputs['years'][0]['cost_components']['直接材料']='1'
  with self.assertRaisesRegex(ValueError,'Cost component'):calculate(W,self.inputs)
 def test_calculation_does_not_confirm_unknowns_or_assumptions(self):
  result=calculate(W,self.inputs)
  self.assertTrue(all(r['state']=='Unknown' for r in result['products']))
  self.assertEqual(result['production_bridge']['state'],'Unknown')
  self.assertTrue(all(r['state']=='Unknown' for r in result['production_bridge']['assumptions']))
 def test_nonpositive_denominator_blocked(self):
  for quantity in [Decimal(0),Decimal(-1)]:
   with self.assertRaises(ValueError):divide(Decimal(10),quantity)
if __name__=='__main__':unittest.main()
