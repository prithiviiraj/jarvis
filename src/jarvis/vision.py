"""Local camera-vision sharing. RAM-only current frame to the loaded LOCAL model only.

Never attaches images to cloud providers: the only wired chat paths are loopback
LM Studio routers. No frame is written to disk, history or team memory; only the
user's typed/spoken text and the model's text answer are stored.
"""
import base64,json,time
from .router import local_http

class LocalVision:
    def __init__(self,frame_source,base_url='http://127.0.0.1:1234',opener=None,clock=time.monotonic,recheck_seconds=15):
        self.frame_source=frame_source;self.base_url=base_url.rstrip('/');self.opener=opener;self.clock=clock;self.recheck_seconds=recheck_seconds
        self.enabled=False;self.checked_model=None;self.checked_at=0
    def _open(self):return (self.opener or local_http()).open(self.base_url+'/api/v1/models',timeout=8)
    def vision_model(self):
        with self._open() as r:
            raw=r.read(262145)
            if len(raw)>262144:raise RuntimeError('Model list too large.')
            models=json.loads(raw).get('models',[])
        if not isinstance(models,list):raise RuntimeError('LM Studio model list unavailable.')
        loaded=[]
        for m in models:
            if not isinstance(m,dict)or m.get('type','llm')!='llm':continue
            for instance in m.get('loaded_instances',[]):
                if isinstance(instance,dict)and isinstance(instance.get('id'),str):loaded.append((instance['id'],m.get('capabilities',{}).get('vision')is True))
        if not loaded:return None
        if len(loaded)!=1:raise RuntimeError('Load exactly one local chat instance for camera vision. Downloaded model files alone are not loaded.')
        return loaded[0][0]if loaded[0][1]else None
    def enable(self,consent=False):
        if not consent:raise ValueError('Camera vision needs explicit consent.')
        model=self.vision_model()
        if not model:raise RuntimeError('The loaded LM Studio model does not advertise vision. Load a vision-capable model (for example qwen2.5-vl), then enable camera vision again.')
        self.enabled=True;self.checked_model=model;self.checked_at=self.clock()
    def disable(self):self.enabled=False
    def attach(self,messages):
        """Return messages with the current frame on the last user turn, or unchanged."""
        if not self.enabled or not messages:return messages
        if self.clock()-self.checked_at>self.recheck_seconds:
            model=self.vision_model()
            if not model:raise RuntimeError('Loaded model no longer advertises vision; frame not sent.')
            self.checked_model=model;self.checked_at=self.clock()
        frame=self.frame_source() if callable(self.frame_source) else None
        if not frame or not isinstance(frame,(bytes,bytearray)) or len(frame)>300000:return messages
        out=list(messages);last=dict(out[-1]);text=last.get('content')
        if not isinstance(text,str):return messages
        last['content']=[{'type':'text','text':text},{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+base64.b64encode(bytes(frame)).decode('ascii')}}]
        out[-1]=last
        return out
