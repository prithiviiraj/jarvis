import unittest,importlib.util,pathlib,json,subprocess,sys,tempfile,os
ROOT=pathlib.Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('protocol_check',ROOT/'optional-embedding/protocol-check.py');check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)
class EmbeddingProtocolCheckTests(unittest.TestCase):
 def test_actual_source_check_with_progress_and_final(self):
  with tempfile.TemporaryDirectory()as folder:
   result=subprocess.run([sys.executable,str(ROOT/'optional-embedding/runtime.py')],input=json.dumps({'action':'check','consent':True})+'\n',capture_output=True,text=True,env={**os.environ,'JARVIS_DATA_DIR':folder},timeout=30)
  self.assertEqual(result.returncode,0,result.stderr);report=check.validate(result.stdout.splitlines());self.assertGreater(report['progress_events'],0);self.assertIn('missing',report['final']['data']['status'].lower())
 def test_invalid_final_not_hidden_by_progress(self):
  with self.assertRaises(ValueError):check.validate([json.dumps({'event':'progress','data':{'percent':100}}),json.dumps({'ok':False,'error':'failure'})])
 def test_invalid_progress_rejected(self):
  with self.assertRaises(ValueError):check.validate([json.dumps({'event':'progress','data':{'percent':101}})])
 def test_multiple_final_replies_rejected(self):
  final=json.dumps({'ok':True,'data':{'model_bytes':1525787092}})
  with self.assertRaises(ValueError):check.validate([final,final])
