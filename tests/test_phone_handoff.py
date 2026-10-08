import unittest,copy,time
from jarvis.phone_controller import PhoneController
from jarvis.phone_audio import PhoneAudio
class Tests(unittest.TestCase):
 def setUp(self):
  self.p=PhoneAudio();self.c=PhoneController(self.p);code=self.c.enable(True);review=self.c.request_pair(code,'Unverified');self.token=self.c.approve(review,True);self.p.history=[{'role':'user','content':'remember this private note'},{'role':'assistant','content':'unverified reply'}]
 def tearDown(self):self.c.stop()
 def test_exact_review_stop_and_no_automatic_send(self):
  r=self.c.prepare_handoff(True);self.assertEqual(r['turns'],1);self.assertIn('unverified',r['text']);self.assertTrue(self.c.snapshot()['paired']);self.assertEqual(self.c.apply_handoff(r,True),r['text']);self.assertFalse(self.c.snapshot()['paired']);self.assertEqual(self.p.history,[]);self.assertIsNone(self.c.snapshot()['handoff'])
 def test_changed_words_and_expiry_refused(self):
  r=self.c.prepare_handoff(True);other=copy.deepcopy(r);other['text']='replacement'
  with self.assertRaises(ValueError):self.c.apply_handoff(other,True)
  self.c.handoff_deadline=time.monotonic()-1
  with self.assertRaises(ValueError):self.c.apply_handoff(r,True)
 def test_stop_cancel_repair_refuse_old_review(self):
  r=self.c.prepare_handoff(True);self.c.stop_handoff()
  with self.assertRaises(ValueError):self.c.apply_handoff(r,True)
  r=self.c.prepare_handoff(True);self.c.enable(True)
  with self.assertRaises(ValueError):self.c.apply_handoff(r,True)
 def test_busy_unpaired_no_consent_refused(self):
  with self.assertRaises(ValueError):self.c.prepare_handoff()
  self.c.session.busy=True
  with self.assertRaises(ValueError):self.c.prepare_handoff(True)
  self.c.session.busy=False;self.c.stop()
  with self.assertRaises(ValueError):self.c.prepare_handoff(True)
 def test_desktop_busy_refuses_apply(self):
  r=self.c.prepare_handoff(True);self.c.conversation_busy=lambda:True
  with self.assertRaises(ValueError):self.c.apply_handoff(r,True)

 def test_new_turn_invalidates_review_before_decode_worker(self):
  r=self.c.prepare_handoff(True)
  import io,wave
  class Hold:
   def __init__(self):
    import threading
    self.release=threading.Event()
   def __call__(self,pcm,cancel):self.release.wait(1);raise ValueError('fixture stop')
  hold=Hold();original=self.c.processor;self.c.processor=hold;buf=io.BytesIO()
  with wave.open(buf,'wb')as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0\0'*1600)
  worker=self.c.submit(self.token,buf.getvalue());self.assertIsNone(self.c.handoff);hold.release.set();worker.join(2);self.c.processor=original
  with self.assertRaises(ValueError):self.c.apply_handoff(r,True)
 def test_stop_generation_blocks_old_text(self):
  r=self.c.prepare_handoff(True);self.p.reset_session()
  with self.assertRaises(ValueError):self.c.apply_handoff(r,True)
