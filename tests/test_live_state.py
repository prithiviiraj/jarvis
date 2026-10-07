import json,time,tempfile,pathlib,unittest
from unittest.mock import patch,Mock
from jarvis.providers import local_live_models
from jarvis.brain_settings import BrainSettings
class LiveState(unittest.TestCase):
 def test_downloaded_not_loaded(self):
  response=Mock();response.read.return_value=json.dumps({'models':[{'type':'llm','key':'downloaded','loaded_instances':[]}]}).encode();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False);http=Mock();http.open.return_value=response
  with patch('jarvis.providers.local_http',return_value=http):self.assertEqual(local_live_models(),[])
 def test_actual_loaded_instance(self):
  response=Mock();response.read.return_value=json.dumps({'models':[{'type':'llm','key':'disk-name','loaded_instances':[{'id':'running'}],'capabilities':{'vision':True}}]}).encode();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False);http=Mock();http.open.return_value=response
  with patch('jarvis.providers.local_http',return_value=http):self.assertEqual(local_live_models(),[{'id':'running','key':'disk-name','vision':True}])
 def test_refresh_and_unload_invalidate(self):
  b=BrainSettings();model={'id':'running','key':'disk','vision':False}
  with patch('jarvis.providers.local_live_models',return_value=[model]):b.refresh_live(True).join(2)
  self.assertEqual(b.live_snapshot()['state'],'loaded');self.assertEqual(b.live_snapshot()['profiles']['SILA']['state'],'loaded route')
  with patch('jarvis.providers.local_live_models',return_value=[]):b.refresh_live(True).join(2)
  self.assertEqual(b.live_snapshot()['state'],'no loaded model');self.assertEqual(b.live_snapshot()['models'],[])
 def test_failure_never_keeps_loaded_claim(self):
  b=BrainSettings();b.live={'state':'loaded','models':[{'id':'old','key':'old'}],'checked_at':time.time()}
  with patch('jarvis.providers.local_live_models',side_effect=OSError()):b.refresh_live(True).join(2)
  self.assertEqual(b.live_snapshot()['state'],'unavailable');self.assertEqual(b.live_snapshot()['models'],[])
 def test_stale_not_claimed_live(self):
  b=BrainSettings();b.live={'state':'loaded','models':[{'id':'old','key':'old'}],'checked_at':time.time()-30}
  self.assertEqual(b.live_snapshot()['state'],'stale')
 def test_legacy_assignment_preserved(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'brain.json';p.write_text(json.dumps({'slots':[{'id':'slot1','provider':'local','model':'chat','enabled':True}],'assignments':{''.join(('K','AI')):'slot1'}}))
   b=BrainSettings(path=p);self.assertEqual(b.assignments,{'SILA':'slot1'})
 def test_loaded_laya_guidance(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice());b.laya_engine.agent=object();b.browser_enabled=True
  try:
   with patch.object(b.brains,'refresh_live'):
    text=b.interface_context('Laya are you loaded?')
   self.assertIn('already',b.execute({'command':'laya-mode','consent':True})['laya']['status']);self.assertIn('do not ask to load or enable it again',text)
  finally:b.close()
 def test_explicit_local_route_with_multiple_loaded_models(self):
  b=BrainSettings();b.configure([{'id':'slot1','provider':'local','model':'chosen','enabled':True}],{'JARVIS':'slot1'})
  router=Mock();router.last_diagnostics=[];router.last_warnings=[];router.stream.return_value=iter([{'text':'actual answer'}])
  with patch('jarvis.brain_settings.local_models',return_value=['other','chosen']),patch('jarvis.brain_settings.BrainRouter',return_value=router)as factory:
   self.assertEqual(b.router('JARVIS').ask([{'role':'user','content':'Hi'}])['text'],'actual answer');self.assertEqual(factory.call_args.args[0][0].model,'chosen')
 def test_ambiguous_local_has_specific_reason(self):
  from jarvis.router import RouterError
  b=BrainSettings()
  with patch('jarvis.brain_settings.local_models',return_value=['one','two']):
   with self.assertRaisesRegex(RouterError,'Several local chat instances'):b.router('JARVIS').ask([{'role':'user','content':'Hi'}])
 def test_failure_no_agent_dump_or_automatic_proposal(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice());b.evolution.generate=Mock()
  try:
   b.explain_failure('Voice','raw private diagnostic');self.assertEqual(b.messages,[]);b.evolution.generate.assert_not_called();self.assertEqual(b.failure_detail['detail'],'raw private diagnostic')
  finally:b.close()
