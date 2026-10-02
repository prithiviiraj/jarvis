"""Single-owner voice runtime. Headphone/half-duplex safety mode, not AEC/barge-in."""
import threading
from .audio import ContinuousMic
class VoiceRuntime:
    def __init__(self,vad,stt,router,speaker,notify=lambda *a:None):
        self.stt=stt;self.router=router;self.speaker=speaker;self.notify=notify
        self.lock=threading.RLock();self.generation=0;self.enabled=False;self.busy=False;self.history=[];self.cloud=False
        self.mic=ContinuousMic(vad,self.on_utterance,notify)
    def enable(self,consent=False,cloud_consent=False):
        if not consent:raise ValueError('Microphone needs session consent.')
        with self.lock:
            if self.enabled:return
            self.cloud=bool(cloud_consent);self.enabled=True;self.generation+=1
            try:self.mic.start(consent=True)
            except Exception:self.enabled=False;raise
    def pause(self):
        # Never wait on the turn worker under its state lock.
        with self.lock:self.enabled=False;self.generation+=1
        self.mic.close();self.speaker.stop();self.notify('state','off')
    def on_utterance(self,audio):
        with self.lock:
            if not self.enabled or self.busy:return
            self.busy=True;generation=self.generation;cloud=self.cloud;history=list(self.history)
        threading.Thread(target=self.turn,args=(audio,generation,cloud,history),daemon=True).start()
    def valid(self,generation):return self.enabled and generation==self.generation
    def turn(self,audio,generation,cloud,history):
        ticket=self.speaker.generation
        try:
            self.notify('state','transcribing');text=self.stt.transcribe(audio)
            with self.lock:
                if not self.valid(generation):return
                self.notify('transcript',text);self.notify('state','thinking')
            answer=self.router.ask([{'role':'system','content':'You are JARVIS, a brief conversational assistant. You cannot perform actions. Do not claim you sent, deleted, booked or changed anything.'}]+history[-6:]+[{'role':'user','content':text}],cloud_consent=cloud)
            with self.lock:
                if not self.valid(generation):return
                self.history=(history+[{'role':'user','content':text},{'role':'assistant','content':answer['text']}])[-6:]
                self.notify('answer',answer);self.notify('state','speaking')
            # Blocking speech is outside lock so Pause can kill playback immediately.
            self.speaker.speak(answer['text'],generation=ticket)
        except Exception:
            with self.lock:
                if self.valid(generation):self.notify('error','Voice turn failed. Check the brain server or repeat clearly. No action was taken.')
        finally:
            with self.lock:
                self.busy=False
                if self.valid(generation):self.mic.resume();self.notify('state','listening')
    def close(self):self.pause();self.history=[]
