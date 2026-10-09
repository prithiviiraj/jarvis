import unittest,tempfile,json
from pathlib import Path
from unittest.mock import Mock
from jarvis.action_intent import parse
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.team_discussion import messages
from jarvis.voice_preferences import VoicePreferences
from jarvis.voice_setup import VoiceSetup
class NightFix(unittest.TestCase):
 def test_natural_bounded(self):
  for t in ['JARVIS open the browser.','Jarvis can you open the browser for me','JARVIS:open the browser','Jarvis, open the browser now','Laya please open the browser']:
   self.assertEqual(parse(t),{'command':'open-window','value':''},t)
 def test_not_effect(self):
  for t in ['Do not open the browser','Jarvis do not open browser','How do I open browser?','Is browser open?','open browser and delete files','open browser tomorrow','open browser; calc.exe']:
   self.assertIsNone(parse(t),t)
 def test_url_integrity(self):
  self.assertEqual(parse('open https://example.com/now')['value'],'https://example.com/now')
  with self.assertRaises(ValueError):parse('open http://127.0.0.1')
 def test_team_typed_actual_bridge(self):
  b=Bridge(WorkspaceVoice());b.browser_enabled=True;b.voice.send_text=Mock()
  try:
   data=b.execute({'command':'chat','text':'JARVIS open the browser.','audio':False});self.assertEqual(data['browser']['pending'],{'command':'open-window','value':''});b.voice.send_text.assert_not_called();self.assertIsNone(b.browser)
  finally:b.close()
 def test_handler_before_enable(self):
  runtime=Mock();voice=WorkspaceVoice(Mock(return_value=runtime));handler=Mock(return_value=True);voice.action_handler=handler
  runtime.enable.side_effect=lambda **kw:self.assertIs(runtime.action_handler,handler)
  voice.start(True).join(2);runtime.enable.assert_called_once();voice.close()
 def test_partner_not_own(self):
  m=messages('DEX','lyra and DEX talk with each other about this',[{'role':'assistant','content':'[LYRA] Dex, we should help.'}],1)
  self.assertIn('Current speaker: DEX. Address LYRA, not yourself',m[0]['content']);self.assertEqual(m[1]['role'],'user');self.assertIn('[LYRA]',m[1]['content'])
 def test_removed_engines(self):
  with tempfile.TemporaryDirectory()as t:
   p=Path(t)/'v.json';v=VoicePreferences(p)
   for engine in ['kitten','pocket']:
    p.write_text(json.dumps({'engine':engine}));self.assertEqual(v.load(),'kokoro')
    with self.assertRaises(ValueError):v.save(engine)
    with self.assertRaises(ValueError):VoiceSetup().start(consent=True,engine=engine)
   v.save('kokoro');self.assertEqual(v.load(),'kokoro')
