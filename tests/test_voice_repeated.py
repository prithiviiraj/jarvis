import unittest,threading
from unittest.mock import Mock
from jarvis.runtime import VoiceRuntime
from jarvis.router import RouterError
class RepeatedVoice(unittest.TestCase):
 def test_twenty_turns_with_intermittent_model_failures(self):
  events=[];v=VoiceRuntime(Mock(),Mock(),Mock(),Mock(),lambda k,x:events.append((k,x)));v.mic=Mock();v.stt.transcribe.return_value='hello';v.streaming=True;v.enable(True)
  successes=0
  for n in range(20):
   if n%4==0:v.router.stream.side_effect=RouterError('local:connection')
   else:v.router.stream.side_effect=lambda *a,**kw:iter([{'text':'Hi.','provider':'local'}]);successes+=1
   v.turn([0],v.generation,False,list(v.history));self.assertFalse(v.busy);self.assertTrue(v.enabled)
  self.assertEqual(v.speaker.speak.call_count,successes);self.assertEqual(v.mic.resume.call_count,20);self.assertEqual(sum(k=='error' and bool(x) for k,x in events),5);self.assertLessEqual(len(v.history),6)
