import unittest
from unittest.mock import Mock
from jarvis.action_intent import parse
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.ui_bridge import Bridge
class TamilCommands(unittest.TestCase):
 def test_exact_tamil_imperatives_map_to_existing_bounded_actions(self):
  for text,command in [('ஜார்விஸ் பிரவுசர் ஓபன் பண்ணு','open-window'),('browser ஓபன் பண்ணு','open-window'),('யூடியூப் ஓபன் பண்ணு','open'),('YouTube திற','open'),('கீழே ஸ்க்ரோல் பண்ணு','scroll-down'),('ஸ்க்ரோல் டவுன்','scroll-down'),('மேலே scroll பண்ணு','scroll-up')]:self.assertEqual(parse(text)['command'],command,text)
 def test_tamil_negation_questions_and_unbounded_clauses_never_become_effects(self):
  for text in ['பிரவுசர் ஓபன் பண்ணாதே','யூடியூப் ஓபன் பண்ண வேண்டாம்','ஏன் பிரவுசர் ஓபன் பண்ணு','பிரவுசர் ஓபன் பண்ணு பின்னர் பணம் அனுப்பு','கீழே ஸ்க்ரோல் பண்ணாதே']:self.assertIsNone(parse(text),text)
 def test_tamil_second_video_uses_current_observed_choice_only(self):
  b=Bridge(WorkspaceVoice());b.browseros=Mock();b.browseros.snapshot.return_value={'state':'connected','url':'https://www.youtube.com/'}
  try:self.assertTrue(b.shared_action('இரண்டாவது வீடியோவை ஓபன் பண்ணு'));b.browseros.choose_video.assert_called_once_with(2,'https://www.youtube.com/')
  finally:b.close()
