"""Frozen clean-cache bundled asset verification with network disabled."""
def run():
 import pathlib,tempfile,sys,socket,json
 from .bundled_models import import_verified,specifications
 from .models import ready as speech_ready
 from .voice_assets import ready as voice_ready
 from .laya_assets import ready as laya_ready
 executable=pathlib.Path(sys.executable).resolve();source=executable.parent.parent/'bundled-models'
 if not source.is_dir():raise RuntimeError('Expected bundle missing; offline-ready claim refused')
 calls=[]
 def denied(*args,**kwargs):calls.append(True);raise RuntimeError('Network disabled in offline bundle acceptance')
 old=socket.create_connection;old_connect=socket.socket.connect;socket.create_connection=denied;socket.socket.connect=denied
 try:
  with tempfile.TemporaryDirectory()as td:
   target=pathlib.Path(td)/'models';installed=import_verified(source,target)
   specs=specifications();assert set(installed)==set(specs),'Every pinned model asset must import into a clean cache'
   assert speech_ready(target)and voice_ready(target/'voices')and laya_ready(target/'laya-browser-v32b-161d54d')
   from .models import digest
   for name,(sha,cap,size)in specs.items():assert digest(target/name)==sha
   assert not calls,'Offline setup attempted a connection'
   print(json.dumps({'scope':('Actual frozen Windows'if getattr(sys,'frozen',False)else'Source-only')+' clean-cache asset import/integrity with network disabled. Not inference quality, sensor or model-loading acceptance.','imported_assets':len(installed),'network_calls':len(calls),'sensors_started':False,'chat_vision_model_bundled':False}),flush=True)
 finally:socket.create_connection=old;socket.socket.connect=old_connect
