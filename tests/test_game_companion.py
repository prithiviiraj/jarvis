import unittest,threading,io,json
from unittest.mock import Mock
from jarvis.game_companion import GameCompanion,LocalGameModel
TARGET={'id':123,'title':'Test Game'}
class Games(unittest.TestCase):
 def make(self):
  self.now=0;self.notes=[];self.source=Mock(return_value=b'jpeg');self.model=Mock();self.model.analyze.return_value={'observed':'A game scene','comment':'Try cover.','confidence':'medium'}
  c=GameCompanion(lambda *a:self.notes.append(a),source=self.source,clock=lambda:self.now);return c
 def test_review_and_off(self):
  c=self.make();self.assertIsNone(c.poll());self.source.assert_not_called()
  with self.assertRaises(ValueError):c.enable(TARGET,TARGET,self.model)
  with self.assertRaises(ValueError):c.enable(TARGET,{**TARGET,'title':'Other'},self.model,True)
  c.enable(TARGET,TARGET,self.model,True);self.model.verify.assert_called_once();c.poll().join();self.assertEqual(len(self.notes),1);self.assertEqual(c.results,[])
 def test_focus_audio_export_and_rate(self):
  c=self.make();c.enable(TARGET,TARGET,self.model,True,False,True);self.source.return_value=None;c.poll().join();self.model.analyze.assert_not_called();self.assertIsNone(c.poll());self.now=4;self.source.return_value=b'jpeg';c.poll().join();self.assertEqual(len(c.results),1);self.assertFalse(self.notes[0][1]['audio']);self.now=8;c.poll().join();self.assertEqual(len(self.notes),1)
 def test_stop_discards_pending(self):
  c=self.make();gate=threading.Event();entered=threading.Event()
  def analyze(f):entered.set();gate.wait(2);return {'observed':'Scene','comment':'Hey','confidence':'high'}
  self.model.analyze=analyze;c.enable(TARGET,TARGET,self.model,True);w=c.poll();entered.wait(1);c.stop();gate.set();w.join();self.assertEqual(self.notes,[]);self.assertFalse(c.enabled)
 def test_busy_and_invalid_frame(self):
  c=self.make();c.enable(TARGET,TARGET,self.model,True);self.assertIsNone(c.poll(True));self.source.return_value=b'x'*200001;c.poll().join();self.assertFalse(c.enabled);self.model.analyze.assert_not_called()
class LocalModel(unittest.TestCase):
 def test_verify_loaded_not_just_downloaded(self):
  class R(io.BytesIO):
   def __enter__(self):return self
   def __exit__(self,*a):self.close()
  model={'key':'tiny','capabilities':{'vision':True},'loaded_instances':[]};op=Mock();op.open.side_effect=lambda *a,**k:R(json.dumps({'models':[model]}).encode());m=LocalGameModel('tiny',op)
  with self.assertRaises(ValueError):m.verify()
  model['loaded_instances']=[{'id':'tiny'}];m.verify()
class MoreGuards(unittest.TestCase):
 def test_gate_released_and_busy_refused(self):
  gate=threading.Lock();m=LocalGameModel('tiny',gate=gate);m._analyze=Mock(side_effect=ValueError('bad'))
  with self.assertRaises(ValueError):m.analyze(b'jpeg')
  self.assertTrue(gate.acquire(False))
  with self.assertRaises(RuntimeError):m.analyze(b'jpeg')
  gate.release()
 def test_stop_button_interrupt_also_stops_capture(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice())
  try:b.game.enabled=True;b.execute({'command':'conversation-interrupt'});self.assertFalse(b.game.enabled)
  finally:b.close()
class CaptureRevocation(unittest.TestCase):
 def test_stop_during_capture_never_sends_model(self):
  gate=threading.Event();entered=threading.Event();model=Mock()
  def source(target):entered.set();gate.wait(2);return b'jpeg'
  c=GameCompanion(Mock(),source=source,clock=lambda:0);c.enable(TARGET,TARGET,model,True);w=c.poll();entered.wait(1);c.stop();gate.set();w.join();model.analyze.assert_not_called()
