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

 def test_deadline_no_drift(self):
  from jarvis.orbs import next_frame_delay
  deadline,delay=next_frame_delay(0,.002)
  self.assertAlmostEqual(deadline,1/60);self.assertEqual(delay,14)
  second,delay=next_frame_delay(deadline,.018)
  self.assertAlmostEqual(second,2/60);self.assertEqual(delay,15)
 def test_deadline_missed_skips(self):
  from jarvis.orbs import next_frame_delay
  deadline,delay=next_frame_delay(0,1)
  self.assertAlmostEqual(deadline,1+1/60);self.assertGreaterEqual(delay,15)

 def test_easing_monotonic_and_bounded(self):
  from jarvis.orbs import ease
  x=21
  for _ in range(15):
   n=ease(x,28,1/60);self.assertGreater(n,x);self.assertLess(n,28);x=n
  self.assertGreater(x,27)
 def test_easing_time_independent(self):
  from jarvis.orbs import ease
  a=b=21
  for _ in range(6):a=ease(a,28,1/60)
  for _ in range(3):b=ease(b,28,1/30)
  self.assertAlmostEqual(a,b)
 def test_easing_reduced_and_clock(self):
  from jarvis.orbs import ease
  self.assertEqual(ease(21,28,.016,True),28);self.assertEqual(ease(21,28,-1),21)
