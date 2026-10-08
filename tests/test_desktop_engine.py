import unittest
from jarvis.desktop_engine import DesktopEngine,validate_steps
class Adapter:
 def __init__(self):self.target={'hwnd':1,'pid':10,'title':'Synthetic Notepad','width':640,'height':480};self.inputs=[];self.fg=1;self.hook=None
 def observe(self,h):return dict(self.target)
 def focus(self,h):pass
 def foreground(self):return self.fg
 def perform(self,target,row):
  self.inputs.append(row)
  if self.hook:self.hook()
class Tests(unittest.TestCase):
 def setUp(self):self.a=Adapter();self.e=DesktopEngine(self.a)
 def plan(self):return self.e.prepare(self.a.target,[{'action':'click','x':10,'y':10},{'action':'type','text':'Fixture text'}],'Synthetic Notepad editing only')
 def test_exact_review_and_foreground(self):
  r=self.plan();self.a.fg=20
  with self.assertRaises(ValueError):self.e.run(r,True,True)
  self.assertEqual(self.a.inputs,[])
 def test_changed_target_and_stop_before_next_step(self):
  r=self.plan();self.a.hook=self.e.stop;self.e.run(r,True,True);self.assertEqual(len(self.a.inputs),1);self.assertEqual(self.e.state,'stopped')
 def test_window_replaced_blocks_next_step(self):
  r=self.plan();self.a.hook=lambda:self.a.target.update(pid=99)
  with self.assertRaises(ValueError):self.e.run(r,True,True)
  self.assertEqual(len(self.a.inputs),1)
 def test_outside_control_keys_unapproved(self):
  for row in ({'action':'key','key':'enter'},{'action':'key','key':'ctrl+a'},{'action':'type','text':'\n'},{'action':'shell','text':'cmd'}):
   with self.assertRaises(ValueError):validate_steps([row])
  with self.assertRaises(ValueError):self.e.prepare(self.a.target,[{'action':'click','x':999,'y':1}],'fixture')
  r=self.plan()
  with self.assertRaises(ValueError):self.e.run(r,True,False)
 def test_no_completion_claim_and_no_repeat(self):
  r=self.plan();out=self.e.run(r,True,True);self.assertEqual(out['completed_steps'],2);self.assertIn('readback',out['result'])
  with self.assertRaises(ValueError):self.e.run(r,True,True)

 def test_typed_hotkey_metacharacters_are_literal(self):
  from jarvis.desktop_engine import literal_keys
  self.assertEqual(literal_keys('^a%f+~'),'{^}a{%}f{+}{~}')
