import unittest,pathlib,tempfile,json
from jarvis.connector_journal import ConnectorJournal
from jarvis.connector_workflows import email_plan
class Tests(unittest.TestCase):
 def test_restart_during_transport_uncertain_no_repeat(self):
  with tempfile.TemporaryDirectory()as t:
   p=pathlib.Path(t)/'ledger.json';j=ConnectorJournal(p,'email');review=j.prepare(email_plan('owner@example.com',['friend@example.com'],'Subject','Body')['payload'])
   def transport(payload):
    restored=ConnectorJournal(p,'email');self.assertEqual(restored.job.state,'uncertain');raise TimeoutError()
   with self.assertRaises(ValueError):j.submit(review,True,lambda p:True,transport)
   restored=ConnectorJournal(p,'email');self.assertEqual(restored.job.state,'uncertain')
   with self.assertRaises(ValueError):restored.prepare(review['payload'])
   restored.reconcile(lambda p:{'verified':True,'external_id':'server-id'});self.assertEqual(ConnectorJournal(p,'email').job.state,'completed')
 def test_invalid_ledger_fails_closed(self):
  with tempfile.TemporaryDirectory()as t:
   p=pathlib.Path(t)/'ledger.json';p.write_text('{broken')
   with self.assertRaises(ValueError):ConnectorJournal(p,'email')
 def test_disk_failure_never_calls_transport(self):
  with tempfile.TemporaryDirectory()as t:
   j=ConnectorJournal(pathlib.Path(t)/'ledger.json','email');r=j.prepare(email_plan('owner@example.com',['friend@example.com'],'Subject','Body')['payload']);calls=[]
   def failure():raise OSError()
   j.save=failure
   with self.assertRaises(Exception):j.submit(r,True,lambda p:True,lambda p:calls.append(p))
   self.assertFalse(calls)
