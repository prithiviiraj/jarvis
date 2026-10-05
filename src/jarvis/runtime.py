"""Single-owner voice runtime. Headphone/half-duplex safety mode, not AEC/barge-in."""
import threading,time
from .audio import ContinuousMic
from .personas import prompt
class VoiceRuntime:
    def __init__(self,vad,stt,router,speaker,notify=lambda *a:None):
        self.stt=stt;self.router=router;self.speaker=speaker;self.notify=notify
        self.cancel=threading.Event();self.streaming=False;self.reasoning_off=False;self.lock=threading.RLock();self.generation=0;self.enabled=False;self.busy=False;self.history=[];self.cloud=False;self.persona='JARVIS'
        self.turn_metrics=None;self.shared_context=None;self.record_turn=None;self.close_hook=None
        self.vision=None;self.barge_in=False
        self.mic=ContinuousMic(vad,self.on_utterance,notify)
        self.speaker.playback_event=lambda event,text,actor,sr,n:self.notify('speech-caption',{'active':event=='start','name':actor or self.persona,'text':text,'duration_s':n/sr if sr else 0,'at':time.monotonic()})
        self.speaker.output_event=self.output_event
    def output_event(self,event,ticket,sr):
        with self.lock:
            current=self.turn_metrics
            if event!='first-write' or not current or ticket!=current['ticket'] or not self.valid(current['generation']) or self.cancel.is_set():return
            current['metrics'].setdefault('first_output_write_s',time.monotonic()-current['started'])
    def enable(self,consent=False,cloud_consent=False):
        if not consent:raise ValueError('Microphone needs session consent.')
        with self.lock:
            if self.enabled:return
            if self.busy:raise RuntimeError('Previous voice turn is still stopping. Wait a moment before enabling.')
            self.cloud=bool(cloud_consent);self.enabled=True;self.generation+=1;self.cancel.clear()
            try:self.mic.start(consent=True)
            except Exception:self.enabled=False;raise
    def pause(self):
        # Never wait on the turn worker under its state lock.
        with self.lock:self.enabled=False;self.generation+=1;self.cancel.set()
        self.mic.close();self.speaker.stop();self.notify('state','off')
    def on_utterance(self,audio):
        with self.lock:
            if not self.enabled or self.busy:return
            self.busy=True;generation=self.generation;cloud=self.cloud;history=list(self.history)
        threading.Thread(target=self.turn,args=(audio,generation,cloud,history),daemon=True).start()
    def valid(self,generation):return self.enabled and generation==self.generation
    def turn(self,audio,generation,cloud,history):
        ticket=self.speaker.generation;started=time.monotonic();metrics={};stage='transcription'
        with self.lock:self.turn_metrics={'ticket':ticket,'started':started,'generation':generation,'metrics':metrics}
        self.notify('metrics',{})
        try:
            self.notify('response-diagnostics',[]);self.notify('error','');self.notify('state','transcribing');cancellable=getattr(type(self.stt),'transcribe_cancellable',None);text=cancellable(self.stt,audio,self.cancel)if callable(cancellable)else self.stt.transcribe(audio);metrics['stt_s']=time.monotonic()-started
            with self.lock:
                if not self.valid(generation):return
                self.notify('transcript',text);self.notify('state','thinking')
                # Experimental headphone barge-in: listen for speech onset while
                # generating/speaking. Headphones only; no AEC on speakers.
                if getattr(self,'barge_in',False):
                    self.mic.on_onset=lambda:self.interrupt(generation)
                    self.mic.resume()
            # Browser mode uses only explicit commands, not model decisions or page text.
            handler=getattr(self,'action_handler',None)
            if callable(handler) and handler(text):return
            from .team_discussion import requested,order,messages as discussion_messages
            if requested(text):
                stage='team discussion';context=list(history[-6:]);answers=[]
                for index,actor in enumerate(order(text)):
                    if not self.valid(generation)or self.cancel.is_set():return
                    choose=getattr(self.router,'select_persona',None)
                    if callable(choose):choose(actor)
                    select=getattr(self.speaker,'select_profile',None)
                    if callable(select):select(actor)
                    self.persona=actor;self.notify('voice-actor',actor);self.notify('state','thinking')
                    reply=self.router.ask(discussion_messages(actor,text,context,index),cloud_consent=cloud,cancel=self.cancel)
                    answer_text=reply.get('text')
                    if not isinstance(answer_text,str)or not answer_text.strip()or len(answer_text)>1500:raise ValueError('Invalid discussion reply')
                    if not self.valid(generation)or self.cancel.is_set():return
                    self.notify('answer',dict(reply,profile=actor));self.notify('state','speaking');self.speaker.speak(answer_text,generation=ticket)
                    if not self.valid(generation)or self.cancel.is_set():return
                    context.append({'role':'assistant','content':'['+actor+'] '+answer_text});answers.append(answer_text)
                    if callable(self.record_turn):self.record_turn(text,answer_text)
                self.history=(history+[{'role':'user','content':text}]+context[-6:])[-12:]
                return
            # Direct spoken address selects one actual persona and installed voice.
            import re
            match=re.match(r'^\s*(?:(?:hey|hi|hello)[,!.:]?\s+)?(jarvis|nova|kai|lyra|dex)\b',text,re.I)
            actor=match.group(1).upper()if match else self.persona
            if actor!=self.persona:
                select=getattr(self.speaker,'select_profile',None)
                if callable(select):select(actor);self.persona=actor
            self.notify('voice-actor',self.persona)
            choose=getattr(self.router,'select_persona',None)
            if callable(choose):choose(self.persona)
            if hasattr(self.router,'reasoning_off'):self.router.reasoning_off=self.reasoning_off
            stage='local model response'
            context=self.shared_context() if callable(self.shared_context) else history[-6:]
            messages=[{'role':'system','content':prompt(self.persona)}]+context+[{'role':'user','content':text}]
            if self.vision is not None:
                try:messages=self.vision.attach(messages)
                except Exception as vision_error:self.notify('error','Vision frame skipped: '+str(vision_error)[:140])
            if self.streaming:
                from .speech_queue import SpeechQueue
                pieces=[];provider=[]
                def chunks():
                    options={}
                    providers=getattr(self.router,'providers',None)
                    if isinstance(providers,list)and len(providers)==1 and not providers[0].cloud and 'spark-x2.5' in providers[0].model.lower():
                        from .lmstudio_rest import NativeSparkTransport,SparkRecoveryTransport
                        options['stream_transport']=NativeSparkTransport() if self.reasoning_off else SparkRecoveryTransport(notify=self.notify)
                    for delta in self.router.stream(messages,cloud_consent=cloud,cancel=self.cancel,**options):
                        with self.lock:
                            if not self.valid(generation):return
                            if 'first_text_s' not in metrics:metrics['first_text_s']=time.monotonic()-started
                            pieces.append(delta['text']);provider[:]=[delta]
                            self.notify('answer',{'text':''.join(pieces),'provider':delta['provider'],'profile':self.persona})
                            if delta.get('model'):self.notify('status',delta['provider']+' model '+delta['model'])
                        yield delta['text']
                def clause(part):
                    nonlocal stage
                    stage='speech synthesis/playback'
                    with self.lock:
                        if self.valid(generation):
                            if 'first_clause_s' not in metrics:metrics['first_clause_s']=time.monotonic()-started
                            self.notify('state','speaking')
                SpeechQueue(self.speaker,self.cancel).play_stream(chunks(),ticket,clause)
                answer={'text':''.join(pieces),'provider':provider[0]['provider'] if provider else 'local'}
                if not answer['text']:raise RuntimeError('Empty reply')
                warnings=getattr(self.router,'last_warnings',[])
                if isinstance(warnings,list):
                    for warning in warnings:self.notify('error',warning)
                records=getattr(self.router,'last_diagnostics',[])
                if isinstance(records,list):self.notify('response-diagnostics',records)
            else:
                answer=self.router.ask(messages,cloud_consent=cloud)
                with self.lock:
                    if not self.valid(generation):return
                    metrics['first_text_s']=time.monotonic()-started
                    self.notify('answer',answer);self.notify('state','speaking')
                stage='speech synthesis/playback'
                self.speaker.speak(answer['text'],generation=ticket)
            with self.lock:
                if not self.valid(generation):return
                if callable(self.record_turn):self.record_turn(text,answer['text'])
                self.history=(history+[{'role':'user','content':text},{'role':'assistant','content':answer['text']}])[-6:]
        except Exception as exc:
            records=getattr(self.router,'last_diagnostics',[])
            if stage=='local model response' and isinstance(records,list):self.notify('response-diagnostics',records)
            from .router import RouterError
            from .speech import UnclearSpeech
            detail=str(exc)[:200] if isinstance(exc,RouterError) else type(exc).__name__
            if 'native-reasoning-off-' in detail:detail+=' Use a non-reasoning model in LM Studio or update LM Studio; no reasoning was spoken'
            with self.lock:
                if self.valid(generation):
                    if isinstance(exc,UnclearSpeech):self.notify('error','Speech was unclear. Please repeat closer to the microphone. Nothing was sent to a model for this turn.')
                    else:self.notify('error','Voice turn failed at '+stage+': '+detail+'. Microphone can listen again; no action was taken.')
        finally:
            with self.lock:
                self.busy=False
                if self.valid(generation):
                    metrics['turn_s']=time.monotonic()-started;metrics['scope']='session voice processing; first output write is PCM submitted to an adapter, not sound heard; no hardware latency measurement';self.notify('metrics',dict(metrics))
                self.turn_metrics=None;self.mic.on_onset=None
                if self.valid(generation) and not self.cancel.is_set():self.mic.resume();self.notify('state','listening')
                elif self.valid(generation):
                    self.enabled=False;self.mic.stop_event.set();self.speaker.stop();self.notify('state','off - voice failed, press Enable to retry')
    def interrupt(self,generation):
        """User speech onset during our reply: stop output, keep their new utterance."""
        with self.lock:
            if not self.valid(generation):return
            old=self.cancel;self.cancel=threading.Event();self.generation+=1
            old.set()
        self.speaker.stop();self.notify('state','listening');self.notify('status','Interrupted - listening to you')
    def close(self):
        self.pause();self.history=[];self.shared_context=None;self.record_turn=None
        hook=self.close_hook;self.close_hook=None
        if hook:hook()
