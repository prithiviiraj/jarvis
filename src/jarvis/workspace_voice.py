"""Workspace bridge. No sensor, model download or network work on construction."""
import queue
import threading
from pathlib import Path
from .persona_text import strip_speaker_tag,spoken_text
from .personas import ROLES

def banter_wait(stop,interval):return stop.wait(interval)

VOICES = {'JARVIS':'am_michael','NOVA':'af_heart','KAI':'am_liam','LYRA':'af_sky','DEX':'am_fenrir'}

class WorkspaceVoice:
    def __init__(self, factory=None, text_factory=None):
        self.events=queue.Queue();self.factory=factory or build_runtime
        self.text_factory=text_factory or build_text_router
        self.endpoint_mode='balanced';self.tts_engine='kokoro';self.runtime=None;self.name='JARVIS';self.busy=False;self.closed=False
        self.generation=0;self.lock=threading.RLock();self.text_cancel=threading.Event();self.reply_actor='JARVIS';self.vision=None
        from .team_memory import TeamMemory
        self.memory=TeamMemory();self.round_speaker=None;self.pool_config=None;self.banter_stop=threading.Event();self.banter_active=False
    def notify(self,kind,value):self.events.put((kind,value))
    def select(self,name):
        if name not in ROLES:raise ValueError('Unknown profile.')
        self.pause()
        while True:
            try:self.events.get_nowait()
            except queue.Empty:break
        with self.lock:self.name=name
        self.notify('state','off')
    def start(self,consent=False,cloud=False,model='',verified_free=False,reasoning_off=False,barge_in=False):
        if not consent:raise ValueError('Microphone session consent required.')
        if cloud and not verified_free:raise ValueError('Groq needs a confirmed Free-tier account.')
        if self.name not in VOICES:raise ValueError(self.name+' is a silent text specialist with no voice. Type to this profile in chat, or select a voiced profile for the microphone.')
        with self.lock:
            if self.closed or self.busy:raise RuntimeError('Voice setup is busy or closed.')
            self.busy=True;self.generation+=1;ticket=self.generation;name=self.name
        self.notify('state','loading voice')
        def run():
            runtime=None
            try:
                def notify(kind,value):
                    if kind=='answer' and isinstance(value,dict):value={**value,'profile':value.get('profile',name)}
                    with self.lock:
                        if not self.closed and ticket==self.generation:self.notify(kind,value)
                if self.pool_config is not None and self.factory is build_runtime:
                    runtime=build_runtime(name,notify,cloud,model,verified_free,pool_config=self.pool_config,tts_engine=self.tts_engine)
                else:runtime=self.factory(name,notify,cloud,model,verified_free)
                with self.lock:
                    if self.closed or ticket!=self.generation:runtime.close();return
                    from .audio import Endpointer,ENDPOINT_FRAMES
                    runtime.mic.endpointer=Endpointer(silence_frames=ENDPOINT_FRAMES[self.endpoint_mode])
                    runtime.vision=self.vision;runtime.barge_in=barge_in is True
                    self.runtime=runtime;runtime.reasoning_off=reasoning_off is True;runtime.shared_context=self.memory.messages;runtime.record_turn=lambda user,answer:self.memory.append(runtime.persona if isinstance(runtime.persona,str)and runtime.persona in VOICES else name,user,answer);runtime.enable(consent=True,cloud_consent=cloud)
                self.notify('state','listening')
            except Exception as exc:
                if runtime:runtime.close()
                with self.lock:
                    if ticket==self.generation:
                        self.runtime=None;self.notify('error',str(exc)[:300])
            finally:
                with self.lock:self.busy=False
        worker=threading.Thread(target=run,daemon=True);worker.start();return worker
    def send_text(self,text,auto_pick=False):
        if not isinstance(text,str) or not text.strip():raise ValueError('Type a message first.')
        if len(text)>2000:raise ValueError('Message limit is2000characters.')
        with self.lock:
            if self.closed or self.busy:raise RuntimeError('A conversation is busy or closed.')
            if self.runtime is not None:raise RuntimeError('Pause voice before typed chat.')
            self.busy=True;self.generation+=1;ticket=self.generation;name=self.name
            context=self.memory.messages()
            if auto_pick:
                from .moderator import pick
                name,reason=pick(text,self.name)
                self.notify('reply-route',name+' / '+reason+' / one reply')
        self.text_cancel=threading.Event();cancel=self.text_cancel;self.reply_actor=name
        self.notify('transcript',text.strip());self.notify('state','thinking')
        def run():
            try:
                from .personas import prompt
                router=self.text_factory()
                choose=getattr(router,'select_persona',None)
                if callable(choose):choose(name)
                pieces=[];answer={}
                messages=[{'role':'system','content':prompt(name)}]+context+[{'role':'user','content':text.strip()}]
                if self.vision is not None:
                    try:messages=self.vision.attach(messages)
                    except Exception as vision_error:self.notify('error','Vision frame skipped: '+str(vision_error)[:140])
                for delta in router.stream(messages,cloud_consent=False,cancel=cancel):
                    with self.lock:
                        if self.closed or ticket!=self.generation:return
                        pieces.append(delta['text']);answer={**delta,'text':strip_speaker_tag(''.join(pieces))}
                        self.notify('answer',{**answer,'profile':name,'stream_id':ticket})
                if not pieces:raise RuntimeError('Empty local stream')
                warnings=getattr(router,'last_warnings',[])
                if isinstance(warnings,list):
                    for warning in warnings:self.notify('error',warning)
                records=getattr(router,'last_diagnostics',[])
                if isinstance(records,list):self.notify('response-diagnostics',records)
                with self.lock:
                    if self.closed or ticket!=self.generation:return
                    self.memory.append(name,text.strip(),answer['text'])
                    self.notify('team-updated',name)
            except Exception as exc:
                if 'router' in locals():
                    records=getattr(router,'last_diagnostics',[])
                    if isinstance(records,list):self.notify('response-diagnostics',records)
                with self.lock:
                    if not self.closed and ticket==self.generation:
                        if 'local-empty-after-retry' in str(exc):
                            recs=locals().get('records',[]);model=recs[0].get('model','') if isinstance(recs,list) and recs else ''
                            detail='LM Studio returned no final text in streaming or normal chat'+((' from model '+model) if model else '')+'. This model may not fit this chat template. Load a proven chat-instruct model in LM Studio (for example spark-x2.5-4b, which worked on this laptop) or test an enabled cloud account. Check its server log and try hi in LM Studio chat to verify the model/template. '
                        else:detail='Local chat failed: '+str(exc)[:180]+'. '
                        self.notify('error',detail+'LM Studio server port1234. Retry your message.')
            finally:
                with self.lock:
                    self.busy=False
                    if not self.closed and ticket==self.generation:self.notify('state','off')
        worker=threading.Thread(target=run,daemon=True);worker.start();return worker
    def dialogue(self,topic,brains,audio=False,rounds=2):
        """Actual routed turns, with previous observed replies. One audible voice at a time."""
        from .team_discussion import order,messages,clean_reply,participants
        if not isinstance(topic,str)or not topic.strip()or len(topic)>1000:raise ValueError('Enter a short team topic')
        if type(rounds)is not int or not 1<=rounds<=3:raise ValueError('Choose1to3conversation rounds')
        with self.lock:
            if self.closed or self.busy or self.runtime is not None:raise RuntimeError('Stop voice and wait for the current reply first')
            self.busy=True;self.generation+=1;ticket=self.generation;context=self.memory.messages();self.text_cancel=threading.Event();cancel=self.text_cancel
        self.notify('transcript',topic);self.notify('state','team discussion')
        def run():
            speaker=None
            try:
                if audio:
                    speaker=build_proactive_speaker(self.tts_engine);self.round_speaker=speaker
                    speaker.playback_event=lambda event,text,name,sr,samples:self.notify('speech-caption',{'active':event=='start','text':text,'name':name or 'JARVIS','at':__import__('time').monotonic(),'duration_s':samples/sr if sr else 0})
                actors=participants(topic)*rounds+('JARVIS',)
                for index,name in enumerate(actors):
                    if cancel.is_set()or self.closed or ticket!=self.generation:return
                    self.reply_actor=name;self.notify('state',name+' thinking')
                    request=messages(name,topic,context,0)
                    instruction=('Conclude using only this actual conversation. Give master the useful answer, no routine report label.' if index==len(actors)-1 else 'Round '+str(index//len(participants(topic))+1)+': reply only as '+name+' in2to3sentences. React to actual preceding teammates, ask or challenge one point, then add something useful. Never write another profile dialogue. Teasing or disagreement only if invited, no invented mistakes or private knowledge.')
                    request[-1]['content']+='\n'+instruction
                    router=brains.router(name)
                    answer=router.ask(request,cancel=cancel)
                    try:text=clean_reply(answer.get('text'))
                    except ValueError:
                        if cancel.is_set():return
                        answer=router.ask(request+[{'role':'user','content':'Reply only as '+name+'. Do not write any other person reply or speaker labels. One short useful sentence.'}],cancel=cancel)
                        text=clean_reply(answer.get('text'))
                    if cancel.is_set()or self.closed or ticket!=self.generation:return
                    self.notify('answer',{**answer,'text':text,'profile':name,'stream_id':str(ticket)+'-dialogue-'+str(index)})
                    self.memory.append(name,topic,text);context.append({'role':'assistant','content':'['+name+'] '+text})
                    if speaker:
                        speaker.select_profile(name);spoken=spoken_text(text)
                        if spoken.strip():speaker.speak(spoken)
                self.notify('status','Team discussion complete; each shown reply came from its named profile route.')
            except Exception as error:
                if not cancel.is_set():self.notify('error','Team discussion stopped: '+str(error)[:160]+'. Earlier actual replies remain; no invented replacement.')
            finally:
                if speaker:
                    speaker.stop();speaker.synth.g2p.close();self.round_speaker=None
                with self.lock:
                    self.busy=False
                    if not self.closed and ticket==self.generation:self.notify('state','off')
        worker=threading.Thread(target=run,daemon=True);worker.start();return worker
    def parallel_round(self,topic,brains,audio=False):
        """Five bounded parallel perspectives, then ordered output and synthesis."""
        if not isinstance(topic,str)or not topic.strip()or len(topic)>1000:raise ValueError('Enter a team topic up to 1000 characters')
        with self.lock:
            if self.closed or self.busy or self.runtime is not None:raise RuntimeError('Stop voice and wait for the current reply first')
            self.busy=True;self.generation+=1;ticket=self.generation;context=self.memory.messages();self.text_cancel=threading.Event();cancel=self.text_cancel
        self.notify('transcript',topic);self.notify('state','five brains generating in parallel')
        def run():
            speaker=None;results={};failures=[]
            try:
                from concurrent.futures import ThreadPoolExecutor,as_completed
                from .personas import prompt
                def generate(name):
                    instructions='Team topic: '+topic+'\nGive your '+name+' perspective in one short useful sentence. These perspectives are generated in parallel; do not claim you have heard another response.'
                    return brains.router(name).ask([{'role':'system','content':prompt(name)}]+context+[{'role':'user','content':instructions}],cancel=cancel)
                pool=ThreadPoolExecutor(max_workers=5)
                futures={pool.submit(generate,name):name for name in VOICES}
                try:
                    for f in as_completed(futures):
                        if cancel.is_set():return
                        name=futures[f]
                        try:results[name]=f.result()
                        except Exception:failures.append(name)
                        self.notify('status',str(len(results))+'/5 perspectives ready; '+str(len(failures))+' failed')
                finally:pool.shutdown(wait=False,cancel_futures=True)
                if cancel.is_set():return
                if not results:raise RuntimeError('All team routes failed. Test account connections.')
                if audio:
                    speaker=build_proactive_speaker(self.tts_engine);self.round_speaker=speaker
                    if cancel.is_set():return
                    speaker.playback_event=lambda event,text,name,sr,samples:self.notify('speech-caption',{'active':event=='start','text':text,'name':name or 'JARVIS','at':__import__('time').monotonic(),'duration_s':samples/sr if sr else 0})
                ordered=[]
                for name in ('NOVA','KAI','LYRA','DEX','JARVIS'):
                    if cancel.is_set():return
                    if name not in results:continue
                    answer=results[name];answer['text']=strip_speaker_tag(answer['text']);ordered.append({'role':'assistant','content':'['+name+'] '+answer['text']})
                    self.notify('answer',{**answer,'profile':name,'stream_id':str(ticket)+'-'+name});self.memory.append(name,topic,answer['text'])
                    if speaker:
                        self.notify('state','speaking');speaker.select_profile(name);spoken=spoken_text(answer['text'])
                        if spoken.strip():speaker.speak(spoken)
                if cancel.is_set():return
                conclusion=brains.router('JARVIS').ask([{'role':'system','content':prompt('JARVIS')}]+ordered+[{'role':'user','content':'Give a one or two sentence conclusion on '+topic+'. Use only the actual supplied perspectives.'}],cancel=cancel)
                if cancel.is_set():return
                conclusion['text']=strip_speaker_tag(conclusion['text'])
                self.notify('answer',{**conclusion,'profile':'JARVIS','stream_id':str(ticket)+'-conclusion'});self.memory.append('JARVIS',topic,conclusion['text'])
                if speaker:
                    speaker.select_profile('JARVIS');spoken=spoken_text(conclusion['text'])
                    if spoken.strip():speaker.speak(spoken)
                if failures:self.notify('error','Missing team perspectives: '+', '.join(failures)+'. Successful replies and conclusion shown; no invented replies.')
            except Exception as e:
                if not cancel.is_set():self.notify('error','Team round failed: '+str(e)[:160])
            finally:
                if speaker:
                    speaker.stop();speaker.synth.g2p.close();self.round_speaker=None
                with self.lock:
                    self.busy=False
                    if not self.closed and ticket==self.generation:self.notify('state','off')
        worker=threading.Thread(target=run,daemon=True);worker.start();return worker
    def team_round(self,topic,names=('NOVA','JARVIS')):
        """Explicit two-to-five-profile local text round. Not autonomous or audible."""
        if not isinstance(topic,str) or not topic.strip() or len(topic)>1000:raise ValueError('Type a topic up to1000characters.')
        if not isinstance(names,tuple) or not 2<=len(names)<=5 or len(set(names))!=len(names) or any(n not in VOICES for n in names):raise ValueError('Choose2to5different known profiles.')
        with self.lock:
            if self.closed or self.busy or self.runtime is not None:raise RuntimeError('Pause voice and wait for the current conversation first.')
            self.busy=True;self.generation+=1;ticket=self.generation;initial_context=self.memory.messages()
        self.notify('state','thinking');self.notify('round-status','Local text round starting; microphone stays OFF.')
        def run():
            staged=[];context=list(initial_context)
            try:
                from .personas import prompt
                router=self.text_factory()
                for name in names:
                    with self.lock:
                        if self.closed or ticket!=self.generation:return
                    instruction='User-requested team conversation: '+topic.strip()+'\nReply as '+name+' in one or two short sentences. Refer only to actual supplied conversation. Playful banter only if invited in this topic. Other profiles are selectable characters, not autonomous workers. Do not invent sensing, actions, or independent work.'
                    answer=router.ask([{'role':'system','content':prompt(name)}]+context+[{'role':'user','content':instruction}],cloud_consent=False)
                    if not isinstance(answer.get('text'),str) or not answer['text'].strip() or len(answer['text'])>3000:raise ValueError('Invalid round answer.')
                    answer['text']=strip_speaker_tag(answer['text'])
                    staged.append((name,topic.strip(),answer['text']))
                    context=context+[{'role':'user','content':instruction},{'role':'assistant','content':'['+name+'] '+answer['text']}]
                with self.lock:
                    if self.closed or ticket!=self.generation:return
                    for name,user,answer in staged:self.memory.append(name,user,answer)
                    self.notify('team-updated',names[-1]);self.notify('round-status','Completed local text round: '+' → '.join(names)+'. No audio or background workers.')
            except Exception:
                with self.lock:
                    if not self.closed and ticket==self.generation:self.notify('round-status','Local round failed. No partial round saved. Check LM Studio.')
            finally:
                with self.lock:
                    self.busy=False
                    if not self.closed and ticket==self.generation:self.notify('state','off')
        worker=threading.Thread(target=run,daemon=True);worker.start();return worker
    def start_banter(self,topic,names,consent=False,turn_limit=2,interval=3):
        """Opt-in bounded local text session. No mic, cloud, tools or sensing."""
        if consent is not True:raise ValueError('Banter session consent required.')
        if not isinstance(topic,str) or not topic.strip() or len(topic)>1000:raise ValueError('Type a topic up to1000characters.')
        if not isinstance(names,tuple) or not 2<=len(names)<=5 or len(set(names))!=len(names) or any(n not in VOICES for n in names):raise ValueError('Choose2to5different known profiles.')
        if type(turn_limit) is not int or not 2<=turn_limit<=12:raise ValueError('Choose2to12turns.')
        if type(interval) is not int or not 2<=interval<=30:raise ValueError('Choose2to30seconds between turns.')
        with self.lock:
            if self.closed or self.busy or self.runtime is not None:raise RuntimeError('Pause voice and wait for the current conversation first.')
            self.busy=True;self.banter_active=True;self.banter_stop=threading.Event();stop=self.banter_stop
            self.generation+=1;ticket=self.generation;context=self.memory.messages()
        self.notify('banter-status','Running local text session. No audio or sensing; Stop discards this session.')
        def run():
            nonlocal context
            import time
            from .personas import prompt
            staged=[];deadline=time.monotonic()+120
            try:
                router=self.text_factory()
                for i in range(turn_limit):
                    with self.lock:
                        if self.closed or ticket!=self.generation or stop.is_set():return
                    if time.monotonic()>=deadline:raise TimeoutError('Session time limit')
                    name=names[i%len(names)]
                    instruction='User-started bounded playful conversation: '+topic.strip()+'\nReply as '+name+' in one punchy sentence, at most20words, to the supplied prior conversation. You have no screen, camera, game, emotion or work observation. Never claim independent work, actions or sensing. Do not invent facts about the user. Other personas are characters sharing one local model. No tools. Keep banter kind, not personal or hostile.'
                    answer=router.ask([{'role':'system','content':prompt(name)}]+context+[{'role':'user','content':instruction}],cloud_consent=False)
                    text=strip_speaker_tag(answer.get('text'))
                    if not isinstance(text,str) or not text.strip() or len(text)>1000:raise ValueError('Invalid banter reply')
                    with self.lock:
                        if self.closed or ticket!=self.generation or stop.is_set():return
                    if time.monotonic()>=deadline:raise TimeoutError('Session time limit')
                    staged.append((name,topic.strip(),text));context=context+[{'role':'user','content':instruction},{'role':'assistant','content':'['+name+'] '+text}]
                    # Bounded supplied context even across repeated persona turns.
                    while len(context)>2 and sum(len(m['content']) for m in context)>12000:context=context[2:]
                    self.notify('banter-preview',(ticket,name,text,i+1,turn_limit))
                    if i+1<turn_limit and banter_wait(stop,interval):return
                with self.lock:
                    if self.closed or ticket!=self.generation or stop.is_set():return
                    for name,user,text in staged:self.memory.append(name,user,text)
                    self.notify('team-updated',names[-1]);self.notify('banter-status','Completed '+str(turn_limit)+' local text turns. Saved to shared conversation. Session OFF.')
            except Exception:
                with self.lock:
                    if not self.closed and ticket==self.generation:self.notify('banter-status','Session failed or reached120seconds. No partial session saved. Check LM Studio.')
            finally:
                with self.lock:
                    self.busy=False;self.banter_active=False
        worker=threading.Thread(target=run,daemon=True);worker.start();return worker
    def stop_banter(self):
        with self.lock:
            self.banter_stop.set();self.generation+=1;self.banter_active=False
        self.notify('banter-status','OFF. Current session discarded. In-flight local request may finish, but its reply will not be saved.')
    def pause(self):
        if self.round_speaker is not None:self.round_speaker.stop()
        with self.lock:self.text_cancel.set();self.banter_stop.set();self.banter_active=False;self.generation+=1;runtime=self.runtime;self.runtime=None
        if runtime:runtime.close()
        self.notify('state','off')
    def close(self):
        with self.lock:self.closed=True
        self.pause();self.memory.clear()

class FreeSessionRouter:
    """Plan confirmation is session scoped. It is not automatic billing verification."""
    def __init__(self,router,verified):self.router=router;self.verified=('groq',) if verified else ()
    def ask(self,*args,**kw):return self.router.ask(*args,verified_free_providers=self.verified,**kw)
    def stream(self,*args,**kw):return self.router.stream(*args,verified_free_providers=self.verified,**kw)

def build_runtime(name,notify,cloud=False,model='',verified_free=False,pool_config=None,tts_engine='kokoro'):
    from .paths import ensure_layout
    from . import models
    from .voice_assets import ready
    from .experimental.kokoro import NativeG2P,KokoroSynth
    from .experimental.kokoro_speaker import KokoroSpeaker
    from .providers import local_models,configured
    from .router import BrainRouter
    from .security import WindowsCredentials
    from .audio import SileroVad
    from .speech import WhisperSTT
    from .runtime import VoiceRuntime
    cache=ensure_layout()/'models';assets=cache/'voices'
    from . import kitten_assets
    if not models.ready(cache) or not (ready(assets)if tts_engine=='kokoro'else kitten_assets.ready(cache/'kitten')):raise RuntimeError('Verified speech assets missing. Download models and install the native voice frontend first.')
    from .native_frontend import verified_frontend
    exe,data=verified_frontend()
    if pool_config is not None:
        pool,consented,free_confirmed=pool_config
        router=pool.router(name,WindowsCredentials(),consented,free_confirmed)
        notify('status','Configured account pool / session confirmed by you, not verified by API.')
    elif cloud:
        if not verified_free:raise ValueError('Confirm Groq Free-tier status.')
        keys=WindowsCredentials()
        if not keys.get('groq'):raise RuntimeError('Save your Groq API key in Settings first.')
        from .groq_models import resolve_model
        model,listed=resolve_model(model,True,True,keys,details=True)
        notify('status','Groq model: '+model+' / Free plan confirmed by you, not verified by API.')
        from dataclasses import replace
        provider=replace(configured('groq',model),allow_20b_fallback='openai/gpt-oss-20b' in listed)
        router=FreeSessionRouter(BrainRouter([provider],key_store=keys),True)
    else:
        ids=local_models()
        if len(ids)!=1:raise RuntimeError('Load exactly one chat model in LM Studio.')
        from dataclasses import replace
        router=BrainRouter([replace(configured('local',ids[0]),timeout=30)])
    g2p=NativeG2P(exe,data)
    try:
        if tts_engine=='kitten':
            from .experimental.kitten_onnx import KittenONNX
            names=dict(zip(VOICES,('Jasper','Luna','Bruno','Rosie','Hugo')))
            profiles={actor:KittenONNX(cache/'kitten',g2p,voice)for actor,voice in names.items()}
            speaker=KokoroSpeaker(profiles[name]);speaker.profiles=profiles
        else:
            synth=KokoroSynth(assets/'model.onnx',assets/(VOICES[name]+'.bin'),assets/'config.json',g2p)
            speaker=KokoroSpeaker(synth)
            speaker.profiles={actor:KokoroSynth(assets/'model.onnx',assets/(voice+'.bin'),assets/'config.json',g2p)for actor,voice in VOICES.items()}
        speaker.select_profile(name)
        runtime=VoiceRuntime(SileroVad(cache/'silero.onnx'),WhisperSTT(cache/'whisper-base',vocabulary='JARVIS team leader. NOVA secretary. KAI researcher. LYRA writer. DEX coder.',language='en'),router,speaker,notify)
        runtime.streaming=True;runtime.persona=name
        # No closure over runtime.close: that cycle delays native engine disposal.
        runtime.close_hook=g2p.close
        return runtime
    except Exception:g2p.close();raise

def build_text_router():
    """Local-only text: no microphone, speech assets, keys or cloud fallback."""
    from .providers import local_models,configured
    from .router import BrainRouter
    ids=local_models()
    if len(ids)!=1:raise RuntimeError('Load exactly one chat model in LM Studio.')
    from dataclasses import replace
    return BrainRouter([replace(configured('local',ids[0]),timeout=30)])

def build_proactive_speaker(tts_engine='kokoro'):
    """JARVIS output only: no microphone/STT/cloud/model download."""
    from .paths import ensure_layout
    from .voice_assets import ready
    from .experimental.kokoro import NativeG2P,KokoroSynth
    from .experimental.kokoro_speaker import KokoroSpeaker
    from .native_frontend import verified_frontend
    cache=ensure_layout()/'models';assets=cache/'voices'
    from . import kitten_assets
    if not (ready(assets)if tts_engine=='kokoro'else kitten_assets.ready(cache/'kitten')):raise RuntimeError('Verified voice assets missing')
    exe,data=verified_frontend();g2p=NativeG2P(exe,data)
    try:
        if tts_engine=='kitten':
            from .experimental.kitten_onnx import KittenONNX
            profiles={n:KittenONNX(cache/'kitten',g2p,v)for n,v in zip(VOICES,('Jasper','Luna','Bruno','Rosie','Hugo'))}
        else:profiles={n:KokoroSynth(assets/'model.onnx',assets/(v+'.bin'),assets/'config.json',g2p)for n,v in VOICES.items()}
        speaker=KokoroSpeaker(profiles['JARVIS']);speaker.profiles=profiles;speaker.select_profile('JARVIS')
        speaker.close=lambda:(speaker.stop(),g2p.close())
        return speaker
    except Exception:g2p.close();raise
