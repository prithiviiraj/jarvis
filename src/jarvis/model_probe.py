"""Explicit text + public synthetic-image generation test for owned runtime.

Health/loaded metadata alone never prove usable text/image answers.
"""
import json,base64,io,threading,time,urllib.request
class ModelProbe:
 def __init__(self,runtime,opener=None):self.runtime=runtime;self.opener=opener;self.worker=None;self.cancel=threading.Event();self.generation=0;self.lock=threading.RLock();self.state={'text':'not tested','image':'not tested','error':'','scope':'Synthetic local test only; not real desktop understanding or control'}
 def snapshot(self):
  with self.lock:return {**self.state,'busy':bool(self.worker and self.worker.is_alive())}
 def start(self,consent=False):
  if consent is not True:raise ValueError('Review local text and synthetic-image test first')
  if self.worker and self.worker.is_alive():raise ValueError('Model test already running')
  route=self.runtime.route();self.generation+=1;ticket=self.generation;self.cancel=threading.Event();cancel=self.cancel
  with self.lock:self.state={'text':'testing','image':'not tested','error':'','scope':'Synthetic local test only; not real desktop understanding or control'}
  def run():
   kind='text'
   try:
    # No user/private pixels. Deterministic solid red PNG rendered in memory.
    from PIL import Image
    image=Image.new('RGB',(64,64),(255,0,0));out=io.BytesIO();image.save(out,format='PNG');uri='data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()
    for kind,content in [('text','Reply with the single word READY.'),('image',[{'type':'text','text':'What is the dominant color of this square? Reply with one color word.'},{'type':'image_url','image_url':{'url':uri}}])]:
     if cancel.is_set()or ticket!=self.generation:return
     if self.runtime.route()!=route:raise ValueError('Owned model changed during test')
     data={'model':route['model'],'messages':[{'role':'user','content':content}],'max_tokens':32,'temperature':0,'stream':False};req=urllib.request.Request(route['url']+'/chat/completions',data=json.dumps(data).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+route['key']})
     from .router import local_http
     started=time.monotonic()
     with (self.opener or local_http()).open(req,timeout=30)as response:raw=response.read(65537)
     if len(raw)>65536:raise ValueError('Test reply too large')
     text=json.loads(raw)['choices'][0]['message']['content']
     if not isinstance(text,str)or not text.strip():raise ValueError('Empty '+kind+' test reply')
     valid=text.strip().strip('.!').upper()=='READY'if kind=='text'else text.strip().strip('.!').lower()=='red'
     if not valid:raise ValueError(kind.title()+' test answered incorrectly')
     if cancel.is_set()or ticket!=self.generation:return
     with self.lock:self.state[kind]='passed';self.state[kind+'_request_s']=round(time.monotonic()-started,3)
   except Exception as e:
    if ticket==self.generation and not cancel.is_set():
     with self.lock:self.state[kind]='failed';self.state['error']=type(e).__name__+': '+str(e)
  self.worker=threading.Thread(target=run,daemon=True);self.worker.start();return self.snapshot()
 def stop(self):
  self.cancel.set();self.generation+=1
  with self.lock:self.state={'text':'not tested','image':'not tested','error':'','scope':'Synthetic local test only; not real desktop understanding or control'}
