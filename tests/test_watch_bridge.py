import unittest
from unittest.mock import Mock,patch
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class Tests(unittest.TestCase):
 def setUp(self):self.b=Bridge(WorkspaceVoice());self.target={'id':123,'title':'Synthetic window'}
 def tearDown(self):self.b.close()
 def test_watch_inert_list_consent(self):
  with self.assertRaises(ValueError):self.b.execute({'command':'watch-windows'})
  with patch('jarvis.game_companion.windows',return_value=[self.target]):s=self.b.execute({'command':'watch-windows','consent':True})
  self.assertFalse(s['game']['enabled']);self.assertEqual(s['game']['windows'],[self.target])
 def test_exact_review_no_audio_and_shared_stop(self):
  self.b.game.enable=Mock()
  with patch('jarvis.game_companion.windows',return_value=[self.target]):
   self.b.execute({'command':'watch-start','target':self.target,'reviewed':self.target,'vision_model':'fixture','consent':True})
  args=self.b.game.enable.call_args.args;self.assertEqual(args[0],args[1]);self.assertEqual(args[3:],(True,False,False));self.assertEqual(type(args[2]).__name__,'LocalWatchModel');self.b.game.enabled=True;self.b.execute({'command':'watch-stop'});self.assertFalse(self.b.game.enabled)
 def test_changed_target_rejected_before_engine(self):
  self.b.game.enable=Mock()
  with patch('jarvis.game_companion.windows',return_value=[]):
   with self.assertRaises(ValueError):self.b.execute({'command':'watch-start','target':self.target,'reviewed':self.target,'vision_model':'fixture','consent':True})
  self.b.game.enable.assert_not_called()
