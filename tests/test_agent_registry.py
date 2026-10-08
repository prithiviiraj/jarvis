import unittest,tempfile,json
from pathlib import Path
from jarvis.agent_registry import AgentRegistry
class Registry(unittest.TestCase):
 def test_exact_active_roster_and_legacy_file_preserved(self):
  from jarvis.personas import ROLES
  from jarvis.workspace_voice import VOICES
  from jarvis.moderator import ROLES as routed
  with tempfile.TemporaryDirectory()as temp:
   path=Path(temp)/'agents.json';row={'name':'MIRA','personality':'Curious patient tutor.','voice':'af_sky'}
   original=json.dumps({'version':1,'agents':[row]});path.write_text(original)
   registry=AgentRegistry(path);registry.apply()
   self.assertEqual(tuple(ROLES),('JARVIS','LYRA','DEX'));self.assertEqual(tuple(VOICES),tuple(ROLES));self.assertEqual(tuple(routed),tuple(ROLES))
   self.assertEqual(registry.snapshot()['agents'],[]);self.assertEqual(registry.snapshot()['archived_agents'],[row]);self.assertEqual(path.read_text(),original)
   for name in ('MIRA','NOVA','SILA','REO'):
    with self.assertRaises(ValueError):registry.create({**row,'name':name},{**row,'name':name},True)
   self.assertEqual(path.read_text(),original)
 def test_corrupt_file_preserved(self):
  with tempfile.TemporaryDirectory()as temp:
   path=Path(temp)/'agents.json';path.write_text('{broken');registry=AgentRegistry(path)
   self.assertTrue(registry.error);self.assertEqual(path.read_text(),'{broken')
   with self.assertRaises(ValueError):registry.create({})
 def test_idle_explicit_separate_permission_and_pause(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice())
  try:
   self.assertFalse(b.execute({'command':'status'})['idle']['enabled'])
   with self.assertRaises(ValueError):b.execute({'command':'idle-mode','enabled':True})
   state=b.execute({'command':'idle-mode','enabled':True,'consent':True,'audio':False});self.assertTrue(state['idle']['enabled']);self.assertFalse(state['voice_active']);self.assertFalse(state['judgment']['enabled'])
   self.assertFalse(b.execute({'command':'pause'})['idle']['enabled'])
  finally:b.close()
 def test_optional_turn_gates_default_no_download(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock,patch
  b=Bridge(WorkspaceVoice());b.turn_setup.start=Mock()
  try:
   self.assertEqual(b.execute({'command':'status'})['turn_mode'],'vad')
   with self.assertRaises(ValueError):b.execute({'command':'turn-mode','mode':'smart'})
   with patch('jarvis.experimental.smart_turn.ready',return_value=True):
    self.assertEqual(b.execute({'command':'turn-mode','mode':'smart','consent':True})['turn_mode'],'smart')
   b.execute({'command':'turn-check'});b.turn_setup.start.assert_called_once_with(consent=False,check=True)
   b.voice.busy=True
   self.assertEqual(b.execute({'command':'turn-mode','mode':'vad'})['turn_mode'],'vad');self.assertFalse(b.voice.busy)
   b.voice.busy=False
  finally:b.close()
