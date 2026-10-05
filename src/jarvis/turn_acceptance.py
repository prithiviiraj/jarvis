"""Explicit frozen Smart Turn software acceptance. No physical microphone proof."""
def run():
 import json,pathlib,time,wave,urllib.request
 import numpy as np
 from .experimental.smart_turn import SmartTurn,download,SHA,SIZE,URL
 from .paths import ensure_layout
 from .audio import Endpointer
 out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True)
 path=ensure_layout()/'models'/'smart-turn.onnx';download(path,consent=True)
 start=time.perf_counter();model=SmartTurn(path);load=time.perf_counter()-start
 audio_url='https://raw.githubusercontent.com/ggerganov/whisper.cpp/master/samples/jfk.wav'
 with urllib.request.urlopen(audio_url,timeout=30)as r:raw=r.read(2000000)
 fixture=out/'smart-turn-public-fixture.wav';fixture.write_bytes(raw)
 with wave.open(str(fixture))as w:
  assert w.getframerate()==16000 and w.getnchannels()==1 and w.getsampwidth()==2
  audio=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(np.float32)/32768
 rows=[]
 for label,x in [('complete-public-English',audio),('truncated-public-English-not-quality-proof',audio[:16000*3]),('silence',np.zeros(16000,np.float32))]:
  start=time.perf_counter();complete=model.complete([x]);seconds=time.perf_counter()-start
  assert type(complete)is bool
  rows.append({'fixture':label,'complete':complete,'cpu_s':seconds})
 e=Endpointer(turn_complete=model.complete)
 for _ in range(7):e.feed(np.zeros(512,np.float32),1)
 for i in range(1,76):
  if e.feed(np.zeros(512,np.float32),0):break
 assert i<=75
 report={'actual_SmartTurn_CPU':True,'model_bytes':SIZE,'sha256':SHA,'model_source':URL,'audio_source':audio_url,'frozen_executable':bool(getattr(__import__('sys'),'frozen',False)),'load_s':load,'rows':rows,'bounded_endpoint':True,'scope':'English public fixture decisions, not an accuracy score. No live mic, Tamil, echo cancellation or owner laptop proof.'}
 (out/'frozen-smart-turn-checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
