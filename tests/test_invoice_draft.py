import unittest
from jarvis.invoice_draft import draft
class Tests(unittest.TestCase):
 def facts(self):return {'seller':'Fixture seller','buyer':'Fixture buyer','invoice_number':'FIXTURE-1','issue_date':'2026-10-08','due_date':'2026-10-10','currency':'INR','items':[{'description':'Fixture service','quantity':2,'unit_price':'0.10'}],'tax_amount':'0.00'}
 def test_missing_not_invented(self):
  r=draft({'seller':'Fixture'});self.assertEqual(r['state'],'needs-details');self.assertIn('tax_amount',r['missing']);self.assertNotIn('total',r)
 def test_exact_decimal_and_no_send(self):
  r=draft(self.facts());self.assertEqual(r['total'],'0.20');self.assertEqual(r['state'],'draft');self.assertNotIn('recipient',r)
 def test_invalid_dates_nan_negative_float_and_precision(self):
  for key,val in [('due_date','2026-10-01'),('tax_amount','NaN'),('tax_amount','-1'),('tax_amount',.1),('tax_amount','0.001')]:
   f=self.facts();f[key]=val
   with self.assertRaises(ValueError):draft(f)
