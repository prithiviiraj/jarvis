"""Explicit owner-bot connection and one-use private-chat pairing. No message sends.
Refuses existing webhook/pending queue instead of taking over another consumer.
"""
import hashlib,json,re,ssl,threading,urllib.request,time
from .security import WindowsCredentials,CredentialError
from .google_read_connector import NoRedirect
from .telegram_pairing import Pairing
TOKEN_SLOT='bot-token'
class TelegramCredentials(WindowsCredentials):
 @staticmethod
 def target(slot):
  if slot!=TOKEN_SLOT:raise CredentialError('Invalid Telegram credential slot')
  return 'JARVIS/telegram/'+slot
class TelegramConnection:
 def __init__(self,store=None,transport=None,path=None):self.store=store;self.transport=transport;self.path=path;self.saved=None;self.pair=Pairing();self.bot=None;self.code=None;self.error='';self.status='Telegram not connected';self.busy=False;self.worker=None;self.generation=0;self.lock=threading.RLock();self.load_saved()
 def load_saved(self):
  if not self.path or not self.path.exists():return
  try:
   row=json.loads(self.path.read_text(encoding='utf-8'));bot=row['bot'];identity=row['identity']
   if type(bot.get('id'))is not int or not isinstance(bot.get('username'),str)or type(identity.get('chat_id'))is not int or identity.get('user_id')!=identity['chat_id']or not isinstance(identity.get('username'),str)or not isinstance(identity.get('display_name'),str):raise ValueError()
   self.saved=row;self.status='Saved private pairing requires explicit bot/chat verification and laptop review'
  except Exception:self.error='Saved Telegram identity invalid. No automatic connection or output sharing.'
 def resume(self,consent=False):
  if consent is not True or not self.saved or self.busy:raise ValueError('Review saved pairing before verifying')
  self.stop();self.busy=True;ticket=self.generation;self.error=''
  def work():
   try:
    bot=self.request('getMe');hook=self.request('getWebhookInfo');saved=self.saved
    if {'id':bot.get('id'),'username':bot.get('username')}!=saved['bot']or bot.get('is_bot')is not True or hook.get('url'):raise ValueError()
    identity=saved['identity'];chat=self.request('getChat',{'chat_id':identity['chat_id']})
    if chat.get('type')!='private'or chat.get('id')!=identity['chat_id']or chat.get('username','')!=identity['username']or ' '.join(str(chat.get(k,''))for k in ('first_name','last_name')).strip()[:120]!=identity['display_name']:raise ValueError()
    with self.lock:
     if self.generation!=ticket:return
     import secrets
     self.bot=dict(saved['bot']);self.pair.expires=time.monotonic()+300;self.pair.candidate={**identity,'update_id':saved.get('update_id',0),'review_id':secrets.token_hex(16),'scope':'Saved identity rechecked, not proof of owner. Confirm on this laptop before output sharing.'};self.status='Saved private chat verified. Review identity on this laptop again.'
   except Exception:
    with self.lock:
     if self.generation==ticket:self.error='Saved bot/chat changed or could not be verified. Nothing shared.'
   finally:self.busy=False
  self.worker=threading.Thread(target=work,name='telegram-saved-verify',daemon=True);self.worker.start()
 def secure(self):
  if self.store is None:self.store=TelegramCredentials()
  return self.store
 def request(self,method,payload=None,token=None):
  if method not in ('getMe','getWebhookInfo','getUpdates','getChat'):raise ValueError('Unsupported read-only Telegram method')
  token=token or self.secure().get(TOKEN_SLOT)
  if not isinstance(token,str)or not re.fullmatch(r'[0-9]{5,20}:[A-Za-z0-9_-]{20,100}',token):raise ValueError('Bot token required')
  try:
   if self.transport:row=self.transport(method,payload or {})
   else:
    import certifi
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    req=urllib.request.Request('https://api.telegram.org/bot'+token+'/'+method,data=json.dumps(payload or {}).encode(),headers={'Content-Type':'application/json'},method='POST')
    with opener.open(req,timeout=25)as r:raw=r.read(500001)
    if len(raw)>500000:raise ValueError()
    row=json.loads(raw)
   if not isinstance(row,dict)or row.get('ok')is not True or 'result'not in row:raise ValueError()
   return row['result']
  except Exception:raise ValueError('Telegram read failed. No retry, takeover or token details logged.')from None
 def configure(self,token,consent=False):
  if consent is not True:raise ValueError('Review bot ownership and credential first')
  if not isinstance(token,str)or not re.fullmatch(r'[0-9]{5,20}:[A-Za-z0-9_-]{20,100}',token):raise ValueError('Invalid bot token')
  if self.busy:raise ValueError('Telegram operation still stopping')
  self.stop();self.bot=None;self.busy=True;ticket=self.generation;self.error=''
  def work():
   try:
    bot=self.request('getMe',token=token);hook=self.request('getWebhookInfo',token=token)
    if not isinstance(bot,dict)or bot.get('is_bot')is not True or type(bot.get('id'))is not int or not isinstance(bot.get('username'),str):raise ValueError()
    if not isinstance(hook,dict)or hook.get('url')or type(hook.get('pending_update_count'))is not int or hook['pending_update_count']!=0:raise ValueError('Existing Telegram consumer or pending queue; use a dedicated bot')
    with self.lock:
     if self.generation!=ticket:return
     self.secure().set(TOKEN_SLOT,token);self.bot={'id':bot['id'],'username':bot['username']};self.status='Dedicated bot verified. Start private-chat pairing explicitly.'
   except Exception:
    with self.lock:
     if self.generation==ticket:self.error='Bot verification failed or existing webhook/pending queue found. Use a dedicated owner bot; nothing taken over.'
   finally:self.busy=False
  self.worker=threading.Thread(target=work,name='telegram-bot-verify',daemon=True);self.worker.start()
 def begin(self,consent=False):
  if consent is not True or not self.bot:raise ValueError('Review dedicated Telegram bot before pairing')
  if self.busy:raise ValueError('Telegram operation still stopping')
  self.stop();result=self.pair.begin();self.code=result['code'];self.busy=True;ticket=self.generation;self.error='';self.status='Send the one-use /start code to your dedicated bot, then review this laptop identity'
  def work():
   try:
    hook=self.request('getWebhookInfo')
    if not isinstance(hook,dict)or hook.get('url')or hook.get('pending_update_count')!=0:raise ValueError()
    while self.generation==ticket and time.monotonic()<self.pair.expires:
     rows=self.request('getUpdates',{'timeout':20,'limit':20})
     if not isinstance(rows,list)or len(rows)>20:raise ValueError()
     # No offset is sent: do not acknowledge/delete updates before review.
     if rows:
      if len(rows)!=1:raise ValueError('Multiple pending updates require owner inspection')
      with self.lock:
       if self.generation!=ticket:return
       valid=[]
       for update in rows:
        try:valid.append(self.pair.offer(update))
        except ValueError:continue
       if len(valid)!=1:raise ValueError()
       self.code=None;self.status='Review observed private chat on this laptop. Nothing shared.';return
    with self.lock:
     if self.generation==ticket:self.code=None;self.pair.disconnect();self.status='Telegram pairing expired or stopped'
   except Exception:
    with self.lock:
     if self.generation==ticket:self.code=None;self.pair.disconnect();self.error='Pairing read failed, unrelated updates or existing consumer detected. No queue acknowledged, message sent or permission granted.'
   finally:self.busy=False
  self.worker=threading.Thread(target=work,name='telegram-private-pair',daemon=True);self.worker.start()
 def approve(self,reviewed,confirm=False):
  with self.lock:
   if self.busy:raise ValueError('Pairing read still completing')
   result=self.pair.confirm(reviewed,confirm)
   if self.path:
    import os
    self.path.parent.mkdir(parents=True,exist_ok=True);temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps({'bot':self.bot,'identity':result,'update_id':reviewed['update_id']}),encoding='utf-8');os.replace(temp,self.path)
   self.saved={'bot':self.bot,'identity':result,'update_id':reviewed['update_id']};self.status='Private chat reviewed. Sharing task output still needs exact review.';return result
 def stop(self):
  with self.lock:self.generation+=1;self.code=None;self.pair.disconnect();self.status='Telegram operation stopped'
 def snapshot(self):
  with self.lock:return {**self.pair.snapshot(),'bot':self.bot,'saved_available':self.saved is not None,'pairing_code':self.code,'busy':self.busy,'status':self.status,'error':self.error,'scope':'Read-only bot verification/private pairing. No task delegation, message send or voice send.'}
