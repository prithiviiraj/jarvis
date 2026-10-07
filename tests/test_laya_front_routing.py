import unittest
from unittest.mock import Mock
from jarvis.action_intent import parse,goal
from jarvis.moderator import pick
from jarvis.runtime import VoiceRuntime
class LayaFrontRouting(unittest.TestCase):
 def test_laya_browser_command_and_query(self):
  self.assertEqual(parse('Laya. Open the browser.'),{'command':'open-window','value':''})
  self.assertEqual(parse('Hey, Laya, open YouTube.'),{'command':'open','value':'https://www.youtube.com/'})
  self.assertIsNone(parse('Laya, why is politics important?'))
  self.assertIsNone(goal('Laya, how can I open the browser?'))
  self.assertEqual(pick('Laya, why is politics important?','LYRA')[0],'JARVIS')
 def test_lyra_spoken_address_speaker_and_router(self):
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.persona='JARVIS';v.stt.transcribe.return_value='Hey, Lyra. Can you hear me?';v.router.ask.return_value={'text':'Hi master.'};v.enable(True);v.turn([0],v.generation,False,[])
  self.assertEqual(v.persona,'LYRA');v.speaker.select_profile.assert_called_once_with('LYRA');v.router.select_persona.assert_called_once_with('LYRA');v.speaker.speak.assert_called_once()
 def test_spoken_laya_query_goes_to_leader_not_selected_profile(self):
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.persona='LYRA';v.stt.transcribe.return_value='Laya, what can you do?';v.router.ask.return_value={'text':'I can help with reviewed browser commands.'};v.enable(True);v.turn([0],v.generation,False,[])
  self.assertEqual(v.persona,'JARVIS');v.speaker.select_profile.assert_called_once_with('JARVIS');v.router.select_persona.assert_called_once_with('JARVIS')

 def test_profile_select_visible_mic_off_no_restart(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  v=WorkspaceVoice();v.start=Mock();b=Bridge(voice=v)
  try:
   state=b.execute({'command':'select','name':'LYRA'})
   self.assertFalse(state['voice_active']);self.assertIn('LYRA selected. Mic OFF',state['status']);v.start.assert_not_called()
  finally:b.close()

class LayaDirectAcceptance(unittest.TestCase):
 def test_active_typed_browser_submits_without_review_or_model(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  v=WorkspaceVoice();v.send_text=Mock();b=Bridge(v);b.execute({'command':'laya-session','enabled':True,'consent':True});browser=Mock();browser.cancel.is_set.return_value=False;browser.snapshot.return_value={'state':'ready','url':'about:blank'};b.browser=browser
  try:
   b.execute({'command':'chat','text':'open the browser'});browser.submit.assert_called_once_with(command='open-window',value='',confirmed=True);self.assertIsNone(b.browser_pending);v.send_text.assert_not_called();self.assertFalse(any('prepared for review' in e['text'] for e in b.reo_log))
  finally:b.close()
 def test_active_spoken_browser_submits_without_review(self):
  from jarvis.ui_bridge import Bridge
  b=Bridge();b.execute({'command':'laya-session','enabled':True,'consent':True});browser=Mock();browser.cancel.is_set.return_value=False;browser.snapshot.return_value={'state':'ready','url':'about:blank'};b.browser=browser
  try:
   self.assertTrue(b.voice_action('Laya, open the browser'));browser.submit.assert_called_once_with(command='open-window',value='',confirmed=True);self.assertIsNone(b.browser_pending)
  finally:b.close()
