import types,unittest,copy,threading
from jarvis.calendar_telegram import CalendarTelegram
class Tests(unittest.TestCase):
 def setUp(self):
  self.source={'state':'completed','plan':{'payload':{'account':'owner@example.invalid','title':'Exact title','start':'2026-10-08T17:00:00+05:30','end':'2026-10-08T17:30:00+05:30','location':'Office','notes':'Private secret notes'}},'result':{'external_id':'event'}};self.drafts=[];self.cal=types.SimpleNamespace(busy=False,generation=0,connection=types.SimpleNamespace(generation=0),snapshot=lambda:copy.deepcopy(self.source),verify_account=lambda a:None,request=lambda *a,**k:{'id':'event'},same=lambda r,p,i:r['id']==i);self.out=types.SimpleNamespace(busy=False,connection=types.SimpleNamespace(generation=0,pair=types.SimpleNamespace(bound={'chat_id':7}),bot={'id':8}),prepare=lambda t:self.drafts.append(t));self.a=CalendarTelegram(self.cal,self.out)
 def test_explicit_live_source_draft_only_omits_notes(self):
  with self.assertRaises(ValueError):self.a.prepare()
  self.a.prepare(True);self.a.worker.join(3);self.assertEqual(len(self.drafts),1);self.assertIn('Exact title',self.drafts[0]);self.assertNotIn('Private secret',self.drafts[0]);self.assertIn('not a restaurant/business',self.drafts[0]);self.assertIn('not sent',self.a.status)
 def test_non_completed_and_changed_event_no_draft(self):
  self.source['state']='uncertain'
  with self.assertRaises(ValueError):self.a.prepare(True)
  self.source['state']='completed';self.cal.same=lambda *a:False;self.a.prepare(True);self.a.worker.join(3);self.assertFalse(self.drafts)
 def test_stop_and_destination_change_during_read(self):
  for stop in (True,False):
   begun=threading.Event();release=threading.Event()
   def read(*a,**k):begun.set();release.wait(3);return {'id':'event'}
   self.cal.request=read;self.a.prepare(True);self.assertTrue(begun.wait(2))
   if stop:self.a.stop()
   else:self.out.connection.generation+=1
   release.set();self.a.worker.join(3);self.assertFalse(self.drafts)

 def test_output_stop_generation_during_live_read_refuses_draft(self):
  self.out.generation=0;self.out.lock=threading.RLock();begun=threading.Event();release=threading.Event()
  def read(*a,**k):begun.set();release.wait(3);return {'id':'event'}
  self.cal.request=read;self.a.prepare(True);self.assertTrue(begun.wait(2))
  with self.out.lock:self.out.generation+=1
  release.set();self.a.worker.join(3);self.assertFalse(self.drafts)
