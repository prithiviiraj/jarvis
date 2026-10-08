import unittest
from jarvis.intent_routing import casual,local_turn
from jarvis.workspace_voice import VOICES
class CasualRouting(unittest.TestCase):
 def test_explicit_casual_only(self):
  for t in ['Hi','LYRA, flirt with me','Jarvis how are you?','Thank you']:self.assertTrue(casual(t),t)
  for t in ['What is quantum gravity?','Maya fix normals','What time is it?','Open the browser','Explain TLS','Hi, tell me about Japan','Why?']:self.assertFalse(casual(t),t)
 def test_last_user_not_injected_system(self):
  self.assertFalse(local_turn([{'role':'system','content':'hi'},{'role':'user','content':'Explain physics'}]))
  self.assertTrue(local_turn([{'role':'user','content':'Hi'},{'role':'assistant','content':'Hello'}]))
 def test_voice_swap(self):
  self.assertEqual(VOICES['LYRA'],'af_heart');self.assertEqual(VOICES['DEX'],'am_fenrir')

 def test_casual_no_api_fallback_when_local_absent(self):
  from unittest.mock import Mock,patch
  from jarvis.brain_settings import BrainSettings
  from jarvis.router import RouterError
  b=BrainSettings(Mock());b.configure([{'id':'slot1','provider':'groq','model':'model','enabled':True,'consent':True,'free':True}],{})
  with patch('jarvis.brain_settings.local_models',return_value=[]),patch('jarvis.brain_settings.BrainRouter')as remote:
   with self.assertRaisesRegex(RouterError,'Casual replies are local-only'):b.router('LYRA').ask([{'role':'user','content':'Hi'}])
   remote.assert_not_called()

 def test_explicit_idle_workflow_no_cloud_fallback(self):
  from unittest.mock import Mock,patch
  from jarvis.brain_settings import BrainSettings
  from jarvis.router import RouterError
  b=BrainSettings(Mock());b.configure([{'id':'slot1','provider':'groq','model':'model','enabled':True,'consent':True,'free':True}],{})
  with patch('jarvis.brain_settings.local_models',return_value=[]),patch('jarvis.brain_settings.BrainRouter')as remote:
   with self.assertRaises(RouterError):b.router('LYRA').ask([{'role':'user','content':'Decide opt-in idle greeting as JSON.'}],local_only=True)
   remote.assert_not_called()
