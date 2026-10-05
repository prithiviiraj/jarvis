import unittest
from unittest.mock import Mock
from jarvis.action_intent import parse
from jarvis.ui_bridge import Bridge
class Intents(unittest.TestCase):
 def test_any_persona_or_bare(self):
  for name in ('Jarvis','Nova','Lyra','Kai','Dex','Reo',''):
   self.assertEqual(parse(name+' can you open the browser?'),{'command':'open-window','value':''})
  self.assertEqual(parse('open browser'),{'command':'open-window','value':''})
 def test_questions_not_commands(self):
  for t in ('Jarvis what is time now?','How do I open browser?','What happens if I scroll down?','Nova is browser open?'):self.assertIsNone(parse(t))
 def test_small_scroll(self):
  self.assertEqual(parse('Nova scroll slightly')['command'],'scroll-down-small');self.assertEqual(parse('scroll up a little')['command'],'scroll-up-small')
 def test_off_blocks_no_chat(self):
  b=Bridge();b.voice.send_text=Mock();b.execute({'command':'chat','text':'Jarvis can you open browser?'});b.voice.send_text.assert_not_called();self.assertIsNone(b.browser);self.assertEqual(b.reo_log[-1]['state'],'blocked');b.close()
 def test_no_laya_mode_needed_direct_review(self):
  b=Bridge();b.browser_enabled=True;b.execute({'command':'chat','text':'Nova open browser'});self.assertEqual(b.browser_pending['command'],'open-window');self.assertFalse(b.laya_enabled);self.assertIsNone(b.browser);b.close()
 def test_scroll_bound_current_page(self):
  b=Bridge();b.browser_enabled=True;b.browser=Mock();b.browser.cancel.is_set.return_value=False;b.browser.snapshot.return_value={'state':'ready','url':'https://example.com/'};b.shared_action('scroll slightly');self.assertEqual(b.browser_pending,{'command':'scroll-down-small','value':'','expected_url':'https://example.com/'});b.browser.submit.assert_not_called();b.close()
 def test_shared_goal_any_profile(self):
  from jarvis.action_intent import goal
  for name in ('Jarvis','Nova','Lyra','Kai','Dex','Reo',''):
   self.assertEqual(goal(name+' find the documentation link'),'find the documentation link')
  self.assertIsNone(goal('Jarvis what is time now'))
  self.assertIsNone(goal('browser read links'))
 def test_shared_goal_laya_still_blocked_without_consent(self):
  b=Bridge();b.voice.send_text=Mock();b.execute({'command':'chat','text':'Nova find the documentation link'});b.voice.send_text.assert_not_called();self.assertEqual(b.reo_log[-1]['state'],'blocked');self.assertIsNone(b.browser);b.close()
 def test_compound_youtube_one_review_not_effect(self):
  self.assertEqual(parse('JARVIS, open the browser and open YouTube.'),{'command':'open','value':'https://www.youtube.com/'})
  self.assertEqual(parse('open YouTube'),{'command':'open','value':'https://www.youtube.com/'})
  b=Bridge();b.browser_enabled=True;b.voice.runtime=Mock();b.execute({'command':'chat','text':'open YouTube'});self.assertEqual(b.browser_pending['value'],'https://www.youtube.com/');self.assertIsNone(b.browser);b.close()
 def test_laya_loading_and_mic_exclusive(self):
  b=Bridge();b.laya_engine.load=Mock();b.voice.runtime=Mock()
  with self.assertRaises(ValueError):b.execute({'command':'laya-load','consent':True})
  b.laya_engine.load.assert_not_called();b.voice.runtime=None;b.laya_engine.loading=True;b.voice.start=Mock()
  with self.assertRaises(ValueError):b.execute({'command':'voice-on','consent':True})
  b.voice.start.assert_not_called();b.laya_engine.loading=False;b.close()
