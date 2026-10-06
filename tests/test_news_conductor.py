import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jarvis.news_conductor import NewsConductor
class NewsTests(unittest.TestCase):
 def test_no_default(self):
  n=NewsConductor();self.assertTrue(n.request("what's the news today?"));self.assertEqual(n.source,'');self.assertIsNone(n.pending)
 def test_changed_review_rejected(self):
  n=NewsConductor();p=n.preview('https://example.com/news');q=dict(p,value='https://example.org/')
  with self.assertRaises(ValueError):n.confirm(q,True)
  self.assertEqual(n.pending,p)
 def test_private_source_rejected(self):
  n=NewsConductor()
  for url in ['http://example.com','https://127.0.0.1/','https://user:pass@example.com/']:
   with self.assertRaises(ValueError):n.preview(url)
 def test_observed_page_only_and_cancel(self):
  n=NewsConductor();p=n.preview('https://example.com/news');n.confirm(p,True);n.observe({'state':'ready','requested_url':'https://example.org/','url':'https://example.org/'});self.assertEqual(n.observed_url,'')
  n.observe({'state':'ready','requested_url':p['value'],'url':p['value']});self.assertTrue(n.snapshot()['reading_available']);self.assertIsNone(n.text_preview);self.assertIn('Shall I read',n.status);n.cancel();self.assertFalse(n.requested)
if __name__=='__main__':unittest.main(verbosity=2)
