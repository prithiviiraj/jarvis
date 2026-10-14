import unittest
from jarvis.runtime_diagnostics import measurements
class RuntimeDiagnostics(unittest.TestCase):
 def test_numeric_stage_split_and_independent_gpu_evidence(self):
  x=measurements('offloaded 34/35 layers to GPU\nCLIP using CPU backend\nimage slice encoded in 82047 ms\nimage decoded (batch 1/2) in 945 ms\nimage processed in 83813 ms\nprompt eval time = 83820.2 ms\neval time = 7000 ms')
  self.assertTrue(x['gpu_offload_confirmed']);self.assertFalse(x['projector_gpu_confirmed']);self.assertEqual(x['image_encoding_ms'],[82047.]);self.assertEqual(x['image_decoding_ms'],[945.]);self.assertEqual(x['image_processing_ms'],[83813.]);self.assertEqual(len(x['text_timings']),2)
 def test_missing_evidence_is_not_gpu_claim(self):
  x=measurements('server loaded. api-key fixture-secret. path /private/file')
  self.assertFalse(x['gpu_offload_confirmed']);self.assertFalse(x['projector_gpu_confirmed']);self.assertEqual(x['projector_backends'],[]);self.assertNotIn('fixture-secret',str(x));self.assertNotIn('/private',str(x))
 def test_untrusted_backend_prose_never_retained(self):
  self.assertEqual(measurements('CLIP using secret-data backend')['projector_backends'],[])
  self.assertTrue(measurements('CLIP using Vulkan0 backend')['projector_gpu_confirmed'])
 def test_zero_layers_is_not_offload(self):
  self.assertFalse(measurements('offloaded 0/35 layers to GPU')['gpu_offload_confirmed'])

 def test_diagnostic_only_spawn_retains_image_floor_and_gpu_policy(self):
  from jarvis.runtime_diagnostics import MeasuredImageProfile
  from unittest.mock import Mock
  original=['llama-server.exe','--n-gpu-layers','auto','--fit','on','--ctx-size','8192'];spawn=Mock()
  MeasuredImageProfile(spawn)(original,cwd='fixture')
  args=spawn.call_args.args[0];self.assertEqual(args[:len(original)],original);self.assertEqual(args[args.index('--image-min-tokens')+1],'1024');self.assertEqual(args[args.index('--log-verbosity')+1],'5');self.assertNotIn('--no-mmproj-offload',args);self.assertNotIn('--image-min-tokens',original)
  with self.assertRaises(ValueError):MeasuredImageProfile(spawn)(original+['--verbosity','3'])
 def test_nonfinite_log_number_not_reported(self):
  self.assertEqual(measurements('image slice encoded in '+('9'*400)+' ms')['image_encoding_ms'],[])
 def test_malformed_timing_rows_do_not_break_closeout(self):
  raw='image slice encoded in 1.2.3 ms\nimage processed in .. ms\nimage decoded (batch 1/2) in 9.1.0 ms\nprompt eval time = 3.4.5 ms\neval time = 12.5 ms'
  x=measurements(raw);self.assertEqual(x['image_encoding_ms'],[]);self.assertEqual(x['image_processing_ms'],[]);self.assertEqual(x['image_decoding_ms'],[]);self.assertEqual(x['text_timings'],[{'stage':'eval','ms':12.5}])
 def test_all_logging_and_image_policy_aliases_refused(self):
  from jarvis.runtime_diagnostics import MeasuredImageProfile
  from unittest.mock import Mock
  for flag in ('--verbose','--log-verbose','-v','--verbosity','--log-verbosity','-lv','--image-min-tokens','--image-max-tokens','--mtmd-batch-max-tokens'):
   spawn=Mock()
   with self.subTest(flag=flag),self.assertRaises(ValueError):MeasuredImageProfile(spawn)(['llama-server.exe',flag,'1'])
   spawn.assert_not_called()
