import unittest
from unittest.mock import Mock
from jarvis.experimental.kokoro import NativeG2P,VoiceError
import queue,threading
class G2PTests(unittest.TestCase):
 def stub(self):
  g=NativeG2P.__new__(NativeG2P);g.lock=threading.Lock();g.lines=queue.Queue();g.closed=False;g.process=Mock();g.process.poll.return_value=None;g.process.stdin=Mock();return g
 def test_literal_input(self):
  g=self.stub();g.lines.put('həlO');self.assertEqual(g.phonemize('hello'),'həlO');g.process.stdin.write.assert_called_once_with('hello\n')
 def test_control_input_refused(self):
  for text in ['','hello\nworld','hello\rworld','a\0b','x'*1001]:
   g=self.stub()
   with self.assertRaises(VoiceError):g.phonemize(text)
   g.process.stdin.write.assert_not_called()
 def test_process_exit(self):
  g=self.stub();g.process.poll.return_value=2
  with self.assertRaises(VoiceError):g.phonemize('hello')
 def test_error_closes(self):
  g=self.stub();g.lines.put('ERROR')
  with self.assertRaises(VoiceError):g.phonemize('hello')
  self.assertTrue(g.closed);g.process.terminate.assert_called_once()
