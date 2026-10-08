import unittest
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.telegram_output import TelegramOutput
from jarvis.telegram_connection import TelegramConnection
from test_google_tokens import Store
class Tests(unittest.TestCase):
 def setUp(self):self.b=Bridge(WorkspaceVoice());self.b.telegram=TelegramConnection(Store(),lambda *a:{});self.b.telegram_output=TelegramOutput(self.b.telegram,self.b.telegram_output.path)
 def tearDown(self):self.b.close()
 def test_inert_no_implicit_bot_and_pause(self):
  s=self.b.execute({'command':'status'})['telegram'];self.assertFalse(s['paired']);self.assertFalse(s['busy']);self.assertIsNone(s['bot'])
  with self.assertRaises(ValueError):self.b.execute({'command':'telegram-pair'})
  with self.assertRaises(ValueError):self.b.execute({'command':'telegram-configure','bot_token':'123456:'+('a'*30)})
  with self.assertRaises(ValueError):self.b.execute({'command':'telegram-approve','reviewed':{},'confirm':True})
  self.b.execute({'command':'pause'});self.assertFalse(self.b.telegram.snapshot()['paired'])
