from unittest.mock import patch
import unittest,tempfile,pathlib,threading,hashlib,io,zipfile
from jarvis.local_model_files import verified,download_checked,extract_runtime
class Response(io.BytesIO):
 status=200;headers={}
class LocalFiles(unittest.TestCase):
 def item(self,data):return{'url':'https://huggingface.co/Qwen/test/resolve/pin/model.gguf','size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 def test_exact(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'model';data=b'checked model';download_checked(self.item(data),p,threading.Event(),opener=lambda *a,**k:Response(data));self.assertTrue(verified(p,self.item(data)));self.assertFalse(p.with_name('model.part').exists())
 def test_bad_hash_never_installed(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'model'
   with self.assertRaises(ValueError):download_checked(self.item(b'good'),p,threading.Event(),opener=lambda *a,**k:Response(b'bad!'))
   self.assertFalse(p.exists());self.assertTrue(p.with_name('model.part').exists())
 def test_oversize(self):
  with tempfile.TemporaryDirectory()as d:
   with self.assertRaises(ValueError):download_checked(self.item(b'one'),pathlib.Path(d)/'m',threading.Event(),opener=lambda *a,**k:Response(b'long payload'))
 def test_stop(self):
  with tempfile.TemporaryDirectory()as d:
   stop=threading.Event();stop.set()
   with self.assertRaises(InterruptedError):download_checked(self.item(b'ok'),pathlib.Path(d)/'m',stop)
 def test_wrong_range(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'m';p.with_name('m.part').write_bytes(b'a');r=Response(b'b');r.status=206;r.headers={'Content-Range':'bytes 2-3/4'}
   with self.assertRaises(ValueError):download_checked(self.item(b'abcd'),p,threading.Event(),opener=lambda *a,**k:r)
 def test_zip_traversal(self):
  with tempfile.TemporaryDirectory()as d:
   z=pathlib.Path(d)/'r.zip'
   with zipfile.ZipFile(z,'w')as f:f.writestr('../llama-server.exe',b'x')
   with self.assertRaises(ValueError):extract_runtime(z,pathlib.Path(d)/'runtime',threading.Event())
 def test_zip_valid_and_preserve_installed(self):
  with tempfile.TemporaryDirectory()as d:
   z=pathlib.Path(d)/'r.zip';p=pathlib.Path(d)/'runtime'
   with zipfile.ZipFile(z,'w')as f:f.writestr('llama-server.exe',b'x');f.writestr('LICENSE.txt',b'MIT')
   with patch('jarvis.local_model_files.verified',return_value=True):extract_runtime(z,p,threading.Event())
   self.assertEqual((p/'llama-server.exe').read_bytes(),b'x')
   with self.assertRaises(ValueError):extract_runtime(z,p,threading.Event())
