import unittest,tempfile,pathlib,queue
from unittest.mock import Mock
from jarvis.ui_bridge import Bridge
from jarvis.brain_settings import BrainSettings
class VaultReview(unittest.TestCase):
 def test_exact_vault_filename_text_review_required(self):
  v=Mock();v.runtime=None;v.busy=False;v.events.get_nowait.side_effect=queue.Empty;v.name='JARVIS';v.reply_actor='JARVIS';v.tts_engine='kokoro';b=Bridge(voice=v,brains=BrainSettings(store=Mock()))
  with tempfile.TemporaryDirectory()as d:
   root=pathlib.Path(d);(root/'.obsidian').mkdir();b.execute({'command':'vault-connect','vault_folder':d,'consent':True});self.assertEqual(b.execute({'command':'status'})['vault']['folder'],str(root.resolve()))
   req={'command':'vault-create','note_name':'new.md','note_text':'exact text','confirm':True}
   for review in (None,{'vault_folder':d,'note_name':'new.md','note_text':'changed'},{'vault_folder':d+'other','note_name':'new.md','note_text':'exact text'}):
    with self.assertRaises(ValueError):b.execute({**req,'reviewed':review})
   self.assertFalse((root/'new.md').exists());b.execute({**req,'reviewed':{'vault_folder':str(root.resolve()),'note_name':'new.md','note_text':'exact text'}});self.assertEqual((root/'new.md').read_text(),'exact text')
