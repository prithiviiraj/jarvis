import unittest,numpy as np
from jarvis.hold_microphone import HoldMic
class Hold(unittest.TestCase):
 def setUp(self):
  self.calls=[];self.audio=[];self.states=[]
  outer=self
  class Stream:
   def __init__(self,**kw):self.cb=kw['callback'];outer.calls.append(self);self.closed=False
   def start(self):pass
   def abort(self):pass
   def close(self):self.closed=True
  self.mic=HoldMic(None,self.audio.append,lambda *a:self.states.append(a),Stream)
 def feed(self,n=6):
  for _ in range(n):self.calls[-1].cb(np.ones((512,1),dtype='float32')*.1,512,None,None)
 def test_no_device_before_explicit_hold(self):
  self.mic.start(True);self.mic.resume();self.assertEqual(self.calls,[])
  with self.assertRaises(ValueError):HoldMic(None,lambda a:None).hold()
 def test_release_closes_device_then_submits_audio_once(self):
  self.mic.start(True);self.mic.hold();self.feed();self.assertTrue(self.mic.release());self.assertTrue(self.calls[0].closed);self.assertEqual(len(self.audio),1);self.assertEqual(len(self.audio[0]),3072);self.assertFalse(self.mic.release());self.mic.resume();self.assertEqual(len(self.calls),1)
 def test_stop_discards_late_device_callback_and_audio(self):
  self.mic.start(True);self.mic.hold();self.feed();self.mic.close();self.feed();self.assertFalse(self.mic.release());self.assertEqual(self.audio,[]);self.assertTrue(self.calls[0].closed)
 def test_overflow_discards_instead_of_sending_truncated_audio(self):
  self.mic.max_frames=6;self.mic.start(True);self.mic.hold();self.feed(7);self.assertFalse(self.mic.release());self.assertEqual(self.audio,[]);self.assertTrue(self.calls[0].closed)
 def test_short_hold_discarded(self):
  self.mic.start(True);self.mic.hold();self.feed(2);self.assertFalse(self.mic.release());self.assertEqual(self.audio,[])
 def test_suspended_turn_does_not_open_or_keep_input(self):
  self.mic.start(True);self.mic.hold();self.feed();self.mic.suspend();self.mic.resume();self.assertTrue(self.calls[0].closed);self.assertEqual(self.audio,[]);self.assertIsNone(self.mic.stream)
 def test_actual_voice_turn_uses_existing_runtime_with_only_transports_mocked(self):
  import threading
  from unittest.mock import Mock
  from jarvis.runtime import VoiceRuntime
  router=Mock();router.ask.return_value={'text':'Ready','provider':'local','model':'fixture'};stt=Mock();stt.transcribe.return_value='Hello';speaker=Mock(generation=0);speaker.speak.return_value=None;runtime=VoiceRuntime(Mock(),stt,router,speaker);runtime.mic=self.mic;self.mic.on_utterance=runtime.on_utterance;runtime.streaming=False;runtime.enable(True);self.assertEqual(self.calls,[]);self.mic.hold();self.feed();self.mic.release()
  deadline=__import__('time').monotonic()+2
  while runtime.busy and __import__('time').monotonic()<deadline:__import__('time').sleep(.01)
  stt.transcribe.assert_called_once();router.ask.assert_called_once();self.assertEqual(len(self.calls),1);self.assertTrue(self.calls[0].closed);self.assertIsNone(self.mic.stream);runtime.close()

 def test_workspace_real_start_converts_to_hold_without_opening_device(self):
  from unittest.mock import Mock
  from jarvis.workspace_voice import WorkspaceVoice
  from jarvis.runtime import VoiceRuntime
  r=VoiceRuntime(Mock(),Mock(),Mock(),Mock(generation=0));v=WorkspaceVoice(factory=lambda *a:r)
  try:
   worker=v.start(True,hold_to_talk=True);worker.join(2);self.assertIs(v.runtime,r);self.assertIsInstance(r.mic,HoldMic);self.assertIsNone(r.mic.stream);self.assertTrue(r.enabled);self.assertFalse(r.mic.accepting)
  finally:v.close()

 def test_status_failure_discards_and_closes_device_without_release(self):
  import time
  self.mic.start(True);self.mic.hold();self.calls[0].cb(np.ones((512,1),dtype='float32'),512,None,'overflow')
  end=time.monotonic()+1
  while not self.calls[0].closed and time.monotonic()<end:time.sleep(.01)
  self.assertTrue(self.calls[0].closed);self.assertEqual(self.audio,[]);self.assertFalse(self.mic.release())

 def test_old_failed_capture_cannot_close_new_hold(self):
  self.mic.start(True);self.mic.hold();old=self.mic.generation;self.mic.release();self.mic.hold();new=self.calls[-1];self.mic._fail_close(old);self.assertIs(self.mic.stream,new);self.assertFalse(new.closed);self.mic.close()

 def test_device_callback_never_waits_on_control_lock_during_close(self):
  import threading
  self.mic.start(True);self.mic.hold();finished=threading.Event()
  with self.mic.lock:
   worker=threading.Thread(target=lambda:(self.calls[0].cb(np.ones((512,1),dtype='float32'),512,None,None),finished.set()));worker.start();self.assertTrue(finished.wait(.5),'Callback must drop frame rather than wait for control close lock')
  worker.join();self.assertEqual(self.mic.frames,[]);self.mic.close()

 def test_bad_frame_shape_count_and_nan_close_immediately(self):
  import time
  for data,count in ((np.ones((512,1)),256),(None,512),(np.ones((512,2)),512),(np.full((512,1),np.nan),512)):
   with self.subTest(count=count,data=str(type(data))):
    self.mic.start(True);self.mic.hold();stream=self.calls[-1];stream.cb(data,count,None,None)
    end=time.monotonic()+1
    while not stream.closed and time.monotonic()<end:time.sleep(.001)
    self.assertTrue(stream.closed);self.assertFalse(self.mic.release());self.assertEqual(self.audio,[])

 def test_selected_language_reaches_real_runtime_without_capture(self):
  from unittest.mock import Mock
  from jarvis.workspace_voice import WorkspaceVoice
  from jarvis.runtime import VoiceRuntime
  for language,expected in (('auto',None),('en','en'),('ta','ta')):
   r=VoiceRuntime(Mock(),Mock(),Mock(),Mock(generation=0));v=WorkspaceVoice(factory=lambda *a:r);v.input_language=language
   try:
    v.start(True,hold_to_talk=True).join(1);self.assertEqual(r.stt.language,expected);self.assertIsNone(r.mic.stream);self.assertTrue(r.enabled)
   finally:v.close()
