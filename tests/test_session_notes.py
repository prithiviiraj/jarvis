import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from jarvis.team_memory import TeamMemory
from jarvis.session_notes import checkpoint
class NotesTests(unittest.TestCase):
 def test_save_then_clear(self):
  m=TeamMemory();m.append('DEX','remember','a real conversation')
  with tempfile.TemporaryDirectory() as d:
   p=checkpoint(m,d);self.assertIn('[DEX] a real conversation',p.read_text());self.assertEqual(m.messages(),[])
 def test_failed_write_preserves(self):
  m=TeamMemory();m.append('JARVIS','a','b')
  with tempfile.TemporaryDirectory() as d,patch('jarvis.session_notes.os.replace',side_effect=OSError('disk')):
   with self.assertRaises(OSError):checkpoint(m,d)
   self.assertEqual(len(m.messages()),2);self.assertEqual(list(Path(d).glob('*.tmp')),[])
 def test_empty(self):
  with self.assertRaises(ValueError):checkpoint(TeamMemory(),'/tmp/not-created')
