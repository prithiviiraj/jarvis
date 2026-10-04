import unittest
from jarvis.local_awareness import LocalContext
class Durations(unittest.TestCase):
 def test_ram_observed_duration_reset(self):
  now=[0];c=LocalContext(clock=lambda:now[0]);c.camera_state('on');c.presence_event('present');now[0]=100
  self.assertEqual(c.snapshot()['durations']['presence_state_seconds'],100)
  c.presence_event('absent');now[0]=400;c.presence_event('present');self.assertEqual(c.snapshot()['durations']['last_observed_absence_seconds'],300)
  c.set_apps(True);c.app_event({'process':'maya.exe'});now[0]=500;self.assertEqual(c.snapshot()['durations']['foreground_seconds'],100)
  c.clear();d=c.snapshot()['durations'];self.assertIsNone(d['foreground_seconds']);self.assertIsNone(d['last_observed_absence_seconds']);self.assertIsNone(d['presence_state_seconds'])
