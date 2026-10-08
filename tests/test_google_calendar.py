import unittest,tempfile,pathlib
from jarvis.google_calendar import GoogleCalendar,plan
from jarvis.google_connection import GoogleConnection
from jarvis.google_tokens import GoogleTokens
from jarvis.google_oauth import SCOPES
from test_google_tokens import Store
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();t=GoogleTokens(Store(),lambda p:{'access_token':'fixture','token_type':'Bearer','expires_in':3600});t.save('owner@example.com','fixture.apps.googleusercontent.com','refresh',[SCOPES['calendar-write-owned'],SCOPES['calendar-freebusy']],True);self.c=GoogleConnection(t);self.c.account='owner@example.com';self.calls=[];self.event=None
 def tearDown(self):self.temp.cleanup()
 def transport(self,m,u,p):
  self.calls.append((m,u,p))
  if u.endswith('/freeBusy'):return {'calendars':{'primary':{'busy':[]}}}
  if m=='POST':self.event=dict(p,status='confirmed',htmlLink='https://fixture.invalid/event');return self.event
  return self.event
 def job(self,transport=None,identity=None):return GoogleCalendar(self.c,pathlib.Path(self.temp.name)/'ledger.json',transport or self.transport,identity or(lambda t:{'email':'owner@example.com','email_verified':True}))
 def prepare(self,j):return j.prepare('Solo bookkeeping','2026-10-08T17:00:00+05:30','2026-10-08T17:30:00+05:30','Office','Exact notes')
 def test_exact_no_invite_event_readback_restart(self):
  j=self.job();r=self.prepare(j);j.submit(r,True);j.worker.join(3);self.assertEqual(j.snapshot()['state'],'completed');post=[x for x in self.calls if x[1].endswith('sendUpdates=none')][0];self.assertTrue(post[1].endswith('sendUpdates=none'));self.assertEqual(post[2]['attendees'],[]);self.assertFalse(post[2]['reminders']['useDefault']);self.assertEqual(self.job().snapshot()['state'],'completed')
  with self.assertRaises(ValueError):j.submit(r,True)
 def test_naive_or_relative_dates_and_changed_review_rejected(self):
  for start,end in [('tomorrow','later'),('2026-10-08T17:00:00','2026-10-08T18:00:00'),('2026-10-08T18:00:00+05:30','2026-10-08T17:00:00+05:30')]:
   with self.assertRaises(ValueError):plan('owner@example.com','Title',start,end)
  j=self.job();r=self.prepare(j)
  with self.assertRaises(ValueError):j.submit(dict(r,sha256='changed'),True)
  self.assertFalse(self.calls)
 def test_wrong_live_identity_no_post(self):
  j=self.job(identity=lambda t:{'email':'other@example.com','email_verified':True});r=self.prepare(j);j.submit(r,True);j.worker.join(3);self.assertEqual(j.snapshot()['state'],'review');self.assertFalse(self.calls)
 def test_timeout_and_empty_readback_stays_uncertain(self):
  def timeout(m,u,p):
   if u.endswith('/freeBusy'):return {'calendars':{'primary':{'busy':[]}}}
   raise TimeoutError()
  j=self.job(timeout);r=self.prepare(j);j.submit(r,True);j.worker.join(3);self.assertEqual(j.snapshot()['state'],'uncertain');j.reconcile(True);j.worker.join(3);self.assertEqual(j.snapshot()['state'],'uncertain')

 def test_conflict_blocks_before_event_insert(self):
  def transport(m,u,p):return {'calendars':{'primary':{'busy':[{'start':'2026-10-08T17:00:00+05:30','end':'2026-10-08T17:30:00+05:30'}]}}}
  j=self.job(transport);r=self.prepare(j);j.submit(r,True);j.worker.join(3);self.assertEqual(j.snapshot()['state'],'review');self.assertIsNone(self.event)
