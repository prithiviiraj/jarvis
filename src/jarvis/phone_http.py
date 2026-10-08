"""HTTP handler factory only. Does not bind/listen or create a certificate.

A future transport must serve a reviewed trusted origin on a private interface.
Never reuse the desktop command bridge. All responses are no-store; no request logs.
"""
import http.server,ipaddress,json,pathlib,ssl,threading,time,urllib.parse
class PhoneHTTP:
 FILES={'/':'index.html','/phone.css':'phone.css','/phone.js':'phone.js','/capture.js':'capture.js'}
 def __init__(self,endpoints,origin,assets,clock=time.monotonic):
  u=urllib.parse.urlsplit(origin)
  if u.scheme!='https'or not u.hostname or u.username or u.password or u.query or u.fragment or u.path not in ('','/'):raise ValueError('Choose one exact HTTPS phone origin')
  self.origin=origin.rstrip('/');self.host=u.netloc;self.assets=pathlib.Path(assets).resolve();self.endpoints=endpoints;self.clock=clock;self.windows={};self.lock=threading.Lock()
 def validate(self,method,path,headers,peer,tls):
  if tls is not True:raise ValueError('TLS required')
  try:addr=ipaddress.ip_address(peer)
  except ValueError:raise ValueError('Invalid network peer')from None
  if not isinstance(addr,ipaddress.IPv4Address)or not any(addr in ipaddress.ip_network(cidr)for cidr in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16','127.0.0.0/8'))or addr.is_multicast or addr.is_unspecified:raise ValueError('Private network peer required')
  # Duplicate Host/Origin/Authorization/Content-Length must be rejected by handler.
  if headers.get('Host')!=self.host or headers.get('Transfer-Encoding'):raise ValueError('Unreviewed host or transfer encoding')
  if method not in ('GET','POST')or '?'in path or '#'in path:raise ValueError('Unsupported method or URL')
  if method=='GET':
   if path not in self.FILES:raise ValueError('Unknown static asset')
   return 0
  if path not in ('/phone/pair','/phone/pair-result','/phone/turn','/phone/reply','/phone/stop'):raise ValueError('Unknown phone route')
  if headers.get('Origin')!=self.origin:raise ValueError('Same origin required')
  if path!='/phone/stop'and headers.get('Content-Type')!='application/json':raise ValueError('JSON required')
  length=headers.get('Content-Length')
  if not isinstance(length,str)or not length.isascii()or not length.isdecimal():raise ValueError('Exact bounded body length required')
  size=int(length)
  if size>1280200:raise ValueError('Phone body too large')
  with self.lock:
   now=self.clock()
   self.windows={p:[t for t in times if now-t<60]for p,times in self.windows.items()if any(now-t<60 for t in times)}
   # Revocation remains available even after noisy polling reaches the limit.
   if path=='/phone/stop':return size
   rows=list(self.windows.get(peer,[]))
   if len(rows)>=150:raise ValueError('Phone rate limit reached')
   if peer not in self.windows and len(self.windows)>=32:raise ValueError('Too many phone peers')
   rows.append(now);self.windows[peer]=rows
  return size
 @staticmethod
 def token(headers):
  auth=headers.get('Authorization','')
  if not auth:return ''
  if not auth.startswith('Bearer ')or len(auth)>220:raise ValueError('Invalid authorization')
  return auth[7:]
 def handler(self):
  boundary=self
  class Handler(http.server.BaseHTTPRequestHandler):
   protocol_version='HTTP/1.0'
   def log_message(self,*args):pass
   def send(self,code,raw,kind='application/json'):
    self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.send_header('Permissions-Policy','microphone=(self), camera=()');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; media-src 'self' blob:; worker-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'");self.end_headers();self.wfile.write(raw)
   def route(self):
    try:
     self.connection.settimeout(10)
     for name in ('Host','Origin','Authorization','Content-Length','Content-Type','Transfer-Encoding'):
      if len(self.headers.get_all(name,[]))>1:raise ValueError('Duplicate sensitive header')
     size=boundary.validate(self.command,self.path,self.headers,self.client_address[0],isinstance(self.connection,ssl.SSLSocket))
     if self.command=='GET':
      filename=boundary.FILES[self.path];raw=(boundary.assets/filename).read_bytes()
      if len(raw)>100000:raise ValueError('Static asset too large')
      self.send(200,raw,'text/html; charset=utf-8'if filename.endswith('.html')else'text/css; charset=utf-8'if filename.endswith('.css')else'application/javascript');return
     body=self.rfile.read(size)
     if len(body)!=size:raise ValueError('Incomplete phone body')
     data=boundary.endpoints.handle(self.path,body,boundary.token(self.headers),True,True);self.send(200,json.dumps(data).encode())
    except (ValueError,OSError,TimeoutError):self.send(400,b'{"error":"Phone request unavailable; reconnect on laptop"}')
   do_GET=route
   do_POST=route
   def do_OPTIONS(self):self.send(405,b'{"error":"Method unavailable"}')
  return Handler
