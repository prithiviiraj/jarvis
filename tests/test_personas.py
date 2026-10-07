import unittest
from jarvis.personas import prompt,ROLES
class PersonaTests(unittest.TestCase):
 def test_five_identities_honest(self):
  for name,role in ROLES.items():
   text=prompt(name);self.assertIn(name,text);self.assertIn(role,text);self.assertIn('not running background workers',text);self.assertIn('cannot execute tools',text)

 def test_roster_known_to_all(self):
  for name in ROLES:
   for other in ROLES:self.assertIn(other,prompt(name))
 def test_lively_no_canned_hearing(self):
  self.assertIn('not proof you heard audio',prompt('LYRA'));self.assertIn('affectionate curious',prompt('LYRA'));self.assertNotIn('Let us settle this and help master',prompt('LYRA'));self.assertIn('experienced manager',prompt('SILA'));self.assertIn('Most introverted',prompt('SILA'))

 def test_short_sweet_all_default_and_custom_profiles(self):
  for name in list(ROLES)+['CUSTOM']:
   self.assertIn('short and sweet:1or2sentences by default',prompt(name));self.assertIn('longer answer only when the actual question genuinely needs depth',prompt(name))
