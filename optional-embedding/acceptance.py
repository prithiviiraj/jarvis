"""Real pinned-model smoke on a capable CI runner. Synthetic corpus, never owner data."""
import pathlib,os,json,time,sys,math,struct,wave
ROOT=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT));import runtime as r
OUT=pathlib.Path('embedding-evidence');OUT.mkdir(exist_ok=True);corpus=OUT/'corpus';corpus.mkdir(exist_ok=True)
(corpus/'planning.md').write_text('# Library plan\nVisit the library and review the project plan.',encoding='utf-8')
(corpus/'groceries.md').write_text('# Grocery list\nMilk, rice and vegetables.',encoding='utf-8')
(corpus/'தமிழ்.md').write_text('இன்று நூலகத்திற்குச் சென்று புத்தகம் படிக்க திட்டம்.',encoding='utf-8')
(corpus/'sum.py').write_text('def add(a,b):\n return a+b\n',encoding='utf-8')
from PIL import Image
Image.new('RGB',(256,256),'red').save(corpus/'red.png');Image.new('RGB',(256,256),'blue').save(corpus/'blue.png')
with wave.open(str(corpus/'tone.wav'),'w')as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000);f.writeframes(b''.join(struct.pack('<h',int(8000*math.sin(2*math.pi*440*i/16000)))for i in range(16000)))
import av,numpy as np
with av.open(str(corpus/'red.mp4'),'w')as c:
 stream=c.add_stream('mpeg4',rate=1);stream.width=256;stream.height=256;stream.pix_fmt='yuv420p'
 for i in range(2):
  frame=av.VideoFrame.from_ndarray(np.full((256,256,3),[255,0,0],dtype=np.uint8),format='rgb24')
  for packet in stream.encode(frame):c.mux(packet)
 for packet in stream.encode():c.mux(packet)
results={'scope':'real model; synthetic fixtures only, not owner-language/3060acceptance','checks':[],'retrieval':[],'started':time.time()}
try:
 r.setup();results['checks'].append('pinned13asset byte/SHA256 verification')
 for mode,query in [('text','library project plan'),('text','நூலகம் புத்தகம்'),('text','library poganum plan'),('vision','a red image'),('audio','a steady tone sound')]:
  start=time.monotonic();result=r.retrieve({'action':'search','folder':str(corpus),'query':query,'encoders':mode,'dimensions':256});elapsed=time.monotonic()-start
  assert result['results']and all(math.isfinite(x['score'])for x in result['results']),result
  if query=='library project plan':assert result['results'][0]['name']=='planning.md',result
  if query=='a red image':assert next(x for x in result['results']if x['name']=='red.png')['score']>next(x for x in result['results']if x['name']=='blue.png')['score'],result
  results['retrieval'].append({'mode':mode,'query':query,'elapsed_s':elapsed,'candidates':result['results']});results['checks'].append(mode+'finite embeddings/shared dimension')
 results['passed']=True
finally:(OUT/'acceptance.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':True,'checks':results['checks']}))
