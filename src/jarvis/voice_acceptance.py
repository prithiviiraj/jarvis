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
 trace=open(out/'voice-watchdog.txt','w');faulthandler.enable(file=trace);
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
   self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'models':[{'type':'llm','key':'speech-fixture-not-real-llm','capabilities':{'vision':True},'loaded_instances':[{'id':'speech-fixture-not-real-llm'}]}]}).encode()if self.path=='/api/v1/models'else b'{"data":[{"id":"speech-fixture-not-real-llm"}]}')
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
  def suspend(self):pass
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
   for name in ['JARVIS','LYRA','DEX']:
    progress('select',persona=name);bridge.execute({'command':'select','name':name});samples.clear();loaded=time.monotonic()
    bridge.execute({'command':'voice-on','consent':True});deadline=time.monotonic()+60
    while bridge.voice.busy and time.monotonic()<deadline:time.sleep(.1)
    progress('runtime-ready',persona=name,load_s=time.monotonic()-loaded)
    runtime=bridge.voice.runtime;assert runtime is not None,bridge.execute({'command':'status'})
    from .audio import ENDPOINT_FRAMES
    assert bridge.voice.endpoint_mode=='fast','Experimental session default must be480ms Fast'
    assert runtime.mic.endpointer.silence_frames==ENDPOINT_FRAMES['fast']==15,'Runtime must apply480ms Fast default'
    runtime.speaker.output_factory=Sink
    caption_events=[];original_playback=runtime.speaker.playback_event
    def playback(event,text,actor,sr,n):
     caption_events.append({'event':event,'text':text,'persona':actor,'at':time.monotonic()});original_playback(event,text,actor,sr,n)
    runtime.speaker.playback_event=playback
    assert len(runtime.speaker.profiles)==3
    assert len({id(x.voice)for x in runtime.speaker.profiles.values()})==3
    assert runtime.speaker.profile==name
    # Threaded execution matches the real mic path and keeps the diagnostic clock responsive.
    progress('turn-start',persona=name);started=time.monotonic();runtime.busy=True
    turn=threading.Thread(target=runtime.turn,args=(audio,runtime.generation,False,[]),daemon=True);faulthandler.dump_traceback_later(60,file=trace);turn.start();turn.join(60);faulthandler.cancel_dump_traceback_later()
    if turn.is_alive():
     progress('turn-timeout',persona=name);faulthandler.dump_traceback(file=trace);trace.flush();raise RuntimeError('Speech software turn exceeded60seconds: '+name)
    progress('turn-done',persona=name,turn_s=time.monotonic()-started);runtime.busy=True;state=bridge.execute({'command':'status'});runtime.busy=False
    assert any('country' in x['text'].lower() for x in state['messages'])
    assert any(x['name']==name and x['text']=='Hello. I am ready when you are.' for x in state['messages']),state
    assert len(samples)>0
    metrics=state['voice_metrics'];assert 0<=metrics['stt_s']<=metrics['first_text_s']<=metrics['first_output_write_s']<=metrics['turn_s']
    assert 'not sound heard'in metrics['scope']
    assert 'caption'in state and not state['caption']['active']
    caption_starts=[e for e in caption_events if e['event']=='start'];assert caption_starts and all(e['persona']==name for e in caption_starts)
    assert ' '.join(e['text']for e in caption_starts)=='Hello. I am ready when you are.'
    assert caption_events[-1]['event']=='finish'
    pcm=np.concatenate(samples)
    with wave.open(str(out/(name+'-local-voice.wav')),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes((pcm*32767).astype('<i2').tobytes())
    rows.append({'persona':name,'voice_metrics':metrics,'turn_s':time.monotonic()-started,'wav_s':len(pcm)/24000,'audio_sha256':hashlib.sha256(pcm.tobytes()).hexdigest(),'clean_caption_playback_events':caption_events,'transcript':runtime.history[-2]['content'],'reply':runtime.history[-1]['content']})
    # Keep initial reply measurements isolated, then exercise real popup question
    # and playback with the installed speaker, only STT input phrase controlled.
    samples.clear();before=len(calls);bridge.execute({'command':'status'})
    assert bridge.neural.row is None and bridge.neural_question is None,'Ordinary microphone conversation opened a popup'
    bridge.voice.notify('transcript','show this answer visually');bridge.voice.notify('answer',{'profile':name,'text':'Hello. I am ready when you are.'});bridge.execute({'command':'status'})
    runtime.popup_worker.join(30);assert not runtime.popup_worker.is_alive(),'Popup question exceeded30seconds'
    row=dict(bridge.neural.row);assert bridge.neural_question and bridge.neural_question['row']==row
    assert any(e['event']=='start'and e['text']=='Master, shall I read this aloud?'for e in caption_events)
    with patch.object(type(runtime.stt),'transcribe_cancellable',return_value='yes'):
     runtime.busy=True;runtime.turn(audio,runtime.generation,False,[])
    assert len(calls)==before,'Popup choice must not call model'
    assert samples,'Popup question/read must synthesize real local PCM'
    with patch.object(type(runtime.stt),'transcribe_cancellable',return_value='not now'):
     runtime.busy=True;runtime.turn(audio,runtime.generation,False,[])
    assert bridge.neural.row is None and len(calls)==before
    rows[-1]['popup_scope']='Real automatic question and current-row speech, controlled yes/not-now STT phrases, simulated mic/output; no new model calls'
    # Actual image-bearing runtime turn to loopback, synthetic pixels only.
    import io
    from PIL import Image
    pixels=io.BytesIO();Image.new('RGB',(64,64),'blue').save(pixels,format='JPEG');frame=pixels.getvalue()
    bridge.vision.base_url=f'http://127.0.0.1:{server.server_port}';bridge.vision.enable_screen(lambda:frame,True)
    before=len(calls)
    with patch.object(type(runtime.stt),'transcribe_cancellable',return_value='what is on my screen'):
     runtime.busy=True;runtime.turn(audio,runtime.generation,False,[])
    assert len(calls)==before+1 and any(part['type']=='image_url'for part in calls[-1]['messages'][-1]['content']),'Screen frame absent from actual loopback user turn'
    assert calls[-1]['model']=='speech-fixture-not-real-llm';bridge.vision.disable_screen()
    rows[-1]['screen_scope']='Actual runtime question contains synthetic JPEG in loopback local vision request; no physical screen or semantic vision verification'
    # Camera plus screen must both reach actual user request as current pixels.
    bridge.vision.frame_source=lambda:frame;bridge.vision.enable(True);bridge.vision.enable_screen(lambda:frame,True)
    before=len(calls)
    with patch.object(type(runtime.stt),'transcribe_cancellable',return_value='what can you see now'):
     runtime.busy=True;runtime.turn(audio,runtime.generation,False,[])
    assert len(calls)==before+1
    images=[p['image_url']['url']for p in calls[-1]['messages'][-1]['content']if p['type']=='image_url']
    import base64
    assert len(images)==2 and all(base64.b64decode(u.split(',',1)[1])==frame for u in images)
    bridge.vision.disable();bridge.vision.disable_screen();before=len(calls)
    with patch.object(type(runtime.stt),'transcribe_cancellable',return_value='hello after sharing stopped'):
     runtime.busy=True;runtime.turn(audio,runtime.generation,False,[])
    assert len(calls)==before+1 and isinstance(calls[-1]['messages'][-1]['content'],str),'Stop left image attached'
    rows[-1]['camera_screen_stop_scope']='Actual runtime carries both synthetic camera/screen JPEGs to loopback local request; stop removes images from next question. No hardware or semantic model proof'
    # CI runner's actual primary desktop frame, only to controlled loopback.
    # This exercises frozen PIL capture, not the owner's hardware/model.
    from .game_companion import capture
    captured=capture({'id':1,'title':'Full primary laptop screen'},question=True)
    assert captured and len(captured)<=300000
    observed=Image.open(io.BytesIO(captured));assert observed.width<=1280 and observed.height<=720
    if name=='JARVIS':(out/'frozen-primary-screen-question.jpg').write_bytes(captured)
    bridge.vision.enable_screen(lambda:captured,True);before=len(calls)
    with patch.object(type(runtime.stt),'transcribe_cancellable',return_value='describe the captured runner desktop'):
     runtime.busy=True;runtime.turn(audio,runtime.generation,False,[])
    assert len(calls)==before+1
    sent=[p['image_url']['url']for p in calls[-1]['messages'][-1]['content']if p['type']=='image_url'];assert len(sent)==1 and base64.b64decode(sent[0].split(',',1)[1])==captured
    bridge.vision.disable_screen()
    rows[-1]['runner_screen_scope']='Frozen actual Windows primary capture reaches loopback fixture; no owner desktop or real model semantic proof'


    # More image test turns can exceed one bounded UI poll event batch.
    # Observe the completed turn's queue, then preserve exact pause equality.
    deadline=time.monotonic()+5
    while True:
     state=bridge.execute({'command':'status'})
     if bridge.voice.events.empty():break
     if time.monotonic()>=deadline:raise RuntimeError('Completed voice event queue did not drain')
    progress('pause-start',persona=name);off=bridge.execute({'command':'pause'});progress('pause-done',persona=name);assert not off['voice_active'] and off['messages']==state['messages'],{'before_messages':state['messages'],'after_messages':off['messages'],'remaining_events':bridge.voice.events.qsize()}
    assert off['awareness']['camera']=='off' and off['awareness']['app_monitor'] is False and off['judgment']['enabled'] is False
    runtime=None;turn=None

  from .telegram_voice import TelegramVoice
  import base64
  preview=TelegramVoice().render('Exact reviewed voice fixture.',lambda:False);encoded=base64.b64decode(preview['audio_base64']);assert len(encoded)>100;assert preview['text']=='Exact reviewed voice fixture.'
  (out/'frozen-telegram-Kokoro-preview.mp3').write_bytes(encoded)
  (out/'frozen-telegram-Kokoro-preview.json').write_text(json.dumps({k:v for k,v in preview.items()if k!='audio_base64'},indent=2))
  assert len({row['audio_sha256']for row in rows})==3,'Persona synth outputs unexpectedly identical'
  report={'frozen_executable':True,'real_local_STT_and_three_Kokoro_syntheses':True,'source_audio':audio_url,'fixture_sha256':hashlib.sha256(raw).hexdigest(),'rows':rows,'brain_scope':'controlled local SSE fixture','mic_output_scope':'test adapters, no hardware','unrun':['physical microphone','audible output','real LM Studio model','owner accent','echo/barge-in','laptop load']}
  (out/'frozen-voice-chain.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
 finally:
  progress('cleanup-start');bridge.close();server.shutdown();server.server_close();progress('cleanup-done');faulthandler.cancel_dump_traceback_later();trace.close()
