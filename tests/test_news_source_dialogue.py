import unittest
from unittest.mock import Mock
from jarvis.news_conductor import NewsConductor
from jarvis.ui_bridge import Bridge
class NewsSourceDialogue(unittest.TestCase):
 def test_three_personas_exact_url_no_open(self):
  for actor in ('Jarvis','Lyra','Dex'):
   n=NewsConductor();self.assertTrue(n.request(actor+', show news with images from https://example.com/news?q=local'));self.assertEqual(n.source,'https://example.com/news?q=local');self.assertEqual(n.pending['value'],n.source);self.assertFalse(n.awaiting_open);self.assertEqual(n.observed_url,'');self.assertIsNone(n.text_preview)
 def test_no_source_still_missing_and_question_not_effect(self):
  n=NewsConductor();self.assertTrue(n.request('Dex what is the news today?'));self.assertEqual(n.source,'');self.assertIsNone(n.pending)
  for t in ('do not open news from https://example.com','explain how to open news','news from https://example.com and send it','news from http://example.com'):
   self.assertFalse(n.request(t),t)
 def test_private_credential_urls_rejected(self):
  for url in ('https://127.0.0.1/','https://user:pass@example.com/'):
   with self.assertRaises(ValueError):NewsConductor().request('news from '+url)
 def test_actual_bridge_visual_handoff_no_model_browser_speech(self):
  b=Bridge();b.voice.send_text=Mock();b.news_speech.start=Mock()
  try:
   b.execute({'command':'chat','text':'Lyra show news with pictures from https://example.com/news'})
   self.assertEqual(b.news.pending['value'],'https://example.com/news');self.assertEqual(b.neural.row['kind'],'news');self.assertIn('https://example.com/news',b.neural.row['text']);self.assertIsNone(b.neural.picture);self.assertIsNone(b.browser);b.voice.send_text.assert_not_called();b.news_speech.start.assert_not_called()
   b.execute({'command':'news-cancel'});self.assertIsNone(b.news.pending);self.assertIsNone(b.neural.row)
  finally:b.close()

 def test_new_missing_source_does_not_reuse_prior_pending(self):
  n=NewsConductor();n.preview('https://example.com/old');n.request('Dex show news');self.assertIsNone(n.pending);self.assertEqual(n.source,'');self.assertFalse(n.awaiting_open)

 def test_actual_microphone_runtime_supplied_url_uses_source_review(self):
  import threading
  from jarvis.runtime import VoiceRuntime
  for actor in ('Jarvis','Lyra','Dex'):
   b=Bridge()
   try:
    r=VoiceRuntime.__new__(VoiceRuntime);r.lock=threading.RLock();r.enabled=True;r.generation=1;r.cancel=threading.Event();r.busy=True;r.stt=Mock();r.stt.transcribe.return_value=actor+' show news with pictures from https://example.com/news';r.speaker=Mock();r.speaker.generation=0;r.notify=b.voice.notify;r.action_handler=b.voice_action;r.neural_handler=b.neural_voice_choice;r.mic=Mock();r.router=Mock()
    r.turn([],1,False,[])
    self.assertEqual(b.news.pending['value'],'https://example.com/news');self.assertIn('https://example.com/news',b.neural.row['text']);self.assertNotIn('Which public',b.neural.row['text']);self.assertIsNone(b.neural.picture);self.assertIsNone(b.browser)
    r.router.ask.assert_not_called();r.router.stream.assert_not_called();r.speaker.speak.assert_not_called();r.mic.resume.assert_called_once()
    b.voice_action(actor+' show news');self.assertIsNone(b.news.pending);self.assertEqual(b.news.source,'');self.assertIn('Which public',b.neural.row['text'])
   finally:b.close()
