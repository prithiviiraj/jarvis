"""Optional Coqui XTTS local demo-server client. Never downloads or auto-accepts CPML."""
import urllib.request,urllib.parse,json,io,wave
LANGUAGES=('en','es','fr','de','it','pt','pl','tr','ru','nl','cs','ar','zh-cn','ja','hu','ko','hi')
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise ValueError('Local voice server redirects are refused')
class XTTSLocal:
 def __init__(self,port=5002,speaker='Craig Gutsy',language='en',noncommercial=False):
  if noncommercial is not True:raise ValueError('Confirm XTTS non-commercial model and output use first')
  if language not in LANGUAGES:raise ValueError('XTTS does not list Tamil support')
  if type(port)is not int or not 1024<=port<=65535:raise ValueError('Invalid local voice server port')
  if speaker!='Craig Gutsy':raise ValueError('Only installed preset voice supported; no implicit voice cloning')
  self.url='http://127.0.0.1:'+str(port)+'/api/tts';self.speaker=speaker;self.language=language
  self.http=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
 def synthesize(self,text):
  if not isinstance(text,str)or not text or len(text)>400 or any('\u0b80'<=c<='\u0bff'for c in text):raise ValueError('Use a short supported-language clause')
  # Text only to exact loopback server. Redirects/proxies disabled, no credentials.
  url=self.url+'?'+urllib.parse.urlencode({'text':text,'speaker-id':self.speaker,'language-id':self.language})
  with self.http.open(url,timeout=30)as response:
   raw=response.read(2_000_001)
  if len(raw)>2_000_000:raise ValueError('Local speech output too large')
  with wave.open(io.BytesIO(raw),'rb')as w:
   if w.getnchannels()!=1 or w.getsampwidth()!=2 or w.getframerate()not in (22050,24000):raise ValueError('Expected mono PCM16 speech')
   sr=w.getframerate();pcm=w.readframes(w.getnframes())
  import numpy as np
  audio=np.frombuffer(pcm,dtype='<i2').astype(np.float32)/32768
  if not 0<len(audio)<=sr*40 or not np.isfinite(audio).all():raise ValueError('Invalid local speech output')
  return audio,sr
