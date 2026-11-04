"""Source-bound supplemental evidence cannot silently follow file changes."""
import hashlib,tempfile,unittest
from pathlib import Path
from .contract import ROOT,bind_supplemental_reports
class SupplementalEvidence(unittest.TestCase):
 def test_changed_and_outside_evidence_is_rejected(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'.bank-data/quality') as folder:
   path=Path(folder)/'review.json';path.write_text('{"status":"fixture"}\n')
   report={'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'purpose':'Source-bound regression fixture; no content admission.'}
   bind_supplemental_reports({'supplementalReports':[report]})
   path.write_text('{"status":"changed"}\n')
   with self.assertRaisesRegex(ValueError,'Missing or changed'):bind_supplemental_reports({'supplementalReports':[report]})
   with self.assertRaises(ValueError):bind_supplemental_reports({'supplementalReports':[{**report,'path':'../outside-review.json'}]})
 def test_missing_scope_or_unbounded_list_is_rejected(self):
  for reports in [None,{},[{}],[{}]*17]:
   with self.subTest(reports=reports),self.assertRaises(ValueError):bind_supplemental_reports({'supplementalReports':reports})
 def test_editorial_evidence_binds_source_and_report(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'.bank-data/quality') as folder:
   path=Path(folder)/'editorial.json';path.write_text('{"status":"fixture"}\n')
   editorial={'rawSha256':'a'*64,'report':str(path.relative_to(ROOT)),'reportSha256':hashlib.sha256(path.read_bytes()).hexdigest()}
   bind_supplemental_reports({'rawSha256':'a'*64,'editorialSupplement':editorial})
   with self.assertRaisesRegex(ValueError,'exact raw item'):bind_supplemental_reports({'rawSha256':'b'*64,'editorialSupplement':editorial})
   path.write_text('changed')
   with self.assertRaisesRegex(ValueError,'Missing or changed'):bind_supplemental_reports({'rawSha256':'a'*64,'editorialSupplement':editorial})
if __name__=='__main__':unittest.main()
