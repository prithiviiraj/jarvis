"""Owner-reviewed one-use Telegram pairing. Does not send, poll or grant other access."""
import secrets,time,hashlib,hmac
class Pairing:
 def __init__(self,clock=time.monotonic):self.clock=clock;self.code_hash=None;self.expires=0;self.candidate=None;self.bound=None
 def begin(self):
  code=secrets.token_urlsafe(24);self.code_hash=hashlib.sha256(code.encode()).digest();self.expires=self.clock()+300;self.candidate=None;return {'code':code,'expires_in_seconds':300,'scope':'Send /start CODE to your chosen bot, then review the observed private chat identity here.'}
 def offer(self,update):
  if not self.code_hash or self.clock()>self.expires:raise ValueError('Pairing expired; start again')
  if not isinstance(update,dict)or type(update.get('update_id'))is not int:raise ValueError('Unverified Telegram update shape')
  row=update.get('message');chat=row.get('chat')if isinstance(row,dict)else None;sender=row.get('from')if isinstance(row,dict)else None
  if not isinstance(chat,dict)or chat.get('type')!='private'or type(chat.get('id'))is not int or not isinstance(sender,dict)or sender.get('id')!=chat['id']or sender.get('is_bot')is not False:raise ValueError('Pair only the observed private human chat')
  text=row.get('text','')
  if not isinstance(text,str)or not text.startswith('/start '):raise ValueError('Expected the pairing start code')
  value=text[7:]
  if not hmac.compare_digest(hashlib.sha256(value.encode()).digest(),self.code_hash):raise ValueError('Pairing code did not match')
  # Consume immediately. Another update cannot replace the candidate silently.
  self.code_hash=None;self.candidate={'chat_id':chat['id'],'user_id':sender['id'],'username':sender.get('username',''),'display_name':' '.join(str(sender.get(k,''))for k in ('first_name','last_name')).strip()[:120],'update_id':update['update_id'],'review_id':secrets.token_hex(16),'scope':'Observed Telegram identity, not proof of owner. Confirm on this laptop before sharing task output.'};return dict(self.candidate)
 def confirm(self,reviewed,confirm=False):
  if confirm is not True or not self.candidate or reviewed!=self.candidate or self.clock()>self.expires:raise ValueError('Review the exact current chat before pairing')
  self.bound={'chat_id':self.candidate['chat_id'],'user_id':self.candidate['user_id'],'username':self.candidate['username'],'display_name':self.candidate['display_name']};self.candidate=None;return dict(self.bound)
 def accepts(self,update):
  if not self.bound or not isinstance(update,dict):return False
  row=update.get('message');chat=row.get('chat')if isinstance(row,dict)else None;sender=row.get('from')if isinstance(row,dict)else None
  return isinstance(chat,dict)and isinstance(sender,dict)and chat.get('type')=='private'and chat.get('id')==self.bound['chat_id']and sender.get('id')==self.bound['user_id']and sender.get('is_bot')is False
 def disconnect(self):self.code_hash=None;self.candidate=None;self.bound=None;self.expires=0
 def snapshot(self):return {'paired':self.bound is not None,'identity':self.bound,'pending':self.candidate,'scope':'Private Telegram pairing only. No delegated calendar/mail/action/money permission.'}
