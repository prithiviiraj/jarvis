import unittest,tempfile,pathlib
from jarvis.telegram_connection import TelegramConnection,TOKEN_SLOT
from jarvis.telegram_output import TelegramOutput
from test_google_tokens import Store
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=pathlib.Path(self.tmp.name)/'ledger.json';self.calls=[];store=Store();store.set(TOKEN_SLOT,'123456:'+('a'*30))
  self.c=TelegramConnection(store,self.read);self.c.bot={'id':123456,'username':'fixture_bot'};self.c.pair.bound={'chat_id':77,'user_id':77,'username':'fixture_user','display_name':'Fixture'}
 def tearDown(self):self.tmp.cleanup()
 def read(self,m,p):return {'ok':True,'result':{'id':123456,'username':'fixture_bot','is_bot':True}if m=='getMe'else {'url':''}if m=='getWebhookInfo'else {'id':77,'type':'private','username':'fixture_user','first_name':'Fixture'}}
 def send(self,m,p):self.calls.append((m,p));return {'message_id':12,'chat':{'id':77,'type':'private'},'text':p['text']}
 def job(self,send=None):return TelegramOutput(self.c,self.path,send or self.send)
 def test_exact_review_result_and_restart_no_retry(self):
  j=self.job();r=j.prepare('Exact $50 and "words"');self.assertFalse(self.calls)
  with self.assertRaises(ValueError):j.submit(r)
  with self.assertRaises(ValueError):j.submit(dict(r,sha256='changed'),True)
  j.submit(r,True);j.worker.join(2);self.assertEqual(j.snapshot()['state'],'completed');self.assertFalse(self.calls[0][1]['allow_paid_broadcast']);self.assertEqual(self.calls[0][1]['text'],'Exact $50 and "words"');self.assertEqual(self.job().snapshot()['state'],'completed')
  with self.assertRaises(ValueError):self.job().submit(r,True)
 def test_timeout_remains_uncertain_across_stop_restart(self):
  def fail(*a):raise TimeoutError()
  j=self.job(fail);r=j.prepare('Words');j.submit(r,True);j.worker.join(2);self.assertEqual(j.snapshot()['state'],'uncertain');j.stop();j=self.job();self.assertEqual(j.snapshot()['state'],'uncertain')
  with self.assertRaises(ValueError):j.prepare('Another')
  with self.assertRaises(ValueError):j.submit(r,True)
 def test_changed_destination_no_output(self):
  j=self.job();r=j.prepare('Words');self.c.transport=lambda m,p:{'ok':True,'result':{'type':'private','id':88}if m=='getChat'else self.read(m,p)['result']};j.submit(r,True);j.worker.join(2);self.assertFalse(self.calls);self.assertEqual(j.snapshot()['state'],'review')
 def test_stop_during_verification_no_send(self):
  j=self.job();r=j.prepare('Words');old=self.c.transport
  def stopped(m,p):j.stop();return old(m,p)
  self.c.transport=stopped;j.submit(r,True);j.worker.join(2);self.assertFalse(self.calls);self.assertEqual(j.snapshot()['state'],'cancelled')
 def test_unverified_sent_result_blocks_retry(self):
  j=self.job(lambda *a:{'message_id':12,'chat':{'id':88,'type':'private'},'text':'Wrong'});r=j.prepare('Words');j.submit(r,True);j.worker.join(2);self.assertEqual(j.snapshot()['state'],'uncertain')
 def test_completed_exact_duplicate_rejected(self):
  j=self.job();r=j.prepare('Words');j.submit(r,True);j.worker.join(2)
  with self.assertRaises(ValueError):self.job().prepare('Words')
