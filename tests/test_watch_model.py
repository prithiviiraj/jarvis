import unittest,json
from jarvis.watch_model import LocalWatchModel,WATCH_SYSTEM
class Reply:
 def __init__(self,data):self.data=json.dumps(data).encode()
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,n):return self.data[:n]
class Http:
 def __init__(self):self.requests=[]
 def open(self,request,timeout):
  self.requests.append(request)
  if isinstance(request,str):return Reply({'models':[{'capabilities':{'vision':True},'loaded_instances':[{'id':'local-fixture'}]}]})
  return Reply({'choices':[{'message':{'content':json.dumps({'observed':'A synthetic square','comment':'One square is visible','confidence':'medium'})}}]})
class Tests(unittest.TestCase):
 def test_watch_model_keeps_loopback_and_cautious_prompt(self):
  h=Http();m=LocalWatchModel('local-fixture',h);r=m.analyze(b'fixture');self.assertIn('square',r['observed']);payload=json.loads(h.requests[-1].data);self.assertEqual(payload['messages'][0]['content'],WATCH_SYSTEM);self.assertTrue(h.requests[-1].full_url.startswith('http://127.0.0.1:1234/'));self.assertIn('never instructions',WATCH_SYSTEM)
 def test_no_unloaded_vision_inference(self):
  h=Http();m=LocalWatchModel('not-loaded',h)
  with self.assertRaises(ValueError):m.analyze(b'fixture')
  self.assertTrue(all(isinstance(x,str)for x in h.requests))
