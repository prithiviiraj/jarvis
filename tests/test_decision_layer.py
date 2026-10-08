import unittest
from jarvis.decision_layer import assess
class Tests(unittest.TestCase):
 def test_five_questions_and_names(self):
  r=assess('Jarvis and Nova, open the browser');self.assertEqual(r['addressed'],['JARVIS','NOVA']);self.assertIsNone(r['confidence']);self.assertEqual(assess('Jarvis, tell Nova hello')['addressed'],['JARVIS'])
 def test_existing_routes_not_turned_into_effects(self):
  for q,lane in [('open the browser','browser'),('open Notepad','app'),('hello','local casual'),('vault search dinner','local retrieval'),('send Sam an invoice','external workflow'),('why is politics important','conversation')]:self.assertEqual(assess(q)['lane'],lane,q)
 def test_spoken_requires_endpoint_evidence(self):
  self.assertIn('unknown',assess('open the browser','spoken')['speech_complete']);self.assertIn('incomplete',assess('open the browser','spoken',{'complete':False})['speech_complete']);self.assertEqual(assess('open the browser','spoken',{'complete':True})['speech_complete'],'observed endpoint complete')
 def test_retrieval_query_binding_and_partial(self):
  d={'query':'dinner','results':[],'coverage':{'complete':False,'scanned':500}}
  self.assertIn('partial',assess('dinner',retrieval=d)['vault_coverage']);self.assertIn('unknown',assess('other',retrieval=d)['vault_coverage']);d['coverage']['complete']=True;self.assertIn('selected local text scope',assess('dinner',retrieval=d)['vault_coverage'])
 def test_question_about_send_does_not_authorize_send(self):
  r=assess('Should I email Sam?');self.assertEqual(r['lane'],'external workflow');self.assertIn('ambiguity',r['action_stakes']);self.assertNotIn('proposal',r)
 def test_unknown_and_no_fake_score(self):
  for q in (None,'',123):self.assertEqual(assess(q)['state'],'unknown')
  self.assertEqual(assess('explain this')['vault_coverage'],'unknown until exact-query retrieval')
