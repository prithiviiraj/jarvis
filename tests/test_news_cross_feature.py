import sys,unittest,types
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class Browser:
 def __init__(self):self.state={'state':'ready','url':'https://example.com/news'}
 def snapshot(self):return dict(self.state)
 def close(self):self.state['state']='stopping'
class Tests(unittest.TestCase):
 def setUp(self):self.b=Bridge(WorkspaceVoice());self.b.browser=Browser();self.b.browser_enabled=True
 def tearDown(self):self.b.close()
 def test_browser_stop_revokes_news_and_speech(self):
  self.b.news.requested=True;self.b.news.observed_url='https://example.com/news';before=self.b.news_speech.generation
  self.b.execute({'command':'browser-stop'});self.assertFalse(self.b.news.requested);self.assertEqual(self.b.news.observed_url,'');self.assertGreater(self.b.news_speech.generation,before)
 def test_same_url_navigation_working_stops_audio(self):
  self.b.news.observed_url='https://example.com/news';self.b.news_speech.busy=True;self.b.browser.state['state']='working';before=self.b.news_speech.generation
  self.b.execute({'command':'status'});self.assertGreater(self.b.news_speech.generation,before);self.b.news_speech.busy=False
 def test_new_source_drops_old_quote(self):
  self.b.news.text_preview={'text':'old quote'};self.b.news.observed_url='https://example.com/news'
  self.b.execute({'command':'news-preview','source_url':'https://example.org/news'});self.assertIsNone(self.b.news.text_preview);self.assertEqual(self.b.news.observed_url,'')
 def test_disabled_browser_cannot_read(self):
  self.b.browser_enabled=False;self.b.news.requested=True;self.b.news.text_preview={'text':'old'}
  with self.assertRaises(ValueError):self.b.execute({'command':'news-speak','reviewed':{'text':'old'},'confirm':True})
if __name__=='__main__':unittest.main(verbosity=2)
