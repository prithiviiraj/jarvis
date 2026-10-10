import unittest
from jarvis.calendar_handoff import draft
from jarvis.calendar_dialogue import update
from jarvis.ui_bridge import Bridge
class CalendarDialogue(unittest.TestCase):
 def test_exact_fields_retained_unsaved(self):
  d=draft('tomorrow this time I have to go to the library')
  for phrase in ('calendar title Library visit','calendar start 2026-10-11T14:00','calendar end 2026-10-11T15:00','calendar timezone Asia/Kolkata'):
   d=update(d,phrase)
  self.assertEqual(d['place'],'the library');self.assertEqual(d['missing'],[]);self.assertEqual(d['weekday'],'Sunday');self.assertIn('Unsaved',d['scope'])
 def test_no_relative_or_default_timezone(self):
  d=draft('calendar appointment')
  for t in ('calendar start tomorrow','calendar start 2026-02-30T10:00','calendar timezone UTC+5:30'):
   with self.assertRaises(ValueError):update(d,t)
  self.assertEqual(d['start'],'');self.assertIsNone(update(None,'calendar title Test'));self.assertIsNone(update(d,'save it'))
 def test_real_dispatch_replaces_pending_without_save(self):
  b=Bridge()
  try:
   b.obsidian.enabled=True;b.calendar_action('show calendar appointment');b.calendar_action('calendar title Test');b.calendar_action('calendar start 2026-10-11T14:00');b.calendar_action('calendar end 2026-10-11T15:00');b.calendar_action('calendar timezone Asia/Kolkata')
   s=b.execute({'command':'status'});self.assertEqual(s['calendar']['draft']['title'],'Test');self.assertIsNone(s['calendar']['pending']);self.assertEqual(b.calendar.result,'')
   b.execute({'command':'calendar-cancel'});self.assertIsNone(b.calendar_draft)
  finally:b.close()
