import unittest
from unittest.mock import Mock,patch
from jarvis.action_intent import parse
from jarvis.desktop_actions import prepare
from jarvis.ui_bridge import Bridge
class BoundedLaunchLanguage(unittest.TestCase):
 def test_natural_launch_grammar(self):
  for text in ('bring up Brave','Dex launch the browser','Jarvis please start Brave browser','Lyra bring up browser please'):
   self.assertEqual(parse(text),{'command':'open-window','value':''},text)
  for text in ('Dex bring up calculator','start Paint now','Jarvis please launch Notepad','bring up the notepad app for me'):
   self.assertIsNotNone(prepare(text),text)
 def test_questions_negation_and_extra_effects_never_launch(self):
  for text in ('How do I start Brave?','Do not bring up Brave','Can you explain how to launch browser?','start browser then send email','start browser tomorrow','start browser; calc.exe','start my browser profile','launch Firefox'):
   self.assertIsNone(parse(text),text)
  for text in ('How do I start Paint?','Do not start Paint','start Calculator and delete files','start Paint tomorrow','launch Notepad secret.txt','bring up cmd'):
   self.assertIsNone(prepare(text),text)
 def test_direct_session_silent_no_model_or_popup_and_revoke(self):
  b=Bridge();b.voice.send_text=Mock();b.understand_action=Mock();b.browser=Mock();b.browser.cancel.is_set.return_value=False
  try:
   b.activation_action('activate laya')
   b.execute({'command':'chat','text':'Dex bring up Brave'})
   b.browser.submit.assert_called_once_with(command='open-window',value='',confirmed=True)
   with patch('jarvis.desktop_actions.launch',return_value={'app':'Calculator','status':'submitted'})as launch:
    b.execute({'command':'chat','text':'start Calculator now'});launch.assert_called_once()
   b.voice.send_text.assert_not_called();b.understand_action.assert_not_called();self.assertIsNone(b.neural.snapshot()['row'])
   b.activation_action('deactivate laya');b.browser.submit.reset_mock()
   b.execute({'command':'chat','text':'bring up Brave'});b.browser.submit.assert_not_called()
  finally:b.close()
 def test_camera_hint_has_current_single_switch(self):
  b=Bridge()
  try:
   hint=b.interface_context('can you see me');self.assertIn('Camera ON starts presence and checks local vision together',hint);self.assertNotIn('then Allow camera vision',hint)
  finally:b.close()
