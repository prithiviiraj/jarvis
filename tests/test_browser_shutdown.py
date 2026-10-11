import unittest,threading,time,queue
from jarvis.browser_control import BrowserSession
class BrowserShutdownTests(unittest.TestCase):
 def session(self,work):
  s=BrowserSession.__new__(BrowserSession);s.cancel=threading.Event();s.lock=threading.RLock();s.state={};s.thread=threading.Thread(target=lambda:work(s),daemon=True);s.thread.start();return s
 def test_close_waits_for_current_operation_and_cleanup(self):
  done=[]
  def work(s):
   s.cancel.wait(1);time.sleep(.03);done.append('closed')
  s=self.session(work);self.assertTrue(s.wait_closed(.5));self.assertEqual(done,['closed']);self.assertFalse(s.thread.is_alive())
 def test_timeout_is_reported_not_ready(self):
  finish=threading.Event();s=self.session(lambda s:finish.wait(1))
  try:
   with self.assertRaises(TimeoutError):s.wait_closed(.01)
   self.assertTrue(s.cancel.is_set())
  finally:finish.set();s.thread.join(1)
 def test_real_worker_has_daemon_exit_fallback(self):
  s=BrowserSession('/tmp/shutdown-no-browser-fixture');self.assertTrue(s.thread.daemon);self.assertTrue(s.wait_closed(1))
