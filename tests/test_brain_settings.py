import unittest,tempfile,json,time,threading
from pathlib import Path
from unittest.mock import Mock,patch
from jarvis.brain_settings import BrainSettings
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.router import RouterError
class BrainTests(unittest.TestCase):
 def setUp(self):
  self.keys=Mock();self.keys.status.return_value={'present':True};self.b=BrainSettings(self.keys)
  self.rows=[{'id':'slot1','provider':'groq','model':'llama-3.1-8b-instant','enabled':True,'consent':True,'free':True},{'id':'slot2','provider':'gemini','model':'gemini-test','enabled':True,'consent':True,'free':True}]
 def test_no_creation_network(self):self.keys.get.assert_not_called()
 def test_secure_key_status_never_secret(self):
  self.b.configure(self.rows,{'DEX':'slot2'});self.b.set_key('slot1','groq','test-value');self.assertNotIn('test-value',json.dumps(self.b.snapshot()));self.keys.set.assert_called_once_with('groq/slot1','test-value')
 def test_persist_without_secrets_or_consent(self):
  with tempfile.TemporaryDirectory()as d:
   path=Path(d)/'routes.json';b=BrainSettings(self.keys,path);b.configure(self.rows,{'DEX':'slot2'});saved=path.read_text();self.assertNotIn('consent',saved);self.assertNotIn('free',saved);loaded=BrainSettings(self.keys,path);self.assertEqual(loaded.assignments['DEX'],'slot2');self.assertEqual(loaded.consent,set());self.assertEqual(loaded.free,set())
 def test_primary_cloud_first_local_last(self):
  self.b.configure(self.rows,{'DEX':'slot2'});self.assertEqual([s.provider for s in self.b.candidates('DEX')],['gemini','groq','local'])
 def test_unconfirmed_cloud_excluded(self):
  self.rows[0]['free']=False;self.rows[1]['consent']=False;self.b.configure(self.rows,{});self.assertEqual([s.provider for s in self.b.candidates('DEX')],['local'])
 def test_shared_rate_limit_cooldown(self):
  self.b.configure(self.rows,{'DEX':'slot1'});routers=[]
  class Fake:
   def __init__(me,ps,**kw):me.p=ps[0];me.last_diagnostics=[];me.last_warnings=[];routers.append(me.p.name)
   def stream(me,*a,**kw):
    if me.p.name=='slot1':raise RouterError('http-429')
    yield {'text':'yes','provider':me.p.name,'model':me.p.model}
  with patch('jarvis.brain_settings.BrainRouter',Fake):
   self.assertEqual(self.b.router('DEX').ask([{'role':'user','content':'Explain a technical question'}])['text'],'yes');self.assertEqual(self.b.router('DEX').ask([{'role':'user','content':'Explain a technical question'}])['text'],'yes')
  self.assertEqual(routers,['slot1','slot2','slot2']);self.assertGreater(self.b.cooldowns['slot1'],time.monotonic())
 def test_partial_no_fallback(self):
  self.b.configure(self.rows,{})
  class Fake:
   def __init__(me,*a,**kw):me.last_diagnostics=[];me.last_warnings=[]
   def stream(me,*a,**kw):yield {'text':'part','provider':'slot1'};raise RouterError('mid stream')
  with patch('jarvis.brain_settings.BrainRouter',Fake):
   with self.assertRaises(RouterError):self.b.router('DEX').ask([{'role':'user','content':'hi'}])
 def test_parallel_round_real_concurrency_order_and_conclusion(self):
  v=WorkspaceVoice();barrier=threading.Barrier(3);seen=[];lock=threading.Lock()
  class Settings:
   def router(me,name):
    class R:
     def ask(me,messages,**kw):
      if 'conclusion' in messages[-1]['content']:
       self.assertEqual(len([m for m in messages if m['role']=='assistant']),3);return {'text':'Conclusion.'}
      barrier.wait(timeout=2)
      with lock:seen.append(name)
      return {'text':name+' perspective.'}
    return R()
  t=v.parallel_round('test topic',Settings());t.join(4);self.assertFalse(t.is_alive());self.assertEqual(len(seen),3);events=[]
  while not v.events.empty():events.append(v.events.get())
  answers=[value for kind,value in events if kind=='answer'];self.assertEqual([a['profile']for a in answers],['LYRA','DEX','JARVIS','JARVIS']);self.assertEqual(answers[-1]['text'],'Conclusion.');v.close()
 def test_local_connection_check_async_current_failure(self):
  with patch('jarvis.brain_settings.local_models',return_value=['current-model']):
   t=self.b.check();t.join(1)
  self.assertEqual(self.b.snapshot()['checks']['local']['model'],'current-model')
  with patch('jarvis.brain_settings.local_models',side_effect=RouterError('server stopped')):
   t=self.b.check();t.join(1)
  self.assertEqual(self.b.snapshot()['checks']['local']['state'],'failed')
 def test_live_api_models_greeting_and_secret_not_in_status(self):
  import io
  from jarvis.router import HttpTransport
  self.b.configure(self.rows,{});self.keys.get.return_value='not-a-real-key'
  models=io.BytesIO(json.dumps({'data':[{'id':'llama-3.1-8b-instant'}]}).encode());http=Mock();http.open.return_value=models
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http),patch.object(HttpTransport,'complete',return_value='Hello.'):
   t=self.b.check('slot1');t.join(1)
  self.assertEqual(self.b.checks['slot1']['state'],'ready');self.assertNotIn('not-a-real-key',json.dumps(self.b.snapshot()))
 def test_local_fallback_is_serialized_across_personas(self):
  active=0;maximum=0;lock=threading.Lock()
  class Fake:
   def __init__(me,*a,**kw):me.last_diagnostics=[];me.last_warnings=[]
   def stream(me,*a,**kw):
    nonlocal active,maximum
    with lock:active+=1;maximum=max(maximum,active)
    time.sleep(.04)
    yield {'text':'local answer','provider':'local'}
    with lock:active-=1
  with patch('jarvis.brain_settings.local_models',return_value=['qwen']),patch('jarvis.brain_settings.BrainRouter',Fake):
   threads=[threading.Thread(target=lambda n=n:self.b.router(n).ask([{'role':'user','content':'hi'}]))for n in ('DEX','DEX','JARVIS')]
   for t in threads:t.start()
   for t in threads:t.join(1)
  self.assertEqual(maximum,1)
 def test_actual_bridge_new_commands_are_allowed(self):
  from jarvis.ui_bridge import Bridge
  v=WorkspaceVoice();b=Bridge(v,self.b)
  with patch.object(self.b,'check')as check:
   b.execute({'command':'brain-check','slot':'local'});check.assert_called_once()
  b.execute({'command':'key-save','slot':'slot1','kind':'groq','secret':'fixture-only'})
  self.keys.set.assert_called_once_with('groq/slot1','fixture-only')
  b.execute({'command':'brain-save','slots':self.rows,'assignments':{'DEX':'slot2'}})
  self.assertEqual(b.execute({'command':'status'})['brains']['assignments']['DEX'],'slot2')
  with patch.object(v,'parallel_round')as round_call:b.execute({'command':'team-round','text':'topic','audio':False});round_call.assert_called_once()
  b.execute({'command':'key-delete','slot':'slot1','kind':'groq'});self.keys.delete.assert_called_once_with('groq/slot1');b.close()
 def test_gemini_automatic_excludes_video_and_tts(self):
  import io
  self.b.configure([{'id':'slot1','provider':'gemini','model':'','enabled':True,'consent':True,'free':True}],{});self.keys.get.return_value='fixture'
  ids=['models/gemini-omni-1.1-flash','models/gemini-2.5-flash','models/gemini-flash-tts'];http=Mock();http.open.return_value=io.BytesIO(json.dumps({'data':[{'id':m}for m in ids]}).encode())
  router=Mock();router.ask.return_value={'text':'Hello'}
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http),patch('jarvis.brain_settings.BrainRouter',return_value=router):t=self.b.check('slot1');t.join(1)
  self.assertEqual(self.b.rows['slot1'].model,'models/gemini-2.5-flash');self.assertEqual(self.b.checks['slot1']['state'],'ready')
 def test_manual_gemini_video_refused_before_greeting(self):
  import io
  self.b.configure([{'id':'slot1','provider':'gemini','model':'models/gemini-omni-1.1-flash','enabled':True,'consent':True,'free':True}],{});self.keys.get.return_value='fixture';http=Mock();http.open.return_value=io.BytesIO(json.dumps({'data':[{'id':'models/gemini-omni-1.1-flash'}]}).encode())
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http),patch('jarvis.brain_settings.BrainRouter')as router:t=self.b.check('slot1');t.join(1);router.assert_not_called()
  self.assertIn('not supported text chat',self.b.checks['slot1']['error'])
 def test_rate_limit_distinct_without_daily_reset_claim(self):
  import io
  self.b.configure(self.rows,{});self.keys.get.return_value='fixture';http=Mock();http.open.return_value=io.BytesIO(json.dumps({'data':[{'id':'llama-3.1-8b-instant'}]}).encode());router=Mock();router.ask.side_effect=RouterError('No enabled brain answered (slot1:http-429)')
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http),patch('jarvis.brain_settings.BrainRouter',return_value=router):t=self.b.check('slot1');t.join(1)
  self.assertIn('rate limit or quota',self.b.checks['slot1']['error']);self.assertIn('reset time is unknown',self.b.checks['slot1']['error'])

