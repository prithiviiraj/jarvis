import unittest
from jarvis.telegram_pairing import Pairing
class Tests(unittest.TestCase):
 def row(self,code,chat_id=10,kind='private'):return {'update_id':1,'message':{'chat':{'id':chat_id,'type':kind},'from':{'id':chat_id,'is_bot':False,'username':'fixture','first_name':'Fixture'},'text':'/start '+code}}
 def test_one_use_code_exact_review_and_author_bound(self):
  p=Pairing();r=p.begin();update=self.row(r['code']);candidate=p.offer(update)
  with self.assertRaises(ValueError):p.offer(update)
  with self.assertRaises(ValueError):p.confirm(dict(candidate,chat_id=20),True)
  p.confirm(candidate,True);self.assertTrue(p.accepts(update));self.assertFalse(p.accepts(self.row('',20)));p.disconnect();self.assertFalse(p.accepts(update))
 def test_no_group_bot_or_wrong_code(self):
  p=Pairing();r=p.begin()
  for u in (self.row(r['code'],kind='group'),self.row('wrong')):
   with self.assertRaises(ValueError):p.offer(u)
  row=self.row(r['code']);row['message']['from']['is_bot']=True
  with self.assertRaises(ValueError):p.offer(row)
 def test_expiry_and_no_unreviewed_effect(self):
  now=[0];p=Pairing(lambda:now[0]);r=p.begin();candidate=p.offer(self.row(r['code']));self.assertFalse(p.accepts(self.row(r['code'])))
  now[0]=301
  with self.assertRaises(ValueError):p.confirm(candidate,True)
 def test_username_never_replaces_numeric_identity(self):
  p=Pairing();r=p.begin();u=self.row(r['code']);p.confirm(p.offer(u),True);other=self.row('',20);other['message']['from']['username']='fixture';self.assertFalse(p.accepts(other))
