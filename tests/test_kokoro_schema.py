import unittest,threading
from unittest.mock import Mock
import numpy as np
from jarvis.experimental.kokoro import KokoroSynth,VoiceError
class KokoroSchemaTests(unittest.TestCase):
 def stub(self):
  k=KokoroSynth.__new__(KokoroSynth);k.np=np;k.g2p=Mock();k.g2p.phonemize.return_value='ab';k.lock=threading.Lock();k.vocab={'a':1,'b':2};k.voice=np.zeros((510,256),np.float32);k.session=Mock();k.session.run.return_value=[np.zeros(240,np.float32)];return k
 def test_raw_input_schema(self):
  k=self.stub();audio,sr=k.synthesize('hello');self.assertEqual(sr,24000);self.assertEqual(audio.shape,(240,));inputs=k.session.run.call_args[0][1];self.assertEqual(inputs['input_ids'].tolist(),[[0,1,2,0]]);self.assertEqual(inputs['style'].shape,(1,256))
 def test_unknown_phones_rejected(self):
  k=self.stub();k.g2p.phonemize.return_value='xyz'
  with self.assertRaises(VoiceError):k.synthesize('hello')
  k.session.run.assert_not_called()
 def test_phone_size_bound(self):
  k=self.stub();k.g2p.phonemize.return_value='a'*511
  with self.assertRaises(VoiceError):k.synthesize('hello')
 def test_nonfinite_rejected(self):
  k=self.stub();k.session.run.return_value=[np.array([np.nan],np.float32)]
  with self.assertRaises(VoiceError):k.synthesize('hello')
 def test_output_cap(self):
  k=self.stub();k.session.run.return_value=[np.zeros(960001,np.float32)]
  with self.assertRaises(VoiceError):k.synthesize('hello')
 def test_speed_bound(self):
  k=self.stub()
  with self.assertRaises(VoiceError):k.synthesize('hello',2.)
  k.g2p.phonemize.assert_not_called()
