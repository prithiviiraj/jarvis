import unittest,threading,time
from unittest.mock import Mock,patch
from jarvis.reo_commands import parse
from jarvis.ui_bridge import Bridge
class Reo(unittest.TestCase):
 def test_explicit_and_queries(self):
  for t in ('Reo open example.com','Jarvis ask Reo to scroll down','hey Reo browser read links','Reo find the docs link'):self.assertIsNotNone(parse(t))
  for t in ('Reo what is Laya?','Open browser','find docs','Reo explain recursion','Tell me about Reo'):self.assertIsNone(parse(t))
 def test_off_no_chat_or_browser(self):
  b=Bridge();b.voice.send_text=Mock();b.execute({'command':'chat','text':'Reo open example.com'});b.voice.send_text.assert_not_called();self.assertIsNone(b.browser_pending);self.assertEqual(b.reo_log[-1]['state'],'blocked');b.close()
 def test_direct_review_no_submit(self):
  b=Bridge();b.laya_enabled=True;b.browser_enabled=True;b.browser=Mock();b.browser.cancel.is_set.return_value=False
  self.assertTrue(b.reo_action('Reo open example.com'));self.assertEqual(b.browser_pending,{'command':'open','value':'https://example.com'});b.browser.submit.assert_not_called();b.close()
 def test_query_stays_chat(self):
  b=Bridge();b.voice.send_text=Mock();b.execute({'command':'chat','text':'Reo explain Laya'});b.voice.send_text.assert_called_once_with('Reo explain Laya',auto_pick=True);b.close()
 def test_laya_goal_and_no_load(self):
  b=Bridge();b.laya_enabled=True;b.browser_enabled=True;b.start_laya=Mock();b.reo_action('Reo find documentation');b.start_laya.assert_not_called();self.assertEqual(b.reo_log[-1]['state'],'blocked');b.laya_engine.agent=Mock();b.reo_action('Reo find documentation');b.start_laya.assert_called_once_with('find documentation');b.close()
 def test_bounded_log(self):
  b=Bridge()
  for i in range(40):b.reo_event('x','test')
  self.assertEqual(len(b.reo_log),30);self.assertEqual(b.reo_log[-1]['id'],40);b.close()
 def test_voice_route_silent(self):
  b=Bridge();b.voice.notify=Mock();self.assertTrue(b.voice_action('Reo open example.com'));b.voice.notify.assert_not_called();b.close()
 def test_browser_completion_is_bounded_status(self):
  b=Bridge();b.browser=Mock();b.browser.snapshot.return_value={'state':'ready','url':'https://example.com'};b.reo_submitted=True;b.poll();self.assertFalse(b.reo_submitted);self.assertEqual(b.reo_log[-1]['state'],'completed');self.assertIn('not the whole user goal',b.reo_log[-1]['text']);b.close()
 def test_no_silent_browser_start(self):
  b=Bridge();b.laya_enabled=True;b.browser_enabled=True;b.reo_action('Reo open example.com');self.assertIsNone(b.browser);self.assertIsNotNone(b.browser_pending);b.close()
