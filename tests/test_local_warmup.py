import unittest,threading,tempfile,json
from unittest.mock import Mock,patch
from jarvis.brain_settings import BrainSettings
class LocalWarmup(unittest.TestCase):
 def test_no_implicit_request_and_consent_required(self):
  with patch('jarvis.brain_settings.local_models')as models:
   s=BrainSettings(store=Mock());models.assert_not_called()
   with self.assertRaises(ValueError):s.prewarm()
   models.assert_not_called()
 def test_fixed_local_request_no_keys_history_cloud(self):
  store=Mock();s=BrainSettings(store=store)
  with patch('jarvis.brain_settings.local_models',return_value=['fixture-model']),patch('jarvis.brain_settings.BrainRouter')as router:
   router.return_value.stream.return_value=iter([{'text':'Ready'}]);s.prewarm(True).join(2)
   p=router.call_args.args[0][0];self.assertFalse(p.cloud);self.assertEqual(p.model,'fixture-model')
   router.return_value.stream.assert_called_once_with([{'role':'user','content':'Say ready in one word.'}],cloud_consent=False,cancel=s.warmup_cancel)
   store.get.assert_not_called();self.assertEqual(s.checks['local-warmup']['state'],'ready');self.assertFalse(s.busy)
 def test_busy_local_gate_fails_without_inference(self):
  s=BrainSettings(store=Mock());s.local_gate=Mock();s.local_gate.acquire.return_value=False
  with patch('jarvis.brain_settings.local_models')as models:s.prewarm(True).join(2);models.assert_not_called()
  self.assertEqual(s.checks['local-warmup']['state'],'failed');s.local_gate.release.assert_not_called()
 def test_failure_does_not_fallback_and_releases_gate(self):
  s=BrainSettings(store=Mock())
  with patch('jarvis.brain_settings.local_models',side_effect=ValueError('No model')):s.prewarm(True).join(2)
  self.assertEqual(s.checks['local-warmup']['state'],'failed');self.assertTrue(s.local_gate.acquire(False));s.local_gate.release()
 def test_duplicate_warmups_coalesce(self):
  s=BrainSettings(store=Mock());entered=threading.Event();release=threading.Event()
  def models(**kw):entered.set();release.wait(2);return ['fixture']
  with patch('jarvis.brain_settings.local_models',side_effect=models),patch('jarvis.brain_settings.BrainRouter')as router:
   router.return_value.stream.return_value=iter([{'text':'Ready'}]);w=s.prewarm(True);entered.wait(1);self.assertIsNone(s.prewarm(True));release.set();w.join(2);router.return_value.stream.assert_called_once()

 def test_pause_cancels_without_ready(self):
  s=BrainSettings(store=Mock());entered=threading.Event();release=threading.Event()
  def stream(*args,**kw):
   entered.set();release.wait(2);yield {'text':'Ready'}
  with patch('jarvis.brain_settings.local_models',return_value=['fixture']),patch('jarvis.brain_settings.BrainRouter')as router:
   router.return_value.stream.side_effect=stream;w=s.prewarm(True);entered.wait(1);s.stop_warmup();release.set();w.join(2)
  self.assertEqual(s.checks['local-warmup']['state'],'cancelled')

 def test_shell_allows_reviewed_bridge_command(self):
  from pathlib import Path
  root=Path(__file__).resolve().parents[1]
  source=(root/'modern-ui/src-tauri/src/main.rs').read_text(encoding='utf-8')
  self.assertIn('"brain-warmup"',source.split('.contains(&command)')[0])
