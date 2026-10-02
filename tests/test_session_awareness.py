import unittest
from jarvis.experimental.session_awareness import SessionAwareness
class AwarenessTests(unittest.TestCase):
 def setUp(self):self.now=100.;self.a=SessionAwareness(lambda:self.now)
 def test_off_default(self):self.assertFalse(self.a.enabled);self.now=10000;self.assertIsNone(self.a.poll())
 def test_consent(self):
  for c in (False,None,'yes',1):
   with self.assertRaises(ValueError):self.a.start('gaming',c)
  self.assertFalse(self.a.enabled)
 def test_scope(self):
  for act in ('detected game','camera','unknown'):
   with self.assertRaises(ValueError):self.a.start(act,True)
  for interval in (True,14,181,30.5):
   with self.assertRaises(ValueError):self.a.start('gaming',True,interval)
 def test_timer_once_per_interval(self):
  self.a.start('gaming',True);self.now=1899;self.assertIsNone(self.a.poll());self.now=1900;n=self.a.poll();self.assertIn('30minutes',n.text);self.assertIn('marked',n.text);self.assertFalse(n.observed_screen);self.assertFalse(n.spoken);self.assertIsNone(self.a.poll());self.now=3700;self.assertIsNotNone(self.a.poll())
 def test_quiet_busy_defer(self):
  self.a.start('working',True);self.now=1900;self.assertIsNone(self.a.poll(quiet=True));self.assertIsNone(self.a.poll(busy=True));self.assertIsNotNone(self.a.poll())
 def test_stop_clear(self):
  self.a.start('gaming',True);self.a.stop();self.assertFalse(self.a.enabled);self.assertEqual(self.a.activity,'');self.assertIsNone(self.a.started);self.now=10000;self.assertIsNone(self.a.poll())
 def test_clock_reset_stops(self):
  self.a.start('gaming',True);self.now=50;self.assertIsNone(self.a.poll());self.assertFalse(self.a.enabled)
 def test_bad_clock(self):
  for t in (float('nan'),float('inf'),-1,True):
   self.now=t
   with self.assertRaises(ValueError):self.a.start('gaming',True)
 def test_no_hallucinated_results(self):
  self.a.start('watching videos',True,15);self.now=1000;n=self.a.poll();self.assertIn('cannot see',n.text);self.assertNotIn('lost',n.text);self.assertEqual(n.source,'user-declared activity + elapsed timer')
