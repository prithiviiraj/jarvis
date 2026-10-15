import unittest
from unittest.mock import Mock
from jarvis.completion_feedback import CompletionFeedback,TEXT
class CompletionFeedbackTests(unittest.TestCase):
 def test_dispatch_cannot_claim_success_and_duplicate_results_do_not_repeat(self):
  a=CompletionFeedback()
  with self.assertRaises(ValueError):a.record('request1','browser-page-ready')
  self.assertIsNone(a.take());self.assertTrue(a.record('request1','browser-page-ready',True));self.assertFalse(a.record('request1','browser-page-ready',True));self.assertEqual(a.take()['text'],TEXT['browser-page-ready']);self.assertIsNone(a.take())
 def test_prepared_playback_has_no_synthesis_or_model_on_action_path(self):
  a=CompletionFeedback();speaker=Mock();speaker.generation=3;speaker.prepare.side_effect=lambda text,generation:(text,'pcm',24000)
  self.assertTrue(a.prepare(speaker,3));before=speaker.prepare.call_count;a.record('request1','browser-tab-ready',True);self.assertTrue(a.play(a.take(),speaker,3));self.assertEqual(speaker.prepare.call_count,before);speaker.speak.assert_not_called();speaker.play_prepared.assert_called_once();self.assertNotIn('visible',TEXT['browser-page-ready'])
 def test_stop_generation_blocks_output_and_clears_queue(self):
  a=CompletionFeedback();speaker=Mock();speaker.generation=3;speaker.prepare.return_value=('text','pcm',24000);a.prepare(speaker,3);a.record('request1','browser-page-ready',True);event=a.take();speaker.generation=4;self.assertFalse(a.play(event,speaker,3));speaker.play_prepared.assert_not_called();a.record('request2','browser-page-ready',True);a.clear();self.assertIsNone(a.take())
 def test_failure_is_not_done_and_unknown_templates_blocked(self):
  a=CompletionFeedback();a.record('request1','browser-failed',True);self.assertIn('did not complete',a.take()['text'])
  with self.assertRaises(ValueError):a.record('request2','anything',True)
 def test_profiles_do_not_play_another_personas_prepared_clip(self):
  a=CompletionFeedback();speaker=Mock();speaker.profile='JARVIS';speaker.generation=0;speaker.prepare.return_value=('text','pcm',24000);a.prepare(speaker,0);a.record('request1','browser-page-ready',True);speaker.profile='DEX';self.assertFalse(a.play(a.take(),speaker,0));speaker.play_prepared.assert_not_called()
 def test_runtime_feedback_reuses_one_speaker_and_never_starts_microphone(self):
  from jarvis.runtime import VoiceRuntime
  speaker=Mock();speaker.profile='JARVIS';speaker.generation=0;speaker.prepare.return_value=('text','pcm',24000);runtime=VoiceRuntime(Mock(),Mock(),Mock(),speaker);runtime.mic=Mock();runtime.enabled=True;runtime.completion_feedback.prepare(speaker,0);runtime.completion_feedback.record('request1','browser-page-ready',True)
  self.assertTrue(runtime.poll_completion());runtime.feedback_worker.join(2);speaker.play_prepared.assert_called_once();runtime.router.ask.assert_not_called();runtime.mic.start.assert_not_called();runtime.mic.suspend.assert_called_once();runtime.mic.resume.assert_called_once();runtime.close()
 def test_no_feedback_playback_when_turn_busy_or_stopped(self):
  from jarvis.runtime import VoiceRuntime
  speaker=Mock();runtime=VoiceRuntime(Mock(),Mock(),Mock(),speaker);runtime.mic=Mock();runtime.enabled=True;runtime.busy=True;runtime.completion_feedback.record('request1','browser-page-ready',True);self.assertFalse(runtime.poll_completion());runtime.pause();runtime.busy=False;self.assertFalse(runtime.poll_completion());speaker.play_prepared.assert_not_called()

 def test_cancelled_preparation_stops_between_clips_and_never_installs_partial_audio(self):
  a=CompletionFeedback();speaker=Mock();speaker.profile='JARVIS';speaker.generation=0;stopped=[False]
  def prepare(*args):stopped[0]=True;return ('text','pcm',24000)
  speaker.prepare.side_effect=prepare
  self.assertFalse(a.prepare(speaker,0,cancelled=lambda:stopped[0]));speaker.prepare.assert_called_once();self.assertNotIn('JARVIS',a.clips);self.assertEqual(a.preparation,[])
 def test_preparation_records_cold_and_cache_cost_without_private_text(self):
  a=CompletionFeedback();speaker=Mock();speaker.profile='test-voice';speaker.generation=0;speaker.prepare.return_value=('text','pcm',24000)
  self.assertTrue(a.prepare(speaker,0,cache_key=('timing-fixture',)));self.assertFalse(a.preparation[-1]['cached']);self.assertEqual(a.preparation[-1]['clips'],len(TEXT));before=speaker.prepare.call_count
  self.assertTrue(a.prepare(speaker,0,cache_key=('timing-fixture',)));self.assertTrue(a.preparation[-1]['cached']);self.assertEqual(speaker.prepare.call_count,before);self.assertNotIn('text',a.preparation[-1]);self.assertGreaterEqual(a.preparation[-1]['seconds'],0)
