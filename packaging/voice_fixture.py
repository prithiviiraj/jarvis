"""Real cloud-runner engines, public JFK test audio. No mic/no owner voice."""
from jarvis.models import download,ready
from jarvis.audio import SileroVad,Endpointer
from jarvis.speech import WhisperSTT
import urllib.request,time,json,pathlib,hashlib
import wave,numpy as np
import platform
root=pathlib.Path('ci-models');download(root,consent=True);assert ready(root)
url='https://raw.githubusercontent.com/ggerganov/whisper.cpp/master/samples/jfk.wav'
with urllib.request.urlopen(url,timeout=30) as r:raw=r.read(2000000)
path=pathlib.Path('ci-jfk.wav');path.write_bytes(raw)
with wave.open(str(path)) as wav:
 assert wav.getframerate()==16000 and wav.getsampwidth()==2 and wav.getnchannels()==1, 'Fixture PCM schema changed'
 x=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(np.float32)/32768
vad=SileroVad(root/'silero.onnx');e=Endpointer();events=[];t=time.perf_counter()
padded=np.concatenate([np.zeros(16000,dtype=np.float32),x,np.zeros(16000,dtype=np.float32)])
for i in range(0,len(padded)-512+1,512):
 event=e.feed(padded[i:i+512],vad.score(padded[i:i+512]))
 if event:events.append({'event':event[0],'time_s':round(i/16000,3),'frames':len(event[1]) if event[1] else 0})
vad_time=time.perf_counter()-t;t=time.perf_counter();stt=WhisperSTT(root/'whisper-base',language='en');load=time.perf_counter()-t
t=time.perf_counter();text=stt.transcribe(x);elapsed=time.perf_counter()-t
assert 'country' in text.lower(), 'STT fixture transcript unexpected'
result={'host':platform.system()+' cloud runner, not owner laptop','audio_url':url,'audio_sha256':hashlib.sha256(raw).hexdigest(),'audio_s':len(x)/16000,'stt_load_s':load,'stt_s':elapsed,'stt_text':text,'vad_processing_s':vad_time,'vad_events':events,'unrun':['physical microphone','accent dataset','echo cancellation','barge-in','live cloud providers','noise suppression','end-to-first-audio']}
pathlib.Path('windows-voice-fixture.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
