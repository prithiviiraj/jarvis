import io,json,threading,urllib.error,unittest
from unittest.mock import Mock
try:import numpy as np
except ImportError:np=None
from jarvis.groq_stt import GroqSTT
from jarvis.speech import SpeechCancelled,UnclearSpeech
class Keys:
 def get(self,name):return 'test-only-not-a-real-key'
class Response(io.BytesIO):pass
class Http:
 def __init__(self,result=b'{"text":"test words"}'):self.result=result;self.calls=[]
 def open(self,r,timeout):self.calls.append((r,timeout));return Response(self.result)
@unittest.skipIf(np is None,"numpy unavailable on host")
class GroqTests(unittest.TestCase):
 def test_no_constructor_network(self):
  http=Http();GroqSTT(Keys(),True,True,http=http);self.assertEqual(http.calls,[])
 def test_requires_both_grants_and_key(self):
  for consent,free in [(False,True),(True,False)]:
   with self.assertRaises(ValueError):GroqSTT(Keys(),consent,free)
  with self.assertRaises(ValueError):GroqSTT(Mock(get=lambda _:None),True,True)
 def test_audio_only_upload(self):
  http=Http();stt=GroqSTT(Keys(),True,True,language='ta',http=http);self.assertEqual(stt.transcribe(np.zeros(1600)), 'test words')
  request,timeout=http.calls[0];self.assertEqual(request.full_url,stt.endpoint);self.assertEqual(timeout,30)
  self.assertIn(b'whisper-large-v3',request.data);self.assertIn(b'RIFF',request.data);self.assertIn(b'language',request.data)
  for forbidden in [b'prompt',b'history',b'screen',b'url',b'conversation']:self.assertNotIn(forbidden,request.data)
 def test_auto_omits_language(self):
  h=Http();GroqSTT(Keys(),True,True,http=h).transcribe(np.zeros(16));self.assertNotIn(b'name="language"',h.calls[0][0].data)
 def test_cancel_before_send(self):
  h=Http();cancel=threading.Event();cancel.set()
  with self.assertRaises(SpeechCancelled):GroqSTT(Keys(),True,True,http=h).transcribe_cancellable(np.zeros(16),cancel)
  self.assertFalse(h.calls)
 def test_cancel_after_send_discards(self):
  cancel=threading.Event()
  class CancelHttp(Http):
   def open(self,*a,**k):cancel.set();return super().open(*a,**k)
  with self.assertRaises(SpeechCancelled):GroqSTT(Keys(),True,True,http=CancelHttp()).transcribe_cancellable(np.zeros(16),cancel)
 def test_errors_no_retry(self):
  h=Http()
  def fail(r,timeout):h.calls.append(r);raise urllib.error.HTTPError(r.full_url,429,'private error body',{},None)
  h.open=fail
  with self.assertRaisesRegex(RuntimeError,'429'):GroqSTT(Keys(),True,True,http=h).transcribe(np.zeros(16))
  self.assertEqual(len(h.calls),1)
 def test_response_limits(self):
  for payload in [b'not json',b'{}',b'{"text":""}',json.dumps({'text':'x'*8001}).encode(),b'x'*65537]:
   with self.assertRaises((RuntimeError,ValueError)):GroqSTT(Keys(),True,True,http=Http(payload)).transcribe(np.zeros(16))
 def test_audio_limits_no_network(self):
  for pcm in [np.zeros(0),np.zeros((2,2)),np.array([np.nan]),np.zeros(480001)]:
   h=Http()
   with self.assertRaises(ValueError):GroqSTT(Keys(),True,True,http=h).transcribe(pcm)
   self.assertFalse(h.calls)

class RouteTests(unittest.TestCase):
 def test_defaults_session_only(self):
  from jarvis.workspace_voice import WorkspaceVoice
  voice=WorkspaceVoice();self.assertEqual(voice.stt_route,'local');self.assertFalse(voice.groq_audio_consent)
 def test_bridge_requires_stop_grants_and_key(self):
  from jarvis.ui_bridge import Bridge
  from unittest.mock import patch
  b=Bridge()
  try:
   self.assertEqual(b.execute({'command':'status'})['stt_route'],'local')
   for req in [{'route':'groq'},{'route':'groq','consent':True}]:
    with self.assertRaises(ValueError):b.execute({'command':'voice-stt-route',**req})
   with patch('jarvis.security.WindowsCredentials')as keys:
    keys.return_value.get.return_value='test-only-key'
    b.execute({'command':'voice-stt-route','route':'groq','consent':True,'free_confirmed':True})
    self.assertEqual(b.execute({'command':'status'})['stt_route'],'groq')
    b.voice.busy=True
    with self.assertRaises(ValueError):b.execute({'command':'voice-stt-route','route':'local'})
    b.voice.busy=False
    with self.assertRaises(ValueError):b.execute({'command':'shortcuts-enable','consent':True})
    b.execute({'command':'voice-stt-route','route':'local'})
    self.assertFalse(b.voice.groq_audio_consent)
  finally:b.close()
