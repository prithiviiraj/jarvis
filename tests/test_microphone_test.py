import unittest,threading
import numpy as np
from jarvis.microphone_test import MicrophoneTest
class MicTests(unittest.TestCase):
 def test_no_implicit_capture(self):
  m=MicrophoneTest(factory=lambda **k:self.fail('opened without consent'))
  self.assertIsNone(m.stream)
  with self.assertRaises(ValueError):m.start()
 def test_actual_callback_stop_closes(self):
  done=threading.Event();calls=[]
  class Stream:
   def __init__(self,**kw):self.cb=kw['callback']
   def start(self):self.cb(np.ones((512,1),dtype='float32')*.05,512,None,None);done.set()
   def abort(self):calls.append('abort')
   def close(self):calls.append('close')
  m=MicrophoneTest(Stream);m.start(True);self.assertTrue(done.wait(1));self.assertEqual(m.snapshot()['frames'],512);self.assertGreater(m.snapshot()['peak'],.04);m.stop();m.worker.join(1);self.assertIn('close',calls);self.assertFalse(m.snapshot()['busy']);self.assertEqual(m.snapshot()['level'],0.)
 def test_permission_error_clears_capture(self):
  def failed(**kw):raise RuntimeError('device blocked')
  m=MicrophoneTest(failed);m.start(True);m.worker.join(1);self.assertIsNone(m.stream);self.assertIn('unavailable',m.snapshot()['status'])

 def test_real_timeout_callback_flow_with_clock_wait_mocked(self):
  calls=[]
  class Stream:
   def __init__(self,**kw):self.cb=kw['callback']
   def start(self):self.cb(np.ones((512,1),dtype='float32')*.1,512,None,None)
   def abort(self):calls.append('abort')
   def close(self):calls.append('close')
  m=MicrophoneTest(Stream,wait=lambda event:False);m.start(True);m.worker.join(1);self.assertEqual(m.snapshot()['status'],'Working capture and sound detected');self.assertIsNone(m.stream);self.assertEqual(calls,['abort','close'])
 def test_invalid_samples_fail_closed(self):
  class Stream:
   def __init__(self,**kw):self.cb=kw['callback']
   def start(self):self.cb(np.full((512,1),float('nan'),dtype='float32'),512,None,None)
   def abort(self):pass
   def close(self):pass
  m=MicrophoneTest(Stream,wait=lambda event:False);m.start(True);m.worker.join(1);self.assertEqual(m.snapshot()['status'],'Test failed');self.assertEqual(m.snapshot()['frames'],0)
