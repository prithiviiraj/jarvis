import unittest,tempfile,pathlib,datetime
from unittest.mock import Mock,patch
from zoneinfo import ZoneInfo
from jarvis.browser_visits import BrowserVisits
from jarvis.browseros_controller import BrowserOSController
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class BrowserVisitsTest(unittest.TestCase):
 def test_saved_own_destinations_only_survive_restart_and_deduplicate(self):
  with tempfile.TemporaryDirectory()as d:
   path=pathlib.Path(d)/'visits.json';v=BrowserVisits(path,clock=lambda:1000);self.assertFalse(path.exists());v.record('about:blank');self.assertFalse(path.exists());v.record('https://example.com/');v.record('https://example.org/');v.record('https://example.com/');self.assertEqual([r['url']for r in BrowserVisits(path).list()],['https://example.com/','https://example.org/'])
   with self.assertRaises(ValueError):v.record('file:///private')
 def test_yesterday_is_computed_in_india_time_not_guessed_weekday(self):
  zone=ZoneInfo('Asia/Kolkata');now=datetime.datetime(2026,10,15,14,0,tzinfo=zone).timestamp();clock=[now-86400];v=BrowserVisits(clock=lambda:clock[0]);v.record('https://example.com/yesterday');clock[0]=now;v.record('https://example.com/today');self.assertEqual([r['url']for r in v.list(True)],['https://example.com/yesterday'])
 def test_invalid_existing_history_is_preserved_not_overwritten(self):
  with tempfile.TemporaryDirectory()as d:
   path=pathlib.Path(d)/'visits.json';path.write_text('broken');v=BrowserVisits(path);self.assertEqual(v.list(),[]);v.record('https://example.com');self.assertEqual(path.read_text(),'broken');self.assertTrue(v.error)
 def test_failed_navigation_never_records_requested_url(self):
  c=Mock();c.connect.return_value={'tools':[]};c.open_blank.return_value={'url':'about:blank'};c.navigate.side_effect=RuntimeError('failed');v=BrowserOSController(lambda _:c);v.connect('http://127.0.0.1:9200/mcp',True,True).join(2);v.navigate('https://example.com').join(2);self.assertEqual(v.visits.list(),[]);v.stop().join(2)
 def test_history_request_stays_local_and_is_visible_on_home(self):
  b=Bridge(WorkspaceVoice());b.browseros.visits.record('https://example.com/own')
  try:
   with patch.object(b.voice,'send_text')as chat:b.shared_action('show recent pages');self.assertTrue(b.browseros.snapshot()['history_visible']);chat.assert_not_called();self.assertNotIn('https://example.com/own',b.interface_context('browser'))
  finally:b.close()
