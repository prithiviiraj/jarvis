import unittest,pathlib,tempfile,importlib.util
from unittest.mock import Mock,patch
from jarvis.embedding_service import EmbeddingService
spec=importlib.util.spec_from_file_location('embedding_runtime',pathlib.Path(__file__).resolve().parents[1]/'optional-embedding/runtime.py');rt=importlib.util.module_from_spec(spec);spec.loader.exec_module(rt)
class Retrieval(unittest.TestCase):
 def model(self):
  import numpy as np
  class M:
   def encode(self,value,**kw):
    dims=kw['truncate_dim'];v=np.zeros(dims);v[0 if isinstance(value,str)and('plan'in value or 'திட்டம்'in value)else 1]=1;return v
  return M()
 def test_shared_text_code_media_and_tamil_queries(self):
  with tempfile.TemporaryDirectory()as d:
   r=pathlib.Path(d);(r/'plan.md').write_text('plan');(r/'code.py').write_text('x=1');(r/'photo.png').write_bytes(b'fixture')
   out=rt.retrieve({'action':'search','folder':d,'encoders':'all','dimensions':256,'query':'திட்டம்'},self.model());self.assertEqual(out['results'][0]['name'],'plan.md');self.assertEqual({x['kind']for x in out['results']},{'text','code','image'});self.assertEqual(out['dimensions'],256)
 def test_links_never_become_wiki_links_or_writes(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'a.md';p.write_text('plan');(pathlib.Path(d)/'b.md').write_text('plan');out=rt.retrieve({'action':'links','folder':d,'encoders':'text','dimensions':768},self.model());self.assertEqual(out['links'][0]['type'],'suggested similarity');self.assertEqual(p.read_text(),'plan')
 def test_invalid_vectors_fail_closed(self):
  with tempfile.TemporaryDirectory()as d:
   (pathlib.Path(d)/'a.md').write_text('plan');m=Mock();m.encode.return_value=[float('nan')]*768
   with self.assertRaises(ValueError):rt.retrieve({'action':'search','folder':d,'query':'x','encoders':'text'},m)
 def test_hidden_and_large_text_omitted(self):
  with tempfile.TemporaryDirectory()as d:
   r=pathlib.Path(d);(r/'.hidden.md').write_text('hidden');(r/'big.md').write_text('x'*100001);(r/'ok.md').write_text('ok');rows,cut=rt.records(d,'text');self.assertEqual([x['name']for x in rows],['ok.md'])
 def test_consent_and_dimensions(self):
  with self.assertRaises(ValueError):rt.execute({'action':'check'})
  with self.assertRaises(ValueError):rt.retrieve({'action':'search','dimensions':12,'folder':'','query':'x'},self.model())
class ProcessBoundary(unittest.TestCase):
 def test_missing_separate_runtime_is_honest(self):
  s=EmbeddingService()
  with patch.dict('os.environ',{},clear=True):s.start('check',{'consent':True}).join(2)
  self.assertIn('separate',s.error);self.assertFalse(s.busy)
 def test_explicit_scope_and_stop(self):
  s=EmbeddingService()
  with self.assertRaises(ValueError):s.start('search',{'consent':False})
  s.process=Mock();s.stop();self.assertIsNone(s.process);self.assertEqual(s.results,[])
