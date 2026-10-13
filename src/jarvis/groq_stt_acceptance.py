"""Frozen keyless Groq request contract. No network or private audio."""
def run():
 import io,threading,json,pathlib
 import numpy as np
 from .groq_stt import GroqSTT
 from .speech import SpeechCancelled
 class Keys:
  def get(self,name):assert name=='groq/slot1';return 'synthetic-key-not-real'
 class Http:
  def __init__(self):self.calls=[]
  def open(self,request,timeout):
   self.calls.append(request)
   assert request.full_url=='https://api.groq.com/openai/v1/audio/transcriptions'
   assert b'whisper-large-v3'in request.data and b'RIFF'in request.data
   for value in (b'history',b'screen',b'prompt',b'name="url"'):assert value not in request.data
   return io.BytesIO(b'{"text":"Synthetic contract only"}')
 http=Http();stt=GroqSTT(Keys(),consent=True,free_confirmed=True,http=http)
 assert not http.calls
 assert stt.transcribe(np.zeros(1600,dtype=np.float32))=='Synthetic contract only'
 cancel=threading.Event();cancel.set()
 try:stt.transcribe_cancellable(np.zeros(16),cancel)
 except SpeechCancelled:pass
 else:raise AssertionError('Cancellation failed')
 assert len(http.calls)==1
 out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True)
 (out/'groq-stt-frozen-contract.json').write_text(json.dumps({'result':'passed','network_calls':0,'real_keys':0,'audio':'fixed synthetic silence','scope':'Frozen HTTP request/cancellation contract only. No live Groq quota, Tamil/Tanglish quality or physical microphone acceptance.'},indent=2),encoding='utf-8')
 print('Frozen Groq keyless audio-only request contract passed. No network.')
