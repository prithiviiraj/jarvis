"""CI-only explicit frozen software test. Real engines, simulated mic/output/brain."""
def validate_turn_evidence(metrics,caption_events,output_events,persona):
 """No canned ack. Every output must follow real model text and match reply captions."""
 import math
 required=('stt_s','first_text_s','first_output_write_s','turn_s')
 assert all(isinstance(metrics.get(k),(int,float))and not isinstance(metrics[k],bool)and math.isfinite(metrics[k])and metrics[k]>=0 for k in required),metrics
 assert metrics['stt_s']<=metrics['first_text_s']<=metrics['turn_s'],metrics
 assert metrics['first_text_s']<=metrics['first_output_write_s']<=metrics['turn_s'],metrics
 assert 'not sound heard'in metrics['scope'],metrics
 starts=[e for e in caption_events if e['event']=='start']
 assert starts and all(e['persona']==persona for e in starts),caption_events
 assert not any(e['text']=='On it.'for e in starts),caption_events
 assert ' '.join(e['text']for e in starts)=='Hello. I am ready when you are.',caption_events
 assert len(output_events)==len(starts)and all(e['event']=='first-write'for e in output_events),output_events
 # Every actual adapter write belongs inside its corresponding caption lifetime.
 assert len(caption_events)==2*len(starts),caption_events
 for index,start in enumerate(starts):
  opening,closing=caption_events[2*index:2*index+2]
  assert opening==start and closing['event']=='finish',caption_events
  assert opening['at']<=output_events[index]['at']<=closing['at'],(caption_events,output_events)
  assert metrics['stt_s']<=output_events[index]['elapsed_s']<=metrics['turn_s'],(metrics,output_events)
  assert metrics['first_text_s']<=output_events[index]['elapsed_s'],(metrics,output_events)
  if index:assert caption_events[2*index-1]['at']<=opening['at'],caption_events
 assert caption_events[-1]['event']=='finish',caption_events

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
    startup=dict(getattr(runtime,'startup_diagnostics',{}));assert len(startup.get('feedback',[]))==3,startup
    progress('voice-startup-diagnostics',persona=name,**startup)
    runtime.speaker.output_factory=Sink
    caption_events=[];output_events=[];original_playback=runtime.speaker.playback_event;original_output=runtime.speaker.output_event
    def playback(event,text,actor,sr,n):
     caption_events.append({'event':event,'text':text,'persona':actor,'at':time.monotonic()});original_playback(event,text,actor,sr,n)
    runtime.speaker.playback_event=playback
    def output(event,ticket,sr):
     stamp=time.monotonic();output_events.append({'event':event,'ticket':ticket,'sr':sr,'at':stamp,'elapsed_s':stamp-runtime.turn_metrics['started'] if runtime.turn_metrics else None});original_output(event,ticket,sr)
    runtime.speaker.output_event=output
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
    metrics=state['voice_metrics']
    diagnostic={'persona':name,'voice_metrics':metrics,'caption_events':caption_events,'output_events':output_events,'pcm_chunks':len(samples),'scope':'Real local engines; simulated mic/output and loopback model. No physical sound or owner latency proof'}
    (out/(name+'-voice-turn-evidence.json')).write_text(json.dumps(diagnostic,indent=2),encoding='utf-8')
    progress('turn-evidence',**diagnostic)
    validate_turn_evidence(metrics,caption_events,output_events,name)
    assert 'caption'in state and not state['caption']['active']
    pcm=np.concatenate(samples)
    with wave.open(str(out/(name+'-local-voice.wav')),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes((pcm*32767).astype('<i2').tobytes())
    rows.append({'persona':name,'voice_metrics':metrics,'turn_s':time.monotonic()-started,'wav_s':len(pcm)/24000,'audio_sha256':hashlib.sha256(pcm.tobytes()).hexdigest(),'clean_caption_playback_events':caption_events,'transcript':runtime.history[-2]['content'],'reply':runtime.history[-1]['content']})
    # Keep initial reply measurements isolated, then exercise real popup question
    # and playback with the installed speaker, only STT input phrase controlled.
    # Prepared real Kokoro completion PCM, one session speaker, no new synthesis
    # or model request on this result path. Sink is still a simulated device.
    samples.clear();before=len(calls);caption_before=len(caption_events)
    from .completion_feedback import TEXT
    from unittest.mock import patch as check_patch
    runtime.completion_feedback.record('frozen-feedback-'+name,'browser-page-ready',True)
    prepared=time.monotonic()
    with check_patch.object(runtime.speaker,'prepare',side_effect=AssertionError('Result feedback synthesized instead of using prepared PCM')):
     assert runtime.poll_completion();runtime.feedback_worker.join(30);assert not runtime.feedback_worker.is_alive(),'Prepared feedback playback hung'
    assert len(calls)==before and samples,'Prepared receipt called model or produced no PCM'
    assert any(e['event']=='start'and e['text']==TEXT['browser-page-ready']and e['persona']==name for e in caption_events[caption_before:]),caption_events[caption_before:]
    rows[-1]['startup_diagnostics']=startup;rows[-1]['prepared_feedback']={'completion_seconds':time.monotonic()-prepared,'pcm_chunks':len(samples),'scope':'Prepared real PCM to simulated output. Not physical audibility/latency.'}
    if name=='JARVIS':
     # One transcribed utterance, actual sequential local voice syntheses and
     # loopback model requests. This does not prove simultaneous full-duplex audio.
     samples.clear();before=len(calls);captions_before=len(caption_events);runtime.team_mode=True
     with patch.object(type(runtime.stt),'transcribe_cancellable',return_value='Describe this controlled test fixture'):
      runtime.busy=True;runtime.turn(audio,runtime.generation,False,[])
     runtime.team_mode=False
     assert len(calls)==before+3,'ALL did not use three real model routes'
     observed=[e['persona']for e in caption_events[captions_before:]if e['event']=='start'];ordered=[actor for index,actor in enumerate(observed)if index==0 or observed[index-1]!=actor]
     assert ordered==['JARVIS','LYRA','DEX']and samples,observed
     runtime.persona=name;runtime.speaker.select_profile(name);runtime.notify('voice-actor',name)
     rows[-1]['all_voice_scope']='One controlled STT utterance, three actual loopback requests and distinct installed Kokoro profiles in order. Simulated mic/output, not physical echo or full-duplex acceptance.'
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
    # Actual frozen voice command routing preserves supplied news source.
    before=len(calls);output_count=len(samples)
    with patch.object(type(runtime.stt),'transcribe_cancellable',return_value=name+' show news with pictures from https://example.com/news'):
     runtime.busy=True;runtime.turn(audio,runtime.generation,False,[])
    assert bridge.news.pending['value']=='https://example.com/news' and 'https://example.com/news'in bridge.neural.row['text'] and 'Which public'not in bridge.neural.row['text']
    assert bridge.neural.picture is None and bridge.browser is None and len(calls)==before and len(samples)==output_count,'Supplied news source performed work before review'
    # Cancel before poll, so the source-review popup does not ask a new question.
    bridge.news.cancel();bridge.neural.clear();bridge.neural_question=None
    with patch.object(type(runtime.stt),'transcribe_cancellable',return_value=name+' show news'):
     runtime.busy=True;runtime.turn(audio,runtime.generation,False,[])
    assert bridge.news.pending is None and not bridge.news.source and 'Which public'in bridge.neural.row['text'] and len(calls)==before and len(samples)==output_count
    bridge.news.cancel();bridge.neural.clear();bridge.neural_question=None
    rows[-1]['news_source_voice_scope']='Actual frozen microphone command route, controlled STT phrases, exact supplied URL retained; missing source asks once; no page/model/speech before review'
    # Real frozen mixed voice turn. Only isolated browser transport is mocked.
    from unittest.mock import Mock
    browser=Mock();browser.cancel.is_set.return_value=False;browser.snapshot.return_value={'state':'working'}
    bridge.browser=browser;bridge.browser_enabled=True;bridge.laya_active=True;before=len(calls)
    with patch.object(type(runtime.stt),'transcribe_cancellable',return_value='open browser and tell me who Iron Man is'):
     runtime.busy=True;runtime.turn(audio,runtime.generation,False,[])
    browser.submit.assert_called_once_with(command='open-window',value='',confirmed=True)
    assert len(calls)==before+1 and calls[-1]['messages'][-1]['content']=='who Iron Man is'
    bridge.browser=None;bridge.browser_enabled=False;bridge.laya_active=False
    rows[-1]['parallel_command_question_scope']='Actual frozen voice mixed command/question dispatch, browser submission mocked; independent model reply proceeds while browser reports working. No actual site/device latency proof'
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
    entered=threading.Event();release=threading.Event()
    def pending_capture():entered.set();release.wait(10);return frame
    bridge.vision.enable_screen(pending_capture,True);before=len(calls)
    with patch.object(type(runtime.stt),'transcribe_cancellable',return_value='see screen during stop'):
     runtime.busy=True;pending=threading.Thread(target=runtime.turn,args=(audio,runtime.generation,False,[]),daemon=True);pending.start();assert entered.wait(5),'Capture did not start'
     bridge.vision.disable_screen();release.set();pending.join(10);assert not pending.is_alive(),'Stopped capture turn hung'
    assert len(calls)==before,'Revoked in-flight frame sent to model'
    rows[-1]['revoked_capture_scope']='Actual runtime Stop during controlled capture prevents loopback model request; synthetic capture only'



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
