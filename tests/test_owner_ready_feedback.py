import unittest
from unittest.mock import Mock,patch
from jarvis.completion_feedback import CompletionFeedback,TEXT
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class ReadyFeedback(unittest.TestCase):
 def test_fixed_audio_is_reused_for_same_assets_not_for_changed_assets(self):
  a=CompletionFeedback();s=Mock();s.profile='JARVIS';s.generation=0;s.prepare.return_value=('fixed','pcm',24000);key=('owner-cache-test',1)
  self.assertTrue(a.prepare(s,0,key));calls=s.prepare.call_count;b=CompletionFeedback();self.assertTrue(b.prepare(s,0,key));self.assertEqual(s.prepare.call_count,calls);self.assertTrue(b.prepare(s,0,('owner-cache-test',2)));self.assertEqual(s.prepare.call_count,calls*2)
 def test_no_ready_ack_from_dispatch_or_empty_search_then_one_per_actual_transition(self):
  b=Bridge(WorkspaceVoice())
  try:
   with patch.object(b.game,'snapshot',return_value={'enabled':True,'preview':None}),patch.object(b.managed_session,'check',return_value={'active':False,'busy':True}),patch.object(b.embedding_service,'snapshot',return_value={'query':'plan','busy':True,'results':[]}):b.check_completions();self.assertEqual(b.messages,[])
   with patch.object(b.game,'snapshot',return_value={'enabled':True,'preview':'data:image/jpeg;base64,fixture','generation':3}),patch.object(b.managed_session,'check',return_value={'active':True,'busy':False,'model_id':'owned-proven'}),patch.object(b.embedding_service,'snapshot',return_value={'query':'plan','busy':False,'selected_folder':'reviewed','results':[{'name':'actual.md'}],'error':''}):b.check_completions();b.check_completions();self.assertEqual(len(b.messages),3);self.assertEqual({m['text']for m in b.messages},{TEXT['screen-ready'],TEXT['local-model-ready'],TEXT['search-ready']})
  finally:b.close()
 def test_interface_context_does_not_disclose_browser_image_as_text_to_chat(self):
  b=Bridge(WorkspaceVoice())
  try:
   with patch.object(b.browseros,'snapshot',return_value={'state':'connected','preview':{'data_url':'private-frame-secret'},'tools':['private schema'],'url':'https://example.com'}):context=b.interface_context('browser')
   self.assertNotIn('private-frame-secret',context);self.assertNotIn('private schema',context)
  finally:b.close()
