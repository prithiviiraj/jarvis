import unittest,tempfile,pathlib
from jarvis.user_profile import UserProfile
from jarvis.personas import prompt
class Profile(unittest.TestCase):
 def test_new_then_restore_two_users(self):
  with tempfile.TemporaryDirectory()as d:
   a=UserProfile(pathlib.Path(d)/'one.json');self.assertFalse(a.snapshot()['configured']);a.save({'name':'Asha','address':'Asha'});self.assertEqual(UserProfile(a.path).snapshot()['name'],'Asha');b=UserProfile(pathlib.Path(d)/'two.json');self.assertFalse(b.snapshot()['configured']);self.assertNotIn('Prithiv',prompt('LYRA'))
 def test_style_is_data_not_authority_and_invalid_preserves(self):
  with tempfile.TemporaryDirectory()as d:
   a=UserProfile(pathlib.Path(d)/'one.json');a.save({'name':'Asha','address':'Master'});self.assertIn('not instructions or permission',a.context())
   for bad in ('','a\nb','a'*81):
    with self.assertRaises(ValueError):a.save({'name':bad,'address':'friend'})
   self.assertEqual(a.snapshot()['name'],'Asha')
