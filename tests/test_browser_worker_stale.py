import unittest,threading,queue,importlib.util
from unittest.mock import Mock,patch
from jarvis.browser_control import BrowserSession
class WorkerStale(unittest.TestCase):
 @unittest.skipUnless(importlib.util.find_spec('playwright'),'Playwright worker integration tested separately')
 def test_same_url_changed_link_does_not_navigate(self):
  s=BrowserSession.__new__(BrowserSession);s.root='/tmp/fixture-profile';s.jobs=queue.Queue();s.lock=threading.RLock();s.cancel=threading.Event();s.state={}
  s.jobs.put(('open','https://example.com/old','https://example.com/'))
  page=Mock();page.url='https://example.com/';context=Mock();context.pages=[page]
  runtime=Mock();runtime.chromium.launch_persistent_context.return_value=context
  opener=Mock();opener.start.return_value=runtime
  def fresh(page):s.cancel.set();return {'links':[{'url':'https://example.com/new','id':'1','label':'new'}]}
  with patch('playwright.sync_api.sync_playwright',return_value=opener),patch('jarvis.browser_links.links',side_effect=fresh):s.run()
  page.goto.assert_not_called();self.assertEqual(s.state['state'],'off');context.close.assert_called_once()

 @unittest.skipUnless(importlib.util.find_spec('playwright'),'Playwright worker integration tested separately')
 def test_changed_page_scroll_does_not_scroll(self):
  s=BrowserSession.__new__(BrowserSession);s.root='/tmp/fixture-profile';s.jobs=queue.Queue();s.lock=threading.RLock();s.cancel=threading.Event();s.state={}
  s.jobs.put(('scroll-down','','https://example.com/old'))
  page=Mock();page.url='https://example.com/new';context=Mock();context.pages=[page]
  def close():s.cancel.set()
  runtime=Mock();runtime.chromium.launch_persistent_context.side_effect=lambda *a,**k:(s.cancel.set()or context)
  opener=Mock();opener.start.return_value=runtime
  with patch('playwright.sync_api.sync_playwright',return_value=opener):s.run()
  page.mouse.wheel.assert_not_called()
