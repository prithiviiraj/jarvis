import unittest,threading
from unittest.mock import Mock
from jarvis.speech_queue import SpeechQueue
class SpeechQueueTests(unittest.TestCase):
 def test_clauses(self):
  s=Mock();q=SpeechQueue(s,threading.Event());q.play_stream(['Hello. ','Next clause.'],1);self.assertEqual(s.speak.call_count,2);s.speak.assert_any_call('Hello.',generation=1)
 def test_cancelled_no_speech(self):
  s=Mock();e=threading.Event();e.set();SpeechQueue(s,e).play_stream(['secret'],1);s.speak.assert_not_called()
 def test_failure_stops(self):
  s=Mock();s.speak.side_effect=RuntimeError('private');e=threading.Event()
  with self.assertRaises(RuntimeError):SpeechQueue(s,e).play_stream(['Hello.'],1)
  self.assertTrue(e.is_set())
