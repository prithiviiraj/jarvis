"""Actual workspace factory -> STT -> synthetic local SSE -> five Kokoro WAVs.
Mic and speaker replaced by test adapters. No real LLM or physical audio claim.
"""
import pathlib,shutil,json,wave,threading,http.server,time
import tkinter as tk
from PIL import ImageGrab
from jarvis.workspace import Workspace
from unittest.mock import patch
import numpy as np
from jarvis.workspace_voice import WorkspaceVoice,VOICES
from jarvis import models,voice_assets,providers
from jarvis.paths import ensure_layout
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  self.send_response(200);self.end_headers();self.wfile.write(b'{"data":[{"id":"synthetic-ci-not-llm"}]}')
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));assert body['stream']
  self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
  for text in ['Hello. ','I am ready when you are.']:
   self.wfile.write(('data: '+json.dumps({'choices':[{'delta':{'content':text}}]})+'\n\n').encode());self.wfile.flush()
  self.wfile.write(b'data: [DONE]\n\n')
class Mic:
 def start(self,**kw):assert kw['consent']
 def close(self):pass
 def resume(self):pass
class Sink:
 def __init__(self,sr):self.sr=sr
 def start(self):pass
 def write(self,x):
  if not timing:timing.append(time.perf_counter()-started)
  samples.append(np.asarray(x,dtype=np.float32).copy())
 def stop(self):pass
 def abort(self):pass
 def close(self):pass
out=pathlib.Path('workspace-chain-evidence');out.mkdir(exist_ok=True)
cache=ensure_layout()/'models';models.download(cache,consent=True);assets=cache/'voices';voice_assets.download(assets,consent=True)
base=pathlib.Path('phonemis-upstream');native=pathlib.Path('native-voice');native.mkdir(exist_ok=True);shutil.copy2(base/'build/Release/phonemis_runner.exe',native/'phonemis_runner.exe');shutil.copytree(base/'data/en-us',native/'en-us',dirs_exist_ok=True)
import hashlib
manifest={name:hashlib.sha256((native/name).read_bytes()).hexdigest() for name in ['phonemis_runner.exe','en-us/lexicon_full.json','en-us/phonemizer_en_us.bin','en-us/tagger.json']};(native/'manifest.json').write_text(json.dumps(manifest))
with wave.open('ci-jfk.wav') as w:x=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(np.float32)/32768
server=http.server.HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();rows=[]
controller=WorkspaceVoice();ui=tk.Tk();app=Workspace(ui,controller);ui.update()
try:
 with patch.dict(providers.ENDPOINTS,{'local':f'http://127.0.0.1:{server.server_port}/v1'}):
  for index,(name,voice) in enumerate(VOICES.items()):
   app.select(index);ui.update()
   # Factory checks real assets, loads actual STT/VAD/native/frontend/model.
   runtime=controller.factory(name,controller.notify,False,'',False);runtime.mic=Mic();runtime.speaker.output_factory=Sink
   controller.runtime=runtime;runtime.enable(consent=True);samples=[];timing=[];started=time.perf_counter()
   runtime.turn(x,runtime.generation,False,[]);elapsed=time.perf_counter()-started
   assert runtime.history and 'country' in runtime.history[-2]['content'].lower();assert runtime.history[-1]['content']=='Hello. I am ready when you are.';assert samples
   app.poll_voice();ui.update();time.sleep(.25);ui.update()
   assert 'country' in app.caption.lower() and 'ready' in app.response.lower()
   ImageGrab.grab().save(out/(name+'.png'))
   audio=np.concatenate(samples)
   with wave.open(str(out/(name+'.wav')),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes((audio*32767).astype('<i2').tobytes())
   rows.append({'agent':name,'voice':voice,'actual_stt':runtime.history[-2]['content'],'first_wav_write_s':timing[0],'turn_s':elapsed,'wav_s':len(audio)/24000});controller.pause()
 result={'host':'Windows cloud runner, CPU','test':'Actual workspace runtime factory, pinned STT/VAD, synthetic localhost SSE, five native Kokoro voices, WAV output adapter','rows':rows,'unrun':['real microphone','real speaker','real LLM provider','1s audible latency','echo/noise/barge-in','owner accent','installer'],'status':'software integration only'}
 (out/'chain.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
finally:app.close();server.shutdown();server.server_close();thread.join()
