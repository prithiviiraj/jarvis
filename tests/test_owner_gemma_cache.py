import unittest,tempfile,pathlib,importlib.util
from unittest.mock import Mock
spec=importlib.util.spec_from_file_location('owner_embedding_cache',pathlib.Path(__file__).resolve().parents[1]/'optional-embedding/runtime.py');rt=importlib.util.module_from_spec(spec);spec.loader.exec_module(rt)
class GemmaCache(unittest.TestCase):
 def setUp(self):rt.VECTOR_CACHE.clear();rt.CACHE_MODEL=None
 def model(self):
  import numpy as np
  m=Mock();m.encode.side_effect=lambda *a,**kw:np.array([1.]+[0.]*(kw['truncate_dim']-1));return m
 def test_repeat_query_reuses_current_documents_but_encodes_new_query(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'plan.md';p.write_text('actual first plan');m=self.model();r={'action':'search','folder':d,'query':'plan','dimensions':128};a=rt.retrieve(r,m);b=rt.retrieve(dict(r,query='another query'),m);self.assertEqual(m.encode.call_count,3);self.assertEqual(b['cache']['document_hits'],1);self.assertEqual(b['cache']['document_encodes'],0);p.write_text('actual changed plan');c=rt.retrieve(r,m);self.assertEqual(c['cache']['document_encodes'],1);self.assertEqual(m.encode.call_count,5)
 def test_encoder_dimension_or_model_change_cannot_reuse_wrong_vector(self):
  with tempfile.TemporaryDirectory()as d:
   (pathlib.Path(d)/'plan.md').write_text('actual plan');m=self.model();r={'action':'search','folder':d,'query':'plan','dimensions':128};rt.retrieve(r,m);self.assertEqual(rt.retrieve(dict(r,dimensions=256),m)['cache']['document_encodes'],1);other=self.model();self.assertEqual(rt.retrieve(r,other)['cache']['document_encodes'],1)
 def test_deleted_file_never_returns_from_previous_cache(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'plan.md';p.write_text('actual plan');m=self.model();r={'action':'search','folder':d,'query':'plan','dimensions':128};rt.retrieve(r,m);p.unlink();self.assertEqual(rt.retrieve(r,m)['results'],[])
