import unittest,threading,time
from jarvis.dialogue_prefetch import Prefetch
class PrefetchTests(unittest.TestCase):
 def test_bounded_queue_cancel_stops_worker(self):
  cancel=threading.Event()
  class Router:
   def stream(self,*a,**kw):
    for i in range(10000):yield {'text':str(i)}
  p=Prefetch(Router(),[],cancel);time.sleep(.08)
  self.assertLessEqual(p.queue.qsize(),3);cancel.set();p.worker.join(1);self.assertFalse(p.worker.is_alive());self.assertEqual(list(p.stream()),[])
 def test_error_propagates_after_actual_delta(self):
  class Router:
   def stream(self,*a,**kw):
    yield {'text':'Actual.'};raise ValueError('fixture failure')
  p=Prefetch(Router(),[],threading.Event());s=p.stream();self.assertEqual(next(s)['text'],'Actual.')
  with self.assertRaisesRegex(ValueError,'fixture failure'):next(s)
  p.worker.join(1)
 def test_local_workflow_flag_preserved(self):
  calls=[]
  class Router:
   def stream(self,*a,**kw):calls.append(kw);yield {'text':'Hi.'}
  p=Prefetch(Router(),[],threading.Event(),local_only=True);self.assertEqual(list(p.stream()),[{'text':'Hi.'}]);self.assertTrue(calls[0]['local_only'])
