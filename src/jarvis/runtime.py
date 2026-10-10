"""Single-owner voice runtime. Headphone/half-duplex safety mode, not AEC/barge-in."""
import threading,time
from .audio import ContinuousMic
from .personas import prompt
from .persona_text import strip_speaker_tag,spoken_text,spoken_chunks
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
    def ask_popup(self,current,asked):
        """One local question between turns. No model request or extra player."""
        with self.lock:
            if not self.enabled or self.busy or self.cancel.is_set():return False
            self.busy=True;self.popup_active=True;generation=self.generation;ticket=self.speaker.generation
            self.mic.suspend()
        def work():
            try:
                if self.valid(generation) and current():
                    self.notify('state','asking Master')
                    self.speaker.speak('Master, shall I read this aloud?',generation=ticket)
                    if self.valid(generation) and self.speaker.generation==ticket and current():asked()
            except Exception as error:self.notify('error','Popup question could not play locally: '+type(error).__name__)
            finally:
                with self.lock:
                    self.busy=False;self.popup_active=False
                    if self.valid(generation) and not self.cancel.is_set():self.mic.resume();self.notify('state','listening')
        self.popup_worker=threading.Thread(target=work,daemon=True);self.popup_worker.start();return True
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
            # An explicit spoken popup choice uses this already paused mic and
            # installed session speaker, not a second playback or model request.
            popup_handler=getattr(self,'neural_handler',None)
            stage='popup choice validation';popup=popup_handler(text)if callable(popup_handler)else None
            if isinstance(popup,dict):
                with self.lock:
                    if not self.valid(generation):return
                    self.notify('popup-transcript',text);self.notify('action-handled',text)
                if popup.get('text'):
                    self.popup_active=True;stage='popup speech synthesis/playback';self.notify('state','reading popup')
                    self.speaker.speak(popup['text'],generation=ticket)
                return
            with self.lock:
                if not self.valid(generation):return
                self.notify('transcript',text);self.notify('state','thinking')
                # Experimental headphone barge-in: listen for speech onset while
                # generating/speaking. Headphones only; no AEC on speakers.
                if getattr(self,'barge_in',False):
                    self.mic.on_onset=lambda:self.interrupt(generation)
                    self.mic.resume()
            from .wake_address import ambiguous
            from .workspace_voice import VOICES
            if ambiguous(text,VOICES):
                self.notify('error','Recognition contains two adjacent teammate names. I did not choose a persona or run the request. Say Hey Jarvis, Hey Lyra, Hey Dex, or type the intended name.')
                return
            # Browser mode uses only explicit commands, not model decisions or page text.
            handler=getattr(self,'action_handler',None)
            if callable(handler) and handler(text):self.notify('action-handled',text);return
            from .persona_text import own_reply
            from .team_discussion import requested,order,clean_reply,messages as discussion_messages
            from .multi_address import addressed,request as addressed_request
            direct=addressed(text)if not requested(text)else()
            if direct or requested(text):
                stage='team discussion';context=list((self.shared_context() if callable(self.shared_context) else history)[-12:]);answers=[]
                actors=direct or order(text,self.persona)
                for index,actor in enumerate(actors):
                    if not self.valid(generation)or self.cancel.is_set():return
                    choose=getattr(self.router,'select_persona',None)
                    if callable(choose):choose(actor)
                    select=getattr(self.speaker,'select_profile',None)
                    if callable(select):select(actor)
                    self.persona=actor;self.notify('voice-actor',actor);self.notify('state',actor+' thinking')
                    request=addressed_request(actor,text,context)if direct else discussion_messages(actor,text,context,index)
                    if callable(getattr(self,'interface_context',None)):request[0]['content']+=self.interface_context(text)
                    if self.streaming:
                        from .speech_queue import SpeechQueue
                        pieces=[];last={};stream_id=str(generation)+'-voice-dialogue-'+str(index)
                        def chunks():
                            nonlocal last
                            for delta in self.router.stream(request,cloud_consent=cloud,cancel=self.cancel):
                                if not self.valid(generation)or self.cancel.is_set():return
                                pieces.append(delta['text']);partial=strip_speaker_tag(''.join(pieces));own_reply(partial,actor,context)
                                if len(partial)>1500:raise ValueError('Team reply too long')
                                last=delta;metrics.setdefault('first_text_s',time.monotonic()-started)
                                self.notify('answer',dict(delta,text=partial,profile=actor,stream_id=stream_id))
                                yield delta['text']
                        def clause(part):
                            metrics.setdefault('first_clause_s',time.monotonic()-started);self.notify('state',actor+' speaking')
                        SpeechQueue(self.speaker,self.cancel).play_stream(spoken_chunks(chunks()),ticket,clause)
                        if not self.valid(generation)or self.cancel.is_set():return
                        answer_text=clean_reply(strip_speaker_tag(''.join(pieces)));own_reply(answer_text,actor,context)
                    else:
                        reply=self.router.ask(request,cloud_consent=cloud,cancel=self.cancel)
                        answer_text=clean_reply(reply.get('text'));own_reply(answer_text,actor,context)
                        if len(answer_text)>1500:raise ValueError('Team reply too long')
                        if not self.valid(generation)or self.cancel.is_set():return
                        self.notify('answer',dict(reply,text=answer_text,profile=actor));self.notify('state',actor+' speaking');spoken=spoken_text(answer_text)
                        if spoken.strip():self.speaker.speak(spoken,generation=ticket)
                    if not self.valid(generation)or self.cancel.is_set():return
                    context.append({'role':'assistant','content':'['+actor+'] '+answer_text});answers.append(answer_text)
                    if callable(self.record_turn):self.record_turn(text,answer_text)
                self.history=(history+[{'role':'user','content':text}]+context[-6:])[-12:]
                return
            # Direct spoken address selects one actual persona and installed voice.
            import re
            from .workspace_voice import VOICES
            names='|'.join(re.escape(n)for n in VOICES)
            match=re.match(r'^\s*(?:(?:hey|hi|hello)[,!.:]?\s+)?('+names+r')\b',text,re.I)
            if not match:match=re.search(r'\b(?:talk|speak|chat)\s+(?:to|with)\s+(jarvis|lyra|dex)\b',text,re.I)
            actor=match.group(1).upper()if match else ('JARVIS'if re.match(r'^\s*(?:(?:hey|hi|hello)[,!.:]?\s+)?laya\b',text,re.I)else self.persona)
            if actor!=self.persona:
                select=getattr(self.speaker,'select_profile',None)
                if callable(select):select(actor);self.persona=actor
            self.notify('voice-actor',self.persona)
            choose=getattr(self.router,'select_persona',None)
            if callable(choose):choose(self.persona)
            if hasattr(self.router,'reasoning_off'):self.router.reasoning_off=self.reasoning_off
            stage='local model response'
            context=self.shared_context() if callable(self.shared_context) else history[-6:]
            messages=[{'role':'system','content':prompt(self.persona)+(self.interface_context(text)if callable(getattr(self,'interface_context',None))else'')}]+context+[{'role':'user','content':text}]
            state_local=False
            for source in (getattr(self,'teammate_awareness',None),getattr(self,'agent_nodes',None)):
                if source is not None:
                    messages,attached=source.attach(messages,self.persona);state_local=state_local or attached
            if state_local:cloud=False
            if self.vision is not None:
                try:messages=self.vision.attach(messages)
                except Exception as vision_error:self.notify('error','Vision frame skipped: '+str(vision_error)[:140])
            if self.streaming:
                from .speech_queue import SpeechQueue
                pieces=[];provider=[]
                def chunks():
                    options={'local_only':True}if state_local else{}
                    providers=getattr(self.router,'providers',None)
                    if isinstance(providers,list)and len(providers)==1 and not providers[0].cloud and 'spark-x2.5' in providers[0].model.lower():
                        from .lmstudio_rest import NativeSparkTransport,SparkRecoveryTransport
                        options['stream_transport']=NativeSparkTransport() if self.reasoning_off else SparkRecoveryTransport(notify=self.notify)
                    for delta in self.router.stream(messages,cloud_consent=cloud,cancel=self.cancel,**options):
                        with self.lock:
                            if not self.valid(generation):return
                            if 'first_text_s' not in metrics:metrics['first_text_s']=time.monotonic()-started
                            pieces.append(delta['text']);provider[:]=[delta]
                            own_reply(strip_speaker_tag(''.join(pieces)),self.persona,context)
                            self.notify('answer',{'text':strip_speaker_tag(''.join(pieces)),**{k:delta[k]for k in ('provider','model','cloud','slot')if k in delta},'profile':self.persona})
                            if delta.get('model'):self.notify('status',delta['provider']+' model '+delta['model'])
                        yield delta['text']
                def clause(part):
                    nonlocal stage
                    stage='speech synthesis/playback'
                    with self.lock:
                        if self.valid(generation):
                            if 'first_clause_s' not in metrics:metrics['first_clause_s']=time.monotonic()-started
                            self.notify('state','speaking')
                SpeechQueue(self.speaker,self.cancel).play_stream(spoken_chunks(chunks()),ticket,clause)
                answer={**(provider[0]if provider else {}),'text':strip_speaker_tag(''.join(pieces))}
                if not answer['text']:raise RuntimeError('Empty reply')
                warnings=getattr(self.router,'last_warnings',[])
                if isinstance(warnings,list):
                    for warning in warnings:self.notify('error',warning)
                records=getattr(self.router,'last_diagnostics',[])
                if isinstance(records,list):self.notify('response-diagnostics',records)
            else:
                answer=self.router.ask(messages,cloud_consent=cloud,**({'local_only':True}if state_local else{}))
                answer['text']=strip_speaker_tag(answer['text'])
                with self.lock:
                    if not self.valid(generation):return
                    metrics['first_text_s']=time.monotonic()-started
                    self.notify('answer',answer);self.notify('state','speaking')
                stage='speech synthesis/playback'
                spoken=spoken_text(answer['text'])
                if spoken.strip():self.speaker.speak(spoken,generation=ticket)
            with self.lock:
                if not self.valid(generation):return
                if callable(self.record_turn):self.record_turn(text,answer['text'])
                self.history=(history+[{'role':'user','content':text},{'role':'assistant','content':answer['text']}])[-6:]
        except Exception as exc:
            records=getattr(self.router,'last_diagnostics',[])
            if stage=='local model response' and isinstance(records,list):self.notify('response-diagnostics',records)
            from .router import RouterError
            from .speech import UnclearSpeech
            detail=str(exc)[:200] if isinstance(exc,RouterError) or (stage=='popup choice validation' and isinstance(exc,ValueError)) else type(exc).__name__
            if 'local-empty-after-retry' in str(exc):detail='local model returned no usable final text after retry (empty streaming and non-streaming replies). This model may not fit this chat template; load a proven chat-instruct model in LM Studio (for example spark-x2.5-4b) or test an enabled cloud account.'
            if 'native-reasoning-off-' in detail:detail+=' Use a non-reasoning model in LM Studio or update LM Studio; no reasoning was spoken'
            with self.lock:
                if self.valid(generation):
                    if isinstance(exc,UnclearSpeech):self.notify('error','Speech was unclear. Please repeat closer to the microphone. Nothing was sent to a model for this turn.')
                    else:self.notify('error','Voice turn failed at '+stage+': '+detail+'. Microphone can listen again; no action was taken.')
        finally:
            with self.lock:
                self.busy=False;self.popup_active=False
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
