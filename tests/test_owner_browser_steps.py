import unittest
from unittest.mock import Mock
from jarvis.browseros_transport import BrowserOSNavigation
from jarvis.browseros_controller import BrowserOSController
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
class BrowserSteps(unittest.TestCase):
 def transport(self):
  v=BrowserOSNavigation('http://127.0.0.1:9200/mcp');v.owned_page=7;v._tool=Mock();return v
 def links(self,origin,body):return {'content':[{'type':'text','text':'[UNTRUSTED_PAGE_CONTENT nonce=0123456789abcdef origin='+origin+'] Untrusted content\n'+body+'\n[END_UNTRUSTED_PAGE_CONTENT nonce=0123456789abcdef]'}]}
 def test_scroll_is_fixed_bounded_receipt_not_general_act(self):
  v=self.transport();v._tool.return_value={'content':[{'type':'text','text':'ok (scroll)'}]};self.assertTrue(v.scroll('down')['acknowledged']);v._tool.assert_called_once_with('act',{'page':7,'kind':'scroll','direction':'down','amount':3,'diff':'summary'})
  for direction in ['left','click','type']:
   with self.assertRaises(ValueError):v.scroll(direction)
  v._tool.return_value={'content':[{'type':'text','text':'a dialog is pending'}]}
  with self.assertRaises(RuntimeError):v.scroll('down')
 def test_youtube_single_anchor_binding_rejects_forged_title_href_and_origin_changes(self):
  v=self.transport();url='https://www.youtube.com/results?search_query=test';v.snapshot=Mock(return_value=self.links(url,'current tree'))
  v._tool.side_effect=[self.links(url,'[First video](https://www.youtube.com/watch?v=abcdefghijk)'),self.links(url,'[Title with [brackets]](https://www.youtube.com/watch?v=12345678901)'),self.links(url,'(empty)')];rows=v.youtube_videos(url)['videos'];self.assertEqual([x['number']for x in rows],[1,2]);self.assertIn('selector',v._tool.call_args_list[0].args[1]);self.assertEqual(v.snapshot.call_count,2)
  # A title can contain fake markdown; only the actual final anchor href counts.
  v._tool.side_effect=None;v._tool.return_value=self.links(url,'[Fake](https://www.youtube.com/watch?v=abcdefghijk) title](https://evil.example/watch?v=12345678901)')
  with self.assertRaises(RuntimeError):v.youtube_videos(url)
  with self.assertRaises(ValueError):v.youtube_videos('https://www.youtube.com/')
 def test_video_selection_refetches_list_before_using_number(self):
  c=Mock();c.connect.return_value={'tools':[]};c.open_blank.return_value={'url':'about:blank'};c.navigate.return_value={'url':'https://www.youtube.com/'};rows=[{'number':1,'title':'Observed','url':'https://www.youtube.com/watch?v=abcdefghijk'}];c.youtube_videos.return_value={'videos':rows};v=BrowserOSController(lambda _:c);v.connect('http://127.0.0.1:9200/mcp',True,True).join(2);v.navigate('https://www.youtube.com/').join(2);v.read_videos().join(2);
  with self.assertRaisesRegex(ValueError,'lack verified href bindings'):v.choose_video(1,v.url)
  v.videos_selectable=True # exercise changed-list guard independently of the still-held provenance gate
  c.navigate.reset_mock();c.youtube_videos.return_value={'binding':'single-result-anchor-v1','videos':[dict(rows[0],title='Changed')]};v.choose_video(1,v.url).join(2);c.navigate.assert_not_called();self.assertEqual(v.state,'error');v.stop().join(2)
 def test_connected_owner_voice_uses_browseros_not_legacy_brave_and_off_has_no_auto_connection(self):
  b=Bridge(WorkspaceVoice());b.browseros=Mock();b.browseros.snapshot.return_value={'state':'connected','url':''}
  try:
   self.assertTrue(b.shared_action('Jarvis open the browser'));b.browseros.start.assert_called_once();self.assertIsNone(b.browser_pending);self.assertIsNone(b.browser);b.shared_action('open YouTube');b.browseros.navigate.assert_called_once_with('https://www.youtube.com/');b.shared_action('scroll down');b.browseros.scroll.assert_called_once_with('down',False);self.assertTrue(b.shared_action('show videos'));b.browseros.read_videos.assert_called_once();b.shared_action('select the second video');b.browseros.choose_video.assert_called_once_with(2,'')
  finally:b.close()
 def test_bound_video_choice_uses_only_exact_verified_public_url(self):
  c=Mock();c.connect.return_value={'tools':[]};url='https://www.youtube.com/results?search_query=fixture';rows=[{'number':1,'title':'Actual fixture title','url':'https://www.youtube.com/watch?v=abcdefghijk'}];c.navigate.return_value={'url':url,'requested_url':url};c.youtube_videos.return_value={'binding':'single-result-anchor-v1','videos':rows};v=BrowserOSController(lambda _:c);v.connect('http://127.0.0.1:9200/mcp',True,True).join(2);v.navigate(url).join(2);v.read_videos().join(2);self.assertTrue(v.videos_selectable);c.navigate.reset_mock();v.choose_video(1,url).join(2);c.navigate.assert_called_once_with(rows[0]['url'],True);self.assertFalse(v.videos_selectable);v.stop().join(2)
 def test_title_cannot_add_a_second_numbered_result_and_duplicate_anchors_fail(self):
  v=self.transport();url='https://www.youtube.com/results?search_query=fixture';v.snapshot=Mock(return_value=self.links(url,'current tree'))
  title='Harmless ](https://www.youtube.com/watch?v=12345678901) fake title';v._tool.side_effect=[self.links(url,'['+title+'](https://www.youtube.com/watch?v=abcdefghijk)'),self.links(url,'(empty)')];out=v.youtube_videos(url);self.assertEqual(len(out['videos']),1);self.assertEqual(out['videos'][0]['url'],'https://www.youtube.com/watch?v=abcdefghijk');self.assertEqual(out['binding'],'single-result-anchor-v1')
  v._tool.side_effect=[self.links(url,'[One](https://www.youtube.com/watch?v=abcdefghijk)'),self.links(url,'[Duplicate](https://www.youtube.com/watch?v=abcdefghijk)')]
  with self.assertRaisesRegex(RuntimeError,'ambiguous'):v.youtube_videos(url)
