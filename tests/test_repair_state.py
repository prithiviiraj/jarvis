import unittest
from jarvis.repair_state import repair_state
class RepairStateTests(unittest.TestCase):
 def test_no_errors_has_no_invented_repairs(self):self.assertEqual(repair_state({})['options'],[])
 def test_only_live_failure_has_retry(self):
  self.assertEqual(repair_state({'game':{'analysis_error':'stale','enabled':False}})['options'],[])
  options=repair_state({'game':{'analysis_error':'Invalid JSON twice','enabled':True}})['options'];self.assertEqual(options[0]['kind'],'game-retry');self.assertEqual(options[0]['reason'],'Invalid JSON twice')
 def test_camera_help_is_not_permission(self):
  options=repair_state({'awareness':{'camera':'error','camera_master_status':'Device blocked'}})['options'];self.assertEqual(options[0]['reason'],'Device blocked');self.assertNotIn('consent',options[0])
 def test_missing_voice_check_never_downloads(self):
  options=repair_state({'voice_setup':{'checked':True,'ready':False,'status':'missing'}})['options'];self.assertEqual(options[0]['kind'],'voice-check');self.assertIn('No microphone or download',options[0]['scope'])
