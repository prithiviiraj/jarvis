"""Deterministic completion receipts, never model-authored or dispatch-time success.

A ready tab is not a visible foreground tab. The template makes that distinction.
Playback is owned by an explicitly started voice session, between its turns only.
"""
import threading,time
from collections import deque,OrderedDict
_CLIPS=OrderedDict();_CLIP_LOCK=threading.RLock()
TEXT={
 'camera-ready':'Master, the camera connection is ready. Ask me about the current image.',
 'screen-ready':'Master, the current screen image is ready. What would you like me to check?',
 'local-model-ready':'Master, the local model passed its startup checks and is ready.',
 'search-ready':'Master, the local search candidates are on screen. Which source shall we inspect?',
 'browser-scroll-ready':'Master, the scroll step finished. What next?',
 'browser-tab-ready':'Master, the BrowserOS tab is ready. What shall I open?',
 'browser-page-ready':'Master, the page loaded in BrowserOS. What next?',
 'browser-failed':'Master, that browser step did not complete. Check the error on screen.',
 'browser-stopped':'Master, the browser session stopped.',
}
class CompletionFeedback:
 def __init__(self):self.lock=threading.RLock();self.pending=deque(maxlen=20);self.seen=set();self.order=deque(maxlen=100);self.clips={};self.preparation=[];self.scope='Prepared local deterministic feedback. No hardware audibility or latency claim.'
 def record(self,operation_id,kind,verified=False):
  if type(operation_id)is not str or not operation_id or len(operation_id)>120 or kind not in TEXT:raise ValueError('Invalid completion receipt')
  if verified is not True:raise ValueError('Completion feedback requires a verified result')
  with self.lock:
   if operation_id in self.seen:return False
   if len(self.order)==self.order.maxlen:self.seen.discard(self.order.popleft())
   self.seen.add(operation_id);self.order.append(operation_id);self.pending.append({'id':operation_id,'kind':kind,'text':TEXT[kind]});return True
 def take(self):
  with self.lock:return self.pending.popleft()if self.pending else None
 def prepare(self,speaker,generation,cache_key=None,cancelled=lambda:False):
  """Explicit voice setup only. No playback or model call; one current persona."""
  clips={};started=time.monotonic()
  if cancelled():return False
  # Reuse only fixed app phrases for the same verified voice assets. No user
  # text/audio is admitted to this bounded process-memory cache.
  key=(cache_key,speaker.profile,tuple(TEXT.items()))if cache_key is not None else None
  if key is not None:
   with _CLIP_LOCK:
    cached=_CLIPS.pop(key,None)
    if cached is not None:
     _CLIPS[key]=cached
     if cancelled()or generation!=speaker.generation:return False
     with self.lock:self.clips[speaker.profile]=cached;self.preparation.append({'profile':speaker.profile,'cached':True,'seconds':time.monotonic()-started,'clips':len(cached)})
     return True
  for kind,text in TEXT.items():
   if cancelled()or generation!=speaker.generation:return False
   clip=speaker.prepare(text,generation)
   if clip is None:return False
   clips[kind]=clip
  if cancelled()or generation!=speaker.generation:return False
  with self.lock:self.clips[speaker.profile]=clips;self.preparation.append({'profile':speaker.profile,'cached':False,'seconds':time.monotonic()-started,'clips':len(clips)})
  if key is not None:
   with _CLIP_LOCK:
    _CLIPS[key]=clips
    while len(_CLIPS)>6:_CLIPS.popitem(last=False)
  return True
 def play(self,event,speaker,generation):
  with self.lock:clip=self.clips.get(speaker.profile,{}).get(event['kind'])
  if clip is None or generation!=speaker.generation:return False
  speaker.play_prepared(clip,generation);return generation==speaker.generation
 def clear(self):
  with self.lock:self.pending.clear();self.clips={}
