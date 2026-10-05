import pathlib,tempfile,unittest
from unittest.mock import patch
from jarvis.obsidian import Vault
class SearchLimits(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);(self.root/'.obsidian').mkdir();self.v=Vault(self.root)
 def tearDown(self):self.tmp.cleanup()
 def test_complete_sorted_and_compatibility(self):
  for name in ['z.md','a.md']:(self.root/name).write_text('match',encoding='utf-8')
  d=self.v.search_details('match');self.assertTrue(d['complete']);self.assertEqual(d['scanned'],2);self.assertEqual([x['name']for x in d['results']],['a.md','z.md']);self.assertEqual(self.v.search('match'),d['results'])
 def test_note_limit_never_false_absence(self):
  for i in range(501):(self.root/f'{i:03}.md').write_text('only'if i==500 else 'other',encoding='utf-8')
  d=self.v.search_details('only');self.assertEqual(d['results'],[]);self.assertFalse(d['complete']);self.assertEqual(d['reason'],'note-limit');self.assertEqual(d['scanned'],500)
 def test_result_limit_explicit(self):
  for i in range(31):(self.root/f'{i:03}.md').write_text('match',encoding='utf-8')
  d=self.v.search_details('match');self.assertEqual(len(d['results']),30);self.assertFalse(d['complete']);self.assertEqual(d['reason'],'result-limit')
 def test_time_limit_explicit(self):
  (self.root/'a.md').write_text('match')
  with patch('jarvis.obsidian.time.monotonic',side_effect=[0,1]):d=self.v.search_details('match')
  self.assertFalse(d['complete']);self.assertEqual(d['reason'],'time-limit');self.assertEqual(d['scanned'],0)
 def test_unreadable_and_excluded_scope(self):
  (self.root/'a.md').write_bytes(b'\xff');(self.root/'.secret.md').write_text('match');(self.root/'huge.md').write_text('x'*65537)
  d=self.v.search_details('match');self.assertFalse(d['complete']);self.assertEqual(d['reason'],'unreadable-notes');self.assertEqual(d['skipped'],2);self.assertEqual(d['scanned'],2)
 def test_empty_vault_complete_only_within_scope(self):
  d=self.v.search_details('word');self.assertTrue(d['complete']);self.assertEqual(d['results'],[]);self.assertIn('visible',d['scope'])
