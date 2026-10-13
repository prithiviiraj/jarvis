"""Ephemeral levels from existing consented capture/playback. No audio retained."""
import math,time
class VoiceMeter:
 def __init__(self,clock=time.monotonic):self.clock=clock;self.level=0.;self.peak=0.;self.at=0.
 def feed(self,frame):
  import numpy as np
  values=np.asarray(frame,dtype='float32')
  if not values.size or not np.isfinite(values).all():self.clear();return
  values=np.clip(values,-1,1)
  rms=math.sqrt(float(np.mean(values*values)));peak=float(np.max(np.abs(values)))
  self.level=min(1.,rms);self.peak=min(1.,peak);self.at=self.clock()
 def clear(self):self.level=0.;self.peak=0.;self.at=0.
 def snapshot(self):
  age=self.clock()-self.at
  return {'level':self.level if 0<=age<.3 else 0.,'peak':self.peak if 0<=age<.3 else 0.,'scope':'Ephemeral PCM level, not proof of audible sound'}
