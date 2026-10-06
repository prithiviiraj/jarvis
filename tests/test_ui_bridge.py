import unittest
from unittest.mock import Mock
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class UiBridgeTests(unittest.TestCase):
 def setUp(self):self.b=Bridge(WorkspaceVoice())
 def tearDown(self):self.b.close()
 def test_default_off(self):
  s=self.b.execute({'command':'status'});self.assertEqual(s['awareness']['camera'],'off');self.assertFalse(s['judgment']['enabled'])
 def test_unknown_refused(self):
  for cmd in ['shell','read-file','cloud-chat','open-url']:
   with self.assertRaises(ValueError):self.b.execute({'command':cmd})
 def test_camera_consent(self):
  with self.assertRaises(ValueError):self.b.execute({'command':'camera-on'})
 def test_judge_consent(self):
  with self.assertRaises(ValueError):self.b.execute({'command':'judgment','enabled':True})
 def test_no_cloud_command(self):
  with self.assertRaises(ValueError):self.b.execute({'command':'judgment','enabled':True,'context_consent':True,'cloud':True})
 def test_pause_clears(self):
  self.b.context.set_apps(True);self.b.messages=[{'name':'You','text':'private'}];s=self.b.execute({'command':'pause'});self.assertEqual(s['messages'],[{'name':'You','text':'private'}]);self.assertFalse(s['awareness']['app_monitor'])
 def test_select(self):self.assertEqual(self.b.execute({'command':'select','name':'DEX'})['selected'],'DEX')
 def test_bad_apps(self):
  with self.assertRaises(ValueError):self.b.execute({'command':'apps','enabled':'yes'})

 def test_judgment_opt_in_and_audio_revoke(self):
  state=self.b.execute({'command':'judgment','enabled':True,'context_consent':True,'audio':True});self.assertTrue(state['judgment']['enabled']);self.assertTrue(state['judgment']['audio'])
  state=self.b.execute({'command':'judgment','enabled':True,'context_consent':True,'audio':False});self.assertFalse(state['judgment']['audio'])
 def test_camera_explicit_opt_in(self):
  self.b.camera.start=Mock();self.b.execute({'command':'camera-on','consent':True});self.b.camera.start.assert_called_once_with(True)
 def test_apps_title_consent_and_clear(self):
  self.b.execute({'command':'apps','enabled':True,'titles':True});self.assertTrue(self.b.titles)
  self.b.context.app_event({'process':'app.exe','title':'private title'});self.b.execute({'command':'apps','enabled':True,'titles':False});self.assertFalse(self.b.titles);self.assertIsNone(self.b.context.app)
 def test_voice_consent_and_local(self):
  self.b.voice.start=Mock()
  with self.assertRaises(ValueError):self.b.execute({'command':'voice-on'})
  self.b.execute({'command':'voice-on','consent':True});self.b.voice.start.assert_called_once_with(consent=True,cloud=False,barge_in=False)
 def test_voice_on_barge_in_opt_in(self):
  self.b.voice.start=Mock();self.b.execute({'command':'voice-on','consent':True,'barge_in':True});self.b.voice.start.assert_called_once_with(consent=True,cloud=False,barge_in=True);self.assertTrue(self.b.execute({'command':'status'})['barge_in'])
 def test_pause_disables_all(self):
  self.b.execute({'command':'judgment','enabled':True,'context_consent':True,'audio':True});self.b.execute({'command':'apps','enabled':True,'titles':True})
  state=self.b.execute({'command':'pause'});self.assertFalse(state['judgment']['enabled']);self.assertFalse(state['judgment']['audio']);self.assertFalse(state['awareness']['app_monitor']);self.assertFalse(self.b.titles)
 def test_no_destinations(self):
  for k in ['cloud','cloud_consent','provider','api_key','model','path','url']:
   with self.assertRaises(ValueError):self.b.execute({'command':'status',k:'x'})

 def test_error_survives_idle_poll(self):
  self.b.voice.notify('error','LM Studio timeout');self.b.voice.notify('state','off')
  self.assertEqual(self.b.execute({'command':'status'})['error'],'LM Studio timeout')
  self.assertEqual(self.b.execute({'command':'status'})['error'],'LM Studio timeout')
  self.assertEqual(self.b.execute({'command':'pause'})['error'],'')

 def test_setup_does_not_enable_audio(self):
  self.b.setup.start=Mock();state=self.b.execute({'command':'voice-setup','consent':True,'reviewed_engine':'kokoro'});self.b.setup.start.assert_called_once_with(consent=True,engine='kokoro');self.assertFalse(state['voice_active'])
 def test_voice_failure_visible(self):
  self.b.voice.notify('error','Speech assets missing');self.b.voice.notify('state','off');self.assertEqual(self.b.execute({'command':'status'})['error'],'Speech assets missing')

 def test_live_expression_busy_and_idle(self):
  self.assertEqual(self.b.execute({'command':'status'})['expression']['state'],'idle')
  self.b.voice.busy=True;self.b.voice.notify('state','thinking')
  self.assertEqual(self.b.execute({'command':'status'})['expression']['state'],'thinking')
  self.b.voice.busy=False
  self.assertEqual(self.b.execute({'command':'status'})['expression']['state'],'idle')

 def test_session_metrics_filter_clear_no_stale_pause(self):
  self.b.voice.notify('metrics',{'stt_s':.2,'first_output_write_s':1.1,'private':'text','turn_s':-1,'first_text_s':True})
  state=self.b.execute({'command':'status'});self.assertEqual(state['voice_metrics'],{'stt_s':.2,'first_output_write_s':1.1})
  self.b.voice.notify('metrics',{'turn_s':2});self.assertEqual(self.b.execute({'command':'pause'})['voice_metrics'],{})
  self.assertEqual(self.b.execute({'command':'status'})['voice_metrics'],{})
 def test_endpoint_session_preset_stopped_only(self):
  self.assertEqual(self.b.execute({'command':'status'})['endpoint_mode'],'balanced')
  self.assertEqual(self.b.execute({'command':'voice-endpoint','mode':'fast'})['endpoint_mode'],'fast')
  with self.assertRaises(ValueError):self.b.execute({'command':'voice-endpoint','mode':'arbitrary'})
  self.b.voice.busy=True
  self.assertEqual(self.b.execute({'command':'voice-endpoint','mode':'balanced'})['endpoint_mode'],'balanced');self.assertFalse(self.b.voice.busy)
  self.b.voice.busy=False;self.b.voice.runtime=Mock()
  self.assertEqual(self.b.execute({'command':'voice-endpoint','mode':'balanced'})['endpoint_mode'],'balanced');self.assertFalse(self.b.voice.busy)
  self.b.voice.runtime=None
  from pathlib import Path
  s=(Path(__file__).resolve().parents[1]/'modern-ui/src-tauri/src/main.rs').read_text(encoding='utf-8');self.assertIn('"voice-endpoint"',s.split('.contains(&command)')[0])

 def test_voice_setup_exact_engine_review(self):
  self.b.setup.start=Mock()
  for reviewed in (None,'kitten'):
   with self.assertRaises(ValueError):self.b.execute({'command':'voice-setup','consent':True,'reviewed_engine':reviewed})
  self.b.setup.start.assert_not_called()
  self.b.voice.tts_engine='kitten';self.b.execute({'command':'voice-setup','consent':True,'reviewed_engine':'kitten'});self.b.setup.start.assert_called_once_with(consent=True,engine='kitten')
 def test_setup_busy_blocks_engine_switch(self):
  self.b.setup.busy=True
  with self.assertRaises(ValueError):self.b.execute({'command':'voice-engine','engine':'kitten'})
  self.b.setup.busy=False

 def test_engine_change_invalidates_ready_without_start(self):
  self.b.setup.ready=True;self.b.setup.checked=True;self.b.setup.start=Mock();self.b.voice.start=Mock()
  state=self.b.execute({'command':'voice-engine','engine':'kitten'});self.assertFalse(state['voice_setup']['ready']);self.assertFalse(state['voice_setup']['checked']);self.assertEqual(state['voice_setup']['engine'],'kitten');self.b.setup.start.assert_not_called();self.b.voice.start.assert_not_called()

