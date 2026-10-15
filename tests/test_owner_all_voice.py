import unittest,time,threading
from unittest.mock import Mock
from jarvis.runtime import VoiceRuntime
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.ui_bridge import Bridge
class AllVoice(unittest.TestCase):
 def runtime(self,text):
  stt=Mock();stt.transcribe.return_value=text;router=Mock();speaker=Mock();speaker.generation=0;router.ask.side_effect=lambda *a,**k:{'text':'Useful current answer '+str(router.ask.call_count)+'.'}
  v=VoiceRuntime(Mock(),stt,router,speaker);v.mic=Mock();v.enabled=True;v.team_mode=True;return v
 def test_one_utterance_uses_one_mic_and_three_actual_voice_profiles_in_order(self):
  v=self.runtime('What is imagination?');v.turn([],0,False,[]);self.assertEqual(v.speaker.select_profile.call_args_list,[(('JARVIS',),),(('LYRA',),),(('DEX',),)]);self.assertEqual(v.router.ask.call_count,3);self.assertEqual(v.speaker.speak.call_count,3);v.stt.transcribe.assert_called_once();v.mic.start.assert_not_called();v.mic.resume.assert_called_once();self.assertIn('Historical teammate reply',str(v.router.ask.call_args_list[1]));self.assertIn('JARVIS: Useful current answer 1.',str(v.router.ask.call_args_list[1]));self.assertIn('LYRA: Useful current answer 2.',str(v.router.ask.call_args_list[2]));v.close()
 def test_explicit_single_name_does_not_force_all_to_answer(self):
  v=self.runtime('Dex what is imagination?');v.turn([],0,False,[]);v.router.ask.assert_called_once();v.speaker.select_profile.assert_called_once_with('DEX');v.close()
 def test_selection_starts_no_microphone_and_single_selection_clears_all(self):
  v=WorkspaceVoice();b=Bridge(v)
  try:
   state=b.execute({'command':'voice-team-mode','enabled':True});self.assertTrue(state['voice_team_mode']);self.assertIsNone(v.runtime);self.assertFalse(v.busy);b.execute({'command':'select','name':'LYRA'});self.assertFalse(v.team_mode)
   v.runtime=Mock();v.runtime.enabled=True
   with self.assertRaises(ValueError):b.execute({'command':'voice-team-mode','enabled':True})
  finally:v.runtime=None;b.close()
 def test_stop_between_team_speakers_prevents_later_turns(self):
  v=self.runtime('Tell me about planets');v.speaker.speak.side_effect=lambda *a,**k:v.pause();v.turn([],0,False,[]);self.assertEqual(v.router.ask.call_count,1);self.assertEqual(v.speaker.speak.call_count,1);v.close()

 def test_all_emits_one_completed_turn_and_nonstream_first_text_metric(self):
  v=self.runtime('Describe the current fixture');v.notify=Mock();v.turn([],0,False,[])
  completed=[c.args[1]for c in v.notify.call_args_list if c.args[0]=='turn-result'];self.assertEqual(len(completed),1);self.assertEqual(completed[0]['result'],'completed');metrics=[c.args[1]for c in v.notify.call_args_list if c.args[0]=='metrics'and c.args[1]];self.assertIn('first_text_s',metrics[-1]);v.close()