class ModelListAndKeyTests(unittest.TestCase):
 def setUp(self):
  self.keys=Mock();self.keys.status.return_value={'present':True};self.b=BrainSettings(self.keys,Path(tempfile.mkdtemp())/'routes.json')
 def test_key_save_strips_surrounding_whitespace(self):
  self.b.set_key('slot1','gemini','  pasted-key \n');self.keys.set.assert_called_once_with('gemini/slot1','pasted-key')
 def test_fetch_models_without_greeting(self):
  import io
  self.b.configure([{'id':'slot1','provider':'gemini','model':'','enabled':True,'consent':True,'free':True}],{});self.keys.get.return_value='fixture'
  http=Mock();http.open.return_value=io.BytesIO(json.dumps({'data':[{'id':'models/gemini-2.5-flash'}]}).encode())
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http),patch('jarvis.brain_settings.BrainRouter')as router:t=self.b.list_models('slot1');t.join(1)
  router.assert_not_called();self.assertEqual(self.b.checks['slot1']['state'],'models-listed');self.assertIn('models/gemini-2.5-flash',self.b.checks['slot1']['models']);self.assertNotIn('fixture',json.dumps(self.b.snapshot()))
 def test_fetch_models_preserves_ready_status(self):
  import io
  self.b.configure([{'id':'slot1','provider':'nim','model':'nvidia/nemotron-3.5-lightning-30b-a3b','enabled':True,'consent':True,'free':True}],{});self.keys.get.return_value='fixture'
  http=Mock();http.open.return_value=io.BytesIO(json.dumps({'data':[{'id':'nvidia/nemotron-3.5-lightning-30b-a3b'}]}).encode())
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http):self.b.checks['slot1']={'state':'ready','model':'nvidia/nemotron-3.5-lightning-30b-a3b'};t=self.b.list_models('slot1');t.join(1)
  self.assertEqual(self.b.checks['slot1']['state'],'ready');self.assertEqual(self.b.checks['slot1']['models'],['nvidia/nemotron-3.5-lightning-30b-a3b'])
 def test_http400_names_invalid_key(self):
  import urllib.error
  self.b.configure([{'id':'slot1','provider':'gemini','model':'','enabled':True,'consent':True,'free':True}],{});self.keys.get.return_value='fixture'
  http=Mock();http.open.side_effect=urllib.error.HTTPError('https://x',400,'Bad Request',{},None)
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http):t=self.b.check('slot1');t.join(1)
  self.assertIn('invalid',self.b.checks['slot1']['error'].lower());self.assertNotIn('fixture',json.dumps(self.b.snapshot()))
 def test_auto_failure_names_each_candidate(self):
  import io
  self.b.configure([{'id':'slot1','provider':'nim','model':'','enabled':True,'consent':True,'free':True}],{});self.keys.get.return_value='fixture'
  ids=['nvidia/nemotron-3.5-lightning-30b-a3b','meta/llama-3.3-70b-instruct'];http=Mock();http.open.return_value=io.BytesIO(json.dumps({'data':[{'id':m}for m in ids]}).encode())
  router=Mock();router.ask.side_effect=RouterError('No enabled brain answered (slot1:http-500)')
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http),patch('jarvis.brain_settings.BrainRouter',return_value=router):t=self.b.check('slot1');t.join(1)
  self.assertIn('nemotron-3.5-lightning-30b-a3b',self.b.checks['slot1']['error']);self.assertIn('http-500',self.b.checks['slot1']['error'])
 def test_auto_429_names_candidate_and_keeps_list(self):
  import io
  self.b.configure([{'id':'slot1','provider':'nim','model':'','enabled':True,'consent':True,'free':True}],{});self.keys.get.return_value='fixture'
  ids=['nvidia/nemotron-3.5-lightning-30b-a3b'];http=Mock();http.open.return_value=io.BytesIO(json.dumps({'data':[{'id':m}for m in ids]}).encode())
  router=Mock();router.ask.side_effect=RouterError('No enabled brain answered (slot1:http-429)')
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http),patch('jarvis.brain_settings.BrainRouter',return_value=router):t=self.b.check('slot1');t.join(1)
  self.assertIn('Automatic selection stopped at nvidia/nemotron-3.5-lightning-30b-a3b',self.b.checks['slot1']['error']);self.assertIn('rate limit or quota',self.b.checks['slot1']['error']);self.assertIn('nvidia/nemotron-3.5-lightning-30b-a3b',self.b.checks['slot1']['models'])
