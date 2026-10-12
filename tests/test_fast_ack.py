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
 def test_real_runtime_model_runs_during_ack_and_reply_waits(self):
  import numpy as np
  from jarvis.runtime import VoiceRuntime
  from jarvis.experimental.kokoro_speaker import KokoroSpeaker
  entered=threading.Event();release=threading.Event();events=[]
  class Output:
   def start(self):pass
   def write(self,audio):events.append('output');entered.set();release.wait(1)
   def stop(self):pass
   def abort(self):release.set()
   def close(self):pass
  synth=Mock();synth.synthesize.return_value=(np.ones(512,dtype='float32'),24000);s=KokoroSpeaker(synth,lambda sr:Output());s.profiles={'JARVIS':synth};s.select_profile('JARVIS');ack=FastAck(s);ack.prepare('JARVIS')
  stt=Mock();stt.transcribe.return_value='hello';router=Mock()
  def answer(*a,**k):self.assertTrue(entered.wait(1));events.append('model');release.set();return {'text':'Hello'}
  router.ask.side_effect=answer;v=VoiceRuntime(Mock(),stt,router,s);v.mic=Mock();v.fast_ack=ack;v.enable(True);v.turn([0],v.generation,False,[]);self.assertEqual(events,['output','model','output']);v.close()
 def test_real_runtime_streaming_generates_before_ack_finishes(self):
  import numpy as np
  from jarvis.runtime import VoiceRuntime
  from jarvis.experimental.kokoro_speaker import KokoroSpeaker
  entered=threading.Event();release=threading.Event();events=[]
  class Output:
   def start(self):pass
   def write(self,audio):events.append('output');entered.set();release.wait(1)
   def stop(self):pass
   def abort(self):release.set()
   def close(self):pass
  synth=Mock();synth.synthesize.return_value=(np.ones(512,dtype='float32'),24000);s=KokoroSpeaker(synth,lambda sr:Output());s.profiles={'JARVIS':synth};s.select_profile('JARVIS');ack=FastAck(s);ack.prepare('JARVIS');stt=Mock();stt.transcribe.return_value='hello';router=Mock()
  def chunks(*a,**k):self.assertTrue(entered.wait(1));events.append('model');release.set();yield {'text':'Hello.','provider':'local'}
  router.stream.side_effect=chunks;v=VoiceRuntime(Mock(),stt,router,s);v.mic=Mock();v.fast_ack=ack;v.streaming=True;v.enable(True);v.turn([0],v.generation,False,[]);self.assertEqual(events,['output','model','output']);v.close()
 def test_real_team_runtime_one_ack_and_actual_persona_voices(self):
  import numpy as np
  from jarvis.runtime import VoiceRuntime
  from jarvis.experimental.kokoro_speaker import KokoroSpeaker
  outputs=[]
  class Output:
   def start(self):pass
   def write(self,audio):outputs.append('output')
   def stop(self):pass
   def abort(self):pass
   def close(self):pass
  synth=Mock();synth.synthesize.return_value=(np.ones(512,dtype='float32'),24000);s=KokoroSpeaker(synth,lambda sr:Output());s.profiles={p:synth for p in ('JARVIS','LYRA','DEX')};s.select_profile('JARVIS');ack=FastAck(s)
  for p in s.profiles:ack.prepare(p)
  s.select_profile('JARVIS');stt=Mock();stt.transcribe.return_value='Discuss among yourselves how to help me study';router=Mock();router.ask.return_value={'text':'One useful reply'};v=VoiceRuntime(Mock(),stt,router,s);v.mic=Mock();v.fast_ack=ack;v.enable(True);v.turn([0],v.generation,False,[]);self.assertEqual(len(outputs),5);self.assertEqual(router.ask.call_count,4);self.assertEqual(v.persona,'JARVIS');v.close()
 def test_real_runtime_pause_during_ack_clears_output_and_drops_reply(self):
  import numpy as np
  from jarvis.runtime import VoiceRuntime
  from jarvis.experimental.kokoro_speaker import KokoroSpeaker
  entered=threading.Event();release=threading.Event();outputs=[]
  class Output:
   def start(self):pass
   def write(self,audio):outputs.append(True);entered.set();release.wait(1)
   def stop(self):pass
   def abort(self):release.set()
   def close(self):pass
  synth=Mock();synth.synthesize.return_value=(np.ones(512,dtype='float32'),24000);s=KokoroSpeaker(synth,lambda sr:Output());s.profiles={'JARVIS':synth};s.select_profile('JARVIS');ack=FastAck(s);ack.prepare('JARVIS');stt=Mock();stt.transcribe.return_value='hello';router=Mock();v=VoiceRuntime(Mock(),stt,router,s);v.mic=Mock();v.fast_ack=ack
  def answer(*a,**k):self.assertTrue(entered.wait(1));v.pause();return {'text':'Late answer'}
  router.ask.side_effect=answer;v.enable(True);v.turn([0],v.generation,False,[]);ack.worker.join(1);self.assertEqual(len(outputs),1);self.assertEqual(v.history,[]);self.assertIsNone(s.output);v.close()
