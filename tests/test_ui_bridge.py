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
  self.b.voice.notify('error','Speech assets missing');self.b.voice.notify('state','off');self.assertEqual(self.b.execute({'command':'status'})['error'],'Local speech assets are missing. Open Voices and check the installed files.')

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
  self.assertEqual(self.b.execute({'command':'status'})['endpoint_mode'],'fast')
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
  self.b.voice.tts_engine='kitten'
  with self.assertRaises(ValueError):self.b.execute({'command':'voice-setup','consent':True,'reviewed_engine':'kitten'})
  self.b.setup.start.assert_not_called()
 def test_setup_busy_blocks_engine_switch(self):
  self.b.setup.busy=True
  with self.assertRaises(ValueError):self.b.execute({'command':'voice-engine','engine':'kokoro'})
  self.b.setup.busy=False

 def test_engine_change_invalidates_ready_without_start(self):
  self.b.setup.ready=True;self.b.setup.checked=True;self.b.setup.start=Mock();self.b.voice.start=Mock()
  state=self.b.execute({'command':'voice-engine','engine':'kokoro'});self.assertFalse(state['voice_setup']['ready']);self.assertFalse(state['voice_setup']['checked']);self.assertEqual(state['voice_setup']['engine'],'kokoro');self.b.setup.start.assert_not_called();self.b.voice.start.assert_not_called()

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
   for name in ('JARVIS','LYRA','DEX'):
    b.voice.notify('answer',{'text':'Cloud actual reply','profile':name,'provider':'nim','model':'actual-model','cloud':True})
   s=b.execute({'command':'status'});self.assertTrue(all(r['provider']=='nim'and r['model']=='actual-model'and r['cloud']is True for r in s['messages']))
  finally:b.close()

class NativeCommandParity(unittest.TestCase):
 def test_scoped_interrupt_passes_native_allowlist(self):
  from pathlib import Path
  source=(Path(__file__).resolve().parents[1]/'modern-ui/src-tauri/src/main.rs').read_text(encoding='utf-8')
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
  text='Can you speak with DEX together? Speak about why politics is important?'
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
   b.execute({'command':'voice-engine','engine':'kokoro'})
   speaker.stop.assert_called();speaker.close.assert_called_once()
   self.assertIsNone(b.game_speech.speaker);self.assertEqual(b.voice.tts_engine,'kokoro')
  finally:b.close()

class ManagedModelBridgeTests(unittest.TestCase):
 def test_real_bridge_inspect_and_review_no_download(self):
  from unittest.mock import patch
  b=Bridge(WorkspaceVoice())
  with patch.object(b.model_manager,'scan',return_value={'ram_gb':16,'vram_gb':6,'dedicated':True,'free_disk_gb':100}):
   state=b.execute({'command':'models-inspect'});self.assertEqual(state['managed_models']['recommendations']['pick'],'qwen3-vl-4b')
   state=b.execute({'command':'models-prepare','model_id':'qwen3-vl-4b'});self.assertEqual(state['managed_models']['pending']['id'],'qwen3-vl-4b')
   with self.assertRaises(ValueError):b.execute({'command':'models-download','reviewed':state['managed_models']['pending']})
   self.assertIsNone(b.model_manager.worker);b.execute({'command':'models-stop'});self.assertIsNone(b.model_manager.pending)
  b.stop()
 def test_microphone_device_callback_and_pause_cleanup(self):
  from jarvis.microphone_test import MicrophoneTest
  import numpy as np,threading
  b=Bridge(WorkspaceVoice());opened=threading.Event();closed=[]
  class Stream:
   def __init__(self,**kw):self.cb=kw['callback']
   def start(self):
    def emit():
     import time
     while not opened.is_set():
      self.cb(np.ones((512,1),dtype='float32')*.1,512,None,None)
      if b.microphone_test.frames:opened.set()
      else:time.sleep(.001)
    threading.Thread(target=emit,daemon=True).start()
   def abort(self):pass
   def close(self):closed.append(True)
  b.microphone_test=MicrophoneTest(Stream)
  with self.assertRaises(ValueError):b.execute({'command':'microphone-test-start'})
  b.execute({'command':'microphone-test-start','consent':True});self.assertTrue(opened.wait(1));self.assertEqual(b.microphone_test.snapshot()['frames'],512)
  b.execute({'command':'pause'});b.microphone_test.worker.join(1);self.assertTrue(closed);self.assertIsNone(b.microphone_test.stream);self.assertFalse(b.microphone_test.snapshot()['busy'])

class ManagedSessionBridgeTests(unittest.TestCase):
 def test_actual_review_requires_exact_confirm_and_close_stops_runtime(self):
  b=Bridge(WorkspaceVoice())
  try:
   state=b.execute({'command':'model-session-prepare','model_id':'qwen3-vl-4b'});review=state['managed_session']['pending'];self.assertEqual(review['id'],'qwen3-vl-4b');self.assertIsNone(b.managed_session.worker)
   with self.assertRaises(ValueError):b.execute({'command':'model-session-start','reviewed':review})
   b.execute({'command':'model-session-stop'});self.assertIsNone(b.managed_session.pending);self.assertFalse(b.managed_session.active)
  finally:b.close()

