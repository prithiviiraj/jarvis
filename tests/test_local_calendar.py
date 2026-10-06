import unittest,tempfile,pathlib
from jarvis.local_calendar import LocalCalendar
from jarvis.obsidian_vault import Vault,NAME
class Calendar(unittest.TestCase):
 def event(self):return {'title':'Go to library','start':'2026-10-07T18:00','end':'2026-10-07T19:00','place':'Local library','notes':'My plan','timezone':'Asia/Kolkata'}
 def test_exact_review_save_and_readback(self):
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);v=Vault(base/'c.json',lambda:base);v.create(NAME,True);c=LocalCalendar(v);r=c.preview(self.event());self.assertEqual(r['weekday'],'Wednesday')
   with self.assertRaises(ValueError):c.save(r)
   with self.assertRaises(ValueError):c.save({**r,'place':'Elsewhere'},True)
   n=c.save(r,True);self.assertTrue((base/NAME/n).exists());self.assertEqual(c.rows()[0]['place'],'Local library');self.assertIsNone(c.pending)
 def test_off_and_bad_time(self):
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);v=Vault(base/'c.json',lambda:base);c=LocalCalendar(v)
   with self.assertRaises(ValueError):c.preview(self.event())
   v.create(NAME,True);e=self.event();e['end']=e['start']
   with self.assertRaises(ValueError):c.preview(e)
