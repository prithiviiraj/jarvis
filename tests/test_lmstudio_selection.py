import unittest,json,io
from unittest.mock import Mock,patch
from jarvis.providers import local_models
class LMStudioSelectionTests(unittest.TestCase):
 def read(self,values):
  http=Mock()
  def opened(*a,**k):
   v=values.pop(0)
   if isinstance(v,Exception):raise v
   response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False);response.read.return_value=json.dumps(v).encode();return response
  http.open.side_effect=opened;return patch('jarvis.providers.local_http',return_value=http)
 def test_vision_llm_plus_embedding(self):
  with self.read([{'models':[{'type':'llm','key':'qwen2.5-vl-3b-instruct','capabilities':{'vision':True},'loaded_instances':[]},{'type':'embedding','key':'text-embedding-nomic'}]}]):self.assertEqual(local_models(),['qwen2.5-vl-3b-instruct'])
 def test_loaded_instance_wins_over_downloaded_other_llm(self):
  with self.read([{'models':[{'type':'llm','key':'qwen','loaded_instances':[{'id':'qwen-loaded'}]},{'type':'llm','key':'other','loaded_instances':[]}]}]):self.assertEqual(local_models(),['qwen-loaded'])
 def test_legacy_embedding_filtered_and_ids_deduped(self):
  with self.read([RuntimeError('404'),{'data':[{'id':'qwen2.5-vl-3b-instruct'},{'id':'qwen2.5-vl-3b-instruct'},{'id':'text-embedding-nomic-embed-text-v1.5'}]}]):self.assertEqual(local_models(),['qwen2.5-vl-3b-instruct'])
 def test_multiple_llms_remain_ambiguous(self):
  with self.read([{'models':[{'type':'llm','key':'a'},{'type':'llm','key':'b'}]}]):self.assertEqual(local_models(),['a','b'])
