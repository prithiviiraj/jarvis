import unittest
from jarvis.voice_review import VoiceReview
class Review(unittest.TestCase):
 def test_exact_show_confirm_cancel_once(self):
  p={'command':'open','value':'https://example.com/'};v=VoiceReview();v.bind('browser',p,p);self.assertEqual(v.choice('Jarvis confirm browser',p)['payload'],p)
  with self.assertRaises(ValueError):v.choice('confirm',p)
  v.bind('browser',p,p);self.assertEqual(v.choice('cancel',p)['choice'],'cancel')
 def test_stale_expiry_multiple_wrong_kind_no_approval(self):
  p={'command':'open-window','value':''};now=[1.];v=VoiceReview(lambda:now[0])
  for changed,multiple,text in [({'command':'open','value':'https://example.com'},False,'confirm'),(p,True,'confirm'),(p,False,'confirm app')]:
   v.bind('browser',p,p)
   with self.assertRaises(ValueError):v.choice(text,changed,multiple)
  v.bind('browser',p,p);now[0]=62
  with self.assertRaises(ValueError):v.choice('confirm',p)
 def test_fuzzy_negation_quotes_do_not_approve(self):
  p={'command':'open-window','value':''};v=VoiceReview();v.bind('browser',p,p)
  for t in ('yes','okay','do not confirm','you said confirm','confirm then pay','cancelled','please confirm everything'):self.assertIsNone(v.choice(t,p))

class BridgeReview(unittest.TestCase):
 def test_spoken_confirm_routes_exact_current_payload_and_consumes(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock
  b=Bridge(WorkspaceVoice());b.browser_enabled=True;b.browser=Mock();b.browser.cancel.is_set.return_value=False
  try:
   p={'command':'open-window','value':''};b.browser_pending=p;b.execute({'command':'voice-review-bind','kind':'browser','reviewed':p});self.assertIsNotNone(b.voice_review.snapshot());self.assertTrue(b.voice_action('confirm browser'));b.browser.submit.assert_called_once_with(command='open-window',value='',confirmed=True);self.assertIsNone(b.browser_pending);self.assertIsNone(b.voice_review.snapshot())
  finally:b.close()
 def test_changed_payload_never_submits(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock
  b=Bridge(WorkspaceVoice());b.browser_enabled=True;b.browser=Mock();b.browser.cancel.is_set.return_value=False
  try:
   p={'command':'open-window','value':''};b.browser_pending=p;b.execute({'command':'voice-review-bind','kind':'browser','reviewed':p});b.browser_pending={'command':'open','value':'https://example.com/'};self.assertTrue(b.voice_action('confirm'));b.browser.submit.assert_not_called();self.assertIsNone(b.voice_review.snapshot())
  finally:b.close()

class DisplayExpiry(unittest.TestCase):
 def test_repeated_display_does_not_renew(self):
  p={'command':'open-window','value':''};now=[1.];v=VoiceReview(lambda:now[0]);first=v.bind('browser',p,p);now[0]=30.;again=v.bind('browser',p,p);self.assertEqual(first['id'],again['id']);now[0]=62.;self.assertIsNone(v.bind('browser',p,p))

class LocalReviewDomains(unittest.TestCase):
 def test_focus_exact_once_and_other_pending_blocks(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice())
  try:
   p=b.focus_session.prepare('Read chapter',25);b.execute({'command':'voice-review-bind','kind':'focus','reviewed':p});result=b.voice_action('confirm focus');self.assertIn('speech_feedback',result);self.assertEqual(b.focus_session.state,'running');b.focus_session.stop()
   p=b.focus_session.prepare('Read chapter',25);b.browser_pending={'command':'open-window','value':''}
   with self.assertRaises(ValueError):b.execute({'command':'voice-review-bind','kind':'focus','reviewed':p})
   self.assertEqual(b.focus_session.state,'review')
  finally:b.close()
 def test_cancel_invoice_is_not_issue_or_open(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  b=Bridge(WorkspaceVoice())
  try:
   b.invoice.pending={'review_id':'fixture','document':{'state':'draft'},'sha256':'fixture'};p=b.invoice.snapshot()['pending'];b.execute({'command':'voice-review-bind','kind':'invoice','reviewed':p});self.assertIn('speech_feedback',b.voice_action('cancel invoice'));self.assertIsNone(b.invoice.pending);self.assertIsNone(b.invoice.result)
  finally:b.close()
