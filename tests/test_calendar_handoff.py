import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jarvis.calendar_handoff import draft
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class Tests(unittest.TestCase):
 def test_relative_words_never_become_date(self):
  d=draft('tomorrow this time I have to go to the library');self.assertEqual(d['place'],'the library');self.assertEqual(d['start'],'');self.assertEqual(d['end'],'');self.assertEqual(d['timezone'],'');self.assertEqual(d['notes'],d['request'])
 def test_real_dispatch_draft_cancel(self):
  b=Bridge(WorkspaceVoice())
  try:
   b.obsidian.enabled=True;self.assertTrue(b.calendar_action('tomorrow this time I have to go to the library'));s=b.execute({'command':'status'});self.assertEqual(s['calendar']['draft']['start'],'');self.assertIsNone(s['calendar']['pending']);s=b.execute({'command':'calendar-cancel'});self.assertIsNone(s['calendar']['draft'])
  finally:b.close()
if __name__=='__main__':unittest.main(verbosity=2)
