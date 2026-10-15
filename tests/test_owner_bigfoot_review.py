import unittest,pathlib
class BigfootReview(unittest.TestCase):
 def test_rendered_structured_reviews_never_emit_raw_json(self):
  root=pathlib.Path(__file__).resolve().parents[1]/'modern-ui/src'
  for p in root.glob('*.tsx'):
   self.assertNotIn('{JSON.stringify(',p.read_text(),p.name)
  text=(root/'reviewText.ts').read_text();self.assertIn("Content fingerprint",text);self.assertNotIn('slice(',text);self.assertNotIn('JSON.stringify',text)
 def test_first_start_and_existing_page_are_different_and_plain_reviews_keep_original_objects(self):
  root=pathlib.Path(__file__).resolve().parents[1]/'modern-ui/src';text=(root/'main.tsx').read_text();self.assertIn("state==='connected'&&!backend.browseros.url",text);self.assertIn("reviewText(backend.news.pending)",text);self.assertIn("reviewed:backend.news?.pending,confirm:true",text);self.assertNotIn('Activate Laya (Brave)',text)
