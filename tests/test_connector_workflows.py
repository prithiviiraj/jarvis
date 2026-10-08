import unittest
from jarvis.connector_workflows import email_plan,duplicate_warning,ReviewedEffect
class Tests(unittest.TestCase):
 def setUp(self):self.mail=email_plan('owner@example.com',['friend@example.com'],'Hello','Exact final words')
 def test_bad_recipient_header_and_attachment(self):
  for recipient in ('Sam','Sam <a@example.com>','a@example.com\nBcc: x@example.com'):
   with self.assertRaises(ValueError):email_plan('owner@example.com',[recipient],'Hi','body')
  with self.assertRaises(ValueError):email_plan('owner@example.com',['a@example.com'],'Hi','body',attachments=['file.pdf'])
 def test_exact_duplicate_only_same_account_and_sent(self):
  row=dict(self.mail['payload'],message_id='real-id',state='sent',sent_at='fixture');h={'account':'owner@example.com','complete':False,'messages':[row]};self.assertEqual(len(duplicate_warning(self.mail,h)['matches']),1);self.assertFalse(duplicate_warning(self.mail,h)['complete']);row['body']='different';self.assertEqual(duplicate_warning(self.mail,h)['matches'],[])
 def test_review_change_and_live_denial(self):
  job=ReviewedEffect('email');r=job.prepare(self.mail['payload']);changed=dict(r,sha256='fake')
  with self.assertRaises(ValueError):job.submit(changed,True,lambda p:True,lambda p:{})
  with self.assertRaises(ValueError):job.submit(r,True,lambda p:False,lambda p:{})
  self.assertEqual(job.state,'review')
 def test_timeout_never_auto_retry_or_reprepare(self):
  job=ReviewedEffect('email');r=job.prepare(self.mail['payload'])
  def timeout(p):raise TimeoutError()
  with self.assertRaises(ValueError):job.submit(r,True,lambda p:True,timeout)
  self.assertEqual(job.state,'uncertain')
  with self.assertRaises(ValueError):job.prepare(self.mail['payload'])
  with self.assertRaises(ValueError):job.reconcile(lambda p:{'verified':True})
  job.reconcile(lambda p:{'verified':True,'external_id':'sent-id'});self.assertEqual(job.state,'completed')
 def test_stop_during_transport_requires_reconcile(self):
  job=ReviewedEffect('email');r=job.prepare(self.mail['payload'])
  def transport(p):job.cancel();return {'verified':True,'external_id':'maybe-id'}
  with self.assertRaises(ValueError):job.submit(r,True,lambda p:True,transport)
  self.assertEqual(job.state,'uncertain')
 def test_success_has_server_id_and_cannot_repeat(self):
  job=ReviewedEffect('email');r=job.prepare(self.mail['payload']);out=job.submit(r,True,lambda p:True,lambda p:{'verified':True,'external_id':'real-id'});self.assertEqual(out['external_id'],'real-id')
  with self.assertRaises(ValueError):job.submit(r,True,lambda p:True,lambda p:{})
