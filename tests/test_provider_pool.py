import unittest
from unittest.mock import Mock
from jarvis.provider_pool import Slot,ProviderPool
from jarvis.router import ProviderFailure
from jarvis.security import WindowsCredentials
class PoolTests(unittest.TestCase):
 def test_five_slots(self):
  slots=[Slot('slot'+str(i),'gemini','model',str(i)) for i in range(1,6)];p=ProviderPool(slots,{'NOVA':[s.id for s in slots]});self.assertEqual(len(p.slots),5)
 def test_session_gate(self):
  p=ProviderPool([Slot('slot1','gemini','model')],{'NOVA':['slot1']})
  with self.assertRaises(ValueError):p.router('NOVA',Mock(),['slot1'],[])
 def test_key_targets_and_profile_fallback(self):
  slots=[Slot('slot1','groq','model'),Slot('slot2','nim','model')];p=ProviderPool(slots,{'DEX':['slot2','slot1']});keys=Mock();keys.get.return_value='synthetic';t=Mock();t.complete.side_effect=[ProviderFailure('http-429'),'ok'];r=p.router('DEX',keys,['slot1','slot2'],['slot1','slot2'],t);a=r.ask([{}],cloud_consent=True);self.assertEqual(a['provider'],'slot1');self.assertEqual([c.args[0] for c in keys.get.call_args_list],['nim/slot2','groq/slot1'])
 def test_local_no_key(self):
  p=ProviderPool([Slot('slot1','local','model')],{'JARVIS':['slot1']});keys=Mock();t=Mock();t.complete.return_value='ok';p.router('JARVIS',keys,transport=t).ask([{}]);keys.get.assert_not_called()
 def test_invalid(self):
  for provider in ['unknown','grok']:
   with self.assertRaises(ValueError):Slot('slot1',provider,'model')
  with self.assertRaises(ValueError):Slot('slot1','gemini','bad key?')
  with self.assertRaises(ValueError):ProviderPool([Slot('slot1','local','model')],{'JARVIS':['slot2']})
 def test_target_allowlist(self):
  self.assertEqual(WindowsCredentials.target('gemini/slot5'),'JARVIS/provider/gemini/slot5')
  with self.assertRaises(Exception):WindowsCredentials.target('gemini/../../bad')

 def test_auth_no_cross_account_retry(self):
  slots=[Slot('slot1','gemini','model'),Slot('slot2','nim','model')];p=ProviderPool(slots,{'NOVA':['slot1','slot2']});keys=Mock();keys.get.return_value='synthetic';t=Mock();t.complete.side_effect=ProviderFailure('http-401',False);r=p.router('NOVA',keys,['slot1','slot2'],['slot1','slot2'],t)
  with self.assertRaises(Exception):r.ask([{}],cloud_consent=True)
  self.assertEqual(t.complete.call_count,1)
