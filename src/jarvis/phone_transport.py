"""Review-bound TLS listener. No trust installation, firewall change, tunnel or auto-start."""
import hashlib,http.server,ipaddress,json,pathlib,ssl,threading,time,urllib.parse
from .phone_http import PhoneHTTP
class PhoneTransport:
 def __init__(self,endpoints,assets):self.endpoints=endpoints;self.assets=pathlib.Path(assets);self.pending=None;self.server=None;self.worker=None;self.timer=None;self.state='off';self.active=None;self.review_deadline=0;self.lock=threading.RLock()
 @staticmethod
 def certificate(path):
  p=pathlib.Path(path).resolve()
  if not p.is_file()or p.stat().st_size>100000:raise ValueError('Choose bounded existing TLS certificate')
  return p,p.read_bytes()
 def prepare(self,origin,certificate,key,consent=False):
  if consent is not True:raise ValueError('Review private phone transport first')
  if any(not(self.assets/name).is_file()for name in PhoneHTTP.FILES.values()):raise ValueError('Bundled phone web assets missing; no listener prepared')
  u=urllib.parse.urlsplit(origin)
  try:address=ipaddress.ip_address(u.hostname);port=u.port
  except Exception:raise ValueError('Use exact private IPv4 origin and port')from None
  if u.scheme!='https'or not isinstance(address,ipaddress.IPv4Address)or not(address.is_private or address.is_loopback)or address.is_multicast or address.is_unspecified or port is None or not 1024<=port<=65535 or u.path or u.query or u.fragment or u.username or u.password:raise ValueError('Use exact private HTTPS IPv4 address and port')
  cert,raw=self.certificate(certificate);private,_=self.certificate(key)
  context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2
  context.load_cert_chain(str(cert),str(private))
  try:names=ssl._ssl._test_decode_cert(str(cert)).get('subjectAltName',[])
  except Exception:raise ValueError('Certificate metadata unavailable; no listener prepared')from None
  if not any(kind=='IP Address' and ipaddress.ip_address(value)==address for kind,value in names):raise ValueError('Certificate IP SAN must match exact listener interface')
  fingerprint=hashlib.sha256(ssl.PEM_cert_to_DER_cert(raw.decode())).hexdigest()
  payload={'origin':origin,'interface':str(address),'port':port,'certificate_sha256':fingerprint,'expires_after_seconds':900,'limits':'Private listener only, no firewall/tunnel/remote actions. Phone must independently trust this certificate; self-signed is not plug-and-play.'}
  with self.lock:
   if self.server:raise ValueError('Stop current listener first')
   self.pending={'review':payload,'context':context,'certificate':cert,'certificate_bytes':raw};self.review_deadline=time.monotonic()+120;self.state='review'
  return dict(payload)
 def start(self,reviewed,confirm=False,phone_trust_confirmed=False):
  with self.lock:
   if time.monotonic()>=self.review_deadline or confirm is not True or phone_trust_confirmed is not True or not self.pending or reviewed!=self.pending['review']:raise ValueError('Review exact transport and confirm phone trusts certificate')
   p=self.pending
   if p['certificate'].read_bytes()!=p['certificate_bytes']:self.pending=None;raise ValueError('Certificate changed; review again')
   review=p['review'];boundary=PhoneHTTP(self.endpoints,review['origin'],self.assets)
   class Server(http.server.ThreadingHTTPServer):
    daemon_threads=True;allow_reuse_address=False
    def get_request(self):
     sock,addr=super().get_request();sock.settimeout(5)
     try:return p['context'].wrap_socket(sock,server_side=True),addr
     except Exception:sock.close();raise
   server=Server((review['interface'],review['port']),boundary.handler());self.server=server;self.pending=None;self.active=dict(review);self.state='listening';self.worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.1},name='private-phone-tls',daemon=True);self.worker.start();self.timer=threading.Timer(900,self.stop);self.timer.daemon=True;self.timer.start()
  return self.snapshot()
 def stop(self):
  with self.lock:
   server=self.server;worker=self.worker;timer=self.timer;self.server=None;self.worker=None;self.timer=None;self.pending=None;self.active=None;self.state='off';self.endpoints.stop_local()
  if timer:timer.cancel()
  if server:server.shutdown();server.server_close()
  if worker and worker is not threading.current_thread():worker.join(2)
 def snapshot(self):
  with self.lock:return {'state':self.state,'pending':dict(self.pending['review'])if self.pending else None,'active':dict(self.active)if self.active else None,'scope':'Prepared listener only until exact local approval. No certificate trust installation, firewall, tunnel, PSTN or remote desktop commands.'}
