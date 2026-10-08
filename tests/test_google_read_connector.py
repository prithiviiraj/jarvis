import unittest
from jarvis.google_read_connector import GoogleReadConnector
class Tests(unittest.TestCase):
 def client(self,rows):
  calls=[]
  def transport(method,url,payload):calls.append((method,url,payload));return rows.pop(0)
  return GoogleReadConnector(lambda:'not-used','owner@example.com',transport),calls
 def test_account_mismatch_stops_history(self):
  c,calls=self.client([{'emailAddress':'wrong@example.com'}])
  with self.assertRaises(ValueError):c.sent_ids()
  self.assertEqual(len(calls),1)
 def test_partial_sent_ids_not_duplicate_verdict(self):
  c,calls=self.client([{'emailAddress':'owner@example.com'},{'messages':[{'id':'one','threadId':'thread'}],'nextPageToken':'next'}]);row=c.sent_ids('to:friend@example.com');self.assertFalse(row['complete']);self.assertEqual(row['messages'][0]['message_id'],'one');self.assertIn('labelIds=SENT',calls[-1][1]);self.assertTrue(all(m=='GET'for m,u,p in calls))
 def test_message_identity_binding(self):
  c,_=self.client([{'emailAddress':'owner@example.com'},{'id':'other'}])
  with self.assertRaises(ValueError):c.read_message('one')
 def test_no_arbitrary_destinations(self):
  c,_=self.client([])
  for u in ('https://attacker.invalid','http://gmail.googleapis.com/gmail/v1/users/me','https://gmail.googleapis.com.evil/gmail/v1'):
   with self.assertRaises(ValueError):c.request(u)
 def test_freebusy_requires_consent_and_explicit_offsets(self):
  c,_=self.client([])
  with self.assertRaises(ValueError):c.freebusy(['primary'],'2026-10-08T10:00:00+05:30','2026-10-08T11:00:00+05:30')
  with self.assertRaises(ValueError):c.freebusy(['primary'],'2026-10-08T10:00','2026-10-08T11:00',True)
 def test_calendar_error_not_free(self):
  c,_=self.client([{'calendars':{'primary':{'busy':[],'errors':[{'reason':'notFound'}]}}}])
  with self.assertRaisesRegex(ValueError,'unknown'):c.freebusy(['primary'],'2026-10-08T10:00:00+05:30','2026-10-08T11:00:00+05:30',True)
 def test_freebusy_real_contract_no_write(self):
  c,calls=self.client([{'calendars':{'primary':{'busy':[{'start':'2026-10-08T10:00:00+05:30','end':'2026-10-08T10:30:00+05:30'}]}}}]);r=c.freebusy(['primary'],'2026-10-08T10:00:00+05:30','2026-10-08T11:00:00+05:30',True);self.assertTrue(r['complete']);self.assertEqual(calls[0][0],'POST');self.assertEqual(calls[0][1],'https://www.googleapis.com/calendar/v3/freeBusy')
