import unittest,threading
from unittest.mock import patch,Mock
from jarvis.local_speed import LocalSpeed,PROMPTS
class LocalSpeedTests(unittest.TestCase):
 def test_review_no_requests(self):
  with patch('jarvis.local_speed.local_models')as models:
   with self.assertRaises(ValueError):LocalSpeed().start()
   models.assert_not_called()
 def test_three_local_fixed_prompts_no_storage(self):
  router=Mock();router.stream.side_effect=lambda *a,**k:iter([{'text':'ready'}]);router.last_diagnostics=[{'usage':{'prompt_tokens':10,'completion_tokens':1}}]
  with patch('jarvis.local_speed.local_models',return_value=['fixture']),patch('jarvis.local_speed.BrainRouter',return_value=router)as factory:
   s=LocalSpeed();s.start(consent=True).join(1);self.assertEqual(len(s.rows),3);self.assertFalse(s.busy);self.assertFalse(factory.call_args.args[0][0].cloud);self.assertNotIn('ready',str(s.rows));self.assertEqual([c.args[0][0]['content']for c in router.stream.call_args_list],[x[1]for x in PROMPTS]);self.assertIn('not pure prefill',s.snapshot()['scope'])
 def test_one_model_required(self):
  with patch('jarvis.local_speed.local_models',return_value=['a','b']),patch('jarvis.local_speed.BrainRouter')as router:
   s=LocalSpeed();s.start(consent=True).join(1);router.assert_not_called();self.assertIn('exactly one',s.error)
 def test_shared_local_gate(self):
  gate=Mock();gate.acquire.return_value=False
  with patch('jarvis.local_speed.local_models')as models:
   s=LocalSpeed(gate);s.start(consent=True).join(1);models.assert_not_called();gate.release.assert_not_called();self.assertIn('busy',s.error)
 def test_empty_refuses_timing(self):
  router=Mock();router.stream.return_value=iter([])
  with patch('jarvis.local_speed.local_models',return_value=['fixture']),patch('jarvis.local_speed.BrainRouter',return_value=router):
   s=LocalSpeed();s.start(consent=True).join(1);self.assertEqual(s.rows,[]);self.assertIn('no usable',s.error)
 def test_bridge_native_boundary(self):
  from jarvis.ui_bridge import Bridge
  from pathlib import Path
  b=Bridge()
  with self.assertRaises(ValueError):b.execute({'command':'local-speed'})
  with patch.object(b.local_speed,'start')as start:b.execute({'command':'local-speed','consent':True});start.assert_called_once_with(consent=True)
  self.assertIn('local_speed',b.execute({'command':'status'}));b.close()
  s=(Path(__file__).parents[1]/'modern-ui/src-tauri/src/main.rs').read_text().split('.contains(&command)')[0]
  self.assertIn('"local-speed"',s);self.assertIn('"local-speed-stop"',s)
 def test_limit_warning_not_error_banner(self):
  from jarvis.ui_bridge import Bridge
  b=Bridge();b.voice.events.put(('error','Reply reached the completion limit and may be incomplete.'));d=b.execute({'command':'status'});self.assertEqual(d['error'],'');self.assertIn('completion limit',d['warning']);b.close()
