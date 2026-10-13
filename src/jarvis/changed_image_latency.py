"""Opt-in synthetic changed-frame diagnostics; no private pixels or settings edits."""
import base64,io,json,time,urllib.request,subprocess,os,re
from .router import local_http
CASES=(('A17','B29','red','blue'),('C43','D61','green','yellow'),('E83','F97','blue','red'))
def frame(case,width=1024):
 from PIL import Image,ImageDraw,ImageFont
 if width not in (1024,960):raise ValueError('Unsupported diagnostic width')
 im=Image.new('RGB',(1024,640),'white');d=ImageDraw.Draw(im)
 fonts=[os.path.join(os.environ.get('WINDIR','C:/Windows'),'Fonts','arial.ttf'),'/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
 font=next((ImageFont.truetype(p,32)for p in fonts if os.path.isfile(p)),None)
 if font is None:raise ValueError('Readable fixture font missing')
 d.rectangle((20,20,1004,70),fill='#e0e0e0');d.text((35,30),'Synthetic task board',fill='black',font=font)
 for x,label,color in [(60,case[0],case[2]),(550,case[1],case[3])]:
  d.rectangle((x,130,x+400,460),fill=color);d.rectangle((x+15,170,x+385,240),fill='white');d.text((x+35,185),label,fill='black',font=font)
 if width!=1024:im=im.resize((width,width*640//1024),Image.Resampling.LANCZOS)
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def grade(answer,case):
 # Parse exact left/right fixture facts; no credit for merely mentioning all values.
 try:
  x=json.loads(answer.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip())
  return x=={'left':{'label':case[0],'color':case[2]},'right':{'label':case[1],'color':case[3]}}
 except (ValueError,TypeError):return False
class ImageProfile:
 def __init__(self,width=1024,encoding_batch=1024):
  if width not in (1024,960)or encoding_batch not in (512,1024,2048):raise ValueError('Unsupported diagnostic profile')
  self.width=width;self.encoding_batch=encoding_batch
 def __call__(self,args,**kwargs):
  if '--image-min-tokens'in args:raise ValueError('Unexpected existing image policy')
  return subprocess.Popen(list(args)+['--image-min-tokens','1024','--image-max-tokens','2048','--mtmd-batch-max-tokens',str(self.encoding_batch)],**kwargs)
def run_changed(runtime,width=1024):
 route=runtime.route();rows=[]
 for trial,case in enumerate(CASES):
  uri='data:image/png;base64,'+base64.b64encode(frame(case,width)).decode()
  content=[{'type':'text','text':'Read the two panels. Return only JSON with left and right objects each containing label and color. No other words.'},{'type':'image_url','image_url':{'url':uri}}]
  req=urllib.request.Request(route['url']+'/chat/completions',data=json.dumps({'model':route['model'],'messages':[{'role':'user','content':content}],'temperature':0,'stream':True,'max_tokens':100,'stream_options':{'include_usage':True}}).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+route['key']})
  start=time.monotonic();first=None;text='';usage={};size=0
  with local_http().open(req,timeout=240)as r:
   for line in r:
    size+=len(line)
    if size>131072:raise ValueError('Oversize diagnostic response')
    if not line.startswith(b'data:'):continue
    raw=line[5:].strip()
    if raw==b'[DONE]':break
    x=json.loads(raw);usage=x.get('usage')or usage;c=x.get('choices')or[];s=c[0].get('delta',{}).get('content')if c else None
    if s:
     if first is None:first=time.monotonic()-start
     text+=s
  if runtime.route()!=route:raise ValueError('Owned route changed')
  if first is None:raise ValueError('No usable answer')
  row={'trial':trial,'changed_frame':True,'width':width,'first_text_s':round(first,4),'total_s':round(time.monotonic()-start,4),'answer':text,'quality_pass':grade(text,case),'usage':usage};rows.append(row);print(json.dumps(row),flush=True)
 return rows
