import unittest
from jarvis.personas import prompt,ROLES
class PersonaTests(unittest.TestCase):
 def test_five_identities_honest(self):
  for name,role in ROLES.items():
   text=prompt(name);self.assertIn(name,text);self.assertIn(role,text);self.assertIn('not running background workers',text);self.assertIn('cannot execute tools',text)
