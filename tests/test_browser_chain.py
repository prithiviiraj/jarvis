import unittest,threading,json
from unittest.mock import Mock,patch
from jarvis.browser_chain import parse,execute,validate
from jarvis.ui_bridge import Bridge
class Chain(unittest.TestCase):
 def test_user_ironman_chain(self):
  p=parse('Jarvis open browser, search Iron Man, open its Wikipedia page, click first link');self.assertEqual([s['command']for s in validate(p['value'])],['open-window','search','observed-site','observed-link'])
 def test_atomic_bad_step_rejected(self):
  for t in ('open browser then send a message','open browser then type password','open browser then open https://127.0.0.1/','do not open browser then search Iron Man'):
   with self.assertRaises(ValueError):parse(t)
 def test_single_command_untouched(self):self.assertIsNone(parse('browser search for Iron Man'))
 def test_order_observed_site_and_links(self):
  p=Mock();p.url='https://example.com/';p.title.return_value='Fixture';events=[]
  def act(self,c,v='',confirmed=False):events.append((c,v));p.url=v if c=='open'else'https://example.com/search';return {'url':p.url,'title':'Fixture'}
  rows={'page_url':p.url,'links':[{'id':'1','label':'Iron Man','url':'https://en.wikipedia.org/wiki/Iron_Man'}]}
  def observed(page):return dict(rows,page_url=p.url)
  with patch('jarvis.browser_control.BrowserControl.execute',act),patch('jarvis.browser_links.links',side_effect=observed):r=execute(p,parse('open browser then search Iron Man then open Wikipedia page')['value'],threading.Event())
  self.assertEqual(events,[('open-window',''),('search','Iron Man'),('open','https://en.wikipedia.org/wiki/Iron_Man')]);self.assertEqual(len(r['chain_steps']),3)
 def test_ambiguous_site_stops_without_guess(self):
  p=Mock();p.url='https://example.com/';p.title.return_value='Fixture'
  with patch('jarvis.browser_control.BrowserControl.execute',return_value={'url':p.url,'title':'Fixture'}),patch('jarvis.browser_links.links',return_value={'page_url':p.url,'links':[]}):
   with self.assertRaises(ValueError):execute(p,parse('open browser then open Wikipedia')['value'],threading.Event())
 def test_stop_discards_remaining_steps(self):
  p=Mock();cancel=threading.Event();actions=[]
  def act(self,c,v='',confirmed=False):actions.append(c);cancel.set();return {'url':'about:blank','title':''}
  with patch('jarvis.browser_control.BrowserControl.execute',act):
   with self.assertRaises(ValueError):execute(p,parse('open browser then search Iron Man')['value'],cancel)
  self.assertEqual(actions,['open-window'])
 def test_bridge_off_and_review_gate(self):
  b=Bridge();b.voice.send_text=Mock()
  try:
   b.execute({'command':'chat','text':'open browser then search Iron Man'});self.assertIsNone(b.browser);b.voice.send_text.assert_not_called()
   b.browser_enabled=True;b.execute({'command':'chat','text':'open browser then search Iron Man'});self.assertEqual(b.browser_pending['command'],'chain');self.assertIsNone(b.browser)
  finally:b.close()
