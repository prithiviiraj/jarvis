import unittest,types,hashlib
from jarvis.news_page import capture
from jarvis.news_speech import NewsSpeech
class Tests(unittest.TestCase):
 def test_snapshot_timestamp_and_label(self):
  page=types.SimpleNamespace(url='https://example.com/news',title=lambda:'Fixture',locator=lambda *a:types.SimpleNamespace(inner_text=lambda **k:'Captured content'))
  row=capture(page,page.url);self.assertIn('+00:00',row['captured_at']);self.assertIn('not live news',row['scope'])
 def test_reviewed_snapshot_read_not_inferred_live_content(self):
  text='Exact captured quote';row={'url':'https://example.com/news','text':text,'sha256':hashlib.sha256(text.encode()).hexdigest(),'captured_at':'2026-10-06T16:48:00+00:00'}
  calls=[];speaker=types.SimpleNamespace(generation=0,speak=lambda t,**k:calls.append(t),stop=lambda:None)
  n=NewsSpeech(lambda:speaker);thread=n.play(row,row,lambda:row['url'],True);thread.join(1);self.assertEqual(calls,[text]);self.assertTrue(n.close())
