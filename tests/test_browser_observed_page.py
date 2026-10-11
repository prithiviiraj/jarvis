import unittest,threading,queue
from types import SimpleNamespace
from jarvis.browser_control import BrowserSession
from jarvis.news_conductor import NewsConductor
class Observed(unittest.TestCase):
 def fixture(self):
  s=BrowserSession.__new__(BrowserSession);s.lock=threading.RLock();s.jobs=queue.Queue();s.cancel=threading.Event();s.state={'state':'ready','url':'https://example.com/news','news_text':{'text':'old'},'links':[{'url':'old'}],'requested_url':'https://example.com/news'}
  callbacks={};page=SimpleNamespace(url='https://example.com/news',main_frame=object(),on=lambda k,f:callbacks.update({k:f}));s.observe_page(page);return s,page,callbacks
 def test_manual_main_navigation_clears_quote_and_links(self):
  s,p,c=self.fixture();p.url='https://example.com/other';c['framenavigated'](p.main_frame);d=s.snapshot();self.assertEqual(d['url'],p.url);self.assertNotIn('news_text',d);self.assertEqual(d['links'],[]);self.assertEqual(d['requested_url'],'');self.assertEqual(d['page_revision'],1)
 def test_iframe_does_not_clear_main_quote(self):
  s,p,c=self.fixture();c['framenavigated'](object());self.assertIn('news_text',s.snapshot())
 def test_close_revokes_page(self):
  s,p,c=self.fixture();c['close']();self.assertEqual(s.state['state'],'off');self.assertNotIn('news_text',s.state)
 def test_reviewed_navigation_clears_quote_before_worker(self):
  for command in ('open','search','open-window'):
   s,p,c=self.fixture();s.submit(command,confirmed=True);self.assertNotIn('news_text',s.snapshot());self.assertEqual(s.state['links'],[])
 def test_same_url_new_document_revokes_observed_news(self):
  n=NewsConductor();p=n.preview('https://example.com/news');n.confirm(p,True);n.observe({'state':'ready','url':p['value'],'requested_url':p['value'],'page_revision':1});self.assertEqual(n.observed_revision,1)
  n.observe({'state':'ready','url':p['value'],'page_revision':2});self.assertEqual(n.observed_url,'');self.assertIsNone(n.text_preview)
