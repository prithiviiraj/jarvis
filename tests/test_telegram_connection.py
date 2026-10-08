import unittest,time
from jarvis.telegram_connection import TelegramConnection,TOKEN_SLOT
from test_google_tokens import Store
TOKEN='123456:'+('a'*30)
class Tests(unittest.TestCase):
 def transport(self,m,p):return {'ok':True,'result':{'id':123456,'is_bot':True,'username':'fixture_bot'}if m=='getMe'else{'url':'','pending_update_count':0}}
 def test_no_implicit_network_and_secure_verification(self):
  s=Store();c=TelegramConnection(s,self.transport)
  with self.assertRaises(ValueError):c.configure(TOKEN)
  self.assertFalse(s.rows);c.configure(TOKEN,True);c.worker.join(2);self.assertEqual(s.get(TOKEN_SLOT),TOKEN);self.assertNotIn(TOKEN,str(c.snapshot()));self.assertEqual(c.bot['id'],123456)
 def test_existing_webhook_or_queue_no_save(self):
  for hook in ({'url':'https://existing.invalid','pending_update_count':0},{'url':'','pending_update_count':1}):
   s=Store();c=TelegramConnection(s,lambda m,p:{'ok':True,'result':{'id':123456,'is_bot':True,'username':'fixture_bot'}if m=='getMe'else hook});c.configure(TOKEN,True);c.worker.join(2);self.assertFalse(s.rows);self.assertTrue(c.error)
 def test_private_code_review_no_send_or_queue_ack(self):
  calls=[];c=TelegramConnection(Store(),self.transport);c.configure(TOKEN,True);c.worker.join(2)
  def transport(m,p):
   calls.append((m,p))
   if m=='getWebhookInfo':return {'ok':True,'result':{'url':'','pending_update_count':0}}
   return {'ok':True,'result':[{'update_id':1,'message':{'chat':{'type':'private','id':77},'from':{'id':77,'is_bot':False,'first_name':'Fixture'},'text':'/start '+c.code}}]}
  c.transport=transport;c.begin(True);c.worker.join(2);review=c.snapshot()['pending'];self.assertEqual(review['chat_id'],77);c.approve(review,True);self.assertTrue(c.snapshot()['paired']);self.assertTrue(all('offset'not in p for m,p in calls));self.assertTrue(all(m in ('getWebhookInfo','getUpdates')for m,p in calls));c.stop();self.assertFalse(c.snapshot()['paired'])
 def test_token_errors_redacted(self):
  def failed(*a):raise ValueError(TOKEN)
  c=TelegramConnection(Store(),failed)
  with self.assertRaises(ValueError)as error:c.request('getMe',token=TOKEN)
  self.assertNotIn(TOKEN,str(error.exception))
 def test_saved_resume_explicit_and_live_changed_identity_blocked(self):
  import tempfile,pathlib,json
  with tempfile.TemporaryDirectory()as d:
   path=pathlib.Path(d)/'pair.json';path.write_text(json.dumps({'bot':{'id':123456,'username':'fixture_bot'},'identity':{'chat_id':77,'user_id':77,'username':'fixture_user','display_name':'Fixture'},'update_id':1}))
   calls=[];store=Store();store.set(TOKEN_SLOT,TOKEN)
   def transport(m,p):
    calls.append(m)
    return {'ok':True,'result':{'id':77,'type':'private','username':'fixture_user','first_name':'Fixture'}if m=='getChat'else self.transport(m,p)['result']}
   c=TelegramConnection(store,transport,path);self.assertFalse(calls);self.assertFalse(c.snapshot()['paired']);self.assertTrue(c.snapshot()['saved_available'])
   with self.assertRaises(ValueError):c.resume()
   c.resume(True);c.worker.join(2);r=c.snapshot()['pending'];self.assertFalse(c.snapshot()['paired']);self.assertEqual(r['chat_id'],77);c.approve(r,True);self.assertTrue(c.snapshot()['paired'])
   c=TelegramConnection(store,lambda m,p:{'ok':True,'result':{'id':88,'type':'private'}if m=='getChat'else self.transport(m,p)['result']},path);c.resume(True);c.worker.join(2);self.assertFalse(c.snapshot()['paired']);self.assertIsNone(c.snapshot()['pending']);self.assertTrue(c.error)
 def test_pair_read_does_not_change_allowed_updates_setting(self):
  c=TelegramConnection(Store(),self.transport);c.configure(TOKEN,True);c.worker.join(2);calls=[]
  def transport(m,p):
   calls.append((m,p))
   if m=='getWebhookInfo':return {'ok':True,'result':{'url':'','pending_update_count':0}}
   return {'ok':True,'result':[{'update_id':1,'message':{'chat':{'type':'private','id':77},'from':{'id':77,'is_bot':False},'text':'/start '+c.code}}]}
  c.transport=transport;c.begin(True);c.worker.join(2);self.assertTrue(all('allowed_updates'not in p and 'offset'not in p for m,p in calls))
