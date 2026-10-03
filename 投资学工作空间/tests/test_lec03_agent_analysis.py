"""Regression checks for scope, column placement and live evidence invalidation."""
from pathlib import Path
from decimal import Decimal
from unittest import TestCase,main,mock
import copy,json,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import lec03_agent_analysis as a
W=Path(__file__).resolve().parents[1]
if not (W/'work/lec03-agent-inputs.json').exists():W=Path('D:/投资学/投资学工作空间')
S=Path(__file__).parent
INPUT_PATH=W/'work/lec03-agent-inputs.json'
if not INPUT_PATH.exists():INPUT_PATH=S/'agent-inputs.json'
I=json.loads(INPUT_PATH.read_text(encoding='utf-8'));R=a.calculate(I)
class AnalysisTests(TestCase):
 def test_blank_cash_columns_are_not_shifted(self):
  y={r['year']:r for r in I['years']}
  loan=y[2022]['cash_rows']['拆出资金净增加额'];refund=y[2024]['cash_rows']['收到的税费返还']
  self.assertTrue(loan['current_blank']);self.assertEqual(loan['current_yuan'],'0');self.assertEqual(loan['previous_yuan'],'-400000000.00')
  self.assertTrue(refund['current_blank']);self.assertEqual(refund['current_yuan'],'0');self.assertEqual(refund['previous_yuan'],'1500047.04')
 def test_channels_use_current_sales_not_prior_or_production(self):
  row=I['years'][1]['channels'][0]
  self.assertEqual(row['sales_tonnes'],'5735.70');self.assertEqual(row['display_revenue_wanyuan'],'2402936.23')
  self.assertEqual(R['years'][-1]['channels'][0]['asp_wanyuan_per_sales_tonne'],'410.73')
 def test_cash_reconciliation_and_full_group_denominator(self):
  for row in R['years']:
   c=row['cash_analysis']
   self.assertEqual(Decimal(c['after_listed_financial_items_residual_yuan'])+Decimal(c['explicit_financial_items_net_yuan']),Decimal(c['cfo_yuan']))
  self.assertEqual(R['years'][-1]['consolidated_net_profit_yuan'],'89334728025.90')
  self.assertEqual(R['years'][-1]['cash_analysis']['cfo_to_consolidated_profit_percent'],'103.50')
  self.assertEqual(R['years'][2]['cash_analysis']['explicit_financial_items_net_yuan'],'-19509184157.51')
 def test_industry_conflict_retains_originals_and_absent_rate(self):
  self.assertEqual(I['years'][3]['industry']['production_wan_kl'],'449.2')
  self.assertEqual(I['years'][3]['industry']['reported_production_yoy_percent'],'-2.8')
  self.assertIsNone(I['years'][4]['industry']['reported_production_yoy_percent'])
  self.assertIn('-33.08',[r['naive_cross_report_yoy_percent'] for r in R['industry_cross_report_conflicts']])
  self.assertEqual(R['industry_stage']['state'],'Interpretation')
 def test_invalid_sales_denominator_stops_calculation(self):
  bad=copy.deepcopy(I);bad['years'][0]['products'][0]['sales_tonnes']='0'
  with self.assertRaises((ValueError,ArithmeticError)):a.calculate(bad)
 def test_missing_source_and_pdf_version_change_stop_extraction(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'sources').mkdir();(p/'sources/manifest.json').write_text(json.dumps([{'year':2020,'pdf':'changed.pdf','pdf_sha256':'0'*64}]),encoding='utf-8');(p/'changed.pdf').write_bytes(b'changed-source')
   with self.assertRaises(ValueError):a.extract(p)
class BindingTests(TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
  for d in ['scripts','work','evidence']:(self.p/d).mkdir()
  code=Path(a.__file__);(self.p/'scripts/lec03_agent_analysis.py').write_bytes(code.read_bytes())
  self.auth={'statement_original':'给你极大权限','delegation':{'authorized_by':'本人','agent_source_verification':True}}
  self.save('evidence/lec03-content-review.json',self.auth)
  self.save('work/lec03-agent-inputs.json',I);self.save('work/lec03-agent-results.json',R)
  self.cache={'authority':'explicit-delegated-agent-source-verification','code_sha256':a.sha(self.p/'scripts/lec03_agent_analysis.py'),'authorization_sha256':a.sha(self.p/'evidence/lec03-content-review.json'),'result_digest':a.digest(R),'facts':[{**r,'state':'Fact','verification_method':'Agent双引擎原文+空间列核对+算术校验'} for r in a.groups(R)]}
  self.save('evidence/lec03-agent-facts.json',self.cache)
  self.extraction=mock.patch.object(a,'extract',return_value=copy.deepcopy(I));self.extraction.start();self.addCleanup(self.extraction.stop);self.addCleanup(self.tmp.cleanup)
 def save(self,relative,value):(self.p/relative).write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
 def test_valid_agent_records_never_claim_human_clicks(self):
  facts=a.current_facts(self.p);self.assertEqual(len(facts),16);self.assertTrue(all(r['human_confirmation'] is False for r in facts))
 def test_changed_authorization_invalidates(self):
  self.auth['delegation']['agent_source_verification']=False;self.save('evidence/lec03-content-review.json',self.auth)
  self.assertEqual(a.current_facts(self.p),[])
 def test_rebinding_without_delegation_is_rejected(self):
  self.auth['delegation']['agent_source_verification']=False;self.save('evidence/lec03-content-review.json',self.auth)
  self.cache['authorization_sha256']=a.sha(self.p/'evidence/lec03-content-review.json');self.save('evidence/lec03-agent-facts.json',self.cache)
  self.assertEqual(a.current_facts(self.p),[])
 def test_modified_code_invalidates(self):
  with (self.p/'scripts/lec03_agent_analysis.py').open('a',encoding='utf-8') as f:f.write('\n# changed\n')
  self.assertEqual(a.current_facts(self.p),[])
 def test_modified_inputs_invalidates(self):
  v=copy.deepcopy(I);v['years'][0]['products'][0]['sales_tonnes']='123';self.save('work/lec03-agent-inputs.json',v)
  self.assertEqual(a.current_facts(self.p),[])
 def test_modified_results_invalidates(self):
  v=copy.deepcopy(R);v['industry_stage']['state']='Fact';self.save('work/lec03-agent-results.json',v)
  self.assertEqual(a.current_facts(self.p),[])
 def test_modified_cached_fact_invalidates(self):
  self.cache['facts'][0]['human_confirmation']=True;self.save('evidence/lec03-agent-facts.json',self.cache)
  self.assertEqual(a.current_facts(self.p),[])
 def test_changed_current_source_invalidates(self):
  with mock.patch.object(a,'extract',side_effect=ValueError('PDF changed')):self.assertEqual(a.current_facts(self.p),[])
if __name__=='__main__':main(verbosity=2)
