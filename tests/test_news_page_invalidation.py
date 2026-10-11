import hashlib,unittest
from unittest.mock import Mock
from jarvis.news_conductor import NewsConductor
from jarvis.ui_bridge import Bridge
class NewsInvalidation(unittest.TestCase):
 def ready(self,n):
  p=n.preview('https://example.com/news');n.confirm(p,True);n.observe({'state':'ready','requested_url':p['value'],'url':p['value']});text='Captured fixture';n.accept_text({'url':p['value'],'text':text,'sha256':hashlib.sha256(text.encode()).hexdigest()})
 def test_changed_page_and_stop_clear_quote(self):
  for state in ({'state':'ready','url':'https://example.com/elsewhere'},{'state':'error'},{'state':'stopping'},{'state':'off'}):
   n=NewsConductor();self.ready(n);n.observe(state);self.assertEqual(n.observed_url,'');self.assertIsNone(n.text_preview);self.assertIn('no longer current',n.status)
 def test_same_observed_page_preserved(self):
  n=NewsConductor();self.ready(n);quote=n.text_preview;n.observe({'state':'ready','url':n.observed_url});self.assertEqual(n.text_preview,quote)
 def test_actual_bridge_clears_picture_popup_question_and_speech(self):
  b=Bridge();b.browser=Mock();b.browser.snapshot.return_value={'state':'ready','url':'https://example.com/elsewhere'};b.news_speech.stop=Mock()
  try:
   self.ready(b.news);b.neural.offer('news','JARVIS','Old','Old picture/text');b.neural.picture='data:image/jpeg;base64,eA==';b.neural_question={'row':dict(b.neural.row)}
   b.execute({'command':'status'});self.assertIsNone(b.neural.row);self.assertIsNone(b.neural.picture);self.assertIsNone(b.neural_question);b.news_speech.stop.assert_called();b.browser.submit.assert_not_called()
  finally:b.close()
 def test_other_visual_area_survives_news_navigation(self):
  b=Bridge();b.browser=Mock();b.browser.snapshot.return_value={'state':'ready','url':'https://example.com/elsewhere'}
  try:
   self.ready(b.news);b.neural.offer('calendar','JARVIS','Unsaved','Local draft');b.execute({'command':'status'});self.assertEqual(b.neural.row['kind'],'calendar')
  finally:b.close()
