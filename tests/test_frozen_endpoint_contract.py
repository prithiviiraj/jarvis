import unittest,ast,inspect
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.audio import ENDPOINT_FRAMES
from jarvis import voice_acceptance
class FrozenEndpointContract(unittest.TestCase):
 def test_fast_default_and_frozen_gate(self):
  voice=WorkspaceVoice(lambda *args:None)
  self.assertEqual(voice.endpoint_mode,'fast');self.assertEqual(ENDPOINT_FRAMES[voice.endpoint_mode]*32,480)
  source=inspect.getsource(voice_acceptance.run)
  self.assertIn("ENDPOINT_FRAMES['fast']==15",source)
  tree=ast.parse(source)
  self.assertFalse(any(isinstance(n,ast.Compare)and isinstance(n.left,ast.Attribute)and n.left.attr=='silence_frames'and any(isinstance(v,ast.Constant)and v.value==25 for v in n.comparators)for n in ast.walk(tree)))