class HoldShortcutBridgeTests(unittest.TestCase):
 def test_opt_in_requires_speech_verification_and_consent(self):
  b=Bridge(WorkspaceVoice())
  try:
   with self.assertRaises(ValueError):b.execute({'command':'shortcuts-enable'})
   with self.assertRaises(ValueError):b.execute({'command':'shortcuts-enable','consent':True})
   self.assertFalse(b.shortcut_monitor.enabled);self.assertIsNone(b.voice.runtime)
  finally:b.close()
 def test_real_bridge_event_callback_captures_only_while_held(self):
  import numpy as np
  from jarvis.runtime import VoiceRuntime
  from jarvis.hold_microphone import HoldMic
  b=Bridge(WorkspaceVoice());audio=[];devices=[]
  class Stream:
   def __init__(self,**kw):self.cb=kw['callback'];devices.append(self);self.closed=False
   def start(self):pass
   def abort(self):pass
   def close(self):self.closed=True
  runtime=VoiceRuntime(Mock(),Mock(),Mock(),Mock(generation=0));runtime.mic=HoldMic(None,audio.append,stream_factory=Stream);runtime.enable(True);b.voice.runtime=runtime;b.shortcut_monitor.enabled=True
  try:
   b.execute({'command':'status'});self.assertEqual(devices,[]);b.shortcut_events.put('talk-start');b.execute({'command':'status'});self.assertEqual(len(devices),1)
   for _ in range(6):devices[0].cb(np.ones((512,1),dtype='float32'),512,None,None)
   b.shortcut_events.put('talk-stop');b.execute({'command':'status'});self.assertTrue(devices[0].closed);self.assertEqual(len(audio),1);b.execute({'command':'shortcuts-stop'});self.assertIsNone(b.voice.runtime);self.assertFalse(b.shortcut_monitor.enabled)
  finally:b.close()

class FailedHoldSetupCleanup(unittest.TestCase):
 def test_failed_runtime_setup_stops_global_monitor(self):
  b=Bridge(WorkspaceVoice())
  try:
   b.shortcut_monitor.enabled=True;b.voice.busy=False;b.voice.runtime=None;b.execute({'command':'status'});self.assertFalse(b.shortcut_monitor.enabled)
  finally:b.close()

class DesktopConversationConcurrencyTests(unittest.TestCase):
 def test_actual_bridge_desktop_worker_does_not_block_active_conversation_or_stop(self):
  import threading
  from jarvis.desktop_controller import DesktopController
  from test_desktop_engine import Adapter
  entered=threading.Event();release=threading.Event();a=Adapter();a.windows=lambda:[dict(a.target)]
  original=a.perform
  def perform(target,row):original(target,row);entered.set();release.wait(1)
  a.perform=perform;b=Bridge(WorkspaceVoice());b.desktop_control=DesktopController(a)
  from jarvis.runtime import VoiceRuntime
  from jarvis.hold_microphone import HoldMic
  speaker=Mock();runtime=VoiceRuntime(Mock(),Mock(),Mock(),speaker)
  runtime.mic=HoldMic(Mock(),runtime.on_utterance,stream_factory=lambda **k:self.fail('No device should open in concurrency fixture'))
  runtime.enable(consent=True);b.voice.runtime=runtime
  try:
   b.execute({'command':'desktop-windows','consent':True})
   state=b.execute({'command':'desktop-task-preview','target':a.target,'steps':[{'action':'move','x':1,'y':1},{'action':'move','x':2,'y':2}],'scope':'Synthetic fixture only'})
   b.execute({'command':'desktop-task-run','reviewed':state['desktop_control']['task']['pending'],'confirm':True,'effect_approved':True})
   self.assertTrue(entered.wait(1));state=b.execute({'command':'status'})
   self.assertTrue(state['desktop_control']['busy']);self.assertTrue(state['voice_active']);self.assertIs(b.voice.runtime,runtime)
   b.execute({'command':'desktop-task-stop'});release.set();b.desktop_control.worker.join(1)
   self.assertEqual(len(a.inputs),1);self.assertIs(b.voice.runtime,runtime);self.assertTrue(runtime.enabled)
  finally:release.set();b.close()

class InputLanguageBridgeTests(unittest.TestCase):
 def test_explicit_language_selection_is_session_only_and_never_opens_microphone(self):
  b=Bridge(WorkspaceVoice())
  try:
   self.assertEqual(b.execute({'command':'status'})['input_language'],'auto')
   for language in ('ta','en','auto'):
    self.assertEqual(b.execute({'command':'voice-input-language','language':language})['input_language'],language)
    self.assertIsNone(b.voice.runtime)
   with self.assertRaises(ValueError):b.execute({'command':'voice-input-language','language':'unknown'})
   b.voice.busy=True
   with self.assertRaises(ValueError):b.execute({'command':'voice-input-language','language':'ta'})
   self.assertEqual(b.voice.input_language,'auto')
  finally:b.close()
