"""Kokoro synthesis-only MP3 preview. No microphone, playback or remote text."""
import base64,hashlib,threading
class TelegramVoice:
 def __init__(self,speaker=None,encoder_factory=None):self.speaker=speaker;self.encoder_factory=encoder_factory;self.lock=threading.Lock()
 def render(self,text,cancel):
  if not isinstance(text,str)or not 1<=len(text)<=900:raise ValueError('Voice output limited to900characters')
  with self.lock:
   if cancel():raise ValueError('Voice stopped')
   if self.speaker is None:
    from .workspace_voice import build_proactive_speaker
    self.speaker=build_proactive_speaker()
   import numpy as np
   from .speech_text import speech_text
   clean=speech_text(text)
   if clean!=text:raise ValueError('Voice text contains unsupported markup. Review plain spoken words.')
   self.speaker.select_profile('JARVIS');parts=[];rate=None;count=0
   for _,audio,sr in self.speaker.prepare_stream(text):
    if cancel():raise ValueError('Voice stopped')
    samples=np.asarray(audio,dtype=np.float32)
    if sr not in (16000,24000)or rate not in (None,sr)or samples.ndim!=1 or not np.isfinite(samples).all():raise ValueError('Voice samples invalid')
    rate=sr;count+=len(samples)
    if count>sr*40:raise ValueError('Voice limited to40seconds')
    parts.append((np.clip(samples,-1,1)*32767).astype('<i2').tobytes())
   if not count or cancel():raise ValueError('Voice empty or stopped')
   factory=self.encoder_factory
   if factory is None:
    import lameenc
    factory=lameenc.Encoder
   e=factory();e.set_bit_rate(64);e.set_in_sample_rate(rate);e.set_channels(1);e.set_quality(2);mp3=bytes(e.encode(b''.join(parts)))+bytes(e.flush())
   if not 100<=len(mp3)<=500000 or cancel():raise ValueError('MP3 output invalid or stopped')
   return {'audio_base64':base64.b64encode(mp3).decode(),'audio_sha256':hashlib.sha256(mp3).hexdigest(),'audio_bytes':len(mp3),'duration_seconds':count/rate,'mime':'audio/mpeg','speaker':'JARVIS','text':text}
 def close(self):
  if self.speaker:self.speaker.close()
  self.speaker=None
