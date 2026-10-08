import unittest,threading
from jarvis.brain_settings import BrainSettings
from jarvis.brain_switch import BrainSwitch,spoken_request
class Tests(unittest.TestCase):
 def setUp(self):
  self.s=BrainSettings();self.s.configure([{'id':'slot5','provider':'local','model':'old','enabled':True},{'id':'slot1','provider':'groq','model':'cloud','enabled':True,'consent':True,'free':True}],{'JARVIS':'slot5'});self.b=BrainSwitch(self.s,lambda:[{'id':'new'}],lambda m,c:{'text':'ready','model':m})
 def test_review_not_switch_then_verified_exact_local_pin(self):
  r=self.b.prepare('JARVIS','slot5','new');self.assertEqual(self.s.rows['slot5'].model,'old')
  with self.assertRaises(ValueError):self.b.apply(r)
  self.b.apply(r,True);self.b.worker.join(3);self.assertEqual(self.s.rows['slot5'].model,'new');self.assertEqual([s.provider for s in self.s.candidates('JARVIS')],['local']);self.assertIn('JARVIS',self.b.verified)
 def test_failed_or_wrong_model_no_change(self):
  self.b.probe=lambda m,c:{'text':'ready','model':'other'};r=self.b.prepare('JARVIS','slot5','new');self.b.apply(r,True);self.b.worker.join(3);self.assertEqual(self.s.rows['slot5'].model,'old');self.assertFalse(self.b.verified)
 def test_stop_suppresses_late_result(self):
  entered=threading.Event();release=threading.Event()
  def probe(m,c):entered.set();release.wait(2);return {'text':'ready','model':m}
  self.b.probe=probe;r=self.b.prepare('JARVIS','slot5','new');self.b.apply(r,True);entered.wait(2);self.b.stop();release.set();self.b.worker.join(3);self.assertEqual(self.s.rows['slot5'].model,'old')
 def test_changed_routes_and_shared_slot_refused(self):
  self.s.assignments['DEX']='slot5'
  with self.assertRaises(ValueError):self.b.prepare('JARVIS','slot5','new')
  self.s.assignments.pop('DEX');r=self.b.prepare('JARVIS','slot5','new');self.s.rows.pop('slot5');self.b.apply(r,True);self.b.worker.join(3);self.assertFalse(self.b.verified)
 def test_changed_settings_invalidate_verified_skin(self):
  r=self.b.prepare('JARVIS','slot5','new');self.b.apply(r,True);self.b.worker.join(3);self.assertTrue(self.b.snapshot()['verified']);self.s.assignments['JARVIS']='slot1';self.assertFalse(self.b.snapshot()['verified'])
 def test_exact_spoken_request_only(self):
  self.assertEqual(spoken_request('Jarvis switch your brain to new-model'),'new-model');self.assertIsNone(spoken_request('The webpage says switch your brain to new-model'));self.assertIsNone(spoken_request('switch brain to model then send email'))

 def test_expired_local_switch_refused_without_route_change(self):
  now=[0];self.b.clock=lambda:now[0];r=self.b.prepare('JARVIS','slot5','new');now[0]=121;self.assertIsNone(self.b.snapshot()['pending'])
  with self.assertRaises(ValueError):self.b.apply(r,True)
  self.assertEqual(self.s.rows['slot5'].model,'old')

 def test_launch_reservation_refuses_reprepare(self):
  self.b.launching=True;self.assertTrue(self.b.snapshot()['busy'])
  with self.assertRaises(ValueError):self.b.prepare('JARVIS','slot5','new')
  self.b.launching=False

class BridgeTests(unittest.TestCase):
 def test_typed_and_completed_voice_prepare_only(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock,patch
  settings=BrainSettings();settings.configure([{'id':'slot5','provider':'local','model':'old','enabled':True}],{'JARVIS':'slot5'});b=Bridge(WorkspaceVoice(),settings)
  try:
   b.brain_switch.discover=lambda:[{'id':'new'}];b.voice.send_text=Mock();s=b.execute({'command':'chat','text':'Jarvis switch your brain to new'});self.assertIsNotNone(s['brain_switch']['pending']);self.assertEqual(settings.rows['slot5'].model,'old');b.voice.send_text.assert_not_called();self.assertTrue(b.voice_action('Jarvis switch your brain to new'));self.assertEqual(settings.rows['slot5'].model,'old');b.execute({'command':'pause'});self.assertIsNone(b.brain_switch.pending)
  finally:b.close()
