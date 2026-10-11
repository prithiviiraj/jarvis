"""Local scene-change sampling. No capture, model calls or persistence here."""
import hashlib,io
class SceneSampler:
 def __init__(self,min_interval=2,keyframe_interval=12,threshold=.065):
  self.min_interval=min_interval;self.keyframe_interval=keyframe_interval;self.threshold=threshold;self.last_at=None;self.last_pixels=None;self.last_hash=None
 def reset(self):self.last_at=None;self.last_pixels=None;self.last_hash=None
 def consider(self,jpeg,now):
  digest=hashlib.sha256(jpeg).digest()
  if self.last_at is not None and now-self.last_at<self.min_interval:return False,'rate budget'
  if digest==self.last_hash:return False,'unchanged bytes'
  pixels=None
  try:
   from PIL import Image
   with Image.open(io.BytesIO(jpeg))as image:
    pixels=image.convert('L').resize((32,18)).tobytes()
  except Exception:pass # Source validates bytes; invalid image still reaches model validation.
  if pixels and self.last_pixels and self.last_at is not None:
   delta=sum(abs(a-b)for a,b in zip(pixels,self.last_pixels))/(len(pixels)*255)
   if delta<self.threshold and now-self.last_at<self.keyframe_interval:return False,'small visual change'
  reason='first frame' if self.last_at is None else 'keyframe'if now-self.last_at>=self.keyframe_interval else 'scene change'
  self.last_at=now;self.last_pixels=pixels;self.last_hash=digest;return True,reason
