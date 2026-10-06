import unittest
from unittest.mock import Mock
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class Plan(unittest.TestCase):
 def test_phrase_review_no_open_until_confirm(self):
  b=Bridge(WorkspaceVoice());b.obsidian.enabled=True;b.obsidian.open=Mock()
  try:
   self.assertTrue(b.planning_action("what's the plan today"));b.obsidian.open.assert_not_called();p=dict(b.plan_pending)
   with self.assertRaises(ValueError):b.execute({'command':'plan-open','reviewed':p})
   b.execute({'command':'plan-open','reviewed':p,'confirm':True});b.obsidian.open.assert_called_once_with('Planning/Today.md');self.assertIsNone(b.plan_pending)
  finally:b.close()
 def test_relative_calendar_phrase_no_event_guess(self):
  b=Bridge(WorkspaceVoice());b.obsidian.enabled=True
  try:
   self.assertTrue(b.calendar_action('Tomorrow this time I have to go to this place'));self.assertTrue(b.calendar_open_pending);self.assertIsNone(b.calendar.pending);self.assertEqual(b.calendar.rows(),[])
  finally:b.close()
