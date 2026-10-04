import unittest,sys,pathlib
from types import SimpleNamespace
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]/'src'))
from jarvis.experimental.browser_gate import ReadScope,gate
class PolicyGate(unittest.TestCase):
 def proposal(self,op='CLICK',target='1'):return SimpleNamespace(operation=op,target_id=target,executed=False,needs_review=True)
 def test_high_confidence_missing_target_and_loading_refused(self):
  for s in (ReadScope('Read docs',('CLICK',),True,()),ReadScope('Read docs',('CLICK',),False,('1',))):
   with self.assertRaises(ValueError):gate(s,self.proposal())
 def test_outside_scope_is_never_permission(self):
  with self.assertRaises(ValueError):gate(ReadScope('Read docs',('WAIT',),True,('1',)),self.proposal())
  with self.assertRaises(ValueError):gate(ReadScope('Pay stranger',('PAY',),True,()),self.proposal('PAY',None))
  with self.assertRaises(ValueError):gate(ReadScope('Read docs',('CLICK',),True,('1',)),self.proposal('DONE',None))
 def test_valid_link_is_review_only(self):
  r=gate(ReadScope('Read docs',('CLICK',),True,('1',)),self.proposal());self.assertTrue(r['needs_review']);self.assertFalse(r['executed'])
 def test_claimed_execution_and_review_bypass_refused(self):
  for f in ('executed','needs_review'):
   p=self.proposal();setattr(p,f,f=='executed')
   with self.assertRaises(ValueError):gate(ReadScope('Read docs',('CLICK',),True,('1',)),p)
