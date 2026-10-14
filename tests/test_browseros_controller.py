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
