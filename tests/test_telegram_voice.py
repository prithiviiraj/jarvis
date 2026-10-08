import unittest,threading,tempfile,pathlib,base64,hashlib
from jarvis.telegram_voice import TelegramVoice
from jarvis.telegram_output import TelegramOutput
import test_telegram_output as output
class Speaker:
 def __init__(self):self.selected=None;self.closed=False
 def select_profile(self,name):self.selected=name
 def prepare_stream(self,text):return iter([('fixture',[0.1]*2400,24000)])
 def close(self):self.closed=True
class Encoder:
 def set_bit_rate(self,*a):pass
 def set_in_sample_rate(self,*a):pass
 def set_channels(self,*a):pass
 def set_quality(self,*a):pass
 def encode(self,p):return b'fixture-MP3'*40
 def flush(self):return b'end'
class Tests(unittest.TestCase):
 def test_synthesis_only_bound_audio_hash_and_cancel(self):
  s=Speaker();v=TelegramVoice(s,Encoder);r=v.render('Exact words',lambda:False);raw=base64.b64decode(r['audio_base64']);self.assertEqual(hashlib.sha256(raw).hexdigest(),r['audio_sha256']);self.assertEqual(r['text'],'Exact words');self.assertEqual(s.selected,'JARVIS')
  with self.assertRaises(ValueError):v.render('Words',lambda:True)
  with self.assertRaises(ValueError):v.render('x'*901,lambda:False)
  v.close();self.assertTrue(s.closed)
 def test_real_mp3_encoder_fixture_audio(self):
  try:import lameenc
  except ImportError:self.skipTest('MP3 binary absent in light source environment')
  r=TelegramVoice(Speaker()).render('Fixture words',lambda:False);raw=base64.b64decode(r['audio_base64']);self.assertTrue(len(raw)>100);self.assertTrue(raw.startswith(b'ID3')or raw[0]==255);self.assertEqual(r['mime'],'audio/mpeg')
class WorkflowTests(output.Tests):
 def test_voice_preview_review_and_exact_caption_no_paid_send(self):
  calls=[]
  def send(m,p):calls.append((m,p));return {'message_id':42,'chat':{'id':77,'type':'private'},'caption':p['caption'],'voice':{'file_id':'controlled-voice'}}
  j=TelegramOutput(self.c,self.path,send,TelegramVoice(Speaker(),Encoder));j.prepare_voice('Exact voice words');j.worker.join(2);r=j.snapshot()['plan'];self.assertFalse(calls);self.assertEqual(r['payload']['format'],'voice')
  with self.assertRaises(ValueError):j.submit(r)
  j.submit(r,True);j.worker.join(2);self.assertEqual(j.snapshot()['state'],'completed');self.assertEqual(calls[0][0],'sendVoice');self.assertFalse(calls[0][1]['allow_paid_broadcast']);self.assertEqual(calls[0][1]['caption'],'Exact voice words')
 def test_audio_hash_mutation_never_sends(self):
  j=TelegramOutput(self.c,self.path,self.send,TelegramVoice(Speaker(),Encoder));j.prepare_voice('Words');j.worker.join(2);r=j.snapshot()['plan'];r['payload']['audio']['audio_sha256']='changed'
  with self.assertRaises(ValueError):j.submit(r,True)
  self.assertFalse(self.calls)
 def test_snapshot_cannot_mutate_durable_audio_review(self):
  j=TelegramOutput(self.c,self.path,self.send,TelegramVoice(Speaker(),Encoder));j.prepare_voice('Words');j.worker.join(2);r=j.snapshot()['plan'];r['payload']['audio']['audio_sha256']='changed';self.assertNotEqual(j.snapshot()['plan']['payload']['audio']['audio_sha256'],'changed')
 def test_stop_during_voice_render_no_late_review(self):
  ready=threading.Event();release=threading.Event()
  class Delayed:
   def render(self,text,cancel):ready.set();release.wait(2);return TelegramVoice(Speaker(),Encoder).render(text,cancel)
  j=TelegramOutput(self.c,self.path,self.send,Delayed());j.prepare_voice('Words');self.assertTrue(ready.wait(2));j.stop();release.set();j.worker.join(2);self.assertIsNone(j.snapshot()['plan']);self.assertFalse(self.calls)
