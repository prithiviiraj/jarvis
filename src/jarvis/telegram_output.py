"""Exact laptop-reviewed private-bot output. No remote commands or autosends.
Telegram lacks bot sent-history reads/idempotency. An uncertain output stays blocked.
"""
import base64,hashlib,json,secrets,ssl,threading,urllib.request
from .connector_journal import ConnectorJournal
from .connector_workflows import digest
from .google_read_connector import NoRedirect
class TelegramOutput:
 def __init__(self,connection,path,transport=None,voice=None):self.lock=threading.RLock();self.voice=voice;self.connection=connection;self.path=path;self.transport=transport;self.ledger=None;self.busy=False;self.error='';self.generation=0;self.worker=None
 def journal(self):
  if self.ledger is None:self.ledger=ConnectorJournal(self.path,'telegram-output')
  return self.ledger
 def prepare(self,text):
  if self.busy or self.connection.busy or not self.connection.pair.bound or not self.connection.bot:raise ValueError('Review connected private chat first')
  if not isinstance(text,str)or not 1<=len(text)<=4000:raise ValueError('Review bounded final Telegram words')
  c=self.connection;payload={'kind':'telegram-output','format':'text','bot':dict(c.bot),'identity':dict(c.pair.bound),'text':text}
  j=self.journal()
  if j.job.state=='completed'and j.job.plan and j.job.plan['payload']==payload:raise ValueError('Exact previous output already sent; no duplicate')
  return j.prepare(payload)
 def prepare_voice(self,text):
  if self.busy or self.connection.busy or not self.connection.pair.bound or not self.connection.bot:raise ValueError('Review connected private chat first')
  if not isinstance(text,str)or not 1<=len(text)<=900:raise ValueError('Voice text limited to900characters')
  j=self.journal()
  if j.job.state in ('submitting','uncertain'):raise ValueError('Uncertain prior output cannot be replaced')
  self.busy=True;self.error='';self.generation+=1;ticket=self.generation;ct=self.connection.generation;c=self.connection;bot=dict(c.bot);identity=dict(c.pair.bound)
  def work():
   try:
    if self.voice is None:
     from .telegram_voice import TelegramVoice
     self.voice=TelegramVoice()
    audio=self.voice.render(text,lambda:self.generation!=ticket or c.generation!=ct)
    payload={'kind':'telegram-output','format':'voice','bot':bot,'identity':identity,'text':text,'audio':audio}
    with self.lock:
     if self.generation!=ticket or c.generation!=ct or c.pair.bound!=identity:raise ValueError()
     if j.job.state=='completed'and j.job.plan and j.job.plan['payload']==payload:raise ValueError()
     j.prepare(payload)
   except Exception:self.error='Voice preparation failed or stopped. No output sent. Verified Kokoro assets and MP3 encoder are required.'
   finally:self.busy=False
  self.worker=threading.Thread(target=work,name='telegram-voice-preview',daemon=True);self.worker.start()
 def validate(self,p,ticket,ct):
  c=self.connection
  if self.generation!=ticket or c.generation!=ct or c.busy or c.bot!=p['bot']or c.pair.bound!=p['identity']:raise ValueError('Telegram review changed or stopped')
  bot=c.request('getMe');hook=c.request('getWebhookInfo');chat=c.request('getChat',{'chat_id':p['identity']['chat_id']})
  if bot.get('id')!=p['bot']['id']or bot.get('username')!=p['bot']['username']or bot.get('is_bot')is not True or hook.get('url'):raise ValueError('Bot identity or consumer changed')
  i=p['identity']
  if chat.get('type')!='private'or chat.get('id')!=i['chat_id']or chat.get('username','')!=i['username']or ' '.join(str(chat.get(k,''))for k in ('first_name','last_name')).strip()[:120]!=i['display_name']:raise ValueError('Private destination changed')
  if self.generation!=ticket or c.generation!=ct:raise ValueError('Stopped during verification')
  return True
 def request(self,p):
  voice=p['format']=='voice';method='sendVoice'if voice else'sendMessage'
  body={'chat_id':p['identity']['chat_id'],'allow_paid_broadcast':False}
  if voice:
   a=p['audio'];raw=base64.b64decode(a['audio_base64'],validate=True)
   if len(raw)!=a['audio_bytes']or hashlib.sha256(raw).hexdigest()!=a['audio_sha256']or a['text']!=p['text']or a['mime']!='audio/mpeg':raise ValueError('Audio review changed')
   body['caption']=p['text'];body['voice_bytes']=raw
  else:body.update({'text':p['text'],'link_preview_options':{'is_disabled':True}})
  if self.transport:row=self.transport(method,body)
  else:
   import certifi
   token=self.connection.secure().get('bot-token');opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
   if voice:
    boundary='jarvis-'+secrets.token_hex(24);parts=[]
    for k in ('chat_id','caption','allow_paid_broadcast'):
     value=str(body[k])if k!='allow_paid_broadcast'else'false';parts.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="'+k+'"\r\n\r\n'+value+'\r\n').encode())
    parts.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="voice"; filename="reviewed-voice.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n').encode()+raw+b'\r\n');parts.append(('--'+boundary+'--\r\n').encode());data=b''.join(parts);ctype='multipart/form-data; boundary='+boundary
   else:data=json.dumps(body).encode();ctype='application/json'
   req=urllib.request.Request('https://api.telegram.org/bot'+token+'/'+method,data=data,headers={'Content-Type':ctype},method='POST')
   with opener.open(req,timeout=25)as r:raw=r.read(500001)
   if len(raw)>500000:raise ValueError()
   result=json.loads(raw)
   if not isinstance(result,dict)or result.get('ok')is not True:raise ValueError()
   row=result.get('result')
  if not isinstance(row,dict)or type(row.get('message_id'))is not int or row['message_id']<=0 or not isinstance(row.get('chat'),dict)or row['chat'].get('type')!='private'or row['chat'].get('id')!=p['identity']['chat_id']:raise ValueError('Sent destination not exact')
  if voice:
   if row.get('caption')!=p['text']or not isinstance(row.get('voice'),dict)or not row['voice'].get('file_id'):raise ValueError('Voice send result unverified')
   scope='Telegram returned voice-message identity/caption. Server-transcoded audio and recipient playback not verified.'
  else:
   if row.get('text')!=p['text']:raise ValueError('Sent text not exact')
   scope='Telegram returned exact private-chat text. Delivery/reading not proved.'
  return {'verified':True,'external_id':str(row['message_id']),'scope':scope}
 def submit(self,reviewed,confirm=False):
  j=self.journal()
  if self.busy or confirm is not True or j.job.state!='review'or reviewed!=j.job.plan or digest(j.job.plan['payload'])!=j.job.plan['sha256']:raise ValueError('Review final bot, private destination and words together')
  self.busy=True;self.error='';self.generation+=1;ticket=self.generation;ct=self.connection.generation
  def transport(p):
   if self.generation!=ticket or self.connection.generation!=ct:raise ValueError('Stopped before output')
   return self.request(p)
  def work():
   try:j.submit(reviewed,True,lambda p:self.validate(p,ticket,ct),transport)
   except Exception:self.error='Telegram output blocked or uncertain. No automatic retry. Check the bot chat if outcome is uncertain.'
   finally:self.busy=False
  self.worker=threading.Thread(target=work,name='telegram-reviewed-output',daemon=True);self.worker.start()
 def stop(self):
  with self.lock:
   self.generation+=1
   if self.ledger and self.ledger.job.state in ('review','submitting','uncertain'):self.ledger.cancel()
 def snapshot(self):
  try:s=self.journal().snapshot()
  except Exception:s={'state':'blocked','plan':None,'result':None};self.error='Output ledger invalid. Preserve it; no send or retry.'
  return {**s,'busy':self.busy,'error':self.error,'scope':'Exact text/audio preview review. No automatic output, remote delegation or history reconciliation. Uncertain sends cannot be retried.'}
