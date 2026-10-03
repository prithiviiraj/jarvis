import unittest,json
from types import SimpleNamespace as N
from jarvis.proactive import *
from jarvis.local_awareness import LocalContext
class ProactiveTests(unittest.TestCase):
 def make(self,text='{"speak":true,"text":"Want some water, master?"}',cloud=False):
  c=LocalContext();c.set_apps(True);calls=[];notes=[]
  r=N(providers=[N(cloud=cloud)],ask=lambda *a,**k:(calls.append((a,k)) or {'text':text,'cloud':False,'model':'test-local'}))
  j=ProactiveJudge(c,lambda:r,lambda *a:notes.append(a),clock=lambda:200,hour=lambda:9);return c,j,calls,notes
 def event(self,c):c.app_event({'process':'code.exe'})
 def test_requires_consent(self):
  c,j,*_=self.make()
  with self.assertRaises(ValueError):j.enable()
 def test_off_no_call(self):
  c,j,calls,_=self.make();self.event(c);self.assertIsNone(j.poll());self.assertFalse(calls)
 def test_one_local_request(self):
  c,j,calls,n=self.make();j.enable(True);self.event(c);j.poll().join(2);self.assertEqual(len(calls),1);self.assertFalse(calls[0][1]['cloud_consent']);self.assertTrue(any(x[0]=='proactive-answer' for x in n));self.assertIsNone(j.poll())
 def test_silence(self):
  c,j,calls,n=self.make('{"speak":false,"text":""}');j.enable(True);self.event(c);j.poll().join(2);self.assertFalse(any(x[0]=='proactive-answer' for x in n))
 def test_cloud_refused(self):
  c,j,calls,n=self.make(cloud=True);j.enable(True);self.event(c);j.poll().join(2);self.assertFalse(calls)
 def test_quiet_drop(self):
  c,j,calls,n=self.make();j.hour=lambda:1;j.enable(True);self.event(c);self.assertIsNone(j.poll());j.hour=lambda:9;self.assertIsNone(j.poll());self.assertFalse(calls)
 def test_gaming_no_local_request(self):
  c,j,calls,n=self.make();j.enable(True);j.gaming=True;self.event(c);self.assertIsNone(j.poll());self.assertFalse(calls)
 def test_busy_drop(self):
  c,j,calls,n=self.make();j.enable(True);self.event(c);self.assertIsNone(j.poll(True));self.assertFalse(calls)
 def test_cooldown(self):
  c,j,calls,n=self.make();j.enable(True);self.event(c);j.poll().join(2);c.app_event({'process':'other.exe'});self.assertIsNone(j.poll());self.assertEqual(len(calls),1)
 def test_schema(self):
  for s in ['bad','{}','{"speak":1,"text":"hi"}','{"speak":true,"text":""}',json.dumps({'speak':True,'text':'a'*241}),'{"speak":true,"text":"hi","tool":"delete"}']:
   with self.assertRaises((ValueError,TypeError)):decision(s)
 def test_quiet_wrap(self):self.assertTrue(quiet_hour(23,22,7));self.assertFalse(quiet_hour(12,22,7))
 def test_no_replay_before_consent(self):
  c,j,calls,n=self.make();self.event(c);j.enable(True);self.assertIsNone(j.poll());self.assertFalse(calls)
 def test_stop_discards_late_answer(self):
  gate=threading.Event();entered=threading.Event();c,j,calls,n=self.make();j.router_factory=lambda:N(providers=[N(cloud=False)],ask=lambda *a,**k:(entered.set(),gate.wait(2),{'text':'{"speak":true,"text":"Hello master."}','cloud':False})[-1]);j.enable(True);self.event(c);w=j.poll();self.assertTrue(entered.wait(1));j.stop();gate.set();w.join(2);self.assertFalse(any(x[0]=='proactive-answer' for x in n))
 def test_changed_source_discards(self):
  c,j,calls,n=self.make();r=j.router_factory();old=r.ask
  def ask(*a,**k):c.app_event({'process':'other.exe'});return old(*a,**k)
  r.ask=ask;j.router_factory=lambda:r;j.enable(True);self.event(c);j.poll().join(2);self.assertFalse(any(x[0]=='proactive-answer' for x in n))
 def test_failure_no_fallback(self):
  c,j,calls,n=self.make('not json');j.enable(True);self.event(c);j.poll().join(2);self.assertEqual(len(calls),1);self.assertFalse(any(x[0]=='proactive-answer' for x in n))
 def test_rate_cap(self):
  c,j,calls,n=self.make();j.requests.extend([199]*12);j.enable(True);self.event(c);self.assertIsNone(j.poll());self.assertFalse(calls)
 def test_non_observation_event_no_request(self):
  c,j,calls,n=self.make();j.enable(True);self.event(c);j.poll().join(2);j.clock=lambda:400;c.emit('camera',{'state':'off'});self.assertIsNone(j.poll());self.assertEqual(len(calls),1)
 def test_stop_during_speaker_load(self):
  gate=threading.Event();entered=threading.Event();played=[];c,j,calls,n=self.make();speaker=N(generation=0,stop=lambda:None,speak=lambda *a,**k:played.append(a))
  def factory():entered.set();gate.wait(2);return speaker
  j.speaker_factory=factory;j.enable(True,True);self.event(c);w=j.poll();self.assertTrue(entered.wait(1));j.stop();gate.set();w.join(2);self.assertFalse(played)
