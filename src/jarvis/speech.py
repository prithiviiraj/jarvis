"""Local STT and OS speech. No cloud speech or voice cloning."""
import os
import subprocess
import threading

class SpeechCancelled(RuntimeError):
    """Cooperative cancellation, not interruption of a native inference call."""

class UnclearSpeech(ValueError):
    """No reliable words in this microphone segment; safe to ask for repetition."""

_STT_MODELS={};_STT_LOCK=threading.RLock()

class WhisperSTT:
    def __init__(self,path,vocabulary='',language=None):
        from faster_whisper import WhisperModel
        # Retain one CPU model for the process; Windows native disposal can block.
        with _STT_LOCK:
            key=str(path)
            if key not in _STT_MODELS:_STT_MODELS[key]=WhisperModel(key,device='cpu',compute_type='int8',cpu_threads=2,num_workers=1,local_files_only=True)
            self.model=_STT_MODELS[key]
        self.lock=_STT_LOCK
        self.vocabulary=vocabulary[:1000];self.language=language
    def transcribe(self,audio):return self.transcribe_cancellable(audio)
    def transcribe_cancellable(self,audio,cancel=None):
        def check():
            if cancel is not None and cancel.is_set():raise SpeechCancelled('Speech recognition cancelled')
        check()
        with self.lock:
            check()
            segments,info=self.model.transcribe(audio,beam_size=1,language=self.language,initial_prompt=self.vocabulary or None,vad_filter=False)
            parts=[];iterator=iter(segments)
            try:
                while True:
                    check()
                    try:s=next(iterator)
                    except StopIteration:break
                    check()
                    if s.no_speech_prob<.6 and s.avg_logprob> -1.0:parts.append(s.text)
            finally:
                close=getattr(iterator,'close',None)
                if callable(close):close()
        check();text=' '.join(parts).strip()
        if not text:raise UnclearSpeech('Speech was unclear. Please repeat.')
        return text

class SapiSpeaker:
    """Installed Windows voice, cancellable subprocess. Text goes over stdin, never code."""
    def __init__(self):self.process=None;self.lock=threading.RLock();self.generation=0
    def speak(self,text,generation=None):
        if os.name!='nt':raise RuntimeError('Windows voice is unavailable on this system.')
        # Constant source only. Speech content cannot become PowerShell commands.
        script="[Console]::InputEncoding=[System.Text.Encoding]::UTF8; $s=New-Object -ComObject SAPI.SpVoice; $text=[Console]::In.ReadToEnd(); [void]$s.Speak($text,16)"
        with self.lock:
            if generation is not None and generation!=self.generation:return
            p=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=0x08000000)
            self.process=p
        try:
            p.communicate(text.encode('utf-8'),timeout=120)
            if p.returncode not in (0,None):raise RuntimeError('Windows speech failed.')
        finally:
            if p.poll() is None:p.kill();p.wait(timeout=3)
            with self.lock:
                if self.process is p:self.process=None
    def stop(self):
        with self.lock:
            self.generation+=1
            p=self.process
            if p and p.poll() is None:p.terminate()
            self.process=None
