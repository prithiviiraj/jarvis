import pathlib,tempfile,unittest
from jarvis.github_issue import GitHubIssue
from jarvis.project_connectors import ProjectConnectors
class Store:
 def get(self,k):return 'fixture-only-token'
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.projects=ProjectConnectors(Store(),lambda *a:{'login':'owner'});self.projects.accounts={'github':'owner'};self.calls=[];self.issue=None
  def transport(m,u,p,t):
   self.calls.append((m,u,p))
   if not '/issues'in u:return {'full_name':'owner/repo','has_issues':True,'archived':False}
   if m=='POST':self.issue={**p,'number':7,'html_url':'https://github.com/owner/repo/issues/7','user':{'login':'owner'}}
   return self.issue
  self.transport=transport;self.a=GitHubIssue(self.projects,pathlib.Path(self.tmp.name)/'issue.json',transport)
 def tearDown(self):self.a.stop();self.tmp.cleanup()
 def prepare(self):return self.a.prepare('owner','repo','Exact title','Exact body',True)
 def test_review_and_exact_readback(self):
  r=self.prepare();self.assertFalse(self.calls)
  with self.assertRaises(ValueError):self.a.submit(r)
  self.a.submit(r,True);self.a.worker.join(3);self.assertEqual(self.a.snapshot()['state'],'completed');self.assertEqual([x[0]for x in self.calls],['GET','POST','GET']);self.assertEqual(self.a.snapshot()['result']['url'],'https://github.com/owner/repo/issues/7')
  with self.assertRaisesRegex(ValueError,'already completed'):self.prepare()
 def test_separate_write_scope_and_identity_change(self):
  with self.assertRaises(ValueError):self.a.prepare('owner','repo','T','B')
  r=self.prepare();self.projects.accounts['github']='other';self.a.submit(r,True);self.a.worker.join(3);self.assertFalse(self.calls);self.assertEqual(self.a.snapshot()['state'],'review')
 def test_uncertain_restart_no_retry(self):
  def uncertain(m,*a):
   if m=='POST':raise OSError('network interrupted')
   return {'full_name':'owner/repo','has_issues':True,'archived':False}
  self.a.transport=uncertain;r=self.prepare();self.a.submit(r,True);self.a.worker.join(3);self.assertEqual(self.a.snapshot()['state'],'uncertain');fresh=GitHubIssue(self.projects,self.a.path,self.transport);self.assertEqual(fresh.snapshot()['state'],'uncertain')
  with self.assertRaises(ValueError):fresh.prepare('owner','repo','T','B',True)
 def test_wrong_readback_unverified(self):
  self.a.transport=lambda m,u,p,t:self.transport(m,u,p,t)if m!='GET'or '/issues/'not in u else {'title':'wrong'};r=self.prepare();self.a.submit(r,True);self.a.worker.join(3);self.assertEqual(self.a.snapshot()['state'],'uncertain')
 def test_stop_review_and_destination(self):
  r=self.prepare();self.a.stop()
  with self.assertRaises(ValueError):self.a.submit(r,True)
  with self.assertRaises(ValueError):self.a.request('POST','/repos/owner/repo/pulls','fixture')
 def test_expired_review_no_transport(self):
  from unittest.mock import patch
  r=self.prepare()
  with patch('jarvis.github_issue.time.time',return_value=r['payload']['expires_at']+1):self.a.submit(r,True);self.a.worker.join(3)
  self.assertEqual(self.a.snapshot()['state'],'review');self.assertFalse(self.calls)
