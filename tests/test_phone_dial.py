import unittest
from jarvis.phone_dial import PhoneDial
class Tests(unittest.TestCase):
 def test_exact_plan_and_no_fake_call(self):
  d=PhoneDial();r=d.prepare('Reviewed contact','+919999999999','Say these exact words',{'id':'fixture','platform':'android','verified_pairing':True})
  with self.assertRaises(ValueError):d.dispatch(r)
  with self.assertRaisesRegex(ValueError,'not installed'):d.dispatch(r,True)
  with self.assertRaises(ValueError):d.dispatch(r,True,transport=lambda:None)
  self.assertIsNone(d.result);d.cancel();self.assertIsNone(d.pending)
 def test_no_name_lookup_phone_guess_or_unpaired_device(self):
  for number,device in (('9999999999',{'id':'fixture','platform':'android','verified_pairing':True}),('+919999999999',{})):
   with self.assertRaises(ValueError):PhoneDial().prepare('brother',number,'hello',device)
