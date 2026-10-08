"""Explicit, temporary IPv4 loopback callback. Never a LAN/public listener.
Only captures the one-use PKCE callback. Token exchange remains in the caller.
"""
import http.server,threading,time,urllib.parse
class GoogleLoopback:
 def __init__(self,authorization,clock=time.monotonic):self.auth=authorization;self.clock=clock;self.server=None;self.thread=None;self.callback=None;self.deadline=0;self.lock=threading.RLock();self.generation=0
 def begin(self,client_id,grants,email,consent=False):
  if consent is not True:raise ValueError('Review Google account and scopes before authorization')
  self.stop();parent=self
  class Handler(http.server.BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):
    with parent.lock:
     expected='127.0.0.1:'+str(self.server.server_port)
     if parent.server is not self.server or parent.clock()>=parent.deadline or self.headers.get('Host')!=expected or self.headers.get('Origin')or len(self.path)>4096 or not self.path.startswith('/callback?'):
      self.reply(400,b'Invalid or expired authorization callback.');return
     url='http://'+expected+self.path
     try:
      parsed=urllib.parse.urlsplit(url)
      if parsed.path!='/callback' or parent.callback is not None:raise ValueError()
      # Validate state/destination without consuming the exchange. Only the caller
      # consumes it after capture. callback may contain private auth code.
      q=urllib.parse.parse_qs(parsed.query,keep_blank_values=True)
      import hmac
      if len(q.get('state',[]))!=1 or not parent.auth.oauth.state or not hmac.compare_digest(q['state'][0],parent.auth.oauth.state):raise ValueError()
      if not(('code'in q)^('error'in q)):raise ValueError()
     except Exception:self.reply(400,b'Invalid authorization state.');return
     parent.callback=url;self.reply(200,b'Authorization received. Return to JARVIS.');parent.generation+=1
   def do_POST(self):self.reply(405,b'Method not supported.')
   def reply(self,status,body):
    self.send_response(status);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('Referrer-Policy','no-referrer');self.send_header('Content-Security-Policy',"default-src 'none'");self.send_header('Connection','close');self.end_headers();self.wfile.write(body)
  server=http.server.HTTPServer(('127.0.0.1',0),Handler);server.timeout=.2
  try:result=self.auth.begin(client_id,server.server_port,grants,email,consent)
  except Exception:server.server_close();raise
  with self.lock:self.server=server;self.deadline=self.clock()+300;ticket=self.generation
  def wait():
   try:
    while parent.server is server and parent.generation==ticket and parent.clock()<parent.deadline:server.handle_request()
   finally:
    server.server_close()
    with parent.lock:
     if parent.server is server:parent.server=None
  self.thread=threading.Thread(target=wait,name='google-loopback',daemon=True);self.thread.start();return result
 def complete(self,client_secret=None,save_guard=None):
  with self.lock:
   if not self.callback:raise ValueError('Google browser authorization has not returned')
   callback=self.callback;self.callback=None
  try:return self.auth.complete(callback,client_secret,save_guard)
  finally:self.stop()
 def stop(self):
  with self.lock:self.generation+=1;self.callback=None;self.server=None;self.deadline=0
  thread=self.thread
  if thread and thread is not threading.current_thread():thread.join(timeout=.5)
  self.thread=None;self.auth.cancel()
 def snapshot(self):
  with self.lock:return {'pending':self.server is not None,'callback_received':self.callback is not None,'account':self.auth.expected,'grants':list(self.auth.grants),'scope':'Temporary loopback only. Browser consent does not perform mail/calendar actions.'}
