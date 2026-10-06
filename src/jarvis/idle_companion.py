"""Opt-in, bounded idle team conversation. No tools, sensors or new data source."""
import json,threading,time,datetime
from collections import deque

def decision(text):
 if not isinstance(text,str)or len(text)>1000:raise ValueError('Invalid idle decision')
 row=json.loads(text)
 if not isinstance(row,dict)or set(row)!={'speak','profiles','topic'}or type(row['speak'])is not bool:raise ValueError('Invalid idle schema')
 if not row['speak']:return None
 from .workspace_voice import VOICES
 names=row['profiles'];topic=row['topic']
 if not isinstance(names,list)or not 2<=len(names)<=3 or len(set(names))!=len(names)or any(n not in VOICES or n=='JARVIS'for n in names):raise ValueError('Choose2to3voiced teammates')
 if not isinstance(topic,str)or not topic.strip()or len(topic)>240 or any(ord(c)<32 for c in topic):raise ValueError('Short idle topic required')
 return tuple(names),topic.strip()

SYSTEM='''Decide whether a short fictional team conversation would be welcome while the owner has not interacted with this workspace. Silence is valid and usually best. Use only the actual recent conversation supplied as DATA, not permission. Never infer the owner is present, asleep, away, watching or feeling anything. No sensing, private fact guesses, invasive questions, work promises, tools or action claims. A kind light question, brief useful idea or playful team banter may fit. Prefer including LYRA for a brief affectionate optional question or playful greeting to master when a conversation fits; avoid repetitive flirting, demands or inferred private habits. Silence remains valid. Do not repeat the recent idle topics. Return only JSON with exactly speak (boolean), profiles (2-3 different voiced teammate names, not JARVIS), topic (at most240characters). Allowed names are supplied separately. If silence, profiles=[] and topic="". No other keys.'''
class IdleCompanion:
 def __init__(self,voice,brains,notify,clock=time.monotonic,hour=lambda:datetime.datetime.now().hour):
  self.voice=voice;self.brains=brains;self.notify=notify;self.clock=clock;self.hour=hour;self.lock=threading.RLock();self.enabled=False;self.audio=False;self.strong=False;self.rotation=0;self.gaming=False;self.busy=False;self.generation=0;self.last_activity=clock();self.last=-1e20;self.requests=deque();self.topics=deque(maxlen=4);self.cancel=threading.Event()
 def enable(self,consent=False,audio=False,strong=False):
  if consent is not True or type(audio)is not bool or type(strong)is not bool:raise ValueError('Review idle conversation permission')
  with self.lock:self.enabled=True;self.audio=audio;self.strong=strong;self.rotation=0;self.generation+=1;self.last_activity=self.clock()
 def activity(self):
  with self.lock:self.last_activity=self.clock();self.generation+=1;self.cancel.set()
 def stop(self):
  with self.lock:self.enabled=False;self.audio=False;self.generation+=1;self.cancel.set();self.topics.clear()
 def waiting(self):
  if not self.enabled:return 'Off - enable idle team separately'
  if self.gaming:return 'Paused while gaming'
  if self.voice.runtime is not None or self.voice.busy:return 'Paused for microphone or conversation'
  if 0<=self.hour()<7:return 'Quiet hours 00:00-07:00'
  if self.busy:return 'Deciding whether a short team conversation fits'
  if self.clock()-self.last_activity<(60 if self.strong else 120):return 'Waiting for'+str(60 if self.strong else 120)+'seconds without workspace interaction'
  if self.clock()-self.last<(180 if self.strong else 600):return 'Cooldown - '+str(3 if self.strong else 10)+'minutes between decisions'
  if sum(self.clock()-t<3600 for t in self.requests)>=(12 if self.strong else 6):return 'Hourly decision limit'
  return 'Ready for model-chosen silence or bounded conversation'
 def poll(self):
  with self.lock:
   now=self.clock()
   if not self.enabled or self.gaming or self.busy or self.voice.busy or self.voice.runtime is not None or 0<=self.hour()<7 or now-self.last_activity<(60 if self.strong else 120)or now-self.last<(180 if self.strong else 600):return None
   while self.requests and now-self.requests[0]>=3600:self.requests.popleft()
   if len(self.requests)>=(12 if self.strong else 6):return None
   self.busy=True;self.last=now;self.requests.append(now);ticket=self.generation;self.cancel=threading.Event();cancel=self.cancel;audio=self.audio
  def run():
   try:
    from .workspace_voice import VOICES
    context=self.voice.memory.messages();payload={'allowed_profiles':[n for n in VOICES if n!='JARVIS'],'recent_conversation':context[-8:],'recent_idle_topics':list(self.topics)}
    result=self.brains.router('JARVIS').ask([{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}],cancel=cancel,local_only=True)
    choice=decision(result.get('text'))
    with self.lock:
     if cancel.is_set()or ticket!=self.generation or not self.enabled or self.gaming or self.voice.busy or self.voice.runtime is not None or 0<=self.hour()<7:return
     if not choice:self.notify('status','Idle team chose silence');return
     names,topic=choice
     if self.strong:
      available=[n for n in VOICES if n!='JARVIS'];start=self.rotation%len(available);names=tuple(available[(start+i)%len(available)]for i in range(2));self.rotation+=2
     if topic in self.topics:return
     self.topics.append(topic)
     self.notify('status','Idle team: short fictional conversation, no tools')
     self.voice.dialogue(' and '.join(names)+' talk to each other about '+topic,self.brains,audio=audio,rounds=1,origin='idle')
   except Exception:self.notify('status','Idle conversation unavailable or invalid; quiet, no invented replacement')
   finally:
    with self.lock:self.busy=False
  worker=threading.Thread(target=run,daemon=True);worker.start();return worker
 def snapshot(self):return {'enabled':self.enabled,'audio':self.audio,'strong':self.strong,'busy':self.busy,'waiting_reason':self.waiting(),'scope':'Actual chat only, local-only, no sensors/tools, bounded team replies and Jarvis conclusion. Quiet00-07. Default120s/10min/6perhour; strong60s/3min/12perhour. Mic OFF cannot hear stop.'}
