import unittest
from jarvis.reflex_session import ReflexSession
class Tests(unittest.TestCase):
 def test_inert_consent_and_stop(self):
  s=ReflexSession();self.assertFalse(s.enabled)
  with self.assertRaises(ValueError):s.preview('Hello')
  with self.assertRaises(ValueError):s.set_enabled(True)
  s.set_enabled(True,True);s.preview('Jarvis send an invoice');s.stop();self.assertIsNone(s.result);self.assertFalse(s.enabled)
 def test_five_actual_questions_no_probability(self):
  s=ReflexSession();s.set_enabled(True,True);r=s.preview('Jarvis call my brother');self.assertIn('JARVIS',r['addressed']);self.assertIn('review',r['action_stakes']);self.assertIsNone(r['confidence']);self.assertIn('unknown',r['vault_coverage']);self.assertIn('typed',r['speech_complete']);self.assertEqual(r['lane'],'external workflow')
 def test_speech_endpoint_and_exact_query_scope(self):
  s=ReflexSession();s.set_enabled(True,True);self.assertIn('unknown',s.preview('hello','speech')['speech_complete']);self.assertIn('incomplete',s.preview('hello','speech',{'complete':False})['speech_complete']);r=s.preview('hello',retrieval={'query':'other','results':[],'coverage':{'complete':True,'scanned':2}});self.assertIn('unknown',r['vault_coverage'])
 def test_detached_result_and_validation(self):
  s=ReflexSession();s.set_enabled(True,True);r=s.preview('Hello');r['lane']='mutated';self.assertNotEqual(s.result['lane'],'mutated');s.set_enabled(False);self.assertIsNone(s.result)
  for value in [1,'yes',None]:
   with self.assertRaises(ValueError):s.set_enabled(value,True)
