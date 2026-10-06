import unittest,io,json,threading
from jarvis.tiny_specialists import Specialists
class Tests(unittest.TestCase):
 def make(self):
  self.models=[{'type':'llm','params_string':'0.6B','loaded_instances':[{'id':'tiny'}]}];self.output='{"kind":"proposed_action"}';self.requests=[]
  owner=self
  class R(io.BytesIO):
   def __enter__(self):return self
   def __exit__(self,*a):self.close()
  class HTTP:
   def open(self,req,timeout=8):
    if isinstance(req,str):return R(json.dumps({'models':owner.models}).encode())
    owner.requests.append(json.loads(req.data));return R(json.dumps({'choices':[{'message':{'content':owner.output}}]}).encode())
  return Specialists(opener=HTTP(),clock=lambda:0)
 def test_review_only_loaded_small_model(self):
  s=self.make()
  with self.assertRaises(ValueError):s.configure({'intent':'tiny'},{'intent':'tiny'})
  s.configure({'intent':'tiny'},{'intent':'tiny'},True);r=s.run('intent','open notepad');self.assertEqual(r['output']['kind'],'proposed_action');self.assertFalse(hasattr(s,'execute'));self.assertEqual(self.requests[0]['model'],'tiny')
 def test_oversize_and_unknown_metadata(self):
  s=self.make();self.models[0]['params_string']='4B'
  with self.assertRaises(ValueError):s.configure({'intent':'tiny'},{'intent':'tiny'},True)
  self.models[0]['params_string']='unknown';self.assertEqual(s.metadata(),[])
 def test_schema_gate_and_stop(self):
  s=self.make();s.configure({'summary':'tiny'},{'summary':'tiny'},True);self.output='{"tool":"send"}'
  with self.assertRaises(ValueError):s.run('summary','data')
  self.assertTrue(s.gate.acquire(False));s.gate.release();s.stop()
  with self.assertRaises(ValueError):s.run('summary','data')
