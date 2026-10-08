import tempfile,threading,pathlib,hashlib,unittest
from jarvis.source_answer import SourceAnswer
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name).resolve();(self.root/'.obsidian').mkdir();self.file=self.root/'source.md';self.file.write_text('Exact source evidence');self.note={'name':'source.md','vault_folder':str(self.root),'text':'Exact source evidence','sha256':hashlib.sha256(self.file.read_bytes()).hexdigest(),'truncated':False};self.a=SourceAnswer(threading.Lock(),lambda:[{'id':'fixture'}],lambda m,q,n,c:{'text':'Draft from source','model':m})
 def tearDown(self):self.a.stop();self.tmp.cleanup()
 def prepare(self):return self.a.prepare(self.root,self.note,'What is observed?','fixture')
 def test_exact_review_and_source_attribution(self):
  r=self.prepare();self.assertIsNone(self.a.result)
  with self.assertRaises(ValueError):self.a.start(self.root,r)
  self.a.start(self.root,r,True);self.a.worker.join(3);self.assertEqual(self.a.result['source_sha256'],self.note['sha256']);self.assertIn('Unverified',self.a.result['scope'])
 def test_changed_suffix_refused(self):
  r=self.prepare();self.file.write_text('Exact source evidence changed')
  with self.assertRaises(ValueError):self.a.start(self.root,r,True)
 def test_late_result_after_stop_discarded(self):
  ready=threading.Event();finish=threading.Event()
  def generate(m,q,n,c):ready.set();finish.wait(2);return {'text':'late','model':m}
  self.a.generate=generate;r=self.prepare();self.a.start(self.root,r,True);ready.wait(2);self.a.stop();finish.set();self.a.worker.join(3);self.assertIsNone(self.a.result)
 def test_wrong_model_no_claim(self):
  self.a.generate=lambda *a:{'text':'reply','model':'other'};r=self.prepare();self.a.start(self.root,r,True);self.a.worker.join(3);self.assertIsNone(self.a.result);self.assertTrue(self.a.error)
 def test_changed_during_generation_no_claim(self):
  def generate(m,*a):self.file.write_text('changed');return {'text':'reply','model':m}
  self.a.generate=generate;r=self.prepare();self.a.start(self.root,r,True);self.a.worker.join(3);self.assertIsNone(self.a.result)

class BridgeTests(unittest.TestCase):
 def test_no_source_inert_and_stop(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice())
  try:
   with self.assertRaises(ValueError):b.execute({'command':'source-answer-prepare','question':'Question','model_id':'fixture'})
   b.source_answer.result={'text':'stale'};b.voice_action('Jarvis stop');self.assertIsNone(b.source_answer.result)
   s=b.execute({'command':'source-answer-stop'});self.assertIsNone(s['source_answer']['result']);self.assertFalse(s['source_answer']['busy'])
  finally:b.close()
