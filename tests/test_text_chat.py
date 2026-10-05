import unittest,threading
from unittest.mock import Mock,patch
from jarvis.workspace_voice import WorkspaceVoice,build_text_router
class TextChatTests(unittest.TestCase):
 def controller(self):
  router=Mock();router.stream.return_value=iter([{'text':'Local reply','provider':'local'}])
  c=WorkspaceVoice(Mock(),Mock(return_value=router));return c,router
 def test_local_no_mic_cloud_or_runtime(self):
  c,r=self.controller();c.send_text('Hello').join(2)
  self.assertIsNone(c.runtime);c.factory.assert_not_called();self.assertFalse(r.stream.call_args.kwargs['cloud_consent']);self.assertEqual(c.memory.snapshot(),[('JARVIS','Hello','Local reply')]);self.assertFalse(c.busy)
 def test_shared_context_profile_identity(self):
  c,r=self.controller();c.memory.append('JARVIS','first','answer');c.select('NOVA');c.send_text('What was said?').join(2)
  m=r.stream.call_args.args[0];self.assertIn('You are NOVA',m[0]['content']);self.assertEqual(m[2]['content'],'[JARVIS] answer');self.assertEqual(c.memory.snapshot()[-1][0],'NOVA')
 def test_blank_and_size(self):
  c,r=self.controller()
  for t in ['', '  ', 'a'*2001,None]:
   with self.assertRaises(ValueError):c.send_text(t)
  r.stream.assert_not_called()
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
   def answer(*a,**k):entered.set();release.wait(2);yield {'text':'stale','provider':'local'}
   r.stream.side_effect=answer;w=c.send_text('private');self.assertTrue(entered.wait(1))
   if operation=='select':c.select('NOVA')
   else:getattr(c,operation)()
   release.set();w.join(2);self.assertEqual(c.memory.snapshot(),[]);self.assertFalse(any(k=='answer' for k,v in c.events.queue))
 def test_failed_reply_not_recorded(self):
  c,r=self.controller();r.stream.side_effect=RuntimeError('private server error');c.send_text('hello').join(2);self.assertEqual(c.memory.snapshot(),[]);self.assertTrue(any(k=='error' for k,v in c.events.queue));self.assertFalse(c.busy)
 def test_snapshot_is_copy(self):
  c,r=self.controller();c.memory.append('JARVIS','a','b');s=c.memory.snapshot();s.clear();self.assertEqual(len(c.memory.snapshot()),1)
 def test_local_model_ambiguity(self):
  with patch('jarvis.providers.local_models',return_value=['one','two']):
   with self.assertRaises(RuntimeError):build_text_router()

class SinglePersonaRoutingTests(unittest.TestCase):
 def test_one_local_call_and_correct_memory(self):
  from unittest.mock import Mock
  from jarvis.workspace_voice import WorkspaceVoice
  r=Mock();r.stream.return_value=iter([{'text':'one answer','provider':'local'}]);c=WorkspaceVoice(Mock(),Mock(return_value=r));c.send_text('debug this Python code',auto_pick=True).join(2)
  self.assertEqual(r.stream.call_count,1);self.assertIn('You are DEX',r.stream.call_args.args[0][0]['content']);self.assertEqual(c.memory.snapshot()[0][0],'DEX');self.assertEqual(c.name,'JARVIS');self.assertFalse(r.stream.call_args.kwargs['cloud_consent'])
 def test_manual_keeps_selected(self):
  from unittest.mock import Mock
  from jarvis.workspace_voice import WorkspaceVoice
  r=Mock();r.stream.return_value=iter([{'text':'one answer'}]);c=WorkspaceVoice(Mock(),Mock(return_value=r));c.select('NOVA');c.send_text('debug code',auto_pick=False).join(2)
  self.assertIn('You are NOVA',r.stream.call_args.args[0][0]['content']);self.assertEqual(r.stream.call_count,1)

class IncrementalChatTests(unittest.TestCase):
 def test_visible_partial_then_final_same_turn(self):
  from jarvis.ui_bridge import Bridge
  entered=threading.Event();release=threading.Event();r=Mock()
  def chunks(*a,**k):
   yield {'text':'Hello ','provider':'local'};entered.set();release.wait(2);yield {'text':'world.','provider':'local'}
  r.stream.side_effect=chunks;c=WorkspaceVoice(text_factory=lambda:r);b=Bridge(c)
  worker=c.send_text('hi');self.assertTrue(entered.wait(1));state=b.execute({'command':'status'})
  self.assertTrue(state['busy']);self.assertEqual(state['messages'][-1]['text'],'Hello ')
  release.set();worker.join(2);state=b.execute({'command':'status'});self.assertEqual(state['messages'][-1]['text'],'Hello world.');self.assertEqual(len(state['messages']),2);b.close()
 def test_partial_failure_stays_visible_but_not_memory(self):
  from jarvis.ui_bridge import Bridge
  r=Mock()
  def chunks(*a,**k):yield {'text':'Partial','provider':'local'};raise RuntimeError('stream stopped')
  r.stream.side_effect=chunks;c=WorkspaceVoice(text_factory=lambda:r);b=Bridge(c);c.send_text('hi').join(2);s=b.execute({'command':'status'})
  self.assertEqual(s['messages'][-1]['text'],'Partial');self.assertIn('stream stopped',s['error']);self.assertEqual(c.memory.snapshot(),[]);b.close()

class OwnProfileRetry(unittest.TestCase):
 def test_narrated_other_reply_retried_without_fake_bubble(self):
  r=Mock();r.stream.return_value=iter([{'text':'Nova argues humans are computers.','provider':'local'}]);r.ask.return_value={'text':'Humans learn through experience.','provider':'local'};v=WorkspaceVoice(text_factory=lambda:r)
  v.send_text('Explain humans').join(2);r.ask.assert_called_once();answers=[a for k,a in list(v.events.queue)if k=='answer'];self.assertEqual(len(answers),1);self.assertEqual(answers[0]['profile'],'JARVIS');self.assertNotIn('Nova argues',answers[0]['text']);self.assertEqual(v.memory.snapshot()[0][2],'Humans learn through experience.');v.close()

class GenerationCleanup(unittest.TestCase):
 def test_old_worker_cannot_clear_new_busy(self):
  from jarvis.workspace_voice import WorkspaceVoice
  first=threading.Event();oldrelease=threading.Event();second=threading.Event();newrelease=threading.Event();count=[]
  class Router:
   def stream(self,*a,**kw):
    count.append(1);n=len(count)
    if n==1:first.set();oldrelease.wait(2)
    else:second.set();newrelease.wait(2)
    yield {'text':'Done.','provider':'fixture'}
  v=WorkspaceVoice(text_factory=Router);old=v.send_text('old');first.wait(1);v.pause();new=v.send_text('new');second.wait(1);oldrelease.set();old.join(1);self.assertTrue(v.busy);newrelease.set();new.join(2);self.assertFalse(v.busy);self.assertEqual(len(v.memory.snapshot()),1);v.close()
