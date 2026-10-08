import unittest,threading
from jarvis.google_queries import GoogleQueries
from jarvis.google_tokens import GoogleTokens
from jarvis.google_connection import GoogleConnection
from jarvis.google_oauth import SCOPES
from test_google_tokens import Store
class Tests(unittest.TestCase):
 def fixture(self,transport):
  t=GoogleTokens(Store());t.save('owner@example.com','fixture.apps.googleusercontent.com','fixture-refresh',[SCOPES['mail-read']],True);c=GoogleConnection(t);c.account='owner@example.com';return GoogleQueries(c,transport)
 def test_list_exact_account_and_message_snippet(self):
  calls=[]
  def transport(method,url,payload):
   calls.append((method,url,payload))
   if url.endswith('/profile'):return {'emailAddress':'owner@example.com'}
   if '?format=full'in url:return {'id':'observed','snippet':'external text','payload':{'headers':[{'name':'Subject','value':'untrusted'},{'name':'Hidden','value':'ignored'}]}}
   return {'messages':[{'id':'observed','threadId':'thread'}],'nextPageToken':'partial'}
  q=self.fixture(transport);q.start('gmail-list',{'query':'in:inbox'},True);q.worker.join(2);self.assertFalse(q.error);self.assertFalse(q.result['complete']);q.start('gmail-message',{'message_id':'observed','_observed_ids':['observed']},True);q.worker.join(2);self.assertEqual(q.result['snippet'],'external text');self.assertEqual(len(q.result['headers']),1);self.assertTrue(all(x[0]=='GET'for x in calls))
 def test_wrong_account_and_unobserved_id(self):
  q=self.fixture(lambda *a:{'emailAddress':'other@example.com'});q.start('gmail-list',{},True);q.worker.join(2);self.assertTrue(q.error);self.assertIsNone(q.result)
  q=self.fixture(lambda *a:{});q.start('gmail-message',{'message_id':'guessed'},True);q.worker.join(2);self.assertTrue(q.error)
 def test_stop_suppresses_late_result(self):
  entered=threading.Event();release=threading.Event()
  def transport(*a):entered.set();release.wait(2);return {'emailAddress':'owner@example.com','messages':[]}
  q=self.fixture(transport);q.start('gmail-list',{},True);self.assertTrue(entered.wait(1));q.stop();release.set();q.worker.join(2);self.assertIsNone(q.result)
 def test_no_implicit_read(self):
  q=self.fixture(lambda *a:{})
  with self.assertRaises(ValueError):q.start('gmail-list',{})
  self.assertIsNone(q.worker)

 def test_calendar_result_and_account_switch_suppresses_late(self):
  def transport(method,url,payload):return {'calendars':{'primary':{'busy':[{'start':'2026-10-08T15:00:00+05:30','end':'2026-10-08T15:30:00+05:30'}]}}}
  q=self.fixture(transport);q.start('calendar-freebusy',{'calendar_ids':['primary'],'start':'2026-10-08T15:00:00+05:30','end':'2026-10-08T16:00:00+05:30'},True);q.worker.join(2);self.assertFalse(q.error);self.assertTrue(q.result['complete']);self.assertEqual(len(q.result['calendars']['primary']),1)
  entered=threading.Event();release=threading.Event()
  def blocked(*a):entered.set();release.wait(2);return {'emailAddress':'owner@example.com','messages':[]}
  q=self.fixture(blocked);q.start('gmail-list',{},True);self.assertTrue(entered.wait(1));q.connection.stop();release.set();q.worker.join(2);self.assertIsNone(q.result)
