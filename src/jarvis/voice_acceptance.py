"""CI-only explicit frozen software test. Real engines, simulated mic/output/brain."""
def run():
 import os,json,pathlib,threading,http.server,wave,urllib.request,time,hashlib
 import numpy as np
 from unittest.mock import patch
 from .ui_bridge import Bridge
 from . import providers
 from .paths import ensure_layout
 from .models import download,ready
 from .voice_assets import download as download_voices
 out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True)
 import faulthandler
 trace=open(out/'voice-watchdog.txt','w');faulthandler.enable(file=trace);faulthandler.dump_traceback_later(60,repeat=True,file=trace)
 def progress(stage,**values):
  row={'stage':stage,**values};print(json.dumps(row),flush=True)
  with open(out/'voice-progress.jsonl','a') as f:f.write(json.dumps(row)+'\n')
 progress('start')
 os.environ['JARVIS_DATA_DIR']=str(pathlib.Path('ci-voice-cache').resolve())
 cache=ensure_layout()/'models';progress('download-assets');download(cache,consent=True);download_voices(cache/'voices',consent=True);progress('assets-ready')
 audio_url='https://raw.githubusercontent.com/ggerganov/whisper.cpp/master/samples/jfk.wav'
 with urllib.request.urlopen(audio_url,timeout=30) as response:raw=response.read(2000000)
 fixture=out/'voice-public-fixture.wav';fixture.write_bytes(raw)
 with wave.open(str(fixture)) as w:
  assert w.getframerate()==16000 and w.getnchannels()==1 and w.getsampwidth()==2
  audio=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(np.float32)/32768
 calls=[]
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   self.send_response(200);self.end_headers();self.wfile.write(b'{"data":[{"id":"speech-fixture-not-real-llm"}]}')
  def do_POST(self):
   body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));calls.append(body)
   assert body['stream']
   self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
   for text in ['Hello. ','I am ready when you are.']:
    self.wfile.write(('data: '+json.dumps({'choices':[{'delta':{'content':text}}]})+'\n\n').encode());self.wfile.flush()
   self.wfile.write(b'data: [DONE]\n\n')
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
 samples=[]
 class Mic:
  def __init__(self,*args):self.enabled=False
  def start(self,consent=False):assert consent;self.enabled=True
  def close(self):self.enabled=False
  def resume(self):pass
 class Sink:
  def __init__(self,sr):assert sr==24000
  def start(self):pass
  def write(self,x):samples.append(np.asarray(x,dtype=np.float32).copy())
  def stop(self):pass
  def abort(self):pass
  def close(self):pass
 bridge=Bridge();rows=[]
 try:
  assert not bridge.execute({'command':'status'})['voice_active']
  with patch.dict(providers.ENDPOINTS,{'local':f'http://127.0.0.1:{server.server_port}/v1'}),patch('jarvis.runtime.ContinuousMic',Mic):
   for name in ['JARVIS','NOVA','KAI','LYRA','DEX']:
    progress('select',persona=name);bridge.execute({'command':'select','name':name});samples.clear();loaded=time.monotonic()
    bridge.execute({'command':'voice-on','consent':True});deadline=time.monotonic()+60
    while bridge.voice.busy and time.monotonic()<deadline:time.sleep(.1)
    progress('runtime-ready',persona=name,load_s=time.monotonic()-loaded)
    runtime=bridge.voice.runtime;assert runtime is not None,bridge.execute({'command':'status'})
    runtime.speaker.output_factory=Sink
    caption_events=[];original_playback=runtime.speaker.playback_event
    def playback(event,text,actor,sr,n):
     caption_events.append({'event':event,'text':text,'persona':actor,'at':time.monotonic()});original_playback(event,text,actor,sr,n)
    runtime.speaker.playback_event=playback
    assert len(runtime.speaker.profiles)==5
    assert len({id(x.voice)for x in runtime.speaker.profiles.values()})==5
    assert runtime.speaker.profile==name
    # Threaded execution matches the real mic path and keeps the diagnostic clock responsive.
    progress('turn-start',persona=name);started=time.monotonic();runtime.busy=True
    turn=threading.Thread(target=runtime.turn,args=(audio,runtime.generation,False,[]),daemon=True);turn.start();turn.join(60)
    if turn.is_alive():
     progress('turn-timeout',persona=name);faulthandler.dump_traceback(file=trace);trace.flush();raise RuntimeError('Speech software turn exceeded60seconds: '+name)
    progress('turn-done',persona=name,turn_s=time.monotonic()-started);state=bridge.execute({'command':'status'})
    assert any('country' in x['text'].lower() for x in state['messages'])
    assert any(x['name']==name and x['text']=='Hello. I am ready when you are.' for x in state['messages']),state
    assert len(samples)>0
    assert 'caption'in state and not state['caption']['active']
    caption_starts=[e for e in caption_events if e['event']=='start'];assert caption_starts and all(e['persona']==name for e in caption_starts)
    assert ' '.join(e['text']for e in caption_starts)=='Hello. I am ready when you are.'
    assert caption_events[-1]['event']=='finish'
    pcm=np.concatenate(samples)
    with wave.open(str(out/(name+'-local-voice.wav')),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes((pcm*32767).astype('<i2').tobytes())
    rows.append({'persona':name,'turn_s':time.monotonic()-started,'wav_s':len(pcm)/24000,'audio_sha256':hashlib.sha256(pcm.tobytes()).hexdigest(),'clean_caption_playback_events':caption_events,'transcript':runtime.history[-2]['content'],'reply':runtime.history[-1]['content']})
    progress('pause-start',persona=name);off=bridge.execute({'command':'pause'});progress('pause-done',persona=name);assert not off['voice_active'] and not off['messages']
    runtime=None;turn=None

  assert len({row['audio_sha256']for row in rows})==5,'Persona synth outputs unexpectedly identical'
  report={'frozen_executable':True,'real_local_STT_and_five_Kokoro_syntheses':True,'source_audio':audio_url,'fixture_sha256':hashlib.sha256(raw).hexdigest(),'rows':rows,'brain_scope':'controlled local SSE fixture','mic_output_scope':'test adapters, no hardware','unrun':['physical microphone','audible output','real LM Studio model','owner accent','echo/barge-in','laptop load']}
  (out/'frozen-voice-chain.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
 finally:
  progress('cleanup-start');bridge.close();server.shutdown();server.server_close();progress('cleanup-done');faulthandler.cancel_dump_traceback_later();trace.close()
