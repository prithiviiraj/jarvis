import unittest,tempfile,pathlib
from unittest.mock import Mock
from jarvis.ui_bridge import Bridge
from jarvis.brain_settings import BrainSettings
class BrowserReview(unittest.TestCase):
 def test_exact_command_recheck_and_invalid_clear(self):
  v=Mock();v.runtime=None;v.busy=False;v.events.get_nowait.side_effect=__import__('queue').Empty;v.name='JARVIS';v.reply_actor='JARVIS';v.tts_engine='kokoro'
  b=Bridge(voice=v,brains=BrainSettings(store=Mock()));b.execute({'command':'browser-mode','consent':True});state=b.execute({'command':'browser-preview','text':'browser open example.com'});self.assertEqual(state['browser']['pending']['value'],'https://example.com')
  with self.assertRaises(ValueError):b.execute({'command':'browser-run','confirm':True,'reviewed':{'command':'open','value':'https://different.com'}})
  self.assertIsNone(b.browser)
  with self.assertRaises(ValueError):b.execute({'command':'browser-preview','text':'browser open localhost'})
  self.assertIsNone(b.browser_pending)
  b.execute({'command':'pause'});self.assertFalse(b.browser_enabled)
