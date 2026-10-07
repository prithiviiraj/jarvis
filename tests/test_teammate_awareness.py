import unittest
from jarvis.teammate_awareness import TeammateAwareness
class Awareness(unittest.TestCase):
 def test_off_and_review(self):
  calls=[];a=TeammateAwareness(lambda:calls.append(1)or{'DEX':'No background jobs'});m=[{'role':'system','content':'DEX'},{'role':'user','content':'what are you doing'}];self.assertEqual(a.attach(m,'DEX'),(m,False));self.assertEqual(calls,[])
  with self.assertRaises(ValueError):a.enable()
  a.enable(True);out,local=a.attach(m,'DEX');self.assertTrue(local);self.assertIn('No background jobs',out[1]['content']);self.assertEqual(a.attach(m,'LYRA'),(m,False));a.stop();self.assertEqual(a.attach(m,'SILA'),(m,False))
 def test_app_actual_state_no_fake_jobs(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice())
  try:
   s=b.teammate_state();self.assertFalse(s['teammates']['DEX']['independent_background_work']);self.assertIsNone(s['teammates']['SILA']['recent_actual_reply']);self.assertEqual(s['permitted_local_sensors']['camera'],'off');b.execute({'command':'teammate-awareness','enabled':True,'consent':True});b.stop();self.assertFalse(b.teammate_awareness.enabled)
  finally:b.close()
 def test_factual_direct_question_does_not_ask_model(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice())
  try:
   b.teammate_awareness.enable(True);self.assertTrue(b.teammate_query('DEX, what app am I using?'));self.assertIn('do not know',b.messages[-1]['text']);self.assertEqual(b.messages[-1]['provider'],'verified-app-state');self.assertTrue(b.teammate_query('SILA, what are you doing?'));self.assertIn('No independent background work',b.messages[-1]['text'])
  finally:b.close()
