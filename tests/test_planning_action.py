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
