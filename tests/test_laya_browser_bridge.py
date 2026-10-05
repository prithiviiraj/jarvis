import unittest,time,threading
from unittest.mock import Mock,patch
from jarvis.ui_bridge import Bridge
from jarvis.laya_browser import prepare
from jarvis.experimental.browser_proposals import Proposal
class LayaBrowser(unittest.TestCase):
 def state(self):return {'state':'ready','url':'https://example.com/','links':[{'id':'1','label':'Docs','url':'https://www.iana.org/help/example-domains'}]}
 def bridge(self):
  b=Bridge();b.browser_enabled=True;b.browser=Mock();b.browser.cancel.is_set.return_value=False;b.browser.snapshot.side_effect=lambda:self.state();return b
 def wait(self,b):
  deadline=time.monotonic()+2
  while b.laya_state['busy']and time.monotonic()<deadline:time.sleep(.01)
  self.assertFalse(b.laya_state['busy'])
 def test_proposal_not_execution_and_exact_url(self):
  client=Mock();client.prepare.side_effect=lambda snapshot,*a:Proposal('CLICK',snapshot.id,'1')
  p,status=prepare(self.state(),'Open docs',client);self.assertEqual(p,{'command':'open','value':'https://www.iana.org/help/example-domains','expected_url':'https://example.com/'})
  self.assertIn('review',status.lower());self.assertNotIn('executed',p)
 def test_outside_operation_and_unobserved_target_refused(self):
  for op,target in [('PAY',None),('CLICK','999')]:
   client=Mock();client.prepare.side_effect=lambda snapshot,*a:Proposal(op,snapshot.id,target)
   with self.assertRaises(ValueError):prepare(self.state(),'Open docs',client)
 def test_explicit_mode_and_threaded_proposal_no_submit(self):
  b=self.bridge()
  with self.assertRaises(ValueError):b.execute({'command':'laya-mode'})
  with self.assertRaises(ValueError):b.execute({'command':'laya-propose','goal':'Open docs'})
  b.execute({'command':'laya-mode','consent':True})
  with patch('jarvis.laya_browser.prepare',return_value=({'command':'scroll-down','value':'','expected_url':'https://example.com/'},'review')):
   b.execute({'command':'laya-propose','goal':'Open docs'});self.wait(b)
  self.assertEqual(b.browser_pending['command'],'scroll-down');b.browser.submit.assert_not_called();b.close()
 def test_stop_discards_late_reply(self):
  b=self.bridge();b.execute({'command':'laya-mode','consent':True});started=threading.Event();finish=threading.Event()
  def slow(*a,**kw):started.set();finish.wait(2);return {'command':'scroll-down','value':'','expected_url':'https://example.com/'},'review'
  with patch('jarvis.laya_browser.prepare',side_effect=slow):
   b.execute({'command':'laya-propose','goal':'Read docs'});self.assertTrue(started.wait(1));b.execute({'command':'laya-stop'});finish.set();time.sleep(.05)
  self.assertIsNone(b.browser_pending);self.assertFalse(b.laya_enabled);b.browser.submit.assert_not_called();b.close()
 def test_changed_links_discards_reply(self):
  b=self.bridge();b.execute({'command':'laya-mode','consent':True});state=self.state();b.browser.snapshot.side_effect=lambda:state
  def change(*a,**kw):state['links']=[];return {'command':'open','value':'https://www.iana.org/help/example-domains','expected_url':'https://example.com/'},'review'
  with patch('jarvis.laya_browser.prepare',side_effect=change):b.execute({'command':'laya-propose','goal':'Open docs'});self.wait(b)
  self.assertIsNone(b.browser_pending);b.browser.submit.assert_not_called();b.close()
 def test_rust_allowlist(self):
  from pathlib import Path
  s=(Path(__file__).parents[1]/'modern-ui/src-tauri/src/main.rs').read_text();self.assertIn('"laya-propose"',s.split('.contains(&command)')[0])
