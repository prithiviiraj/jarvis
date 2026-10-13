"""Explicit session-only Groq STT. Audio only, no disk recording or fallback."""
import io,json,uuid,wave,urllib.request,urllib.error
from .speech import SpeechCancelled,UnclearSpeech
from .router import cloud_http

class GroqSTT:
    endpoint='https://api.groq.com/openai/v1/audio/transcriptions'
    def __init__(self,key_store,consent=False,free_confirmed=False,language=None,http=None):
        if consent is not True:raise ValueError('Groq microphone audio sharing consent required')
        if free_confirmed is not True:raise ValueError('Confirm your Groq Free-tier account first')
        self.key_store=key_store;self.language=language
        if not key_store.get('groq/slot1'):raise ValueError('Save your Groq key in Windows Credentials first')
        self.http=http or cloud_http()
    def transcribe(self,audio):return self.transcribe_cancellable(audio)
    def transcribe_cancellable(self,audio,cancel=None):
        def check():
            if cancel is not None and cancel.is_set():raise SpeechCancelled('Speech recognition cancelled')
        check()
        import numpy as np
        pcm=np.asarray(audio,dtype=np.float32)
        if pcm.ndim!=1 or not 0<len(pcm)<=16000*30 or not np.all(np.isfinite(pcm)):raise ValueError('Groq STT accepts one finite mono segment up to30seconds')
        if self.language not in (None,'en','ta'):raise ValueError('Unsupported speech language')
        key=self.key_store.get('groq/slot1')
        if not key:raise ValueError('Groq key is missing')
        wav=io.BytesIO()
        with wave.open(wav,'wb')as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes((np.clip(pcm,-1,1)*32767).astype('<i2').tobytes())
        boundary='jarvis-'+uuid.uuid4().hex
        parts=[]
        for name,value in [('model','whisper-large-v3'),('response_format','json'),('temperature','0')]+([('language',self.language)]if self.language else[]):
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="microphone.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()+wav.getvalue()+b'\r\n')
        parts.append(f'--{boundary}--\r\n'.encode())
        request=urllib.request.Request(self.endpoint,data=b''.join(parts),headers={'Authorization':'Bearer '+key,'Content-Type':'multipart/form-data; boundary='+boundary},method='POST')
        check()
        try:
            with self.http.open(request,timeout=30)as response:
                raw=response.read(65537)
                if len(raw)>65536:raise ValueError('Groq speech response too large')
        except urllib.error.HTTPError as e:
            check();raise RuntimeError('Groq STT request failed ('+str(e.code)+'). No local retry or cloud fallback was made.')from None
        except (urllib.error.URLError,TimeoutError):
            check();raise RuntimeError('Groq STT network request failed. Nothing was retried.')from None
        check()
        try:text=json.loads(raw).get('text')
        except (ValueError,AttributeError):raise RuntimeError('Groq STT returned an invalid response')from None
        if not isinstance(text,str)or not text.strip():raise UnclearSpeech('Groq speech was unclear. Please repeat.')
        if len(text)>8000:raise RuntimeError('Groq transcript too long')
        return text.strip()
