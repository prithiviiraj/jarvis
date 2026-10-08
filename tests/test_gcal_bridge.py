import unittest,tempfile,pathlib
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.google_calendar import GoogleCalendar
class Tests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.b=Bridge(WorkspaceVoice());self.b.google.account='owner@example.com';self.b.google_calendar=GoogleCalendar(self.b.google,pathlib.Path(self.temp.name)/'ledger.json')
 def tearDown(self):self.b.close();self.temp.cleanup()
 def test_exact_solo_review_pause_and_no_dates_guessed(self):
  with self.assertRaises(ValueError):self.b.execute({'command':'gcal-prepare','title':'Title','start':'tomorrow','end':'later'})
  r=self.b.execute({'command':'gcal-prepare','title':'Solo bookkeeping','start':'2026-10-08T17:00:00+05:30','end':'2026-10-08T17:30:00+05:30'})['google']['calendar'];self.assertEqual(r['plan']['payload']['attendees'],[]);self.assertEqual(r['plan']['payload']['account'],'owner@example.com');self.assertFalse(r['busy'])
  with self.assertRaises(ValueError):self.b.execute({'command':'gcal-submit','reviewed':r['plan']})
  self.b.execute({'command':'pause'});self.assertEqual(self.b.google_calendar.snapshot()['state'],'cancelled')