class Broker(unittest.TestCase):
 def test_strict_intents(self):
  from jarvis.intent_understanding import validate
  self.assertEqual(validate('{"kind":"app","app":"notepad"}','bring up notepad')['app'],'notepad')
  for raw,t in [('{"kind":"app","app":"paint"}','bring up notepad'),('{"kind":"browser","target":"https://evil.example"}','open browser'),('{"kind":"app","app":"cmd"}','open cmd'),('{"kind":"app","app":"notepad","arguments":"secret"}','open notepad')]:
   with self.assertRaises(ValueError):validate(raw,t)
  self.assertEqual(validate('{"kind":"browser","target":""}','laya brave browser')['kind'],'clarify')
  self.assertEqual(validate('{"kind":"browser","target":""}','do not open browser')['kind'],'clarify')
 def test_broker_no_execution(self):
  import time
  brains=Mock();brains.router.return_value.stream.return_value=iter([{'text':'{"kind":"app","app":"notepad"}'}]);b=Bridge(WorkspaceVoice(),brains=brains);b.desktop_enabled=True
  try:
   b.execute({'command':'desktop-preview','text':'bring up notepad'});
   for _ in range(100):
    if not b.intent_busy:break
    time.sleep(.01)
   self.assertEqual(b.desktop_pending['app'],'notepad');self.assertFalse(b.laya_active);self.assertIsNone(b.browser)
  finally:b.close()
 def test_active_browser_only_and_revoke(self):
  b=Bridge(WorkspaceVoice());b.browser=Mock();b.browser.cancel.is_set.return_value=False
  try:
   b.execute({'command':'chat','text':'activate laya'});self.assertTrue(b.laya_active)
   b.execute({'command':'chat','text':'Jarvis open the browser.'});b.browser.submit.assert_called_once_with(command='open-window',value='',confirmed=True);self.assertIsNone(b.browser_pending)
   b.desktop_enabled=True
   from unittest.mock import patch
   with patch('jarvis.desktop_actions.launch',return_value={'app':'Notepad','status':'submitted'})as launch:
    b.execute({'command':'chat','text':'open Notepad'});launch.assert_called_once();self.assertIsNone(b.desktop_pending)
   b.execute({'command':'chat','text':'deactivate laya'});self.assertFalse(b.laya_active);self.assertFalse(b.browser_enabled);b.browser.close.assert_called()
  finally:b.close()
 def test_stale_model_result_after_revoke(self):
  import threading,time
  entered=threading.Event();release=threading.Event()
  def stream(*a,**kw):entered.set();release.wait(2);yield {'text':'{"kind":"browser","target":""}'}
  brains=Mock();brains.router.return_value.stream=stream;b=Bridge(WorkspaceVoice(),brains=brains)
  try:
   b.execute({'command':'chat','text':'activate laya'});b.understand_action('bring up browser');entered.wait(1);b.execute({'command':'chat','text':'deactivate laya'});release.set();time.sleep(.05);self.assertFalse(b.laya_active);self.assertIsNone(b.browser);self.assertIsNone(b.browser_pending)
  finally:release.set();b.close()
 def test_awareness_actual_toggles(self):
  b=Bridge(WorkspaceVoice())
  try:
   self.assertIn('"enabled": false',b.interface_context());b.browser_enabled=True;self.assertIn('"enabled": true',b.interface_context());self.assertIn('isolated Brave only',b.interface_context());self.assertIn('credentials',b.interface_context())
  finally:b.close()

class Notice(unittest.TestCase):
 def test_relevant_off_notice_once(self):
  b=Bridge(WorkspaceVoice())
  try:
   self.assertIn('Relevant first-use OFF notice',b.interface_context('can you see me'));self.assertNotIn('Relevant first-use OFF notice',b.interface_context('can you see me'));self.assertNotIn('Relevant first-use OFF notice',b.interface_context('hello'));b.vision.enabled=True;b.interface_context('camera');b.vision.enabled=False;self.assertIn('Relevant first-use OFF notice',b.interface_context('camera'))
  finally:b.close()
class AdditionalGates(unittest.TestCase):
 def test_voice_stop_revokes(self):
  b=Bridge(WorkspaceVoice());b.browser=Mock();b.browser.cancel.is_set.return_value=False
  try:
   b.activation_action('activate laya');self.assertTrue(b.voice_action('stop'));self.assertFalse(b.laya_active);self.assertFalse(b.browser_enabled);b.browser.close.assert_called()
  finally:b.close()
 def test_support_is_no_install(self):
  b=Bridge(WorkspaceVoice())
  try:
   b.activation_action('activate laya');b.evolution.generate=Mock();b.support_gap('browser','Brave is not controlled.');
   import time
   for _ in range(100):
    if not b.evolution_busy:break
    time.sleep(.01)
   b.evolution.generate.assert_called_once();self.assertEqual(b.laya_support['surface'],'browser');self.assertEqual([m['name']for m in b.messages[1:3]],['DEX','DEX']);self.assertIn('not install',' '.join(m['text']for m in b.messages));self.assertIsNone(b.evolution.pending);b.activation_action('deactivate laya');self.assertIsNone(b.laya_support)
  finally:b.close()
 def test_setup_cannot_reach_removed_engine_even_corrupt_state(self):
  b=Bridge(WorkspaceVoice());b.voice.tts_engine='kitten';b.setup.start=Mock()
  try:
   with self.assertRaises(ValueError):b.execute({'command':'voice-setup','consent':True,'reviewed_engine':'kitten'})
   b.setup.start.assert_not_called()
  finally:b.close()

class SupportScope(unittest.TestCase):
 def test_brave_reason_does_not_claim_path_inspection(self):
  b=Bridge(WorkspaceVoice());b.evolution.generate=Mock()
  try:
   b.activation_action('activate laya');b.support_gap('browser','Brave adapter not implemented')
   text=next(m['text']for m in b.messages if m['name']=='DEX'and 'adapter' in m['text']);self.assertIn('check pannala',text);self.assertIn('Master',text)
  finally:b.close()
