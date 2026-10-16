import unittest,tempfile,threading
from unittest.mock import Mock
from jarvis.managed_session import ManagedSession
from jarvis.local_endpoint import managed_route
class Session(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.runtime=Mock();self.runtime.snapshot.return_value={'state':'loaded','model':'qwen3-vl-4b'};self.runtime.check.return_value={'state':'loaded'};self.runtime.route.return_value={'url':'http://127.0.0.1:42345/v1','key':'RAMsecret','model':'qwen3-vl-4b'};self.probe=Mock();self.probe.snapshot.return_value={'busy':False,'text':'passed','image':'passed','error':''};self.session=ManagedSession(self.tmp.name,self.runtime,self.probe)
 def tearDown(self):self.session.stop();self.tmp.cleanup()
 def test_inactive_until_review_and_confirmation(self):
  self.assertIsNone(managed_route());self.session.prepare('qwen3-vl-4b');self.runtime.start.assert_not_called();self.probe.start.assert_not_called()
  with self.assertRaises(ValueError):self.session.start(self.session.pending,False)
  with self.assertRaises(ValueError):self.session.start({'id':'qwen3-vl-4b'},True)
 def test_start_checks_then_tests_then_binds_real_route(self):
  review=self.session.prepare('qwen3-vl-4b')['pending'];self.session.start(review,True);self.session.worker.join(2);self.assertTrue(self.session.snapshot()['active']);self.runtime.start.assert_called_once_with('qwen3-vl-4b',True,cancel=self.session.cancel);self.probe.start.assert_called_once_with(True);self.assertEqual(managed_route()['key'],'RAMsecret');self.assertNotIn('RAMsecret',str(self.session.snapshot()))
 def test_bad_image_does_not_become_ready_or_fall_back(self):
  self.probe.snapshot.return_value={'busy':False,'text':'passed','image':'failed','error':'wrong color'};self.runtime.route.side_effect=ValueError('stopped')
  review=self.session.prepare('qwen3-vl-4b')['pending'];self.session.start(review,True);self.session.worker.join(2);self.assertFalse(self.session.active);self.assertIn('wrong color',self.session.error);self.runtime.stop.assert_called()
  with self.assertRaises(ValueError):managed_route()
 def test_stop_unbinds_and_stops_only_owned_runtime(self):
  self.session.start(self.session.prepare('qwen3-vl-4b')['pending'],True);self.session.worker.join(2);self.session.stop();self.assertIsNone(managed_route());self.runtime.stop.assert_called();self.probe.stop.assert_called();self.assertFalse(self.session.snapshot()['active'])
 def test_dead_active_runtime_not_silently_switched(self):
  self.session.start(self.session.prepare('qwen3-vl-4b')['pending'],True);self.session.worker.join(2);self.runtime.snapshot.return_value={'state':'failed'};self.runtime.route.side_effect=ValueError('stopped');self.assertFalse(self.session.check()['active'])
  with self.assertRaises(ValueError):managed_route()
 def test_stop_during_loading_cannot_later_bind(self):
  self.runtime.check.return_value={'state':'loading'};self.session.start(self.session.prepare('qwen3-vl-4b')['pending'],True);self.session.stop();self.session.worker.join(2);self.assertFalse(self.session.active);self.assertIsNone(managed_route());self.probe.start.assert_not_called()
 def test_unknown_model_rejected(self):
  with self.assertRaises(ValueError):self.session.prepare('not-our-model')

 def test_actual_session_runtime_probe_route_with_only_external_transports_mocked(self):
  import pathlib,json,hashlib,io
  from unittest.mock import patch
  from jarvis.managed_runtime import ManagedRuntime,CATALOG
  from jarvis.model_probe import ModelProbe
  root=pathlib.Path(self.tmp.name);runtime_dir=root/'runtime'/CATALOG['runtime']['tag'];runtime_dir.mkdir(parents=True);(runtime_dir/'llama-server.exe').write_bytes(b'fixture exe')
  receipt={'archive_sha256':CATALOG['runtime']['sha256'],'files':{'llama-server.exe':hashlib.sha256(b'fixture exe').hexdigest()}};(runtime_dir/'verified-files.json').write_text(json.dumps(receipt))
  model=json.loads(json.dumps(CATALOG['models'][0]));model_dir=root/'models'/model['id'];model_dir.mkdir(parents=True)
  for file in model['files']:
   raw=b'synthetic model fixture';(model_dir/file['name']).write_bytes(raw);file['size']=len(raw);file['sha256']=hashlib.sha256(raw).hexdigest()
  child=Mock();child.poll.return_value=None;child.wait.return_value=0;spawn=Mock(return_value=child);r=ManagedRuntime(root,spawn,lambda endpoint:True);http=Mock();answers=iter(['READY','red']);http.open.side_effect=lambda *a,**kw:io.BytesIO(json.dumps({'choices':[{'message':{'content':next(answers)}}]}).encode());probe=ModelProbe(r,http);session=ManagedSession(root,r,probe)
  with patch('jarvis.managed_runtime.CATALOG',dict(CATALOG,models=[model])):
   try:
    session.start(session.prepare(model['id'])['pending'],True);session.worker.join(2);self.assertTrue(session.active);spawn.assert_called_once();self.assertEqual(http.open.call_count,2);self.assertEqual(managed_route()['model'],model['id']);self.assertEqual(http.open.call_args.args[0].get_header('Authorization'),'Bearer '+r.route()['key'])
    child.poll.return_value=1
    with self.assertRaises(ValueError):managed_route()
    self.assertFalse(session.check()['active'])
   finally:session.stop()

 def test_backend_and_native_handlers_exist_and_ui_reviews_each_effect(self):
  import pathlib
  root=pathlib.Path(__file__).resolve().parents[1];backend=(root/'src/jarvis/ui_bridge.py').read_text(encoding='utf-8');native=(root/'modern-ui/src-tauri/src/main.rs').read_text(encoding='utf-8');ui=(root/'modern-ui/public/bigfoot-ui/jarvis-adapter.js').read_text(encoding='utf-8')
  for command in ('model-session-prepare','model-session-start','model-session-stop'):
   self.assertIn(command,backend);self.assertIn(command,native);self.assertIn(command,ui)
  self.assertIn('reviewed:review,confirm:true',ui);self.assertIn('if(confirm(`${review.label}: ${review.scope}`))',ui)

 def test_loaded_runtime_cannot_route_before_synthetic_tests_finish(self):
  entered=threading.Event();release=threading.Event()
  def start_probe(consent):entered.set();release.wait(1)
  self.probe.start.side_effect=start_probe
  self.session.start(self.session.prepare('qwen3-vl-4b')['pending'],True);self.assertTrue(entered.wait(1))
  # Session lock is held only during short probe launch in production. Avoid
  # blocking it in this transport fixture when checking the route gate.
  release.set();self.probe.snapshot.return_value={'busy':True,'text':'testing','image':'not tested','error':''}
  import time
  time.sleep(.01)
  with self.assertRaises(ValueError):managed_route()
  self.session.stop();self.session.worker.join(1)

 def test_background_verification_does_not_block_status_or_stop(self):
  entered=threading.Event();release=threading.Event()
  def starting(model,consent,cancel=None):entered.set();release.wait(1)
  self.runtime.start.side_effect=starting
  self.session.start(self.session.prepare('qwen3-vl-4b')['pending'],True);self.assertTrue(entered.wait(1));result=[];done=threading.Event()
  def status():result.append(self.session.snapshot());done.set()
  worker=threading.Thread(target=status);worker.start();self.assertTrue(done.wait(.2),'UI status must not wait on multi-GB verification');self.session.stop();self.assertTrue(self.session.cancel.is_set());release.set();self.session.worker.join(1);worker.join();self.assertFalse(self.session.active)
