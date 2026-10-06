import unittest,threading
from unittest.mock import Mock
from jarvis.workspace_voice import WorkspaceVoice,VOICES,FreeSessionRouter
from jarvis import voice_assets
class BridgeTests(unittest.TestCase):
 def test_five_locked_voices(self):
  self.assertEqual(VOICES,{'JARVIS':'am_michael','NOVA':'af_heart','KAI':'am_liam','LYRA':'af_sky','DEX':'am_fenrir'})
 def test_no_start_on_construction(self):
  factory=Mock();c=WorkspaceVoice(factory);factory.assert_not_called();self.assertIsNone(c.runtime)
 def test_consent_gate(self):
  factory=Mock();c=WorkspaceVoice(factory)
  with self.assertRaises(ValueError):c.start()
  factory.assert_not_called()
 def test_cloud_gate(self):
  factory=Mock();c=WorkspaceVoice(factory)
  for args in [(True,True,'model',False)]:
   with self.assertRaises(ValueError):c.start(*args)
  factory.assert_not_called()
 def test_selected_voice_to_runtime(self):
  runtime=Mock();factory=Mock(return_value=runtime);c=WorkspaceVoice(factory);c.select('DEX');c.start(True).join(2)
  self.assertEqual(factory.call_args.args[0],'DEX');runtime.enable.assert_called_once_with(consent=True,cloud_consent=False)
 def test_pause_and_switch_release_runtime(self):
  runtime=Mock();c=WorkspaceVoice(Mock(return_value=runtime));c.start(True).join(2);c.select('NOVA');runtime.close.assert_called_once();self.assertIsNone(c.runtime)
 def test_pause_during_load_cannot_start(self):
  entered=threading.Event();release=threading.Event();runtime=Mock()
  def factory(*args):entered.set();release.wait(2);return runtime
  c=WorkspaceVoice(factory);worker=c.start(True);self.assertTrue(entered.wait(1));c.pause();release.set();worker.join(2);runtime.enable.assert_not_called();runtime.close.assert_called_once()
 def test_stale_captions_dropped(self):
  runtime=Mock();factory=Mock(return_value=runtime);c=WorkspaceVoice(factory);c.start(True).join(2);notify=factory.call_args.args[1];c.select('KAI');notify('transcript','old private text')
  items=[]
  while not c.events.empty():items.append(c.events.get())
  self.assertNotIn(('transcript','old private text'),items)
 def test_close_blocks_start(self):
  c=WorkspaceVoice(Mock());c.close()
  with self.assertRaises(RuntimeError):c.start(True)
 def test_factory_failure_reported(self):
  c=WorkspaceVoice(Mock(side_effect=RuntimeError('Missing models')));c.start(True).join(2);self.assertIn(('error','Missing models'),list(c.events.queue));self.assertFalse(c.busy)
 def test_router_session_plan(self):
  router=Mock();wrapper=FreeSessionRouter(router,True);wrapper.ask([{}],cloud_consent=True);router.ask.assert_called_once_with([{}],verified_free_providers=('groq',),cloud_consent=True)
 def test_assets_all_five(self):
  self.assertTrue(all(v+'.bin' in voice_assets.FILES for v in VOICES.values()))
 def test_download_requires_consent(self):
  with self.assertRaises(Exception):voice_assets.download('/nonexistent')
 def test_unknown_profile(self):
  with self.assertRaises(ValueError):WorkspaceVoice(Mock()).select('EXTRA')
 def test_reo_removed_from_default_profiles(self):
  factory=Mock();c=WorkspaceVoice(factory)
  with self.assertRaises(ValueError):c.select('REO')
  factory.assert_not_called()

 def test_queued_old_caption_cleared_on_select(self):
  c=WorkspaceVoice(Mock());c.notify('transcript','Old profile');c.select('LYRA');self.assertNotIn(('transcript','Old profile'),list(c.events.queue))
 def test_failure_does_not_leave_runtime_reference(self):
  runtime=Mock();runtime.enable.side_effect=RuntimeError('No mic');c=WorkspaceVoice(Mock(return_value=runtime));c.start(True).join(2)
  self.assertIsNone(c.runtime);runtime.close.assert_called_once()

 def test_cloud_auto_allowed_after_consent(self):
  runtime=Mock();factory=Mock(return_value=runtime);c=WorkspaceVoice(factory);c.start(True,True,'',True).join(2)
  self.assertEqual(factory.call_args.args[3],'');runtime.enable.assert_called_once_with(consent=True,cloud_consent=True)

 def test_shared_memory_survives_profile_switch_and_clears_close(self):
  c=WorkspaceVoice(Mock(return_value=Mock()));c.start(True).join(2);c.runtime.record_turn('a','b');c.select('NOVA');c.start(True).join(2)
  self.assertEqual(c.runtime.shared_context()[1]['content'],'[JARVIS] b');c.close();self.assertEqual(c.memory.messages(),[])
 def test_endpoint_preset_applied_before_mic_enable(self):
  runtime=Mock();c=WorkspaceVoice(Mock(return_value=runtime));c.endpoint_mode='fast'
  runtime.enable.side_effect=lambda **kw:self.assertEqual(runtime.mic.endpointer.silence_frames,15)
  c.start(True).join(2);runtime.enable.assert_called_once()
