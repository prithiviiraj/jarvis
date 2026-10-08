import tempfile,pathlib,types,unittest,copy
from jarvis.drive_text import DriveText
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.conn=types.SimpleNamespace(account='owner@example.invalid',busy=False,generation=0,tokens=types.SimpleNamespace(access=lambda a,s:'fixture'));self.calls=[];self.created=None;self.shared=False
  def transport(m,u,p):
   self.calls.append((m,u,p))
   base={'ownedByMe':True,'shared':self.shared,'trashed':False,'owners':[{'emailAddress':self.conn.account}],'permissions':[{'type':'user','role':'owner','emailAddress':self.conn.account}]}
   if '/root?'in u:return {**base,'id':'root_fixture','mimeType':'application/vnd.google-apps.folder','capabilities':{'canAddChildren':True}}
   if '/generateIds?'in u:return {'ids':['file_fixture']}
   if m=='POST':self.created={**base,'id':p['file_id'],'name':p['name'],'mimeType':'text/plain','parents':[p['root_id']],'size':str(p['bytes']),'md5Checksum':p['md5'],'sha256Checksum':p['sha256'],'webViewLink':'https://example.invalid/fixture'}
   return copy.deepcopy(self.created)
  self.transport=transport;self.a=DriveText(self.conn,pathlib.Path(self.tmp.name)/'ledger.json',transport,lambda t:{'email_verified':True,'email':self.conn.account})
 def tearDown(self):self.a.stop();self.tmp.cleanup()
 def prepare(self):self.a.prepare('exact.txt','Exact reviewed text',True);self.a.worker.join(3);self.assertFalse(self.a.error);return self.a.snapshot()['plan']
 def test_exact_create_checksum_visibility_restart(self):
  r=self.prepare();self.assertFalse(any(x[0]=='POST'for x in self.calls))
  with self.assertRaises(ValueError):self.a.submit(r)
  self.a.submit(r,True);self.a.worker.join(3);self.assertEqual(self.a.snapshot()['state'],'completed');self.assertEqual(len([x for x in self.calls if x[0]=='POST']),1);self.assertEqual(DriveText(self.conn,self.a.path).snapshot()['state'],'completed');self.assertIn('ignoreDefaultVisibility=true',[u for m,u,p in self.calls if m=='POST'][0])
 def test_shared_root_refused(self):
  self.shared=True;self.a.prepare('exact.txt','text',True);self.a.worker.join(3);self.assertTrue(self.a.error);self.assertFalse(any(x[0]=='POST'for x in self.calls))
 def test_permission_changed_before_submit_blocks(self):
  r=self.prepare();self.shared=True;self.a.submit(r,True);self.a.worker.join(3);self.assertEqual(self.a.snapshot()['state'],'review');self.assertFalse(any(x[0]=='POST'for x in self.calls))
 def test_uncertain_no_retry(self):
  r=self.prepare();old=self.a.transport
  def bad(m,u,p):
   if m=='POST':raise OSError('interrupted')
   return old(m,u,p)
  self.a.transport=bad;self.a.submit(r,True);self.a.worker.join(3);fresh=DriveText(self.conn,self.a.path);self.assertEqual(fresh.snapshot()['state'],'uncertain')
  with self.assertRaises(ValueError):fresh.prepare('a.txt','text',True)
 def test_scope_bounds_stop_expiry(self):
  with self.assertRaises(ValueError):self.a.prepare('a.txt','text')
  for name,text in [('../a.txt','text'),('a.txt',''),('a.txt','a'*8001)]:
   with self.assertRaises(ValueError):self.a.content(name,text)
  r=self.prepare();from unittest.mock import patch
  with patch('jarvis.drive_text.time.time',return_value=r['payload']['expires_at']+1):self.a.submit(r,True);self.a.worker.join(3)
  self.assertFalse(any(x[0]=='POST'for x in self.calls));self.a.stop()
  with self.assertRaises(ValueError):self.a.submit(r,True)
