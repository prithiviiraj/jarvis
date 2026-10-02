"""Opt-in conversation controller. Hardware adapters are separate and unverified."""
from enum import Enum
import threading

class State(str,Enum):
    OFF='off';LISTENING='listening';CAPTURING='capturing';TRANSCRIBING='transcribing';THINKING='thinking';SPEAKING='speaking';ERROR='error'

class VoiceLoop:
    def __init__(self,recorder,transcriber,brain,speaker,notify=lambda *a:None):
        self.recorder=recorder;self.transcriber=transcriber;self.brain=brain;self.speaker=speaker;self.notify=notify
        self.state=State.OFF;self.enabled=False;self.generation=0;self.lock=threading.RLock();self.history=[]
    def set_state(self,state):self.state=state;self.notify('state',state.value)
    def enable(self,consent=False):
        if not consent:raise ValueError('Microphone listening needs explicit session consent.')
        with self.lock:
            if self.enabled:return
            self.enabled=True;self.generation+=1;self.set_state(State.LISTENING)
    def pause(self):
        with self.lock:
            self.enabled=False;self.generation+=1;
            try:self.recorder.cancel()
            finally:
                self.speaker.stop();self.set_state(State.OFF)
    def speech_started(self):
        with self.lock:
            if not self.enabled:return False
            if self.state==State.SPEAKING:self.speaker.stop()
            elif self.state!=State.LISTENING:return False
            try:self.recorder.start()
            except Exception:
                self.notify('error','Microphone start failed.');self.enabled=False;self.set_state(State.OFF);return False
            self.set_state(State.CAPTURING);return True
    def speech_finished(self,cloud_consent=False):
        with self.lock:
            if not self.enabled or self.state!=State.CAPTURING:return False
            generation=self.generation
            try:audio=self.recorder.stop()
            except Exception:
                self.notify('error','Microphone capture failed.');self.set_state(State.LISTENING);return False
            self.set_state(State.TRANSCRIBING)
        # Run on a worker, never the UI/audio callback. No audio files saved here.
        try:
            text=self.transcriber.transcribe(audio)
            with self.lock:
                if not self.enabled or generation!=self.generation:return False
                self.notify('transcript',text);self.set_state(State.THINKING)
            answer=self.brain.ask([{'role':'system','content':'You are a brief local conversation assistant. No actions, tool calls or claims of actions.'}]+self.history[-6:]+[{'role':'user','content':text}],cloud_consent=cloud_consent)
            with self.lock:
                if not self.enabled or generation!=self.generation:return False
                self.history=(self.history+[{'role':'user','content':text},{'role':'assistant','content':answer['text']}])[-6:]
                self.notify('answer',answer);self.set_state(State.SPEAKING);self.speaker.speak(answer['text']);return True
        except Exception:
            with self.lock:
                if generation==self.generation and self.enabled:
                    self.notify('error','Voice turn failed. No action was taken.');self.set_state(State.LISTENING)
            return False
    def speech_playback_finished(self):
        with self.lock:
            if self.enabled and self.state==State.SPEAKING:self.set_state(State.LISTENING)
    def close(self):self.pause();self.history=[]