class ScopedInterruption(unittest.TestCase):
 def test_change_keeps_sensor_and_tool_permissions(self):
  b=Bridge(WorkspaceVoice())
  try:
   b.context.set_apps(True);b.browser_enabled=True;b.laya_enabled=True;b.voice.runtime=Mock();b.voice.busy=True
   state=b.execute({'command':'voice-endpoint','mode':'fast'})
   self.assertEqual(state['endpoint_mode'],'fast');self.assertFalse(state['voice_active']);self.assertTrue(state['awareness']['app_monitor']);self.assertTrue(state['browser']['enabled']);self.assertTrue(state['laya']['enabled'])
  finally:b.close()
 def test_typed_message_supersedes_mic_without_pause_all(self):
  b=Bridge(WorkspaceVoice());b.context.set_apps(True);runtime=Mock();b.voice.runtime=runtime;b.voice.send_text=Mock()
  try:
   s=b.execute({'command':'chat','text':'hello'});runtime.close.assert_called_once();b.voice.send_text.assert_called_once_with('hello',auto_pick=True);self.assertTrue(s['awareness']['app_monitor'])
  finally:b.close()

class ResponseSource(unittest.TestCase):
 def test_all_profiles_keep_true_route(self):
  b=Bridge(WorkspaceVoice())
  try:
   for name in ('JARVIS','NOVA','KAI','LYRA','DEX'):
    b.voice.notify('answer',{'text':'Cloud actual reply','profile':name,'provider':'nim','model':'actual-model','cloud':True})
   s=b.execute({'command':'status'});self.assertTrue(all(r['provider']=='nim'and r['model']=='actual-model'and r['cloud']is True for r in s['messages']))
  finally:b.close()

