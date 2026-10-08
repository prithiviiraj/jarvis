"""Controlled frozen Telegram software checks. No real bot or output effects."""
def run():
 import json,tempfile,uuid
 from pathlib import Path
 from .telegram_connection import TelegramConnection,TelegramCredentials,TOKEN_SLOT
 from .telegram_output import TelegramOutput
 real=TelegramCredentials();key='fixture-'+uuid.uuid4().hex
 # A scoped target prevents touching the owner's fixed bot-token slot.
 class Scoped(TelegramCredentials):
  @staticmethod
  def target(slot):
   if slot!=TOKEN_SLOT:raise ValueError()
   return 'JARVIS/telegram-acceptance/'+key
 store=Scoped();token='123456:'+('f'*30);calls=[]
 def read(m,p):
  calls.append(m)
  if m=='getMe':return {'ok':True,'result':{'id':123456,'username':'fixture_bot','is_bot':True}}
  if m=='getWebhookInfo':return {'ok':True,'result':{'url':'','pending_update_count':0}}
  if m=='getChat':return {'ok':True,'result':{'id':77,'type':'private','username':'fixture_user','first_name':'Fixture'}}
  return {'ok':True,'result':[{'update_id':1,'message':{'chat':{'id':77,'type':'private'},'from':{'id':77,'is_bot':False,'username':'fixture_user','first_name':'Fixture'},'text':'/start '+c.code}}]}
 try:
  with tempfile.TemporaryDirectory()as d:
   path=Path(d);c=TelegramConnection(store,read,path/'pair.json');assert not calls;c.configure(token,True);c.worker.join(3);assert not c.error;assert store.get(TOKEN_SLOT)==token and token not in json.dumps(c.snapshot());c.begin(True);c.worker.join(3);c.approve(c.snapshot()['pending'],True)
   posts=[]
   def send(m,p):posts.append(p);return {'message_id':12,'chat':{'id':77,'type':'private'},'text':p['text']}
   j=TelegramOutput(c,path/'output.json',send);review=j.prepare('Exact fixture $50 and words');j.submit(review,True);j.worker.join(3);assert j.snapshot()['state']=='completed'and len(posts)==1 and posts[0]['allow_paid_broadcast']is False;assert TelegramOutput(c,path/'output.json',send).snapshot()['state']=='completed'
   c.stop();restored=TelegramConnection(store,read,path/'pair.json');assert not restored.snapshot()['paired'];restored.resume(True);restored.worker.join(3);assert restored.snapshot()['pending'];restored.approve(restored.snapshot()['pending'],True)
   def timeout(*a):raise TimeoutError()
   uncertain=TelegramOutput(restored,path/'uncertain.json',timeout);review=uncertain.prepare('Uncertain fixture');uncertain.submit(review,True);uncertain.worker.join(3);uncertain.stop();assert TelegramOutput(restored,path/'uncertain.json',timeout).snapshot()['state']=='uncertain';restored.stop()
  result={'host':'actual frozen Windows core','real_scoped_Windows_credentials':True,'controlled_private_pair_resume_exact_text_result_restart':True,'uncertain_no_retry_restart':True,'live_telegram':False,'real_bot_connected':False,'output_sent':False,'voice_unrun':True};Path('ui-evidence').mkdir(exist_ok=True);Path('ui-evidence/frozen-telegram-acceptance.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
 finally:store.delete(TOKEN_SLOT)
