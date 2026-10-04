import unittest,socket
from unittest.mock import Mock,patch
from jarvis.browser_control import BrowserSession
class NetworkScope(unittest.TestCase):
 def route(self,url,method='GET'):
  r=Mock();r.request.url=url;r.request.method=method;return r
 def test_private_dns_and_post_rejected(self):
  r=self.route('https://example.com')
  with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]):BrowserSession.route(r)
  r.abort.assert_called_once();r.continue_.assert_not_called()
  r=self.route('https://example.com','POST')
  with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('93.184.216.34',443))]):BrowserSession.route(r)
  r.abort.assert_called_once()
 def test_public_read_allowed(self):
  r=self.route('https://example.com')
  with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('93.184.216.34',443))]):BrowserSession.route(r)
  r.continue_.assert_called_once()
 def test_stopped_session_refuses_new_work(self):
  import threading,queue
  s=BrowserSession.__new__(BrowserSession);s.cancel=threading.Event();s.cancel.set();s.jobs=queue.Queue();s.lock=threading.RLock();s.state={}
  with self.assertRaises(ValueError):s.submit('open','https://example.com',True)
  self.assertTrue(s.jobs.empty())
