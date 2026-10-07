import unittest,tempfile,pathlib
from jarvis.knowledge_graph import KnowledgeGraph
class GraphTests(unittest.TestCase):
 def test_actual_links_only_and_preview(self):
  with tempfile.TemporaryDirectory()as d:
   root=pathlib.Path(d);(root/'Planning').mkdir();(root/'Planning/a.md').write_text('# Real plan\n[[b]] [[missing]] [[b#heading|label]]');(root/'Planning/b.md').write_text('# Real second')
   g=KnowledgeGraph().snapshot(root);self.assertEqual(len(g['nodes']),2);self.assertEqual(g['edges'],[{'source':'Planning/a.md','target':'Planning/b.md'}]*2);self.assertTrue(g['nodes'][0]['preview'].startswith('# Real plan'))
 def test_disconnected_empty_and_invalid(self):
  g=KnowledgeGraph();self.assertEqual(g.snapshot(None)['nodes'],[])
  with tempfile.TemporaryDirectory()as d:self.assertEqual(g.snapshot(d)['state'],'ready');self.assertEqual(g.snapshot(d+'/absent')['state'],'unavailable')
 def test_bound_hidden_invalid_and_symlink(self):
  with tempfile.TemporaryDirectory()as d,tempfile.TemporaryDirectory()as ext:
   r=pathlib.Path(d);(r/'.hidden').mkdir();(r/'.hidden/a.md').write_text('private');(r/'bad.md').write_bytes(b'\xff');p=pathlib.Path(ext)/'external.md';p.write_text('outside');
   try:(r/'link.md').symlink_to(p)
   except OSError:pass
   for i in range(250):(r/f'{i}.md').write_text('note')
   g=KnowledgeGraph().snapshot(r);self.assertLessEqual(len(g['nodes']),240);self.assertTrue(g['truncated']);self.assertFalse(any(n['id'].startswith('.')or n['id']=='link.md'for n in g['nodes']))
