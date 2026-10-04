import unittest,hashlib
from jarvis.experimental.kitten_onnx import SYMBOLS
from jarvis import kitten_assets
class KittenContract(unittest.TestCase):
 def test_published_token_index(self):
  vocab={c:i for i,c in enumerate(SYMBOLS)}
  self.assertEqual(vocab['ɭ'],104);self.assertEqual(vocab['ⱱ'],137);self.assertEqual(vocab['ᵻ'],177);self.assertEqual(vocab['ˈ'],156)
 def test_assets_pinned_consent(self):
  self.assertIn('84781d74e29ee25217551556398b42f80593a813',kitten_assets.BASE)
  with self.assertRaises(Exception):kitten_assets.download('/tmp/not-used',False)
  self.assertEqual(sum(cap for _,_,cap in kitten_assets.FILES.values()),28402000)
