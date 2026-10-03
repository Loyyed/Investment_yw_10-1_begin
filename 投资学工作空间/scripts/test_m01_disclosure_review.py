import hashlib,json,tempfile,unittest
from pathlib import Path
from m01_disclosure_review import M01DisclosureReview,digest

class DisclosureGuardTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  self.pdf=self.root/'sources/annual_reports/pdf/2024.pdf'
  self.pdf.parent.mkdir(parents=True);self.pdf.write_bytes(b'fixed annual source fixture')
  self.source_sha=hashlib.sha256(self.pdf.read_bytes()).hexdigest()
  (self.root/'sources/manifest.json').write_text(json.dumps([{'year':2024,'pdf':'sources/annual_reports/pdf/2024.pdf','pdf_sha256':self.source_sha}]))
  (self.root/'evidence').mkdir()
  self.row={'id':'M01-D01','claim':'Company lists brand as a core competence','kind':'company-self-disclosure',
   'review_excerpt':'brand is a core competence','page':8,'pdf_path':'sources/annual_reports/pdf/2024.pdf',
   'pdf_sha256':self.source_sha,'submitted_state':'Fact'}
  self.ledger={'schema_version':1,'user_response':'brand is a core competence','records':[self.row],
   'events':[{'type':'chat-disclosure-review','response_digest':digest('brand is a core competence'),'records':[dict(self.row)]}]}
  self.store=M01DisclosureReview(self.root);self.save()
 def save(self):self.store.path.write_text(json.dumps(self.ledger),encoding='utf-8')
 def test_valid_review_is_disclosure_fact(self):
  self.assertEqual(1,len(self.store.facts()));self.assertEqual('company-self-disclosure',self.store.facts()[0]['kind'])
 def test_changed_source_invalidates_and_keeps_history(self):
  self.pdf.write_bytes(b'changed');self.assertEqual([],self.store.facts())
  self.assertEqual(1,len(json.loads(self.store.path.read_text())['events']))
 def test_tampered_claim_without_matching_review_fails(self):
  self.ledger['records'][0]['claim']='Brand causes pricing power';self.save();self.assertEqual([],self.store.facts())
 def test_changed_response_or_missing_review_event_fails(self):
  self.ledger['user_response']='research brand';self.save();self.assertEqual([],self.store.facts())
 def test_outside_source_path_fails(self):
  self.ledger['records'][0]['pdf_path']='../../other.pdf';self.save();self.assertEqual([],self.store.facts())
 def test_removed_or_corrupted_version_fails(self):
  (self.root/'sources/manifest.json').write_text('[]');self.assertEqual([],self.store.facts())

if __name__=='__main__':unittest.main(verbosity=2)
