import unittest,threading
from unittest.mock import Mock
from jarvis.experimental.kokoro import KokoroSynth,VoiceError
from jarvis.experimental.kokoro_speaker import KokoroSpeaker
from jarvis.speech_queue import SpeechQueue
class SpeedStreamTests(unittest.TestCase):
 def test_synthesis_generator_is_lazy_and_bounded(self):
  synth=object.__new__(KokoroSynth);synth.synthesize=Mock(return_value=([.1]*10,24000))
  text=' '.join(['Long readable words']*18)+'.';stream=synth.synthesize_stream(text)
  synth.synthesize.assert_not_called();part,audio,sr=next(stream);self.assertLessEqual(len(part),120);self.assertEqual(sr,24000);self.assertEqual(synth.synthesize.call_count,1)
  parts=[part]+[p for p,a,s in stream];self.assertEqual(' '.join(parts),text)
 def test_synthesis_stream_invalid_bound(self):
  synth=object.__new__(KokoroSynth)
  with self.assertRaises(VoiceError):list(synth.synthesize_stream('Hi',max_chars=0))
 def test_speaker_pause_between_chunks(self):
  class Synth:
   def synthesize_stream(self,text):
    yield 'First clause.',[.1]*10,24000
    yield 'Next clause.',[.1]*10,24000
  sp=KokoroSpeaker(Synth(),Mock());g=sp.prepare_stream('First clause. Next clause.',0)
  self.assertEqual(next(g)[0],'First clause.');sp.stop();self.assertEqual(list(g),[]);sp.output_factory.assert_not_called()
 def test_queue_prepares_lazy_stream(self):
  class Speaker:
   def __init__(self):self.parts=[]
   def prepare_stream(self,text,ticket):
    yield ('First',[],24000);yield ('Second',[],24000)
   def play_prepared(self,part,generation):self.parts.append(part[0])
   def stop(self):pass
  sp=Speaker();SpeechQueue(sp,threading.Event()).play_stream(['First and second.'],0);self.assertEqual(sp.parts,['First','Second'])
 def test_stream_exception_cancels(self):
  class Speaker:
   def prepare_stream(self,text,ticket):raise ValueError('synthesis failed');yield
   def stop(self):pass
  with self.assertRaises(ValueError):SpeechQueue(Speaker(),threading.Event()).play_stream(['Hi.'],0)
