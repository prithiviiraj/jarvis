"""Single-owner voice runtime. Headphone/half-duplex safety mode, not AEC/barge-in."""
import threading,time
from .audio import ContinuousMic
from .personas import prompt
class VoiceRuntime:
    def __init__(self,vad,stt,router,speaker,notify=lambda *a:None):
        self.stt=stt;self.router=router;self.speaker=speaker;self.notify=notify
        self.cancel=threading.Event();self.streaming=False;self.lock=threading.RLock();self.generation=0;self.enabled=False;self.busy=False;self.history=[];self.cloud=False;self.persona='JARVIS'
        self.mic=ContinuousMic(vad,self.on_utterance,notify)
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
        ticket=self.speaker.generation;started=time.monotonic();metrics={}
        try:
            self.notify('state','transcribing');text=self.stt.transcribe(audio);metrics['stt_s']=time.monotonic()-started
            with self.lock:
                if not self.valid(generation):return
                self.notify('transcript',text);self.notify('state','thinking')
            messages=[{'role':'system','content':prompt(self.persona)}]+history[-6:]+[{'role':'user','content':text}]
            if self.streaming:
                from .speech_queue import SpeechQueue
                pieces=[];provider=[]
                def chunks():
                    for delta in self.router.stream(messages,cloud_consent=cloud,cancel=self.cancel):
                        with self.lock:
                            if not self.valid(generation):return
                            if 'first_text_s' not in metrics:metrics['first_text_s']=time.monotonic()-started
                            pieces.append(delta['text']);provider[:]=[delta]
                            self.notify('answer',{'text':''.join(pieces),'provider':delta['provider']})
                        yield delta['text']
                def clause(part):
                    with self.lock:
                        if self.valid(generation):
                            if 'first_clause_s' not in metrics:metrics['first_clause_s']=time.monotonic()-started
                            self.notify('state','speaking')
                SpeechQueue(self.speaker,self.cancel).play_stream(chunks(),ticket,clause)
                answer={'text':''.join(pieces),'provider':provider[0]['provider'] if provider else 'local'}
                if not answer['text']:raise RuntimeError('Empty reply')
            else:
                answer=self.router.ask(messages,cloud_consent=cloud)
                with self.lock:
                    if not self.valid(generation):return
                    self.notify('answer',answer);self.notify('state','speaking')
                self.speaker.speak(answer['text'],generation=ticket)
            with self.lock:
                if not self.valid(generation):return
                self.history=(history+[{'role':'user','content':text},{'role':'assistant','content':answer['text']}])[-6:]
        except Exception:
            with self.lock:
                if self.valid(generation):self.notify('error','Voice turn failed. Check the brain server or repeat clearly. No action was taken.')
        finally:
            with self.lock:
                self.busy=False
                if self.valid(generation):
                    metrics['turn_s']=time.monotonic()-started;metrics['scope']='processing/queued clause timing, not first audible audio';self.notify('metrics',metrics)
                if self.valid(generation) and not self.cancel.is_set():self.mic.resume();self.notify('state','listening')
                elif self.valid(generation):
                    self.enabled=False;self.mic.stop_event.set();self.speaker.stop();self.notify('state','off - voice failed, press Enable to retry')
    def close(self):self.pause();self.history=[]
