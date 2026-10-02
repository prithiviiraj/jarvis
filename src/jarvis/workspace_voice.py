"""Workspace bridge. No sensor, model download or network work on construction."""
import queue
import threading
from pathlib import Path

VOICES = {'JARVIS':'am_michael','NOVA':'af_heart','KAI':'am_liam','LYRA':'af_sky','DEX':'am_fenrir'}

class WorkspaceVoice:
    def __init__(self, factory=None):
        self.events=queue.Queue();self.factory=factory or build_runtime
        self.runtime=None;self.name='JARVIS';self.busy=False;self.closed=False
        self.generation=0;self.lock=threading.RLock()
        from .team_memory import TeamMemory
        self.memory=TeamMemory();self.pool_config=None
    def notify(self,kind,value):self.events.put((kind,value))
    def select(self,name):
        if name not in VOICES:raise ValueError('Unknown voice profile.')
        self.pause()
        while True:
            try:self.events.get_nowait()
            except queue.Empty:break
        with self.lock:self.name=name
        self.notify('state','off')
    def start(self,consent=False,cloud=False,model='',verified_free=False):
        if not consent:raise ValueError('Microphone session consent required.')
        if cloud and not verified_free:raise ValueError('Groq needs a confirmed Free-tier account.')
        with self.lock:
            if self.closed or self.busy:raise RuntimeError('Voice setup is busy or closed.')
            self.busy=True;self.generation+=1;ticket=self.generation;name=self.name
        self.notify('state','loading voice')
        def run():
            runtime=None
            try:
                def notify(kind,value):
                    with self.lock:
                        if not self.closed and ticket==self.generation:self.notify(kind,value)
                if self.pool_config is not None and self.factory is build_runtime:
                    runtime=build_runtime(name,notify,cloud,model,verified_free,pool_config=self.pool_config)
                else:runtime=self.factory(name,notify,cloud,model,verified_free)
                with self.lock:
                    if self.closed or ticket!=self.generation:runtime.close();return
                    self.runtime=runtime;runtime.shared_context=self.memory.messages;runtime.record_turn=lambda user,answer:self.memory.append(name,user,answer);runtime.enable(consent=True,cloud_consent=cloud)
                self.notify('state','listening')
            except Exception as exc:
                if runtime:runtime.close()
                with self.lock:
                    if ticket==self.generation:
                        self.runtime=None;self.notify('error',str(exc)[:300])
            finally:
                with self.lock:self.busy=False
        worker=threading.Thread(target=run,daemon=True);worker.start();return worker
    def pause(self):
        with self.lock:self.generation+=1;runtime=self.runtime;self.runtime=None
        if runtime:runtime.close()
        self.notify('state','off')
    def close(self):
        with self.lock:self.closed=True
        self.pause();self.memory.clear()

class FreeSessionRouter:
    """Plan confirmation is session scoped. It is not automatic billing verification."""
    def __init__(self,router,verified):self.router=router;self.verified=('groq',) if verified else ()
    def ask(self,*args,**kw):return self.router.ask(*args,verified_free_providers=self.verified,**kw)
    def stream(self,*args,**kw):return self.router.stream(*args,verified_free_providers=self.verified,**kw)

def build_runtime(name,notify,cloud=False,model='',verified_free=False,pool_config=None):
    from .paths import ensure_layout
    from . import models
    from .voice_assets import ready
    from .experimental.kokoro import NativeG2P,KokoroSynth
    from .experimental.kokoro_speaker import KokoroSpeaker
    from .providers import local_models,configured
    from .router import BrainRouter
    from .security import WindowsCredentials
    from .audio import SileroVad
    from .speech import WhisperSTT
    from .runtime import VoiceRuntime
    cache=ensure_layout()/'models';assets=cache/'voices'
    if not models.ready(cache) or not ready(assets):raise RuntimeError('Verified speech assets missing. Download models and install the native voice frontend first.')
    from .native_frontend import verified_frontend
    exe,data=verified_frontend()
    if pool_config is not None:
        pool,consented,free_confirmed=pool_config
        router=pool.router(name,WindowsCredentials(),consented,free_confirmed)
        notify('status','Configured account pool / session confirmed by you, not verified by API.')
    elif cloud:
        if not verified_free:raise ValueError('Confirm Groq Free-tier status.')
        keys=WindowsCredentials()
        if not keys.get('groq'):raise RuntimeError('Save your Groq API key in Settings first.')
        from .groq_models import resolve_model
        model,listed=resolve_model(model,True,True,keys,details=True)
        notify('status','Groq model: '+model+' / Free plan confirmed by you, not verified by API.')
        from dataclasses import replace
        provider=replace(configured('groq',model),allow_20b_fallback='openai/gpt-oss-20b' in listed)
        router=FreeSessionRouter(BrainRouter([provider],key_store=keys),True)
    else:
        ids=local_models()
        if len(ids)!=1:raise RuntimeError('Load exactly one chat model in LM Studio.')
        router=BrainRouter([configured('local',ids[0])])
    g2p=NativeG2P(exe,data)
    try:
        synth=KokoroSynth(assets/'model.onnx',assets/(VOICES[name]+'.bin'),assets/'config.json',g2p)
        speaker=KokoroSpeaker(synth)
        runtime=VoiceRuntime(SileroVad(cache/'silero.onnx'),WhisperSTT(cache/'whisper-base',vocabulary='JARVIS team leader. NOVA secretary. KAI researcher. LYRA writer. DEX coder.',language='en'),router,speaker,notify)
        runtime.streaming=True;runtime.persona=name
        original_close=runtime.close
        def close():original_close();g2p.close()
        runtime.close=close
        return runtime
    except Exception:g2p.close();raise
