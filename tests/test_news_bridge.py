import sys,unittest,hashlib,types,tempfile,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class Browser:
 def __init__(self):self.state={'state':'ready','url':'https://example.com/news','requested_url':'https://example.com/news'};self.calls=[]
 def snapshot(self):return dict(self.state)
 def submit(self,*a,**k):self.calls.append((a,k));self.state['state']='working'
 def close(self):pass
class Tests(unittest.TestCase):
 def setUp(self):self.b=Bridge(WorkspaceVoice());self.browser=Browser();self.b.browser=self.browser;self.b.browser_enabled=True
 def tearDown(self):self.b.close()
 def test_real_dispatch_source_review_observation_capture(self):
  s=self.b.execute({'command':'news-preview','source_url':'https://example.com/news'});p=s['news']['pending'];self.assertFalse(self.browser.calls)
  with self.assertRaises(ValueError):self.b.execute({'command':'news-open','reviewed':dict(p,value='https://example.org'),'confirm':True})
  self.b.execute({'command':'news-open','reviewed':p,'confirm':True});self.browser.state['state']='ready'
  s=self.b.execute({'command':'status'});self.assertEqual(s['news']['observed_url'],'https://example.com/news')
  self.b.execute({'command':'news-text','observed_url':'https://example.com/news','confirm':True});text='Fixture news text';row={'url':'https://example.com/news','text':text,'sha256':hashlib.sha256(text.encode()).hexdigest(),'scope':'Fixture quote'}
  self.browser.state.update(state='ready',news_text=row);s=self.b.execute({'command':'status'});self.assertEqual(s['news']['text_preview'],row)
  calls=[];self.b.setup.snapshot=lambda:{'ready':True};self.b.news_speech.play=lambda *a,**k:calls.append((a,k))
  self.b.execute({'command':'news-speak','reviewed':row,'confirm':True});self.assertEqual(calls[0][0][1],row)
  self.b.execute({'command':'news-cancel'});self.assertFalse(self.b.news.requested)
 def test_stop_and_malformed_capture_poll(self):
  self.b.news.observed_url='https://example.com/news';self.b.news.requested=True;self.browser.state['news_text']={'url':self.b.news.observed_url,'text':'tampered','sha256':'bad'}
  self.b.execute({'command':'status'});self.assertIsNone(self.b.news.text_preview)
  before=self.b.news_speech.generation;self.b.execute({'command':'pause'});self.assertGreater(self.b.news_speech.generation,before)
if __name__=='__main__':unittest.main(verbosity=2)
