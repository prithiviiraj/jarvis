import sys,unittest,threading,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jarvis.news_speech import NewsSpeech
class Speaker:
 generation=0
 def __init__(self):self.calls=[];self.stopped=False
 def speak(self,text,**k):self.calls.append(text)
 def stop(self):self.stopped=True
class Tests(unittest.TestCase):
 def setUp(self):self.s=Speaker();self.n=NewsSpeech(lambda:self.s);text='Quoted page text';self.row={'url':'https://example.com/news','text':text,'sha256':hashlib.sha256(text.encode()).hexdigest()}
 def test_exact_review_only(self):
  with self.assertRaises(ValueError):self.n.play(self.row,self.row,lambda:self.row['url'])
  with self.assertRaises(ValueError):self.n.play(self.row,self.row,lambda:'https://example.org',True)
  t=self.n.play(self.row,self.row,lambda:self.row['url'],True);t.join(1);self.assertEqual(self.s.calls,['Quoted page text']);self.n.stop();self.assertTrue(self.s.stopped)
 def test_stop_during_factory_no_playback(self):
  entered=threading.Event();release=threading.Event()
  def factory():entered.set();release.wait(1);return self.s
  self.n=NewsSpeech(factory);t=self.n.play(self.row,self.row,lambda:self.row['url'],True);entered.wait(1);self.n.stop();release.set();t.join(1);self.assertFalse(self.s.calls);self.assertFalse(self.n.busy)
 def test_busy_conversation_rejected(self):
  with self.assertRaises(ValueError):self.n.play(self.row,self.row,lambda:self.row['url'],True,True)
 def test_chunked_page_read_and_changed_page_stop(self):
  current=[self.row['url']]
  class Stream(Speaker):
   def prepare_stream(self,text,generation=None):yield 'first',b'pcm',24000;yield 'late',b'pcm',24000
   def play_prepared(self,prepared,generation=None):self.calls.append(prepared[0]);current[0]='https://example.org/changed'
  speaker=Stream();self.n=NewsSpeech(lambda:speaker);self.n.play(self.row,self.row,lambda:current[0],True).join(1);self.assertEqual(speaker.calls,['first']);self.assertEqual(self.n.status,'Page changed; reading stopped')
if __name__=='__main__':unittest.main(verbosity=2)
