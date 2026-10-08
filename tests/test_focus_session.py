import unittest
from jarvis.focus_session import FocusSession
class Tests(unittest.TestCase):
 def setUp(self):self.now=0;self.f=FocusSession(lambda:self.now)
 def start(self):r=self.f.prepare('Read one chapter',25);self.f.start(r,True)
 def test_inert_exact_review(self):
  self.assertEqual(self.f.snapshot()['state'],'off');r=self.f.prepare('Goal',5)
  with self.assertRaises(ValueError):self.f.start(r)
  with self.assertRaises(ValueError):self.f.start({'payload':{'goal':'changed'}},True)
  self.assertEqual(self.f.snapshot()['state'],'review')
 def test_due_checkin_no_auto_action(self):
  self.start();self.now=1499;self.assertEqual(self.f.snapshot()['state'],'running');self.now=1500;row=self.f.snapshot();self.assertEqual(row['state'],'check-in');self.assertEqual(row['remaining_seconds'],0);self.assertIn('Read one chapter',row['message']);self.f.finish(True);self.assertTrue(self.f.history[0]['done'])
 def test_pause_resume_elapsed_and_stop(self):
  self.start();self.now=100;self.f.pause();self.now=900;self.assertEqual(self.f.snapshot()['remaining_seconds'],1400)
  with self.assertRaises(ValueError):self.f.resume()
  self.f.resume(True);self.now=1000;self.assertEqual(self.f.snapshot()['remaining_seconds'],1300);self.f.stop();self.assertEqual(self.f.state,'off');self.assertFalse(self.f.goal)
 def test_reject_invalid_and_running_replace(self):
  for goal,minutes in [('',25),('x\n',25),('x',0),('x',121),('x',True)]:
   with self.assertRaises(ValueError):self.f.prepare(goal,minutes)
  self.start()
  with self.assertRaises(ValueError):self.f.prepare('Other',10)
 def test_cancelled_review_cannot_start(self):
  r=self.f.prepare('Goal',5);self.f.stop()
  with self.assertRaises(ValueError):self.f.start(r,True)
