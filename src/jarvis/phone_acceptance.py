"""Explicit CI-only phone software acceptance. No phone, LAN listener or carrier service."""
def run():
 import hashlib,http.server,io,json,os,pathlib,threading,time,urllib.request,wave
 from unittest.mock import patch
 from . import providers
 from .phone_controller import PhoneController
 from .phone_audio import PhoneAudio
 from .paths import ensure_layout
 from .models import download
 from .voice_assets import download as download_voices
 out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True)
 os.environ['JARVIS_DATA_DIR']=str(pathlib.Path('ci-voice-cache').resolve());cache=ensure_layout()/'models'
 download(cache,consent=True);download_voices(cache/'voices',consent=True)
 fixture=out/'voice-public-fixture.wav';url='https://raw.githubusercontent.com/ggerganov/whisper.cpp/master/samples/jfk.wav'
 if not fixture.exists():
  with urllib.request.urlopen(url,timeout=30)as r:fixture.write_bytes(r.read(960045))
 raw=fixture.read_bytes();calls=[]
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   self.send_response(200);self.end_headers();self.wfile.write(b'{"data":[{"id":"phone-fixture-not-real-llm"}]}')
  def do_POST(self):
   body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));calls.append(body)
   self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':'Hello. I can hear your private call.'},'finish_reason':'stop'}]}).encode())
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();p=PhoneAudio();c=PhoneController(p)
 try:
  with patch.dict(providers.ENDPOINTS,{'local':f'http://127.0.0.1:{server.server_port}/v1'}):
   review=c.request_pair(c.enable(True),'CI synthetic device, not verified owner');token=c.approve(review,True);started=time.monotonic();worker=c.submit(token,raw);worker.join(90)
   if worker.is_alive():raise RuntimeError('Phone software pipeline timeout')
   result=c.take_reply(token)
   assert result and result['text']=='Hello. I can hear your private call.',c.snapshot()
   assert len(calls)==1 and 'country'in calls[0]['messages'][-1]['content'].lower()
   with wave.open(io.BytesIO(result['wav']))as w:assert w.getframerate()==24000 and w.getnchannels()==1 and w.getnframes()>2400
   (out/'phone-local-reply.wav').write_bytes(result['wav']);c.stop()
   try:c.take_reply(token)
   except ValueError:pass
   else:raise AssertionError('Revoked phone token accepted')
   report={'frozen_executable':True,'real_Whisper_and_Kokoro':True,'local_brain_scope':'controlled loopback HTTP fixture, not actual LM Studio model','no_hardware_playback':True,'session_revoke':True,'duration_s':time.monotonic()-started,'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256(result['wav']).hexdigest(),'source_audio':url,'unrun':['phone browser capture/playback','TLS trust and LAN transport','physical device','echo/interruption','real LM Studio model','outside-network route','PSTN calling']}
   (out/'frozen-phone-chain.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
 finally:c.close();server.shutdown();server.server_close()