class NimAutomaticTests(unittest.TestCase):
 def setUp(self):
  from jarvis.brain_settings import BrainSettings
  from unittest.mock import Mock
  import tempfile
  from pathlib import Path
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.keys=Mock();self.b=BrainSettings(self.keys,Path(self.tmp.name)/'routes.json')
 def test_nim_automatic_prefers_verified_nemotron_when_listed(self):
  import io
  from unittest.mock import Mock,patch
  self.b.configure([{'id':'slot2','provider':'nim','model':'','enabled':True,'consent':True,'free':True}],{});self.keys.get.return_value='fixture'
  ids=['meta/llama-3.3-70b-instruct','nvidia/nemotron-3.5-lightning-30b-a3b'];http=Mock();http.open.return_value=io.BytesIO(json.dumps({'data':[{'id':m}for m in ids]}).encode())
  router=Mock();router.ask.return_value={'text':'Hello'}
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http),patch('jarvis.brain_settings.BrainRouter',return_value=router):t=self.b.check('slot2');t.join(1)
  self.assertEqual(self.b.rows['slot2'].model,'nvidia/nemotron-3.5-lightning-30b-a3b');self.assertEqual(self.b.checks['slot2']['state'],'ready')
 def test_nim_automatic_falls_back_on_transient_failure_not_429(self):
  import io
  from unittest.mock import Mock,patch
  from jarvis.router import RouterError
  self.b.configure([{'id':'slot2','provider':'nim','model':'','enabled':True,'consent':True,'free':True}],{});self.keys.get.return_value='fixture'
  ids=['meta/llama-3.3-70b-instruct','nvidia/nemotron-3.5-lightning-30b-a3b'];http=Mock();http.open.return_value=io.BytesIO(json.dumps({'data':[{'id':m}for m in ids]}).encode())
  router=Mock();router.ask.side_effect=[RouterError('No enabled brain answered (slot2:http-500)'),{'text':'Hello'}]
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http),patch('jarvis.brain_settings.BrainRouter',return_value=router):t=self.b.check('slot2');t.join(1)
  self.assertEqual(self.b.rows['slot2'].model,'meta/llama-3.3-70b-instruct');self.assertEqual(self.b.checks['slot2']['state'],'ready');self.assertEqual(router.ask.call_count,2)
 def test_nim_automatic_stops_on_429_without_second_candidate(self):
  import io
  from unittest.mock import Mock,patch
  from jarvis.router import RouterError
  self.b.configure([{'id':'slot2','provider':'nim','model':'','enabled':True,'consent':True,'free':True}],{});self.keys.get.return_value='fixture'
  ids=['meta/llama-3.3-70b-instruct','nvidia/nemotron-3.5-lightning-30b-a3b'];http=Mock();http.open.return_value=io.BytesIO(json.dumps({'data':[{'id':m}for m in ids]}).encode())
  router=Mock();router.ask.side_effect=RouterError('No enabled brain answered (slot2:http-429)')
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http),patch('jarvis.brain_settings.BrainRouter',return_value=router):t=self.b.check('slot2');t.join(1)
  self.assertEqual(router.ask.call_count,1);self.assertIn('rate limit or quota',self.b.checks['slot2']['error']);self.assertEqual(self.b.rows['slot2'].model,'automatic')
 def test_nim_manual_id_unchanged_by_candidates(self):
  import io
  from unittest.mock import Mock,patch
  self.b.configure([{'id':'slot2','provider':'nim','model':'some/custom-manual-id','enabled':True,'consent':True,'free':True}],{});self.keys.get.return_value='fixture'
  http=Mock();http.open.return_value=io.BytesIO(json.dumps({'data':[{'id':'some/custom-manual-id'}]}).encode())
  router=Mock();router.ask.return_value={'text':'Hello'}
  with patch('jarvis.brain_settings.urllib.request.build_opener',return_value=http),patch('jarvis.brain_settings.BrainRouter',return_value=router):t=self.b.check('slot2');t.join(1)
  self.assertEqual(self.b.rows['slot2'].model,'some/custom-manual-id')

