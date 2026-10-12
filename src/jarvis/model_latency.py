"""Explicit synthetic owned-model latency measurements, never private screen input."""
import time,json,io,base64,statistics,threading,urllib.request
from .router import local_http
class ModelLatency:
 def __init__(self,runtime,opener=None,clock=time.monotonic):self.runtime=runtime;self.opener=opener or local_http();self.clock=clock
 def run(self,consent=False,cancel=None):
  if consent is not True:raise ValueError('Review synthetic latency test first')
  cancel=cancel or threading.Event();route=self.runtime.route()
  from PIL import Image,ImageDraw
  image=Image.new('RGB',(1024,640),'white');draw=ImageDraw.Draw(image);draw.rectangle((50,100,450,540),fill='red');draw.rectangle((550,100,950,540),fill='blue');buf=io.BytesIO();image.save(buf,format='PNG');uri='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
  cases=[('text','Explain in two short sentences why saving a draft before editing is useful.'),('image',[{'type':'text','text':'Describe the two colored rectangles and their left/right positions in two short sentences. This is a synthetic test.'},{'type':'image_url','image_url':{'url':uri}}])]
  rows=[]
  for kind,content in cases:
   for trial in range(3):
    if cancel.is_set():raise InterruptedError('Latency test stopped')
    if self.runtime.route()!=route:raise ValueError('Owned model changed before latency request')
    req=urllib.request.Request(route['url']+'/chat/completions',data=json.dumps({'model':route['model'],'messages':[{'role':'user','content':content}],'stream':True,'temperature':0,'max_tokens':96,'stream_options':{'include_usage':True}}).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+route['key']})
    start=self.clock();first=None;text='';size=0;usage={}
    with self.opener.open(req,timeout=30)as response:
     for line in response:
      if cancel.is_set():raise InterruptedError('Latency test stopped')
      if self.runtime.route()!=route:raise ValueError('Owned model changed before latency result')
      size+=len(line)
      if size>131072 or len(line)>16384:raise ValueError('Oversize latency stream')
      if not line.startswith(b'data:'):continue
      raw=line[5:].strip()
      if raw==b'[DONE]':break
      event=json.loads(raw);usage=event.get('usage')or usage
      choices=event.get('choices')or[];delta=choices[0].get('delta',{}).get('content')if choices else None
      if isinstance(delta,str)and delta:
       if first is None:first=self.clock()-start
       text+=delta
       if len(text)>6000:raise ValueError('Oversize synthetic answer')
    elapsed=self.clock()-start
    if self.runtime.route()!=route or cancel.is_set():raise InterruptedError('Latency route stopped')
    if first is None or not text.strip():raise ValueError('No final text in latency stream')
    rows.append({'kind':kind,'trial':trial,'first_text_s':round(first,4),'total_s':round(elapsed,4),'output_chars':len(text),'answer':text,'usage':usage})
  return {'scope':'Six real synthetic text/image streaming requests. Trial0 includes first-use effects; trials1/2 repeat exact input and may use prefix caching. No owner hardware, microphone, video, grounding quality or full-duplex claim.','rows':rows,'median_first_text_s':{kind:statistics.median(r['first_text_s']for r in rows if r['kind']==kind)for kind in ('text','image')}}
