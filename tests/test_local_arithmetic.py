import unittest
from jarvis.local_arithmetic import answer
class Arithmetic(unittest.TestCase):
 def test_exact_question(self):self.assertEqual(answer('JARVIS 52 plus 53.'),'52 plus 53 is 105.')
 def test_operations(self):
  for text,result in [('what is 2.5 plus 3?','5.5'),('calculate 15 minus 7','8'),('4 times 7','28'),('10 divided by 4','2.5')]:self.assertTrue(answer(text).endswith(' is '+result+'.'))
 def test_no_digit_or_intent_guess(self):
  for text in ['JARVIS ertu 52 plus 53.','what time is 52 plus 53','open 52 plus 53','52 plus 53 and delete file','__import__("os")','52 plus','2+3*4','what time is it','52 minus minus 2']:self.assertIsNone(answer(text),text)
 def test_zero(self):self.assertEqual(answer('5 divided by 0'),'I cannot divide by zero.')
class ArithmeticRuntime(unittest.TestCase):
 def test_spoken_uses_no_model_and_records_history(self):
  from unittest.mock import Mock
  from jarvis.runtime import VoiceRuntime
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.stt.transcribe.return_value='52 plus 53';v.enable(True);v.turn([0],v.generation,False,[])
  v.router.ask.assert_not_called();v.speaker.speak.assert_called_once_with('52 plus 53 is 105.',generation=v.speaker.generation);self.assertEqual(v.history[-1]['content'],'52 plus 53 is 105.');v.mic.resume.assert_called_once()
 def test_spoken_cancelled_playback_drops_history(self):
  from unittest.mock import Mock
  from jarvis.runtime import VoiceRuntime
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.stt.transcribe.return_value='52 plus 53';v.enable(True);v.speaker.speak.side_effect=lambda *a,**k:v.pause();v.turn([0],v.generation,False,[]);self.assertEqual(v.history,[])
class ArithmeticTyped(unittest.TestCase):
 def test_typed_uses_no_model_and_records_memory(self):
  from unittest.mock import Mock
  from jarvis.workspace_voice import WorkspaceVoice
  factory=Mock(side_effect=AssertionError('no chat model needed'));v=WorkspaceVoice(text_factory=factory);t=v.send_text('52 plus 53');t.join(2)
  factory.assert_not_called();self.assertFalse(v.busy);self.assertIn('105',str(v.memory.messages()));events=[]
  while not v.events.empty():events.append(v.events.get())
  self.assertTrue(any(k=='answer-complete'and x.get('provider')=='local-arithmetic'for k,x in events))
 def test_time_parser_does_not_accept_arithmetic(self):
  from jarvis.ui_bridge import Bridge
  # Invalid questions return before reading bridge or clock state.
  for text in ['52 plus 53','JARVIS ertu 52 plus 53.','52 plus 53 what time','calculate 52 plus 53']:
   self.assertFalse(Bridge.time_action(None,text))
