import threading,unittest,wave,io
import numpy as np
from jarvis.phone_audio import PhoneAudio
class STT:
 def transcribe_cancellable(self,samples,cancel):self.samples=samples;return 'open the browser and pay'
class Router:
 def __init__(self,cloud=False):self.cloud=cloud
 def ask(self,messages,cloud_consent):self.messages=messages;self.consent=cloud_consent;return {'text':'I cannot perform actions from this call.','cloud':self.cloud}
class Speaker:
 def prepare_stream(self,text):yield text,np.ones(2400,dtype=np.float32)*.1,24000
 def close(self):pass
class Tests(unittest.TestCase):
 def test_local_pipeline_no_action_dispatch_or_playback(self):
  stt=STT();r=Router();p=PhoneAudio(stt,r,Speaker());reply=p(b'\0\0'*1600,threading.Event());self.assertFalse(r.consent);self.assertEqual(len(stt.samples),1600);self.assertEqual(r.messages[-1]['content'],'open the browser and pay')
  with wave.open(io.BytesIO(reply['wav']))as w:self.assertEqual(w.getframerate(),24000);self.assertEqual(w.getnframes(),2400)
 def test_cloud_output_rejected(self):
  with self.assertRaises(ValueError):PhoneAudio(STT(),Router(True),Speaker())(b'\0\0'*1600,threading.Event())
 def test_cancel_before_loading(self):
  c=threading.Event();c.set()
  with self.assertRaises(ValueError):PhoneAudio()(b'\0\0'*1600,c)
 def test_bad_synth_samples(self):
  class Bad(Speaker):
   def prepare_stream(self,text):yield text,np.array([float('nan')]),24000
  with self.assertRaises(ValueError):PhoneAudio(STT(),Router(),Bad())(b'\0\0'*1600,threading.Event())
 def test_bounded_three_turn_context_reset_no_storage(self):
  r=Router();p=PhoneAudio(STT(),r,Speaker());c=threading.Event()
  for _ in range(5):p(b'\0\0'*1600,c)
  self.assertEqual(len(p.history),6);self.assertEqual(len(r.messages),8);self.assertFalse(r.consent);self.assertEqual(r.messages[1]['role'],'user');p.reset_session();self.assertEqual(p.history,[]);p(b'\0\0'*1600,c);self.assertEqual(len(r.messages),2)
 def test_stop_during_synthesis_clears_context(self):
  r=Router()
  class Reset(Speaker):
   def prepare_stream(self,text):p.reset_session();yield from super().prepare_stream(text)
  p=PhoneAudio(STT(),r,Reset())
  with self.assertRaises(ValueError):p(b'\0\0'*1600,threading.Event())
  self.assertEqual(p.history,[])
 def test_empty_transcript_not_sent_to_model(self):
  class Empty(STT):
   def transcribe_cancellable(self,s,c):return ''
  r=Router()
  with self.assertRaises(ValueError):PhoneAudio(Empty(),r,Speaker())(b'\0\0'*1600,threading.Event())
  self.assertFalse(hasattr(r,'messages'))
