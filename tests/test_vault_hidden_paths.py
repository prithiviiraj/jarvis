import unittest,pathlib,tempfile,sys
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]/'src'))
from jarvis.obsidian import Vault
class HiddenNotes(unittest.TestCase):
 def test_hidden_paths_excluded_from_read_and_create_not_just_search(self):
  with tempfile.TemporaryDirectory()as d:
   r=pathlib.Path(d);(r/'.obsidian').mkdir();(r/'.private').mkdir();(r/'.private/secret.md').write_text('hidden');(r/'.hidden.md').write_text('hidden');v=Vault(d)
   for name in ('.private/secret.md','.hidden.md','../outside.md','notes/.hidden.md'):
    with self.assertRaises(ValueError):v.read(name)
    with self.assertRaises(ValueError):v.create(name,'text',True)
   self.assertEqual(v.search('hidden'),[])
