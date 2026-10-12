import unittest,tempfile,pathlib
from jarvis.managed_runtime import ManagedRuntime
class Managed(unittest.TestCase):
 def test_no_effect_construction(self):
  calls=[]
  with tempfile.TemporaryDirectory()as d:
   r=ManagedRuntime(d,spawn=lambda *a,**k:calls.append(a));self.assertEqual(r.snapshot()['state'],'off');self.assertEqual(calls,[])
   with self.assertRaises(ValueError):r.route()
 def test_no_consent(self):
  with tempfile.TemporaryDirectory()as d:
   r=ManagedRuntime(d)
   with self.assertRaises(ValueError):r.start('qwen3-vl-4b')
 def test_missing_verification(self):
  with tempfile.TemporaryDirectory()as d:
   r=ManagedRuntime(d)
   with self.assertRaisesRegex(ValueError,'receipt'):r.start('qwen3-vl-4b',True)
 def test_wrong_model(self):
  with tempfile.TemporaryDirectory()as d:
   with self.assertRaises(ValueError):ManagedRuntime(d).start('../../bad',True)
 def test_stop_only_own_process(self):
  class Child:
   stopped=False
   def terminate(self):self.stopped=True
   def wait(self,**k):return 0
  with tempfile.TemporaryDirectory()as d:
   r=ManagedRuntime(d);c=Child();r.child=c;r.endpoint={'key':'not-a-secret-test','model':'fixture'};r.stop();self.assertTrue(c.stopped);self.assertIsNone(r.endpoint)

 def test_actual_argument_contract_with_only_process_transport_mocked(self):
  import hashlib,json
  from unittest.mock import patch
  from jarvis.managed_runtime import CATALOG
  calls=[]
  class Child:
   def poll(self):return None
   def terminate(self):pass
   def wait(self,**k):return 0
  with tempfile.TemporaryDirectory()as d:
   root=pathlib.Path(d);runtime=root/'runtime'/CATALOG['runtime']['tag'];runtime.mkdir(parents=True);(runtime/'llama-server.exe').write_bytes(b'fixture exe');(runtime/'ggml.dll').write_bytes(b'fixture DLL')
   receipt={'archive_sha256':CATALOG['runtime']['sha256'],'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in runtime.iterdir()}};(runtime/'verified-files.json').write_text(json.dumps(receipt))
   r=ManagedRuntime(root,spawn=lambda a,**kw:(calls.append((a,kw))or Child()),health=lambda endpoint:True)
   with patch('jarvis.managed_runtime.verified',return_value=True):r.start('qwen3-vl-4b',True)
   self.assertEqual(r.snapshot()['state'],'loading');self.assertNotIn('key',r.snapshot());r.check();route=r.route();self.assertIn('127.0.0.1:',route['url']);self.assertGreater(len(route['key']),30)
   args,kw=calls[0];self.assertEqual(args[args.index('--host')+1],'127.0.0.1');self.assertEqual(args[args.index('--alias')+1],'qwen3-vl-4b');self.assertNotIn('shell',kw);self.assertIn('--mmproj',args);r.stop();self.assertIsNone(r.endpoint)
 def test_unreceipted_DLL_blocks_launch(self):
  import hashlib,json
  from unittest.mock import patch
  from jarvis.managed_runtime import CATALOG
  with tempfile.TemporaryDirectory()as d:
   root=pathlib.Path(d);runtime=root/'runtime'/CATALOG['runtime']['tag'];runtime.mkdir(parents=True);(runtime/'llama-server.exe').write_bytes(b'x');(runtime/'extra.dll').write_bytes(b'unreviewed')
   (runtime/'verified-files.json').write_text(json.dumps({'archive_sha256':CATALOG['runtime']['sha256'],'files':{'llama-server.exe':hashlib.sha256(b'x').hexdigest()}}))
   r=ManagedRuntime(root,spawn=lambda *a,**k:self.fail('must not spawn'))
   with patch('jarvis.managed_runtime.verified',return_value=True):
    with self.assertRaisesRegex(ValueError,'set changed'):r.start('qwen3-vl-4b',True)

 def test_cancel_before_verification_never_spawns(self):
  import threading,json,hashlib
  from jarvis.managed_runtime import CATALOG
  from unittest.mock import Mock
  with tempfile.TemporaryDirectory()as d:
   root=pathlib.Path(d);runtime=root/'runtime'/CATALOG['runtime']['tag'];runtime.mkdir(parents=True);(runtime/'llama-server.exe').write_bytes(b'x');(runtime/'verified-files.json').write_text(json.dumps({'archive_sha256':CATALOG['runtime']['sha256'],'files':{'llama-server.exe':hashlib.sha256(b'x').hexdigest()}}));cancel=threading.Event();cancel.set();spawn=Mock();r=ManagedRuntime(root,spawn)
   with self.assertRaises(InterruptedError):r.start('qwen3-vl-4b',True,cancel)
   spawn.assert_not_called()

 def test_diagnostic_log_is_optional_not_a_status_secret(self):
  import io
  with tempfile.TemporaryDirectory()as d:
   out=io.StringIO();r=ManagedRuntime(d,log=out);self.assertIs(r.log,out);self.assertNotIn('log',r.snapshot());self.assertNotIn('key',r.snapshot())
