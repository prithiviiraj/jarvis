import unittest
from pathlib import Path
class BundleSourceContractTests(unittest.TestCase):
 def test_current_pinned_sources_and_no_user_data(self):
  from jarvis.bundled_models import specifications
  rows=specifications();self.assertEqual(len(rows),31)
  self.assertTrue(all(len(sha)==64 and isinstance(cap,int)and cap>0 for sha,cap,size in rows.values()));self.assertTrue(any(n.startswith('voices/')for n in rows));self.assertTrue(any(n.startswith('embeddinggemma-2-')for n in rows))
  self.assertTrue(all(not any(x in n for x in ['history','credentials','logs','chat-history'])for n in rows))
 def test_distribution_retains_policy_caveat(self):
  s=(Path(__file__).resolve().parent.parent/'modern-ui/prepare-bundled-models.py').read_text(encoding='utf-8');self.assertIn('Prohibited Use Policy',s);self.assertIn('manifest.json',s)
 def test_local_import_has_no_network_execution(self):
  s=(Path(__file__).resolve().parent.parent/'src/jarvis/bundled_models.py').read_text(encoding='utf-8');self.assertNotIn('urlopen',s);self.assertNotIn('subprocess',s);self.assertIn('Never overwrite',s)
