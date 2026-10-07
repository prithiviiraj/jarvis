import unittest,threading
from unittest.mock import Mock
from jarvis.workspace_voice import WorkspaceVoice
class RoundTests(unittest.TestCase):
 def setup_controller(self):
  r=Mock();r.ask.side_effect=[{'text':'NOVA: a joke about the supplied topic.','provider':'local'},{'text':'JARVIS: I heard NOVA.','provider':'local'}];c=WorkspaceVoice(Mock(),Mock(return_value=r));return c,r
 def test_two_profiles_context_local_no_audio(self):
  c,r=self.setup_controller();c.memory.append('DEX','prior question','prior answer');c.team_round('Banter about our conversation').join(2)
  calls=r.ask.call_args_list;self.assertEqual(len(calls),2);self.assertIn('You are NOVA',calls[0].args[0][0]['content']);self.assertIn('You are JARVIS',calls[1].args[0][0]['content']);self.assertIn('[NOVA]',calls[1].args[0][-2]['content']);self.assertEqual(c.memory.snapshot()[-1][0],'JARVIS');self.assertTrue(all(x.kwargs['cloud_consent']==False for x in calls));c.factory.assert_not_called();self.assertIsNone(c.runtime)
 def test_failure_no_partial_round(self):
  c,r=self.setup_controller();r.ask.side_effect=[{'text':'first'},RuntimeError('fail')];c.team_round('topic').join(2);self.assertEqual(c.memory.snapshot(),[]);self.assertFalse(c.busy)
 def test_cancel_switch_close_no_partial(self):
  for action in ['pause','select','close']:
   c,r=self.setup_controller();entered=threading.Event();release=threading.Event()
   def answer(*a,**k):entered.set();release.wait(1);return {'text':'reply'}
   r.ask.side_effect=answer;w=c.team_round('topic');entered.wait(1)
   if action=='select':c.select('DEX')
   else:getattr(c,action)()
   release.set();w.join(2);self.assertEqual(c.memory.snapshot(),[]);self.assertEqual(r.ask.call_count,1)
 def test_scope_input(self):
  c,r=self.setup_controller()
  for topic,names in [('',('NOVA','JARVIS')),('x'*1001,('NOVA','JARVIS')),('x',('NOVA','NOVA')),('x',('UNKNOWN','JARVIS')),('x',('NOVA',))]:
   with self.assertRaises(ValueError):c.team_round(topic,names)
  r.ask.assert_not_called()
 def test_busy_voice_closed(self):
  c,r=self.setup_controller();c.busy=True
  with self.assertRaises(RuntimeError):c.team_round('topic')
  c.busy=False;c.runtime=Mock()
  with self.assertRaises(RuntimeError):c.team_round('topic')
  c.runtime=None;c.close()
  with self.assertRaises(RuntimeError):c.team_round('topic')
 def test_oversized_or_blank_reply(self):
  for reply in ['', 'x'*3001,None]:
   c,r=self.setup_controller();r.ask.side_effect=None;r.ask.return_value={'text':reply};c.team_round('topic').join(2);self.assertEqual(c.memory.snapshot(),[])

 def test_all_five_sequential_context(self):
  c,r=self.setup_controller();names=('JARVIS','NOVA','SILA','LYRA','DEX');r.ask.side_effect=[{'text':n+' actual reply','provider':'local'} for n in names]
  c.team_round('Topic',names).join(2);self.assertEqual([n for n,u,a in c.memory.snapshot()],list(names))
  for i,call in enumerate(r.ask.call_args_list):
   self.assertIn('You are '+names[i],call.args[0][0]['content'])
   for prior in names[:i]:self.assertTrue(any('['+prior+'] '+prior+' actual reply'==m['content'] for m in call.args[0]))
 def test_three_profiles_failure_atomic(self):
  c,r=self.setup_controller();c.memory.append('JARVIS','old','kept');r.ask.side_effect=[{'text':'one'},{'text':'two'},RuntimeError('last failed')];c.team_round('topic',('NOVA','LYRA','DEX')).join(2);self.assertEqual(c.memory.snapshot(),[('JARVIS','old','kept')])
 def test_three_profiles_selection_order(self):
  c,r=self.setup_controller();r.ask.side_effect=[{'text':'one'},{'text':'two'},{'text':'three'}];c.team_round('topic',('DEX','SILA','NOVA')).join(2);self.assertEqual([n for n,u,a in c.memory.snapshot()],['DEX','SILA','NOVA'])
