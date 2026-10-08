import unittest,queue
from unittest.mock import Mock
from jarvis.browser_control import parse_voice
from jarvis.ui_bridge import Bridge
from jarvis.brain_settings import BrainSettings
class VoiceLinks(unittest.TestCase):
 def bridge(self):
  v=Mock();v.runtime=None;v.busy=False;v.events.get_nowait.side_effect=queue.Empty;v.name='JARVIS';v.reply_actor='JARVIS';v.tts_engine='kokoro'
  return Bridge(voice=v,brains=BrainSettings(store=Mock()))
 def test_explicit_speech_parser(self):
  self.assertEqual(parse_voice('Jarvis browser read links'),{'command':'read-links','value':''})
  self.assertEqual(parse_voice('browser choose link 20.'),{'command':'select-link','value':'20'})
  self.assertIsNone(parse_voice('choose link 1'));self.assertIsNone(parse_voice('browser choose link 21'))
 def test_speech_read_and_select_only_prepare(self):
  b=self.bridge();b.browser_enabled=True;b.browser=Mock();b.browser.cancel.is_set.return_value=False;b.browser.snapshot.return_value={'state':'ready','url':'https://example.com','links':[{'id':'1','url':'https://www.iana.org/domains/example','label':'Learn more'}]}
  self.assertTrue(b.voice_action('browser read links'));b.browser.submit.assert_called_once_with('read-links',confirmed=True);b.browser.submit.reset_mock()
  self.assertTrue(b.voice_action('browser choose link 1'));self.assertEqual(b.browser_pending['value'],'https://www.iana.org/domains/example');b.browser.submit.assert_not_called()
 def test_invalid_selection_clears_stale_and_stopping_rejected(self):
  b=self.bridge();b.browser_enabled=True;b.browser=Mock();b.browser.cancel.is_set.return_value=True;b.browser_pending={'command':'open','value':'https://old.com'}
  self.assertTrue(b.voice_action('browser choose link 1'));self.assertIsNone(b.browser_pending);b.browser.submit.assert_not_called()
 def test_text_preparation_link_command_uses_same_path(self):
  b=self.bridge();b.browser_enabled=True;b.browser=Mock();b.browser.cancel.is_set.return_value=False;b.browser.snapshot.return_value={'state':'ready','url':'https://example.com','links':[{'id':'1','url':'https://www.iana.org/domains/example','label':'Learn more'}]}
  b.execute({'command':'browser-preview','text':'browser choose link 1'});self.assertEqual(b.browser_pending['command'],'open');b.browser.submit.assert_not_called()

 def test_off_and_unsupported_browser_commands_consumed_locally(self):
  b=self.bridge()
  self.assertTrue(b.voice_action('Dex browser open example.com'));self.assertIsNone(b.browser_pending);b.voice.send_text.assert_not_called()
  b.browser_enabled=True
  for text in ['browser choose link 21','Dex browser pay stranger','browser open']:
   self.assertTrue(b.voice_action(text));self.assertIsNone(b.browser_pending);b.voice.send_text.assert_not_called()
  self.assertFalse(b.voice_action('My browser feels slow'))
