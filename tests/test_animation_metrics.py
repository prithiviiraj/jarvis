import unittest
from jarvis.experimental.animation_metrics import summarize,percentile
class AnimationMetricsTests(unittest.TestCase):
 def test_exact_rate(self):
  m=summarize([0,.02,.04,.06],[.001]*4)
  self.assertAlmostEqual(m['callback_rate_hz'],50);self.assertAlmostEqual(m['interval_ms']['p50'],20);self.assertEqual(m['interval_over_16_667_ms_pct'],100);self.assertFalse(m['display_fps_measured'])
 def test_slow_tail(self):
  m=summarize([0,.016,.032,.082],[0,.001,.002,.003]);self.assertAlmostEqual(m['interval_ms']['max'],50);self.assertAlmostEqual(m['interval_over_33_333_ms_pct'],100/3)
 def test_interpolation(self):self.assertEqual(percentile([4,1,2,3],.5),2.5)
 def test_invalid_samples(self):
  for a,b in [([0,1],[0,0]),([0,1,2],[0]),([0,0,2],[0]*3),([0,2,1],[0]*3),([0,1,float('inf')],[0]*3),([0,1,True],[0]*3),([0,1,2],[0,-1,0])]:
   with self.assertRaises(ValueError):summarize(a,b)
