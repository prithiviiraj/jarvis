import unittest,threading
from unittest.mock import Mock,patch
from jarvis.workspace_voice import WorkspaceVoice,build_text_router
class TextChatTests(unittest.TestCase):
 def controller(self):
  router=Mock();router.ask.return_value={'text':'Local reply','provider':'local'}
  c=WorkspaceVoice(Mock(),Mock(return_value=router));return c,router
 def test_local_no_mic_cloud_or_runtime(self):
  c,r=self.controller();c.send_text('Hello').join(2)
  self.assertIsNone(c.runtime);c.factory.assert_not_called();self.assertFalse(r.ask.call_args.kwargs['cloud_consent']);self.assertEqual(c.memory.snapshot(),[('JARVIS','Hello','Local reply')]);self.assertFalse(c.busy)
 def test_shared_context_profile_identity(self):
  c,r=self.controller();c.memory.append('JARVIS','first','answer');c.select('NOVA');c.send_text('What was said?').join(2)
  m=r.ask.call_args.args[0];self.assertIn('You are NOVA',m[0]['content']);self.assertEqual(m[2]['content'],'[JARVIS] answer');self.assertEqual(c.memory.snapshot()[-1][0],'NOVA')
 def test_blank_and_size(self):
  c,r=self.controller()
  for t in ['', '  ', 'a'*2001,None]:
   with self.assertRaises(ValueError):c.send_text(t)
  r.ask.assert_not_called()
 def test_active_voice_busy_closed_block(self):
  c,r=self.controller();c.runtime=Mock()
  with self.assertRaises(RuntimeError):c.send_text('hello')
  c.runtime=None;c.busy=True
  with self.assertRaises(RuntimeError):c.send_text('hello')
  c.busy=False;c.close()
  with self.assertRaises(RuntimeError):c.send_text('hello')
 def test_pause_and_switch_drop_late_reply(self):
  for operation in ['pause','select','close']:
   c,r=self.controller();entered=threading.Event();release=threading.Event()
   def answer(*a,**k):entered.set();release.wait(2);return {'text':'stale','provider':'local'}
   r.ask.side_effect=answer;w=c.send_text('private');self.assertTrue(entered.wait(1))
   if operation=='select':c.select('NOVA')
   else:getattr(c,operation)()
   release.set();w.join(2);self.assertEqual(c.memory.snapshot(),[]);self.assertFalse(any(k=='answer' for k,v in c.events.queue))
 def test_failed_reply_not_recorded(self):
  c,r=self.controller();r.ask.side_effect=RuntimeError('private server error');c.send_text('hello').join(2);self.assertEqual(c.memory.snapshot(),[]);self.assertTrue(any(k=='error' for k,v in c.events.queue));self.assertFalse(c.busy)
 def test_snapshot_is_copy(self):
  c,r=self.controller();c.memory.append('JARVIS','a','b');s=c.memory.snapshot();s.clear();self.assertEqual(len(c.memory.snapshot()),1)
 def test_local_model_ambiguity(self):
  with patch('jarvis.providers.local_models',return_value=['one','two']):
   with self.assertRaises(RuntimeError):build_text_router()