class NativeCommandParity(unittest.TestCase):
 def test_scoped_interrupt_passes_native_allowlist(self):
  from pathlib import Path
  source=(Path(__file__).resolve().parents[1]/'modern-ui/src-tauri/src/main.rs').read_text()
  self.assertIn('"conversation-interrupt"',source)
class SemanticBridgeTests(unittest.TestCase):
 def setUp(self):self.b=Bridge(WorkspaceVoice())
 def tearDown(self):self.b.close()
 def test_setup_explicit_only(self):
  self.b.search_setup.start=Mock();self.b.execute({'command':'status'});self.b.search_setup.start.assert_not_called();self.b.execute({'command':'embedding-check'});self.b.search_setup.start.assert_called_once_with(consent=False,check=True)
 def test_search_exact_review(self):
  import tempfile,pathlib
  with tempfile.TemporaryDirectory()as t:
   root=pathlib.Path(t);(root/'.obsidian').mkdir();self.b.execute({'command':'vault-connect','vault_folder':t,'consent':True});self.b.semantic_search.start=Mock()
   with self.assertRaises(ValueError):self.b.execute({'command':'vault-semantic','query':'dinner','consent':True,'reviewed':{'vault_folder':t,'query':'different'}})
   self.b.semantic_search.start.assert_not_called();self.b.execute({'command':'vault-semantic','query':'dinner','consent':True,'reviewed':{'vault_folder':str(root.resolve()),'query':'dinner'}});self.b.semantic_search.start.assert_called_once()
 def test_stop_unloads_and_clears(self):
  self.b.search_setup.model=object();self.b.semantic_search.results=[{'name':'old'}];s=self.b.execute({'command':'embedding-stop'});self.assertFalse(s['embedding_setup']['ready']);self.assertEqual(s['semantic_search']['results'],[])

class LaptopTeamTrigger(unittest.TestCase):
 def test_exact_typed_phrase_dispatches_dialogue_not_solo(self):
  b=Bridge(WorkspaceVoice());b.voice.dialogue=Mock();b.voice.send_text=Mock()
  text='Can you speak with NOVA together? Speak about why politics is important?'
  try:
   state=b.execute({'command':'chat','text':text})
   b.voice.dialogue.assert_called_once_with(text,b.brains,False);b.voice.send_text.assert_not_called()
   self.assertFalse(state['idle']['enabled']);self.assertFalse(state['voice_active'])
  finally:b.close()

class GameSpeechPriority(unittest.TestCase):
 def test_user_voice_stops_current_game_output_first(self):
  b=Bridge(WorkspaceVoice());order=[]
  try:
   b.game_speech.stop=Mock(side_effect=lambda:order.append('game-stop'))
   b.voice.start=Mock(side_effect=lambda **kw:order.append('voice-start'))
   b.execute({'command':'voice-on','consent':True})
   self.assertEqual(order,['game-stop','voice-start'])
  finally:b.close()
 def test_user_chat_stops_game_before_text_dispatch(self):
  b=Bridge(WorkspaceVoice());order=[]
  try:
   b.game_speech.stop=Mock(side_effect=lambda:order.append('game-stop'))
   b.voice.send_text=Mock(side_effect=lambda *a,**kw:order.append('text-start'))
   b.execute({'command':'chat','text':'hello'})
   self.assertEqual(order,['game-stop','text-start'])
  finally:b.close()

class GameEngineReset(unittest.TestCase):
 def test_engine_change_discards_cached_game_speaker(self):
  b=Bridge(WorkspaceVoice())
  try:
   speaker=Mock(generation=1);b.game_speech.speaker=speaker
   b.execute({'command':'voice-engine','engine':'kitten'})
   speaker.stop.assert_called();speaker.close.assert_called_once()
   self.assertIsNone(b.game_speech.speaker);self.assertEqual(b.voice.tts_engine,'kitten')
  finally:b.close()
