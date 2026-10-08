import threading,unittest
from jarvis.phone_controller import PhoneController
from test_phone_session import audio
class Processor:
 def __call__(self,p,c):return {'text':'reply','wav':audio()}
 def close(self):pass
class Tests(unittest.TestCase):
 def paired(self,p=None,busy=lambda:False):
  c=PhoneController(p or Processor(),busy);r=c.request_pair(c.enable(True),'unverified phone');t=c.approve(r,True);return c,t
 def test_private_async_reply_single_use(self):
  c,t=self.paired();c.submit(t,audio()).join(2);self.assertTrue(c.snapshot()['reply_ready']);self.assertEqual(c.take_reply(t)['text'],'reply');self.assertIsNone(c.take_reply(t));self.assertNotIn(t,str(c.snapshot()));self.assertTrue(c.close())
 def test_desktop_busy_rejects_before_process(self):
  c,t=self.paired(busy=lambda:True)
  with self.assertRaises(ValueError):c.submit(t,audio())
  self.assertIsNone(c.worker);c.close()
 def test_stop_late_reply_and_restart_gate(self):
  started=threading.Event();release=threading.Event()
  class Slow(Processor):
   def __call__(self,p,c):started.set();release.wait(2);return super().__call__(p,c)
  c,t=self.paired(Slow());w=c.submit(t,audio());self.assertTrue(started.wait(2));c.stop()
  with self.assertRaises(ValueError):c.enable(True)
  release.set();w.join(2);self.assertFalse(c.snapshot()['reply_ready']);self.assertEqual(c.snapshot()['error'],'');c.close()
 def test_callback_secrets_not_status(self):
  class Bad(Processor):
   def __call__(self,p,c):raise RuntimeError('secret transcripts and credential')
  c,t=self.paired(Bad());c.submit(t,audio()).join(2);self.assertNotIn('credential',str(c.snapshot()));c.close()
