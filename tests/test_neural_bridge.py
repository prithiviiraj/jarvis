import unittest,tempfile,pathlib
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class NeuralBridgeTests(unittest.TestCase):
 def test_completed_reply_actual_poll_popup_and_clear(self):
  b=Bridge(WorkspaceVoice())
  try:
   b.voice.notify('transcript','make a plan');b.voice.notify('answer',{'profile':'LYRA','text':'1. Draft.\n2. Review.','provider':'groq','stream_id':1});s=b.execute({'command':'status'});row=s['neural']['row'];self.assertEqual(row['actor'],'LYRA');self.assertEqual(row['kind'],'plan');self.assertEqual(row['text'],'1. Draft.\n2. Review.')
   self.assertIsNone(b.neural.worker)
   with self.assertRaisesRegex(ValueError,'speech models'):b.execute({'command':'neural-read','reviewed':row,'confirm':True})
   b.execute({'command':'neural-dismiss'});self.assertIsNone(b.neural.row)
  finally:b.close()
 def test_no_partial_stream_popup_and_interrupt_drops(self):
  b=Bridge(WorkspaceVoice())
  try:
   b.voice.busy=True;b.voice.notify('transcript','make a plan');b.voice.notify('answer',{'profile':'DEX','text':'partial','stream_id':3});s=b.execute({'command':'status'});self.assertIsNone(s['neural']['row']);self.assertIsNotNone(b.neural_pending)
   b.execute({'command':'conversation-interrupt'});self.assertIsNone(b.neural_pending);self.assertIsNone(b.neural.row)
  finally:b.close()
 def test_today_plan_source_no_auto_open(self):
  b=Bridge(WorkspaceVoice())
  try:
   with tempfile.TemporaryDirectory()as d:
    root=pathlib.Path(d);(root/'.obsidian').mkdir();(root/'Planning').mkdir();(root/'Planning/Today.md').write_text('Actual quoted plan.');b.obsidian.root=root;b.obsidian.enabled=True
    s=b.execute({'command':'plan-preview'});self.assertEqual(s['neural']['row']['text'],'Actual quoted plan.');self.assertEqual(s['neural']['row']['kind'],'plan');self.assertIsNone(b.neural.worker)
  finally:b.close()
 def test_changed_plan_note_rejected_before_speech(self):
  b=Bridge(WorkspaceVoice())
  try:
   with tempfile.TemporaryDirectory()as d:
    root=pathlib.Path(d);(root/'.obsidian').mkdir();(root/'Planning').mkdir();note=root/'Planning/Today.md';note.write_text('Original plan');b.obsidian.root=root;b.obsidian.enabled=True;b.setup.ready=True
    row=b.execute({'command':'plan-preview'})['neural']['row'];note.write_text('Changed plan')
    with self.assertRaisesRegex(ValueError,'changed'):b.execute({'command':'neural-read','reviewed':row,'confirm':True})
    self.assertIsNone(b.neural.worker)
  finally:b.close()
 def test_camera_master_cascade_and_stop(self):
  from unittest.mock import Mock
  b=Bridge(WorkspaceVoice())
  try:
   b.context.camera_state('on');b.vision.enable=Mock();s=b.execute({'command':'camera-master','enabled':True,'consent':True});b.vision.enable.assert_called_once_with(True);self.assertEqual(s['awareness']['camera_master_status'],'Camera + local vision ready')
   b.camera.stop=Mock();b.execute({'command':'camera-master','enabled':False});b.camera.stop.assert_called_once();self.assertFalse(b.camera_master)
  finally:b.close()
 def test_empty_runtime_error_clears_old_banner(self):
  b=Bridge(WorkspaceVoice())
  try:
   b.explain_failure('Fixture','failure');self.assertTrue(b.error);b.voice.notify('error','');b.execute({'command':'status'});self.assertEqual(b.error,'')
  finally:b.close()
 def test_explicit_note_search_in_neural_area_no_model(self):
  b=Bridge(WorkspaceVoice())
  try:
   with tempfile.TemporaryDirectory()as d:
    root=pathlib.Path(d);(root/'.obsidian').mkdir();(root/'a.md').write_text('deadline Friday');b.execute({'command':'vault-connect','vault_folder':str(root),'consent':True});s=b.execute({'command':'chat','text':'Lyra search my notes for deadline'});self.assertIn('a.md',s['neural']['row']['text']);self.assertEqual(s['neural']['row']['kind'],'sources');self.assertFalse(b.voice.busy)
  finally:b.close()
 def test_screen_master_requires_vision_never_cloud(self):
  from unittest.mock import patch
  b=Bridge(WorkspaceVoice())
  try:
   with patch('jarvis.providers.local_live_models',return_value=[]):
    with self.assertRaisesRegex(ValueError,'local vision'):b.execute({'command':'screen-master','enabled':True,'consent':True})
   self.assertFalse(b.game.enabled)
   with self.assertRaisesRegex(ValueError,'consent'):b.execute({'command':'screen-master','enabled':True})
  finally:b.close()

 def test_owner_unsaved_edit_exact_and_no_vault_write(self):
  b=Bridge(WorkspaceVoice())
  try:
   row=b.neural.offer('plan','LYRA','Plan','Original')
   s=b.execute({'command':'neural-edit','reviewed':row,'text':'Owner change'})
   self.assertEqual(s['neural']['row']['text'],'Owner change');self.assertIn('unsaved',s['neural']['row']['source']);self.assertIsNone(b.neural_source)
   with self.assertRaises(ValueError):b.execute({'command':'neural-edit','reviewed':row,'text':'late'})
  finally:b.close()
