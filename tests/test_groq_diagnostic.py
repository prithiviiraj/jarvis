import unittest,importlib.util,pathlib,io,json,urllib.error
from unittest.mock import MagicMock,Mock
p=pathlib.Path(__file__).resolve().parents[1]/'diagnostics/GROQ-DIAG.py';spec=importlib.util.spec_from_file_location('diag',p);diag=importlib.util.module_from_spec(spec);spec.loader.exec_module(diag)
class DiagnosticTests(unittest.TestCase):
 def error(self,code,body):return urllib.error.HTTPError('https://example.invalid',code,'SECRET',{},io.BytesIO(body))
 def test_known_org(self):
  r=diag.classify(self.error(403,b'{"error":{"message":"SECRET","code":"model_permission_blocked_org","type":"permissions_error"}}'));self.assertEqual(r['detail'],'MODEL_PERMISSION_BLOCKED_ORG');self.assertNotIn('SECRET',str(r))
 def test_project(self):self.assertEqual(diag.classify(self.error(403,b'{"error":{"code":"model_permission_blocked_project"}}'))['detail'],'MODEL_PERMISSION_BLOCKED_PROJECT')
 def test_edge_not_account_claim(self):self.assertEqual(diag.classify(self.error(403,b'<!doctype html>SECRET'))['detail'],'NON_JSON_EDGE_OR_PROXY_REJECTION')
 def test_unknown_redacted(self):
  r=diag.classify(self.error(403,b'{"error":{"code":"SECRET","message":"SECRET"}}'));self.assertNotIn('SECRET',str(r));self.assertEqual(r['detail'],'STRUCTURED_ERROR_UNCLASSIFIED')
 def test_nonhashable(self):self.assertEqual(diag.classify(self.error(403,b'{"error":{"code":[]}}'))['detail'],'STRUCTURED_ERROR_UNCLASSIFIED')
 def test_models_then_one_greeting(self):
  http=MagicMock();resp=Mock();resp.read.side_effect=[json.dumps({'data':[{'id':'model','active':True}]}).encode(),b'{"choices":[{"message":{"content":"SECRET"}}]}'];http.open.return_value.__enter__.return_value=resp
  rows=diag.probe('SECRET','model',None,Mock(return_value=http));self.assertEqual([r['step'] for r in rows],['models','greeting']);self.assertEqual(http.open.call_count,2);self.assertNotIn('SECRET',str(rows))
  for call in http.open.call_args_list:self.assertIn('JARVIS-experimental',call.args[0].get_header('User-agent'))
 def test_list_denied_no_greeting(self):
  http=Mock();http.open.side_effect=self.error(403,b'edge');rows=diag.probe('SECRET','model',None,Mock(return_value=http));self.assertEqual(http.open.call_count,1);self.assertEqual(len(rows),1)
 def test_missing_model_no_greeting(self):
  http=MagicMock();http.open.return_value.__enter__.return_value.read.return_value=b'{"data":[]}';rows=diag.probe('SECRET','model',None,Mock(return_value=http));self.assertEqual(http.open.call_count,1);self.assertEqual(rows[-1]['code'],'SKIPPED_NO_SELECTED_LISTED_CHAT_MODEL')

 def test_optional_active_field_auto(self):
  http=MagicMock();resp=Mock();resp.read.side_effect=[b'{"data":[{"id":"openai/gpt-oss-20b"}]}',b'{"choices":[{"message":{"content":"hello"}}]}'];http.open.return_value.__enter__.return_value=resp
  rows=diag.probe('SECRET','',None,Mock(return_value=http));self.assertEqual(rows[0]['selected_model'],'openai/gpt-oss-20b');self.assertEqual(rows[-1]['code'],'OK_GROQ_REPLY_RECEIVED')
