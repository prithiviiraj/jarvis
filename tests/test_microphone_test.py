import unittest,threading,time
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

 def test_stop_during_open_never_starts_capture(self):
  opening=threading.Event();resume=threading.Event();calls=[]
  class Stream:
   def __init__(self,**kw):opening.set();resume.wait(1)
   def start(self):calls.append('start')
   def abort(self):calls.append('abort')
   def close(self):calls.append('close')
  m=MicrophoneTest(Stream);m.start(True);self.assertTrue(opening.wait(1));m.stop();resume.set();m.worker.join(1)
  self.assertEqual(calls,['abort','close']);self.assertEqual(m.snapshot()['status'],'Stopped')
 def test_callback_does_not_wait_on_ui_lock(self):
  calls=[];durations=[]
  class Stream:
   def __init__(self,**kw):self.cb=kw['callback']
   def start(self):
    ready=threading.Event();done=threading.Event()
    def held():
     with m.lock:ready.set();done.wait(1)
    worker=threading.Thread(target=held);worker.start();ready.wait(1);started=time.monotonic()
    self.cb(np.ones((512,1),dtype='float32'),512,None,None);calls.append('returned');durations.append(time.monotonic()-started);done.set();worker.join(1)
   def abort(self):pass
   def close(self):pass
  m=MicrophoneTest(Stream,wait=lambda e:False);m.start(True);m.worker.join(1)
  self.assertEqual(calls,['returned']);self.assertLess(durations[0],.1);self.assertEqual(m.snapshot()['frames'],0)
 def test_malformed_samples_close_without_callback_exception(self):
  calls=[]
  class Stream:
   def __init__(self,**kw):self.cb=kw['callback']
   def start(self):self.cb(None,512,None,None)
   def abort(self):calls.append('abort')
   def close(self):calls.append('close')
  m=MicrophoneTest(Stream,wait=lambda e:False);m.start(True);m.worker.join(1)
  self.assertEqual(m.snapshot()['status'],'Test failed');self.assertEqual(calls,['abort','close'])
