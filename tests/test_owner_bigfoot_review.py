import unittest,pathlib
class BigfootReview(unittest.TestCase):
 def test_rendered_structured_reviews_never_emit_raw_json(self):
  root=pathlib.Path(__file__).resolve().parents[1]/'modern-ui/src'
  for p in root.glob('*.tsx'):
   self.assertNotRegex(p.read_text(encoding='utf-8'),r'>\s*\{JSON\.stringify\(',p.name)
  text=(root/'reviewText.ts').read_text(encoding='utf-8');self.assertIn("Content fingerprint",text);self.assertNotIn('slice(',text);self.assertNotIn('JSON.stringify',text)
 def test_first_start_and_existing_page_are_different_and_plain_reviews_keep_original_objects(self):
  root=pathlib.Path(__file__).resolve().parents[1]/'modern-ui/src';text=(root/'main.tsx').read_text(encoding='utf-8');self.assertIn("state==='connected'&&!backend.browseros.url",text);self.assertIn("reviewText(backend.news.pending)",text);self.assertIn("reviewed:backend.news?.pending,confirm:true",text);self.assertNotIn('Activate Laya (Brave)',text)

 def test_app_review_guard_compares_objects_not_display_text(self):
  text=(pathlib.Path(__file__).resolve().parents[1]/'modern-ui/src/main.tsx').read_text(encoding='utf-8')
  self.assertIn('JSON.stringify(appReview)!==JSON.stringify(backend?.desktop?.pending)',text)
  self.assertNotIn('reviewText(appReview)!==JSON.stringify',text)
