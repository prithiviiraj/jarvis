import unittest,threading
from unittest.mock import Mock
from jarvis.fast_ack import FastAck
class FastAckTests(unittest.TestCase):
 def speaker(self):
  s=Mock();s.generation=0;s.profile='JARVIS';s.prepare.return_value=('On it.',[.1],24000);return s
 def test_no_constructor_effect_or_uncached_synthesis(self):
  s=self.speaker();a=FastAck(s);s.prepare.assert_not_called();self.assertFalse(a.acknowledge('JARVIS',0,threading.Event()));s.prepare.assert_not_called();s.play_prepared.assert_not_called()
 def test_prepared_nonblocking_callback_and_queue_order(self):
  s=self.speaker();entered=threading.Event();release=threading.Event();s.play_prepared.side_effect=lambda *a:(entered.set(),release.wait(1));a=FastAck(s);a.prepare('JARVIS');self.assertTrue(a.acknowledge('JARVIS',0,threading.Event()));self.assertTrue(entered.wait(1));self.assertEqual(s.prepare.call_count,1);release.set();self.assertTrue(a.wait(threading.Event()));self.assertIn('playback_adapter_s',a.metrics)
 def test_generation_cancel_profile_gates(self):
  s=self.speaker();a=FastAck(s);a.prepare('JARVIS');cancel=threading.Event();cancel.set();self.assertFalse(a.acknowledge('JARVIS',0,cancel));self.assertFalse(a.acknowledge('JARVIS',1,threading.Event()));self.assertFalse(a.acknowledge('LYRA',0,threading.Event()));s.play_prepared.assert_not_called()
 def test_clear_drops_cache(self):
  s=self.speaker();a=FastAck(s);a.prepare('JARVIS');a.clear();self.assertFalse(a.acknowledge('JARVIS',0,threading.Event()))
 def test_actual_prepared_speaker_callback_with_only_output_mocked(self):
  import numpy as np
  from jarvis.experimental.kokoro_speaker import KokoroSpeaker
  writes=[]
  class Output:
   def start(self):pass
   def write(self,audio):writes.append(len(audio))
   def stop(self):pass
   def abort(self):pass
   def close(self):pass
  synth=Mock();synth.synthesize.return_value=(np.ones(1024,dtype='float32')*.01,24000);s=KokoroSpeaker(synth,lambda sr:Output());s.profiles={'JARVIS':synth};s.select_profile('JARVIS');ack=FastAck(s);ack.prepare('JARVIS');synth.synthesize.reset_mock();self.assertTrue(ack.acknowledge('JARVIS',0,threading.Event()));ack.wait(threading.Event());self.assertEqual(writes,[512,512]);synth.synthesize.assert_not_called()
 def test_live_runtime_never_uses_legacy_ack(self):
  from jarvis.runtime import VoiceRuntime
  for streaming in (False,True):
   with self.subTest(streaming=streaming):
    events=[];speaker=Mock();stt=Mock();stt.transcribe.return_value='hello';router=Mock();router.ask.return_value={'text':'Useful reply'};router.stream.return_value=iter([{'text':'Useful reply.','provider':'local'}]);v=VoiceRuntime(Mock(),stt,router,speaker,lambda *e:events.append(e));v.mic=Mock();v.fast_ack=Mock();v.streaming=streaming
    v.enable(True);v.turn([0],v.generation,False,[]);v.fast_ack.acknowledge.assert_not_called();v.fast_ack.wait.assert_not_called();self.assertTrue(v.history);self.assertFalse(any(k=='metrics'and x.get('output_includes_ack')for k,x in events));v.close()
 def test_pause_before_reply_still_discards_output(self):
  from jarvis.runtime import VoiceRuntime
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.stt.transcribe.return_value='hello';v.fast_ack=Mock();v.router.ask.side_effect=lambda *a,**kw:(v.pause()or{'text':'late'});v.enable(True);v.turn([0],v.generation,False,[]);self.assertEqual(v.history,[]);v.speaker.speak.assert_not_called();v.fast_ack.acknowledge.assert_not_called();v.close()
