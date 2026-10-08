import unittest
from jarvis.desktop_controller import DesktopController
from test_desktop_engine import Adapter
class Tests(unittest.TestCase):
 def setUp(self):self.a=Adapter();self.a.windows=lambda:[dict(self.a.target)];self.c=DesktopController(self.a)
 def test_current_observed_target_and_review(self):
  with self.assertRaises(ValueError):self.c.discover(False)
  with self.assertRaises(ValueError):self.c.prepare(self.a.target,[{'action':'move','x':10,'y':10}],'fixture')
  self.c.discover(True);r=self.c.prepare(self.a.target,[{'action':'move','x':10,'y':10}],'fixture');self.c.run(r,True,True).join();self.assertEqual(self.c.snapshot()['task']['completed_steps'],1)
 def test_stop_revokes_pending_and_next_run(self):
  self.c.discover(True);r=self.c.prepare(self.a.target,[{'action':'move','x':1,'y':1}],'fixture');self.c.stop()
  with self.assertRaises(ValueError):self.c.run(r,True,True)
 def test_long_typing_stop_per_character(self):
  self.c.discover(True);r=self.c.prepare(self.a.target,[{'action':'type','text':'abcdef'}],'fixture');self.a.hook=self.c.stop;self.c.run(r,True,True).join();self.assertEqual(len(self.a.inputs),1);self.assertEqual(self.c.snapshot()['task']['state'],'stopped')
