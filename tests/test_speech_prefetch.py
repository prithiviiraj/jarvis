import unittest,threading,time
from jarvis.speech_queue import SpeechQueue
class PrefetchTests(unittest.TestCase):
 def test_next_synthesis_during_current_playback(self):
  playing=threading.Event();second_ready=threading.Event();order=[]
  class Speaker:
   def prepare(self,text,ticket):
    if text=='Second.':
     self_test.assertTrue(playing.wait(1));second_ready.set()
    return text,[0],24000
   def play_prepared(self,p,generation=None):
    order.append(p[0])
    if p[0]=='First.':playing.set();self_test.assertTrue(second_ready.wait(1))
   def stop(self):pass
  self_test=self;SpeechQueue(Speaker(),threading.Event()).play_stream(iter(['First. ','Second.']),0);self.assertEqual(order,['First.','Second.'])
