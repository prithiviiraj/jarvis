import unittest,tempfile,pathlib
from unittest.mock import Mock,patch
from jarvis.embedding_service import EmbeddingService
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class GemmaSearch(unittest.TestCase):
 def test_owner_note_request_starts_bounded_local_text_search_no_download(self):
  s=EmbeddingService()
  with patch.object(s,'executable',return_value=['fixture']),patch.object(s,'start')as start:
   self.assertTrue(s.search_notes('/reviewed-vault','the saved plan'));start.assert_called_once_with('search',{'folder':'/reviewed-vault','query':'the saved plan','encoders':'text','dimensions':256,'consent':True})
 def test_missing_runtime_or_busy_does_not_start_any_download(self):
  s=EmbeddingService()
  with patch.object(s,'executable',side_effect=ValueError('missing')),patch.object(s,'start')as start:self.assertFalse(s.search_notes('/reviewed-vault','plan'));start.assert_not_called()
  s.busy=True
  with patch.object(s,'start')as start:self.assertFalse(s.search_notes('/reviewed-vault','plan'));start.assert_not_called()
 def test_bridge_exact_matches_remain_while_semantic_candidates_are_optional(self):
  with tempfile.TemporaryDirectory()as d:
   root=pathlib.Path(d);(root/'.obsidian').mkdir();(root/'plan.md').write_text('Actual plan')
   b=Bridge(WorkspaceVoice());b.vault=Mock();b.vault.root=root
   try:
    with patch.object(b.embedding_service,'search_notes',return_value=True)as search:
     self.assertTrue(b.knowledge_action('search my notes for plan'));search.assert_called_once_with(root,'plan');self.assertTrue(any(r['name']=='plan.md'for r in b.knowledge.results));self.assertIsNone(b.knowledge.note)
   finally:b.vault=None;b.close()
