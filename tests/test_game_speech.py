import unittest,threading
from unittest.mock import Mock
from jarvis.game_speech import GameSpeech
class Speech(unittest.TestCase):
 def make(self):
  self.game=Mock(enabled=True,audio=True,generation=2);self.speaker=Mock(generation=1);self.factory=Mock(return_value=self.speaker);return GameSpeech(self.game,self.factory)
 def row(self):return {'audio':True,'comment':'Try cover.','generation':2}
 def test_off_stale_and_busy_no_speech(self):
  s=self.make();self.assertIsNone(s.play(self.row(),True));self.game.audio=False;self.assertIsNone(s.play(self.row()));self.game.audio=True;self.assertIsNone(s.play({**self.row(),'generation':1}));self.factory.assert_not_called()
 def test_reviewed_output_and_stop(self):
  s=self.make();s.play(self.row()).join();self.speaker.speak.assert_called_once_with('Try cover.',generation=1);s.stop();self.speaker.stop.assert_called()
 def test_stop_during_load_discards(self):
  s=self.make();gate=threading.Event();entered=threading.Event()
  def load():entered.set();gate.wait(2);return self.speaker
  s.factory=load;t=s.play(self.row());entered.wait(1);s.stop();gate.set();t.join();self.speaker.speak.assert_not_called();self.speaker.close.assert_called_once();self.assertFalse(s.busy)
