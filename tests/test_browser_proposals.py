import unittest
from dataclasses import replace
from jarvis.experimental.browser_proposals import *
class ProposalTests(unittest.TestCase):
 def setUp(self):
  self.s=Snapshot('page1','https://www.youtube.com/results?secret=query',100,(Element('search','Search','button',True),Element('password','SECRET','textbox',True,sensitive=True),Element('disabled','disabled','button',True,disabled=True)))
  self.hosts=('www.youtube.com',)
 def answer(self,choice='0',target='0'):
  p={str(i):float(str(i)==choice) for i in range(6)};return {'answers':{'operation':{'choice':choice,'probabilities':p},'target':{'choice':target,'probabilities':{'0':1.}}}}
 def run_proposal(self,s=None,response=None,now=101,current='page1'):
  return propose(s or self.s,'Search a comedy video',self.hosts,now,response or self.answer(),current)
 def test_proposal_no_execution(self):
  p=self.run_proposal();self.assertEqual(p.target_id,'search');self.assertTrue(p.needs_review);self.assertFalse(p.executed)
 def test_model_state_minimized(self):
  r=request(self.s,'search',self.hosts,101);self.assertEqual(r['state'],{'page':{'host':'www.youtube.com'}});self.assertNotIn('SECRET',str(r));self.assertNotIn('secret=query',str(r));self.assertEqual(set(r['questions']['target']['criteria']),{'0'})
 def test_changed_page(self):
  with self.assertRaises(ProposalError):self.run_proposal(current='page2')
 def test_stale_future(self):
  for now in (99,116,float('nan')):
   with self.assertRaises(ProposalError):self.run_proposal(now=now)
 def test_host_scheme_credentials(self):
  for u in ('https://youtube.com.evil.test','http://www.youtube.com','https://x:y@www.youtube.com','https://www.youtube.com:444'):
   with self.assertRaises(ProposalError):self.run_proposal(replace(self.s,url=u))
 def test_duplicates_and_oversize(self):
  for es in ((self.s.elements[0],)*2,tuple(Element(str(i),'x','button') for i in range(21))):
   with self.assertRaises(ProposalError):self.run_proposal(replace(self.s,elements=es))
 def test_unobserved_disabled_sensitive_target(self):
  for i in ('1','2','99',"document.cookie"):
   with self.assertRaises(ProposalError):self.run_proposal(response=self.answer(target=i))
 def test_type_write_not_offered(self):
  r=self.answer();r['answers']['operation']['choice']='TYPE_TEXT'
  with self.assertRaises(ProposalError):self.run_proposal(response=r)
 def test_bad_distribution(self):
  for value in (True,float('inf'),-.1,2):
   r=self.answer();r['answers']['operation']['probabilities']['0']=value
   with self.assertRaises(ProposalError):self.run_proposal(response=r)
 def test_low_confidence(self):
  r=self.answer();r['answers']['operation']['probabilities']={'0':.6,'1':.4,**{str(i):0. for i in range(2,6)}}
  with self.assertRaises(ProposalError):self.run_proposal(response=r)
 def test_injected_extra_field(self):
  r=self.answer();r['answers']['operation']['execute']='send private data'
  with self.assertRaises(ProposalError):self.run_proposal(response=r)
 def test_done_not_completion(self):
  p=self.run_proposal(response=self.answer('4'));self.assertEqual(p.operation,'DONE');self.assertTrue(p.needs_review);self.assertFalse(p.executed)
