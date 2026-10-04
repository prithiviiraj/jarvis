import unittest,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]/'src'))
from jarvis.experimental.browser_proposals import *
class Criteria(unittest.TestCase):
 def test_meaningful_choices_and_safe_state(self):
  s=Snapshot('s','https://example.com/private?q=secret',1,(Element('1','Learn more','link',True),Element('2','Password value','input',True,sensitive=True)))
  q=request(s,'Read example documentation',{'example.com'},2);self.assertIn('observed state',q['questions']['operation']['criteria']['4']);self.assertEqual(q['state']['observed_safe_targets'],[{'label':'Learn more','role':'link'}]);self.assertNotIn('secret',str(q));self.assertNotIn('Password value',str(q))
 def test_selected_meaning_maps_to_known_enum_only(self):
  s=Snapshot('s','https://example.com',1,());r={'answers':{'operation':{'choice':'3','probabilities':{str(i):1.0 if i==3 else 0.0 for i in range(6)}}}}
  p=propose(s,'Wait safely',{'example.com'},2,r,'s');self.assertEqual(p.operation,'WAIT');self.assertFalse(p.executed);self.assertTrue(p.needs_review)
