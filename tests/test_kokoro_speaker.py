import unittest
from unittest.mock import Mock
from jarvis.experimental.kokoro_speaker import KokoroSpeaker
class SpeakerTests(unittest.TestCase):
 def setUp(self):
  self.synth=Mock();self.synth.synthesize.return_value=([.1]*1200,24000);self.output=Mock();self.factory=Mock(return_value=self.output);self.speaker=KokoroSpeaker(self.synth,self.factory)
 def test_no_effect_on_creation(self):self.synth.synthesize.assert_not_called();self.factory.assert_not_called()
 def test_blocks_close(self):
  self.speaker.speak('hello');self.assertEqual(self.output.write.call_count,3);self.output.close.assert_called_once();self.assertIsNone(self.speaker.output)
 def test_stale_before_synthesis(self):
  self.speaker.stop();self.speaker.speak('stale',generation=0);self.synth.synthesize.assert_not_called()
 def test_pause_during_synthesis(self):
  self.synth.synthesize.side_effect=lambda t:(self.speaker.stop() or ([.1],24000));self.speaker.speak('hello');self.factory.assert_not_called()
 def test_pause_during_write(self):
  self.output.write.side_effect=lambda a:self.speaker.stop();self.speaker.speak('hello');self.output.abort.assert_called_once();self.assertEqual(self.output.write.call_count,1);self.output.close.assert_called_once()
 def test_write_failure_closes(self):
  self.output.write.side_effect=RuntimeError('audio unavailable')
  with self.assertRaises(RuntimeError):self.speaker.speak('hello')
  self.output.close.assert_called_once();self.assertIsNone(self.speaker.output)
 def test_one_first_write_event_after_write_not_start(self):
  seen=[];self.speaker.output_event=lambda *a:seen.append((a,self.output.write.call_count))
  self.speaker.speak('hello');self.assertEqual(seen,[(('first-write',0,24000),1)])
 def test_failed_write_no_metric(self):
  seen=[];self.speaker.output_event=lambda *a:seen.append(a);self.output.write.side_effect=RuntimeError('failed')
  with self.assertRaises(RuntimeError):self.speaker.speak('hello')
  self.assertEqual(seen,[])
 def test_pause_during_first_write_no_metric(self):
  seen=[];self.speaker.output_event=lambda *a:seen.append(a);self.output.write.side_effect=lambda a:self.speaker.stop();self.speaker.speak('hello');self.assertEqual(seen,[])
