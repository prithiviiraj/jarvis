import unittest,tempfile,pathlib
from unittest.mock import Mock
from jarvis.obsidian import Vault
from jarvis.browser_control import BrowserControl
class Connectors(unittest.TestCase):
 def test_vault_read_search_create_not_overwrite(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d);(p/'.obsidian').mkdir();v=Vault(p)
   for bad in ['../x.md','.obsidian/x.md','/x.md','a\\b.md','C:a.md','x.txt']:
    with self.assertRaises(ValueError):v.note(bad,False)
   with self.assertRaises(ValueError):v.create('Tamil.md','வணக்கம்')
   u=v.create('Tamil.md','வணக்கம்',True);self.assertIn('obsidian://open?',u);self.assertEqual(v.read('Tamil.md'),'வணக்கம்');self.assertEqual(v.search('வணக்கம்')[0]['name'],'Tamil.md')
   with self.assertRaises(FileExistsError):v.create('Tamil.md','overwrite',True)
   (p/'linked.md').symlink_to(p/'Tamil.md')
   with self.assertRaises(ValueError):v.read('linked.md')
 def test_browser_no_hidden_actions(self):
  page=Mock();page.url='https://example.com';page.title.return_value='Example';b=BrowserControl(page)
  for u in ['file:///a','http://example.com','https://127.0.0.1','https://localhost','https://10.0.0.1','https://user:pass@example.com','https://[::1]']:
   with self.assertRaises(ValueError):b.destination(u)
  with self.assertRaises(ValueError):b.execute('open','https://example.com')
  page.goto.assert_not_called();b.execute('open','https://example.com',True);page.goto.assert_called_once()
  for c in ['click','submit','type','delete','shell']:
   with self.assertRaises(ValueError):b.execute(c,confirmed=True)
  b.execute('scroll-down');page.mouse.wheel.assert_called_once_with(0,600)
 def test_voice_parser(self):
  from jarvis.browser_control import parse_voice
  self.assertEqual(parse_voice('Jarvis browser open example.com')['value'],'https://example.com')
  self.assertEqual(parse_voice('browser scroll down')['command'],'scroll-down')
  self.assertEqual(parse_voice('browser search for weather')['value'],'weather')
  self.assertIsNone(parse_voice('click pay now'))
  with self.assertRaises(ValueError):parse_voice('browser open localhost')
