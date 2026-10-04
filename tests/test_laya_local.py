import unittest
from jarvis.experimental.laya_local import LayaLocal
class LocalLaya(unittest.TestCase):
 def test_loopback_only(self):
  self.assertEqual(LayaLocal().url,'http://127.0.0.1:8000/v1/systemone')
  for p in ['8080',True,80,65536]:
   with self.assertRaises(ValueError):LayaLocal(p)
