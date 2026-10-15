import unittest
from unittest.mock import Mock
from jarvis.browseros_controller import BrowserOSController
class Controller(unittest.TestCase):
 def setUp(self):
  self.client=Mock();self.client.connect.return_value={'tools':[{'name':'run'}]};self.client.open_blank.return_value={'url':'about:blank'};self.v=BrowserOSController(lambda _:self.client)
 def connect(self):self.v.connect('http://127.0.0.1:9200/mcp',True,True).join(2)
 def test_construction_no_network_and_consent(self):
  self.client.connect.assert_not_called()
  with self.assertRaises(ValueError):self.v.connect('http://127.0.0.1:9200/mcp',True,False)
 def test_exact_review_and_stop_revoke(self):
  self.connect();r=self.v.prepare('open-window')
  with self.assertRaises(ValueError):self.v.run({**r,'value':'different'},True)
  self.v.run(r,True).join(2);self.client.open_blank.assert_called_once_with(True)
  r=self.v.prepare('open','https://example.com');self.v.stop().join(2)
  with self.assertRaises(ValueError):self.v.run(r,True)
  self.client.stop.assert_called_once();self.assertEqual(self.v.snapshot()['state'],'off')
 def test_unsupported_effects(self):
  self.connect()
  for a in ['run','type','pay','download']:
   with self.assertRaises(ValueError):self.v.prepare(a,'x')
 def test_completion_event_only_after_verified_worker_and_stop_drops_it(self):
  import threading
  entered=threading.Event();release=threading.Event()
  def opened(*args):entered.set();release.wait(2);return {'url':'about:blank'}
  self.client.open_blank.side_effect=opened;self.connect();review=self.v.prepare('open-window');worker=self.v.run(review,True);self.assertTrue(entered.wait(1));self.assertEqual(self.v.drain_events(),[]);release.set();worker.join(2);events=self.v.drain_events();self.assertEqual(events[0]['kind'],'browser-tab-ready');self.assertTrue(events[0]['verified']);self.assertEqual(self.v.drain_events(),[])
  self.client.open_blank.side_effect=RuntimeError('failed');worker=self.v.run(self.v.prepare('open-window'),True);worker.join(2);self.assertEqual(self.v.drain_events()[0]['kind'],'browser-failed');self.v.stop().join(2);self.assertEqual(self.v.drain_events(),[])
 def test_start_is_immediate_fixed_blank_no_review_and_cannot_duplicate(self):
  with self.assertRaises(ValueError):self.v.start()
  self.connect();self.v.start().join(2);self.client.open_blank.assert_called_once_with(True);self.assertIsNone(self.v.pending);self.assertEqual(self.v.url,'about:blank')
  with self.assertRaises(ValueError):self.v.start()
  self.assertEqual(self.v.drain_events()[0]['kind'],'browser-tab-ready')
 def test_exact_typed_destination_runs_without_second_json_card(self):
  self.connect();self.v.start().join(2);self.client.navigate.return_value={'url':'https://example.com'};self.v.navigate('https://example.com').join(2);self.client.navigate.assert_called_once_with('https://example.com',True);self.assertIsNone(self.v.pending)
  for url in ['file:///tmp/private','javascript:alert(1)','http://example.com','https://127.0.0.1/']:
   with self.assertRaises(ValueError):self.v.navigate(url)
