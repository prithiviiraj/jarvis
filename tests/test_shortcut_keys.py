import unittest,threading
from jarvis.shortcut_keys import ShortcutEdges,ModifierMonitor
class Shortcuts(unittest.TestCase):
 def test_talk_delay_release_and_rearm(self):
  t=[0.];e=ShortcutEdges(lambda:t[0]);self.assertEqual(e.feed(True,True,False,False),[]);t[0]=.2;self.assertEqual(e.feed(True,True,False,False),['talk-start']);self.assertEqual(e.feed(True,True,False,False),[]);self.assertEqual(e.feed(False,False,False,False),['talk-stop'])
 def test_interrupt_edge_no_wait_and_conflicts(self):
  e=ShortcutEdges();self.assertEqual(e.feed(False,True,True,False),['interrupt']);self.assertEqual(e.feed(False,True,True,False),[]);e.feed(False,False,False,False);self.assertEqual(e.feed(True,True,True,False),[]);self.assertEqual(e.feed(False,True,True,True),[])
 def test_monitor_actual_loop_transport_only_mocked(self):
  entered=threading.Event();events=[]
  def notify(event):events.append(event);entered.set()
  m=ModifierMonitor(notify,lambda:(False,True,True,False));self.assertIsNone(m.worker)
  with self.assertRaises(ValueError):m.start()
  m.start(True);self.assertTrue(entered.wait(1));m.stop();m.worker.join(1);self.assertEqual(events,['interrupt']);self.assertFalse(m.enabled)