class NativeModelListBoundary(unittest.TestCase):
 def test_native_allows_list_command(self):
  p=Path(__file__).parents[1]/'modern-ui/src-tauri/src/main.rs'
  self.assertIn('"brain-models"',p.read_text().split('.contains(&command)')[0])

class ApiOnlyRouting(unittest.TestCase):
 def test_api_unavailable_never_discovers_local(self):
  b=BrainSettings(Mock())
  with patch('jarvis.brain_settings.local_models')as local:
   with self.assertRaises(RouterError):b.router('JARVIS').ask([{'role':'user','content':'hi'}],configured_chat=True,api_only=True)
   local.assert_not_called()
 def test_api_failure_never_falls_back_to_local(self):
  b=BrainSettings(Mock());b.configure([{'id':'slot1','provider':'groq','model':'llama-3.1-8b-instant','enabled':True,'consent':True,'free':True}],{})
  class Failed:
   def __init__(self,*a,**k):self.last_diagnostics=[];self.last_warnings=[]
   def stream(self,*a,**k):raise RouterError('http-500');yield
  with patch('jarvis.brain_settings.BrainRouter',Failed),patch('jarvis.brain_settings.local_models')as local:
   with self.assertRaises(RouterError):b.router('DEX').ask([{'role':'user','content':'A friendly chat'}],configured_chat=True,api_only=True)
   local.assert_not_called()
