import io,threading,unittest,wave
from jarvis.phone_session import PhoneSession

def audio(frames=1600):
 b=io.BytesIO()
 with wave.open(b,'wb')as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\0\0'*frames)
 return b.getvalue()
class Tests(unittest.TestCase):
 def paired(self):
  s=PhoneSession();code=s.enable(True);r=s.request_pair(code,'phone');token=s.approve(r,True);return s,code,token
 def test_consent_and_exact_review(self):
  s=PhoneSession()
  with self.assertRaises(ValueError):s.enable()
  code=s.enable(True);r=s.request_pair(code,'claims to be owner')
  with self.assertRaises(ValueError):s.approve(r)
  with self.assertRaises(ValueError):s.approve(dict(r,label='other'),True)
  token=s.approve(r,True);self.assertTrue(s.snapshot()['paired']);self.assertNotIn(token,str(s.snapshot()));self.assertNotIn(code,str(s.snapshot()))
  with self.assertRaises(ValueError):s.request_pair(code,'replay')
 def test_expiry_and_revoke(self):
  t=[0];s=PhoneSession(lambda:t[0]);code=s.enable(True);r=s.request_pair(code,'phone');t[0]=120
  with self.assertRaises(ValueError):s.approve(r,True)
  s,_,token=self.paired();s.stop()
  with self.assertRaises(ValueError):s.authorize(token)
 def test_audio_bounds(self):
  for raw in (b'x'*44,audio(1599),audio(480001),audio()[:-2]):
   with self.assertRaises(ValueError):PhoneSession.decode(raw)
  self.assertEqual(len(PhoneSession.decode(audio())),3200)
 def test_turn_and_bad_reply(self):
  s,_,token=self.paired();reply={'text':'Hello','wav':audio()};self.assertEqual(s.turn(token,audio(),lambda pcm,c:reply),reply)
  with self.assertRaises(ValueError):s.turn(token,audio(),lambda pcm,c:{'command':'desktop-run'})
  with self.assertRaises(ValueError):s.turn(token,audio(),lambda pcm,c:{'text':'bad','wav':b'not wav'})
  self.assertFalse(s.busy)
 def test_stop_during_turn_suppresses_reply(self):
  s,_,token=self.paired();started=threading.Event();release=threading.Event();errors=[]
  def process(pcm,c):started.set();release.wait(2);return {'text':'late','wav':audio()}
  def run():
   try:s.turn(token,audio(),process)
   except ValueError as e:errors.append(str(e))
  th=threading.Thread(target=run);th.start();self.assertTrue(started.wait(2));s.stop()
  with self.assertRaises(ValueError):s.enable(True)
  release.set();th.join(2);self.assertEqual(errors,['Phone turn revoked']);self.assertFalse(s.busy)
 def test_session_expiry_after_process(self):
  t=[0];s=PhoneSession(lambda:t[0]);r=s.request_pair(s.enable(True),'phone');token=s.approve(r,True)
  def process(p,c):t[0]=900;return {'text':'late','wav':audio()}
  with self.assertRaises(ValueError):s.turn(token,audio(),process)
