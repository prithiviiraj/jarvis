import unittest,tempfile,pathlib,hashlib,json,io
from jarvis.models import fetch_verified,DownloadError
class Response(io.BytesIO):
 def __init__(self,data,status=200,cr='',url='https://test.invalid/model'):super().__init__(data);self.status=status;self.headers={'Content-Range':cr};self.url=url
 def getcode(self):return self.status
class HTTP:
 def __init__(self,response):self.response=response;self.request=None
 def open(self,req,timeout):self.request=req;return self.response
class ResumeTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.p=pathlib.Path(self.temp.name)/'model';self.url='https://test.invalid/model';self.sha=hashlib.sha256(b'abcdef').hexdigest()
 def part(self,data=b'abc'):
  self.p.with_name('model.part').write_bytes(data);self.p.with_name('model.part.json').write_text(json.dumps({'url':self.url,'sha256':self.sha,'cap':6}))
 def call(self,http):fetch_verified(http,self.url,self.p,self.sha,6)
 def test_valid_resume(self):
  self.part();h=HTTP(Response(b'def',206,'bytes 3-5/6'));self.call(h);self.assertEqual(h.request.get_header('Range'),'bytes=3-');self.assertEqual(self.p.read_bytes(),b'abcdef')
 def test_server_ignores_range_restart(self):
  self.part();self.call(HTTP(Response(b'abcdef')));self.assertEqual(self.p.read_bytes(),b'abcdef')
 def test_wrong_offset_purges(self):
  self.part()
  with self.assertRaises(DownloadError):self.call(HTTP(Response(b'def',206,'bytes 2-4/6')))
  self.assertFalse(self.p.with_name('model.part').exists());self.assertFalse(self.p.exists())
 def test_unbound_partial_not_resumed(self):
  self.p.with_name('model.part').write_bytes(b'abc');h=HTTP(Response(b'abcdef'));self.call(h);self.assertIsNone(h.request.get_header('Range'))
 def test_bad_hash_not_published(self):
  with self.assertRaises(DownloadError):self.call(HTTP(Response(b'xxxxxx')))
  self.assertFalse(self.p.exists());self.assertFalse(self.p.with_name('model.part').exists())
 def test_network_preserves_bound_partial(self):
  self.part();h=HTTP(None)
  with self.assertRaises(DownloadError):self.call(h)
  self.assertEqual(self.p.with_name('model.part').read_bytes(),b'abc')
 def test_non_tls_purges(self):
  with self.assertRaises(DownloadError):self.call(HTTP(Response(b'abcdef',url='http://test.invalid')))
  self.assertFalse(self.p.exists())
 def test_oversize_purges(self):
  with self.assertRaises(DownloadError):self.call(HTTP(Response(b'abcdefg')))
  self.assertFalse(self.p.with_name('model.part').exists())
 def test_complete_partial_no_network(self):
  self.part(b'abcdef');h=HTTP(None);self.call(h);self.assertIsNone(h.request)
