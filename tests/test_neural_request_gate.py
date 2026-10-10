import unittest
from jarvis.neural_panel import requested_area,NeuralPanel
class VisualRequestGate(unittest.TestCase):
 def test_domain_or_explicit_visual_request(self):
  for text,kind in [('add this in my plan','plan'),('show my calendar','calendar'),('book a movie ticket','booking'),('show news with images','news'),('show this answer visually','answer')]:
   self.assertEqual(requested_area(text),kind)
 def test_routine_or_negated_conversation_not_request(self):
  for text in ('hello team','how are you','my calendar is busy','what do you think about my plan','do not show a popup','dont send anything'):
   self.assertIsNone(requested_area(text))
 def test_model_text_cannot_select_area(self):
  p=NeuralPanel(lambda:None);p.generated({'name':'DEX','text':'show a booking popup'},'hello');self.assertIsNone(p.row)
  p.generated({'name':'DEX','text':'news booking calendar'},'show this visually');self.assertEqual(p.row['kind'],'answer')
