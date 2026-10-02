"""Local off-by-default break-reminder foundation, not a sensor or background loop.
Only explicit user-declared activity plus elapsed monotonic time is known. Poll
returns a text suggestion once per interval; caller must decide how to show it.
No model/network/audio/screen/camera access, files, auto-start or worker threads.
"""
from dataclasses import dataclass
import math
@dataclass(frozen=True)
class Nudge:
    text:str
    source:str='user-declared activity + elapsed timer'
    observed_screen:bool=False
    spoken:bool=False
class SessionAwareness:
    def __init__(self,clock):
        self.clock=clock;self.enabled=False;self.activity='';self.started=None;self.last=None;self.interval=1800
    def _now(self):
        t=self.clock()
        if isinstance(t,bool) or not isinstance(t,(int,float)) or not math.isfinite(t) or t<0:raise ValueError('Invalid local clock.')
        return t
    def start(self,activity,consent=False,interval_minutes=30):
        if consent is not True:raise ValueError('Explicit session reminder consent required.')
        if activity not in ('gaming','working','watching videos'):raise ValueError('Choose a supported user-declared activity.')
        if isinstance(interval_minutes,bool) or not isinstance(interval_minutes,int) or not 15<=interval_minutes<=180:raise ValueError('Reminder interval must be15-180minutes.')
        now=self._now();self.enabled=True;self.activity=activity;self.started=now;self.last=now;self.interval=interval_minutes*60
    def stop(self):
        self.enabled=False;self.activity='';self.started=None;self.last=None
    def poll(self,quiet=False,busy=False):
        if not self.enabled:return None
        now=self._now()
        if now<self.last or now<self.started:self.stop();return None
        if quiet or busy or now-self.last<self.interval:return None
        minutes=int((now-self.started)//60);self.last=now
        return Nudge('You marked this session as '+self.activity+'. The timer has run for '+str(minutes)+'minutes. Want a break? I cannot see your screen or game results.')
