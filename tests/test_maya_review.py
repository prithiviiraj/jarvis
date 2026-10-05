import unittest
from jarvis.experimental.maya_review import MayaReview
class Tests(unittest.TestCase):
 def test_off_no_inspection(self):
  with self.assertRaises(ValueError):MayaReview().inspect('scene.info',{})
 def test_fixed_reads_ignore_annotations(self):
  r=MayaReview();self.assertEqual(r.inspect('scene.info',{},True)['name'],'scene.info')
  for name in ['script.run','script.execute','scene.save','scene.delete','viewport.capture']:
   with self.assertRaises(ValueError):r.inspect(name,{},True)
 def test_effect_exact_one_use(self):
  r=MayaReview();x=r.prepare('nodes.rename',{'name':'cube','new_name':'box'},True)
  with self.assertRaises(ValueError):r.approve(x)
  x=r.prepare('nodes.rename',{'name':'cube','new_name':'box'},True);self.assertEqual(r.approve(x,True)['arguments']['new_name'],'box')
  with self.assertRaises(ValueError):r.approve(x,True)
 def test_changed_and_cancel(self):
  r=MayaReview();x=r.prepare('selection.set',{'names':['cube']},True);x['arguments']['names']=['all']
  with self.assertRaises(ValueError):r.approve(x,True)
  x=r.prepare('animation.set_time',{'time':4},True);r.cancel()
  with self.assertRaises(ValueError):r.approve(x,True)
 def test_scripts_deletion_files_rejected(self):
  for n in ['script.execute','script.run','nodes.delete','scene.open','scene.save','scene.export']:
   with self.assertRaises(ValueError):MayaReview().prepare(n,{},True)
if __name__=='__main__':unittest.main()
