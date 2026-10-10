import datetime,unittest
from unittest.mock import patch,Mock
from zoneinfo import ZoneInfo
from jarvis.calendar_dialogue import update
from jarvis.calendar_handoff import draft
from jarvis.ui_bridge import Bridge
class CalendarMoveDraft(unittest.TestCase):
 def complete(self):
  d=draft('show calendar appointment')
  for t in ('calendar title Library visit','calendar start 2026-10-11T23:30','calendar end 2026-10-12T00:30','calendar timezone Asia/Kolkata'):d=update(d,t)
  return d
 def test_exact_date_atomic_overnight(self):
  d=self.complete();m=update(d,'Jarvis move calendar draft to 2026-10-13');self.assertEqual(m['start'],'2026-10-13T23:30');self.assertEqual(m['end'],'2026-10-14T00:30');self.assertEqual(m['weekday'],'Tuesday');self.assertEqual(m['revision'],d['revision']+1);self.assertEqual(m['timezone'],d['timezone']);self.assertEqual(d['start'],'2026-10-11T23:30')
 def test_relative_uses_explicit_timezone_clock(self):
  d=self.complete();clock=datetime.datetime(2026,10,12,23,tzinfo=datetime.timezone.utc);m=update(d,'move draft to tomorrow',clock);self.assertEqual(m['start'],'2026-10-14T23:30');self.assertEqual(m['weekday'],'Wednesday')
 def test_night_requires_exact_day(self):
  for hour in (0,1,2,3):
   with self.assertRaisesRegex(ValueError,'ambiguous'):update(self.complete(),'move draft to tomorrow',datetime.datetime(2026,10,11,hour,tzinfo=ZoneInfo('Asia/Kolkata')))
 def test_no_guessed_timezone_or_incomplete_time(self):
  d=self.complete()
  for field in ('timezone','start','end'):
   missing=dict(d);missing[field]=''
   with self.assertRaises(ValueError):update(missing,'move draft to today')
  with self.assertRaises(ValueError):update(d,'move draft to 2026-02-30')
 def test_unsupported_or_question_is_not_command(self):
  for text in ('move meeting to tomorrow','move draft to next Tuesday','how do I move draft to tomorrow','do not move draft to tomorrow','move draft to tomorrow and save it','move draft to 2026-10-13 and send invite'):
   self.assertIsNone(update(self.complete(),text),text)
 def test_dst_missing_ambiguous_and_transition_refused(self):
  d=self.complete();d['timezone']='America/New_York';d['start']='2026-10-11T01:30';d['end']='2026-10-11T02:30'
  with self.assertRaises(ValueError):update(d,'move draft to 2026-11-01')
  d['start']='2026-10-11T02:30';d['end']='2026-10-11T03:30'
  with self.assertRaises(ValueError):update(d,'move draft to 2026-03-08')
 def test_actual_bridge_cancels_old_review_no_save_or_open(self):
  b=Bridge()
  try:
   b.calendar_draft=self.complete();b.calendar.pending={'old':'review'};b.calendar.save=Mock();b.obsidian.open=Mock();b.voice.send_text=Mock()
   b.execute({'command':'chat','text':'move calendar draft to 2026-10-13'})
   self.assertEqual(b.calendar_draft['start'],'2026-10-13T23:30');self.assertIsNone(b.calendar.pending);self.assertEqual(b.neural.row['kind'],'calendar');self.assertIn('2026-10-13',b.neural.row['text']);b.calendar.save.assert_not_called();b.obsidian.open.assert_not_called();b.voice.send_text.assert_not_called()
  finally:b.close()
