import unittest,tempfile,pathlib,base64,email
from jarvis.google_mail import GoogleMail
from jarvis.google_connection import GoogleConnection
from jarvis.google_tokens import GoogleTokens
from jarvis.google_oauth import SCOPES
from test_google_tokens import Store
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();t=GoogleTokens(Store(),lambda p:{'token_type':'Bearer','access_token':'fixture','expires_in':3600});t.save('owner@example.com','fixture.apps.googleusercontent.com','refresh',[SCOPES['mail-read'],SCOPES['mail-send']],True);self.c=GoogleConnection(t);self.c.account='owner@example.com';self.calls=[];self.sent=None
 def tearDown(self):self.temp.cleanup()
 def transport(self,method,url,payload):
  self.calls.append((method,url,payload))
  if url.endswith('/profile'):return {'emailAddress':'owner@example.com'}
  if 'messages?'in url:return {'messages':[]}
  if method=='POST':
   msg=email.message_from_bytes(base64.urlsafe_b64decode(payload['raw']+'='*(-len(payload['raw'])%4)),policy=email.policy.default);self.sent={'id':'sent-fixture','labelIds':['SENT'],'payload':{'mimeType':'text/plain','headers':[{'name':k,'value':str(msg[k])}for k in ('To','Subject','Message-ID')],'body':{'data':base64.urlsafe_b64encode(msg.get_content().encode()).decode()}}};return {'id':'sent-fixture','threadId':'thread'}
  return self.sent
 def job(self,transport=None):return GoogleMail(self.c,pathlib.Path(self.temp.name)/'ledger.json',transport or self.transport)
 def test_exact_send_and_readback_no_repeat(self):
  j=self.job();r=j.prepare(['friend@example.com'],'Subject','Exact body');j.submit(r,True);j.worker.join(3);self.assertEqual(j.snapshot()['state'],'completed');self.assertEqual(sum(m=='POST'for m,u,p in self.calls),1)
  with self.assertRaises(ValueError):j.submit(r,True)
  restored=self.job();self.assertEqual(restored.snapshot()['state'],'completed')
 def test_no_review_or_changed_review_no_send(self):
  j=self.job();r=j.prepare(['friend@example.com'],'Subject','Body')
  with self.assertRaises(ValueError):j.submit(r)
  changed=dict(r,sha256='changed')
  with self.assertRaises(ValueError):j.submit(changed,True)
  self.assertFalse(self.calls)
 def test_partial_history_blocks_before_post(self):
  def transport(m,u,p):return {'emailAddress':'owner@example.com'}if u.endswith('/profile')else{'messages':[],'nextPageToken':'partial'}
  j=self.job(transport);r=j.prepare(['friend@example.com'],'Subject','Body');j.submit(r,True);j.worker.join(3);self.assertEqual(j.snapshot()['state'],'review');self.assertIn('partial',j.error)
 def test_timeout_persists_uncertainty_no_retry_or_empty_reconcile(self):
  def transport(m,u,p):
   if m=='POST':raise TimeoutError('private error')
   return self.transport(m,u,p)
  j=self.job(transport);r=j.prepare(['friend@example.com'],'Subject','Body');j.submit(r,True);j.worker.join(3);self.assertEqual(j.snapshot()['state'],'uncertain');self.assertNotIn('private error',j.error);restored=self.job();restored.reconcile(True);restored.worker.join(3);self.assertEqual(restored.snapshot()['state'],'uncertain')
 def test_duplicate_blocks_and_stop_in_validation(self):
  duplicate={'id':'existing','labelIds':['SENT'],'payload':{'mimeType':'text/plain','headers':[{'name':'To','value':'friend@example.com'},{'name':'Subject','value':'Subject'}],'body':{'data':base64.urlsafe_b64encode(b'Body\n').decode()}}}
  def transport(m,u,p):
   if u.endswith('/profile'):return {'emailAddress':'owner@example.com'}
   if 'messages?'in u:return {'messages':[{'id':'existing'}]}
   return duplicate
  j=self.job(transport);r=j.prepare(['friend@example.com'],'Subject','Body');j.submit(r,True);j.worker.join(3);self.assertEqual(j.snapshot()['state'],'review');self.assertIn('already sent',j.error)
  import threading
  entered=threading.Event();release=threading.Event()
  def blocked(m,u,p):
   if u.endswith('/profile'):entered.set();release.wait(2)
   return self.transport(m,u,p)
  j=self.job(blocked);j.stop();r=j.prepare(['friend@example.com'],'Different','Body');j.submit(r,True);self.assertTrue(entered.wait(1));j.stop();release.set();j.worker.join(3);self.assertFalse(any(m=='POST'for m,u,p in self.calls));self.assertEqual(j.snapshot()['state'],'cancelled')
