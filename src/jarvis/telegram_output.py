"""Exact laptop-reviewed private-bot output. No remote commands or autosends.
Telegram lacks bot sent-history reads/idempotency. An uncertain output stays blocked.
"""
import json,ssl,threading,urllib.request
from .connector_journal import ConnectorJournal
from .google_read_connector import NoRedirect
class TelegramOutput:
 def __init__(self,connection,path,transport=None):self.connection=connection;self.path=path;self.transport=transport;self.ledger=None;self.busy=False;self.error='';self.generation=0;self.worker=None
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
  body={'chat_id':p['identity']['chat_id'],'text':p['text'],'link_preview_options':{'is_disabled':True},'allow_paid_broadcast':False}
  if self.transport:row=self.transport('sendMessage',body)
  else:
   import certifi
   token=self.connection.secure().get('bot-token')
   opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
   req=urllib.request.Request('https://api.telegram.org/bot'+token+'/sendMessage',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
   with opener.open(req,timeout=25)as r:raw=r.read(500001)
   if len(raw)>500000:raise ValueError()
   result=json.loads(raw)
   if not isinstance(result,dict)or result.get('ok')is not True:raise ValueError()
   row=result.get('result')
  if not isinstance(row,dict)or type(row.get('message_id'))is not int or row['message_id']<=0 or row.get('text')!=p['text']or not isinstance(row.get('chat'),dict)or row['chat'].get('type')!='private'or row['chat'].get('id')!=p['identity']['chat_id']:raise ValueError('Sent result not exact')
  return {'verified':True,'external_id':str(row['message_id']),'scope':'Telegram returned exact private-chat text. Delivery/reading not proved.'}
 def submit(self,reviewed,confirm=False):
  j=self.journal()
  if self.busy or confirm is not True or j.job.state!='review'or reviewed!=j.job.plan:raise ValueError('Review final bot, private destination and words together')
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
  self.generation+=1
  if self.ledger and self.ledger.job.state in ('review','submitting','uncertain'):self.ledger.cancel()
 def snapshot(self):
  try:s=self.journal().snapshot()
  except Exception:s={'state':'blocked','plan':None,'result':None};self.error='Output ledger invalid. Preserve it; no send or retry.'
  return {**s,'busy':self.busy,'error':self.error,'scope':'Exact text review. No automatic output, remote delegation or history reconciliation. Uncertain sends cannot be retried.'}
