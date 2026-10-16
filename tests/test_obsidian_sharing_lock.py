import hashlib,pathlib,tempfile,unittest
from unittest.mock import patch
from jarvis.obsidian_vault import replace_managed,Vault,NAME
class SharingLock(unittest.TestCase):
 def test_transient_lock_retries_and_rechecks(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'note';p.write_bytes(b'old');t=pathlib.Path(d)/'temp';t.write_bytes(b'new');real=pathlib.Path.replace;n=[0];clock=[0.]
   def replace(self,dest):
    n[0]+=1
    if n[0]<3:raise PermissionError('sharing lock')
    return real(self,dest)
   with patch.object(pathlib.Path,'replace',replace):replace_managed(t,p,hashlib.sha256(b'old').hexdigest(),lambda:clock[0],lambda s:clock.__setitem__(0,clock[0]+s))
   self.assertEqual(n[0],3);self.assertEqual(p.read_bytes(),b'new');self.assertFalse(t.exists())
 def test_edit_during_lock_preserved(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'note';p.write_bytes(b'old');t=pathlib.Path(d)/'temp';t.write_bytes(b'new')
   def wait(s):p.write_bytes(b'user edit')
   with patch.object(pathlib.Path,'replace',side_effect=PermissionError('lock')):
    with self.assertRaisesRegex(ValueError,'edited note preserved'):replace_managed(t,p,hashlib.sha256(b'old').hexdigest(),sleep=wait)
   self.assertEqual(p.read_bytes(),b'user edit');self.assertFalse(t.exists())
 def test_permanent_lock_bounded_cleanup(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'note';p.write_bytes(b'old');t=pathlib.Path(d)/'temp';t.write_bytes(b'new');clock=[0.]
   with patch.object(pathlib.Path,'replace',side_effect=PermissionError('lock')):
    with self.assertRaises(PermissionError):replace_managed(t,p,hashlib.sha256(b'old').hexdigest(),lambda:clock[0],lambda s:clock.__setitem__(0,clock[0]+s))
   self.assertLess(clock[0],2);self.assertEqual(p.read_bytes(),b'old');self.assertFalse(t.exists())
 def test_partial_success_hashes_persist_after_later_lock(self):
  import json
  with tempfile.TemporaryDirectory()as d:
   base=pathlib.Path(d);v=Vault(base/'config',lambda:base);v.create(NAME,True);real=pathlib.Path.replace
   def replace(self,dest):
    if dest.name=='DEX.md':raise PermissionError('lock')
    return real(self,dest)
   with patch.object(pathlib.Path,'replace',replace):v.sync([],{}, {},force=True)
   self.assertTrue(v.error);self.assertFalse(list(v.root.rglob('*.jarvis-tmp')));data=json.loads((v.root/'.jarvis-vault.json').read_text(encoding='utf-8'));self.assertEqual(data['hashes']['Team/LYRA.md'],hashlib.sha256((v.root/'Team/LYRA.md').read_bytes()).hexdigest())
   v.sync([],{}, {},force=True);self.assertFalse(v.error);self.assertNotIn('Team/LYRA.md',v.skipped)
