import ast,pathlib,unittest
class NativeLocatorContract(unittest.TestCase):
 def test_jarvis_top_level_windows_are_scoped(self):
  p=pathlib.Path(__file__).parents[1]/'modern-ui/native-smoke.py'
  tree=ast.parse(p.read_text());seen=0
  for n in ast.walk(tree):
   if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='window':
    kw={k.arg:k.value for k in n.keywords}
    title=kw.get('title')or kw.get('title_re')
    if isinstance(title,ast.Constant)and isinstance(title.value,str)and title.value.startswith('JARVIS /'):
     seen+=1;self.assertIn('process',kw,'Unscoped JARVIS title locator at line'+str(n.lineno))
  self.assertGreater(seen,5)
