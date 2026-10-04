import unittest
from unittest.mock import Mock
from jarvis.browser_links import links,prepare_select
class Links(unittest.TestCase):
 def test_observed_https_links_only(self):
  p=Mock();p.url='https://example.com'
  p.locator.return_value.evaluate_all.return_value=[{'label':'Watch','href':'https://youtube.com/watch?v=abc'},{'label':'send','href':'javascript:submit()'},{'label':'local','href':'https://127.0.0.1'},{'label':'duplicate','href':'https://youtube.com/watch?v=abc'}]
  s=links(p);self.assertEqual(len(s['links']),1);self.assertEqual(prepare_select(s,'1',p.url)['value'],'https://youtube.com/watch?v=abc')
  with self.assertRaises(ValueError):prepare_select(s,'1','https://changed.com')
  with self.assertRaises(ValueError):prepare_select(s,'2',p.url)
 def test_youtube_search_is_prepared_url_not_action(self):
  from jarvis.browser_control import parse_voice
  p=parse_voice('Jarvis browser youtube search for Parithabangal');self.assertEqual(p,{'command':'open','value':'https://www.youtube.com/results?search_query=Parithabangal'})
