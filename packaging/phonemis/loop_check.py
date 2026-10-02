"""Real local Whisper -> localhost synthetic SSE -> native Kokoro -> WAV sink.
No LLM reasoning, no physical mic/output; measures first WAV output only.
"""
import pathlib,wave,json,time,threading,http.server,platform
import numpy as np
from jarvis.speech import WhisperSTT
from jarvis.router import BrainRouter,Provider
from jarvis.runtime import VoiceRuntime
from jarvis.experimental.kokoro import NativeG2P,KokoroSynth
from jarvis.experimental.kokoro_speaker import KokoroSpeaker
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  assert body['stream'] is True
  self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
  for text in ['Hello. ','I am ready when you are.']:
   self.wfile.write(('data: '+json.dumps({'choices':[{'delta':{'content':text}}]})+'\n\n').encode());self.wfile.flush()
  self.wfile.write(b'data: [DONE]\n\n')
rows=[];samples=[];started=time.perf_counter()
class Sink:
 def __init__(self,sr):self.sr=sr
 def start(self):pass
 def write(self,x):
  if not rows:rows.append({'first_wav_output_s':time.perf_counter()-started})
  samples.append(np.asarray(x,dtype=np.float32).copy())
 def stop(self):pass
 def abort(self):pass
 def close(self):pass
class Mic:
 def resume(self):pass
 def close(self):pass
class VAD:pass
root=pathlib.Path('phonemis-upstream');exe=root/'build/Release/phonemis_runner.exe'
if platform.system()!='Windows':exe=pathlib.Path('/tmp/jarvis-phonemis/build/phonemis_persistent');root=pathlib.Path('/tmp/jarvis-phonemis')
g=NativeG2P(exe,root/'data/en-us');m=pathlib.Path('tts-eval-models');k=KokoroSynth(m/'model.onnx',m/'voice.bin',m/'config.json',g)
stt=WhisperSTT('ci-models/whisper-base',language='en')
with wave.open('ci-jfk.wav') as w:
 assert w.getframerate()==16000 and w.getnchannels()==1 and w.getsampwidth()==2
 x=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(np.float32)/32768
server=http.server.HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
router=BrainRouter([Provider('local',f'http://127.0.0.1:{server.server_port}/v1','synthetic-server-not-llm')]);speaker=KokoroSpeaker(k,Sink);events=[]
v=VoiceRuntime(VAD(),stt,router,speaker,lambda kind,value:events.append({'event':kind,'value':value}));v.mic=Mic();v.enabled=True;v.streaming=True;v.generation=1
try:
 started=time.perf_counter();v.turn(x,1,False,[]);elapsed=time.perf_counter()-started
 assert rows and v.history and 'country' in v.history[-2]['content'].lower();assert v.history[-1]['content']=='Hello. I am ready when you are.'
 audio=np.concatenate(samples)
 with wave.open('candidate-loop.wav','wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes((audio*32767).astype('<i2').tobytes())
 result={'host':platform.system()+' cloud runner, not owner laptop','test':'actual PCM-STT, real localhost SSE, actual native direct Kokoro, WAV sink','first_wav_output_s':rows[0]['first_wav_output_s'],'turn_s':elapsed,'audio_s':len(audio)/24000,'history':v.history,'events':events,'unrun':['physical mic/output','real LLM network latency','first audible audio','echo/noise/barge-in','owner accent','installed EXE'],'status':'software chain evidence only'}
 pathlib.Path('candidate-loop.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
finally:v.close();g.close();server.shutdown();server.server_close();thread.join()
