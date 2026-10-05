import unittest,time,types,threading
from unittest.mock import patch,Mock
from jarvis.laya_engine import LayaEngine
from jarvis.experimental.browser_proposals import Snapshot,Element
class Engine(unittest.TestCase):
 def test_missing_no_import_download_or_inference(self):
  e=LayaEngine()
  with patch('jarvis.laya_engine.laya_assets.ready',return_value=False),patch('jarvis.laya_engine.laya_assets.download')as net:
   e.load(consent=True).join(1);self.assertIsNone(e.agent);self.assertIn('could not load',e.error);net.assert_not_called()
 def test_review_required(self):
  with self.assertRaises(ValueError):LayaEngine().load()
 def test_local_load_and_stop(self):
  agent=Mock();agent.cfg={'head_max_len_train':50};laya=types.SimpleNamespace(load=Mock(return_value=agent));torch=types.SimpleNamespace(set_num_threads=Mock())
  with patch('jarvis.laya_engine.laya_assets.ready',return_value=True),patch.dict('sys.modules',{'laya':laya,'torch':torch}):
   e=LayaEngine();e.load(consent=True).join(1);self.assertIs(e.agent,agent);self.assertEqual(agent.cfg['head_max_len'],50);agent.predict.assert_not_called();self.assertEqual(laya.load.call_args.kwargs['device'],'cpu');e.stop();self.assertIsNone(e.agent)
 def test_late_load_discarded(self):
  started=threading.Event();finish=threading.Event();agent=Mock();agent.cfg={}
  def load(*a,**k):started.set();finish.wait(1);return agent
  with patch('jarvis.laya_engine.laya_assets.ready',return_value=True),patch.dict('sys.modules',{'laya':types.SimpleNamespace(load=load),'torch':types.SimpleNamespace(set_num_threads=Mock())}):
   e=LayaEngine();t=e.load(consent=True);self.assertTrue(started.wait(1));e.stop();finish.set();t.join(1);self.assertIsNone(e.agent)
 def test_predict_is_proposal_only(self):
  e=LayaEngine();e.agent=Mock();e.agent.predict.return_value={'answers':{'operation':{'choice':'0','probabilities':{str(i):1.0 if i==0 else 0.0 for i in range(6)}},'target':{'choice':'0','probabilities':{'0':1.0}}}}
  s=Snapshot('x','https://example.com',time.monotonic(),(Element('1','Docs','link',True),));p=e.prepare(s,'Open docs',('example.com',),time.monotonic(),'x');self.assertFalse(p.executed);self.assertTrue(p.needs_review);self.assertEqual(p.target_id,'1')
 def test_bridge_managed_commands_are_reviewed(self):
  from jarvis.ui_bridge import Bridge
  b=Bridge()
  for c in ('laya-setup','laya-load'):
   with self.assertRaises(ValueError):b.execute({'command':c})
  with patch.object(b.laya_setup,'start')as setup,patch.object(b.laya_engine,'load')as load:
   b.execute({'command':'laya-check'});setup.assert_called_with(consent=False,check=True)
   b.execute({'command':'laya-setup','consent':True});setup.assert_called_with(consent=True,check=False)
   b.execute({'command':'laya-load','consent':True});load.assert_called_with(consent=True)
  b.execute({'command':'laya-cancel'});self.assertIsNone(b.browser_pending);b.close()
 def test_native_setup_commands_allowed(self):
  from pathlib import Path
  s=(Path(__file__).parents[1]/'modern-ui/src-tauri/src/main.rs').read_text().split('.contains(&command)')[0]
  for c in ('laya-setup','laya-check','laya-load','laya-cancel'):self.assertIn('"'+c+'"',s)
