import unittest,threading
from unittest.mock import Mock
from jarvis.action_intent import parse
class LivePhraseRepair(unittest.TestCase):
 def test_exact_screenshot_spoken_dots(self):
  for text in ['JARVIS. OPEN. BROWSER.','Open. The. Browser.','Open. Browser.']:
   self.assertEqual(parse(text),{'command':'open-window','value':''})
  self.assertEqual(parse('open https://example.com/hello.world'),{'command':'open','value':'https://example.com/hello.world'})
  self.assertIsNone(parse('Why open. browser?'))
 def test_action_before_cloud_chat(self):
  from jarvis.runtime import VoiceRuntime
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.stt.transcribe.return_value='JARVIS. OPEN. BROWSER.';v.action_handler=lambda text:parse(text)is not None;v.enable(True);v.turn([0],v.generation,True,[])
  v.router.ask.assert_not_called();v.router.stream.assert_not_called();v.speaker.speak.assert_not_called()
 def test_later_turn_clears_old_limit_warning(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(voice=WorkspaceVoice())
  try:
   b.voice.notify('error','Reply reached the completion limit and may be incomplete.');self.assertTrue(b.execute({'command':'status'})['warning'])
   b.voice.notify('transcript','new successful turn');self.assertEqual(b.execute({'command':'status'})['warning'],'')
   b.warning='previous limit';b.execute({'command':'chat','text':'Open the browser.'});self.assertEqual(b.warning,'')
  finally:b.close()
 def test_en_wrong_script_rejected_before_dispatch(self):
  from jarvis.speech import WhisperSTT,UnclearSpeech
  v=WhisperSTT.__new__(WhisperSTT);v.lock=threading.RLock();v.language='en';v.vocabulary='Jarvis';v.model=Mock()
  segment=Mock(text='JARVIS トープアンド ブラウザル',no_speech_prob=.1,avg_logprob=-.2);v.model.transcribe.return_value=(iter([segment]),Mock())
  with self.assertRaises(UnclearSpeech):v.transcribe([0])
  self.assertEqual(v.model.transcribe.call_args.kwargs['language'],'en')
  v.model.transcribe.return_value=(iter([Mock(text='Jarvis open the browser',no_speech_prob=.1,avg_logprob=-.2)]),Mock());self.assertEqual(v.transcribe([0]),'Jarvis open the browser')
