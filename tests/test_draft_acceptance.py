import unittest,tempfile,os,json,pathlib
from jarvis.draft_acceptance import run
class Tests(unittest.TestCase):
 def test_synthetic_local_contracts_and_truthful_unrun_report(self):
  old=os.getcwd()
  with tempfile.TemporaryDirectory()as folder:
   try:
    os.chdir(folder);run();row=json.loads(pathlib.Path('ui-evidence/frozen-local-draft-contracts.json').read_text());self.assertFalse(row['frozen_executable']);self.assertTrue(row['synthetic_text_only']);self.assertTrue(row['synthetic_source_answer_attribution_cloud_reject']);self.assertTrue(row['synthetic_brain_switch_exact_route_cloud_reject']);self.assertIn('carrier calling',row['unrun']);self.assertIn('physical phone',row['unrun'])
   finally:os.chdir(old)
