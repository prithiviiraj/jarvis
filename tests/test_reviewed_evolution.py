import json,unittest
from jarvis.reviewed_evolution import Proposal
class Proposals(unittest.TestCase):
 def row(self):return {'summary':'A pure helper','module':'extension_help.py','source':'def greet():\n return "hi"','tests':'assert greet()=="hi"','risks':'Untested, review required'}
 def test_parse_is_not_execution(self):
  p=Proposal();r=p.prepare(json.dumps(self.row()),'Make a helper');self.assertIn('Not executed',r['validation']);self.assertEqual(len(r['sha256']),64)
  with self.assertRaises(ValueError):p.export_reviewed(r)
  self.assertIn('NOT installed',p.export_reviewed(r,True));self.assertFalse(hasattr(p,'apply'));p.cancel();self.assertIsNone(p.pending)
 def test_traversal_and_malformed_source(self):
  p=Proposal();r=self.row();r['module']='../ui_bridge.py'
  with self.assertRaises(ValueError):p.prepare(json.dumps(r),'help')
  r=self.row();r['source']='bad (('
  with self.assertRaises(SyntaxError):p.prepare(json.dumps(r),'help')
 def test_changed_review_refused(self):
  p=Proposal();r=p.prepare(json.dumps(self.row()),'help');r['source']='print("different")'
  with self.assertRaises(ValueError):p.export_reviewed(r,True)
 def test_local_only_generation_and_cancel(self):
  from unittest.mock import Mock
  import threading
  p=Proposal();router=Mock();router.ask.return_value={'text':json.dumps(self.row()),'cloud':False};r=p.generate('helper',router);self.assertEqual(r['goal'],'helper');self.assertTrue(router.ask.call_args.kwargs['local_only'])
  cancel=threading.Event();cancel.set()
  with self.assertRaises(ValueError):p.generate('helper',router,cancel)
 def test_cloud_refused(self):
  from unittest.mock import Mock
  router=Mock();router.ask.return_value={'text':json.dumps(self.row()),'cloud':True}
  with self.assertRaises(ValueError):Proposal().generate('helper',router)
 def test_cancel_during_model_discards(self):
  from unittest.mock import Mock
  import threading
  p=Proposal();cancel=threading.Event();router=Mock()
  def ask(*a,**k):p.cancel();return {'text':json.dumps(self.row()),'cloud':False}
  router.ask.side_effect=ask
  with self.assertRaises(ValueError):p.generate('helper',router,cancel)
  self.assertIsNone(p.pending)
