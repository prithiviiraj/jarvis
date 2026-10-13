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

class RuntimeReviewFeedback(unittest.TestCase):
 def test_runtime_uses_mic_transcript_and_speaks_exact_action_feedback(self):
  from jarvis.runtime import VoiceRuntime
  from unittest.mock import Mock
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.stt.transcribe.return_value='confirm focus';v.action_handler=Mock(return_value={'speech_feedback':'The exact reviewed action was submitted.'})
  try:
   v.enable(True);v.turn([0],v.generation,False,[]);v.action_handler.assert_called_once_with('confirm focus');v.router.ask.assert_not_called();v.speaker.speak.assert_called_once();self.assertEqual(v.speaker.speak.call_args.args[0],'The exact reviewed action was submitted.');self.assertEqual(v.history,[])
  finally:v.close()

class BrainReviewSpeechBoundary(unittest.TestCase):
 def test_brain_ack_before_close_and_stop_during_ack_never_submits(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from jarvis.runtime import VoiceRuntime
  from unittest.mock import Mock
  for stopped in (False,True):
   b=Bridge(WorkspaceVoice());v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.enable(True);b.voice.runtime=v
   p={'payload':{'model':'fixture'},'sha256':'fixture'};b.brain_switch=Mock();b.brain_switch.snapshot.return_value={'pending':p};order=[]
   b.brain_switch.apply.side_effect=lambda *a:order.append('apply')
   def speech(*a,**kw):
    order.append('speech')
    if stopped:b.voice.pause()
   v.speaker.speak.side_effect=speech
   try:
    b.execute({'command':'voice-review-bind','kind':'brain','reviewed':p});self.assertTrue(b.voice_action('confirm brain'));self.assertIsNone(b.voice.runtime);self.assertEqual(order,['speech']if stopped else['speech','apply']);self.assertIsNone(b.voice_review.snapshot())
    if not stopped:b.brain_switch.apply.assert_called_once_with(p,True)
    else:b.brain_switch.apply.assert_not_called()
   finally:b.close()

class CrossDomainAmbiguity(unittest.TestCase):
 def test_connector_plan_blocks_bind_and_late_confirm_without_any_effect(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock
  for attr in ('github_issue','notion_text','drive_text','sheets_write','google_mail','google_calendar','telegram_output'):
   for state in ('review','submitting','uncertain','blocked'):
    with self.subTest(service=attr,state=state):
     b=Bridge(WorkspaceVoice());service=getattr(b,attr)
     try:
      p=b.focus_session.prepare('Read chapter',25);b.execute({'command':'voice-review-bind','kind':'focus','reviewed':p})
      service.snapshot=Mock(return_value={'state':state,'plan':{'payload':{'recipient':'fixture'},'review_id':'exact'}})
      self.assertIn('speech_feedback',b.voice_action('confirm focus'));self.assertEqual(b.focus_session.state,'review');self.assertIsNone(b.voice_review.snapshot())
      with self.assertRaises(ValueError):b.execute({'command':'voice-review-bind','kind':'focus','reviewed':p})
     finally:b.close()
 def test_completed_connector_plan_does_not_block_unrelated_review(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock
  b=Bridge(WorkspaceVoice())
  try:
   b.github_issue.snapshot=Mock(return_value={'state':'completed','plan':{'payload':{'body':'old'}},'result':{'verified':True}})
   p=b.focus_session.prepare('Read chapter',25);b.execute({'command':'voice-review-bind','kind':'focus','reviewed':p});b.voice_action('confirm focus');self.assertEqual(b.focus_session.state,'running')
  finally:b.close()
 def test_model_start_download_and_phone_transport_pending_block(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock
  for attr in ('model_manager','managed_session','phone_transport','phone','news','calendar'):
   with self.subTest(service=attr):
    b=Bridge(WorkspaceVoice());service=getattr(b,attr)
    try:
     p=b.focus_session.prepare('Read chapter',25);service.snapshot=Mock(return_value={'pending':{'id':'different-permission'}})
     with self.assertRaises(ValueError):b.execute({'command':'voice-review-bind','kind':'focus','reviewed':p})
     self.assertEqual(b.focus_session.state,'review')
    finally:b.close()

class ExternalExactVoiceDomains(unittest.TestCase):
 def test_external_confirm_and_cancel_routes_exact_review_once_mocked_only(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock
  for kind,attr in [('github','github_issue'),('notion','notion_text'),('drive','drive_text'),('sheets','sheets_write'),('mail','google_mail'),('calendar','google_calendar'),('telegram','telegram_output')]:
   for action in ('confirm','cancel'):
    with self.subTest(kind=kind,action=action):
     b=Bridge(WorkspaceVoice());service=getattr(b,attr);p={'review_id':'fixture','sha256':'fixture','payload':{'kind':'fixture','format':'text','identity':'fixture','words':'exact'}}
     original_snapshot=service.snapshot;original_submit=service.submit;original_stop=service.stop
     try:
      service.snapshot=Mock(return_value={'state':'review','plan':p});service.submit=Mock();service.stop=Mock()
      b.execute({'command':'voice-review-bind','kind':kind,'reviewed':p});result=b.voice_action(action+' '+kind)
      self.assertIn('speech_feedback',result);self.assertIsNone(b.voice_review.snapshot())
      if action=='confirm':service.submit.assert_called_once_with(p,True);service.stop.assert_not_called()
      else:service.submit.assert_not_called();service.stop.assert_called_once()
      b.voice_action('confirm '+kind);self.assertLessEqual(service.submit.call_count,1)
     finally:service.snapshot=original_snapshot;service.submit=original_submit;service.stop=original_stop;b.close()
 def test_uncertain_and_changed_account_never_submit(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock
  for change in ('account','uncertain'):
   b=Bridge(WorkspaceVoice());service=b.google_mail;p={'review_id':'fixture','payload':{'account':'first@example.com','to':['recipient@example.com'],'body':'exact'}}
   original_snapshot=service.snapshot;original_submit=service.submit
   try:
    service.snapshot=Mock(return_value={'state':'review','plan':p});service.submit=Mock()
    b.execute({'command':'voice-review-bind','kind':'mail','reviewed':p})
    service.snapshot.return_value={'state':'uncertain','plan':p}if change=='uncertain'else{'state':'review','plan':{**p,'payload':{**p['payload'],'account':'other@example.com'}}}
    b.voice_action('confirm mail');service.submit.assert_not_called()
   finally:service.snapshot=original_snapshot;service.submit=original_submit;b.close()
 def test_telegram_audio_requires_exact_listening_review_not_spoken_yes(self):
  v=VoiceReview();p={'payload':{'format':'voice','audio':{'audio_sha256':'fixture'}}}
  with self.assertRaises(ValueError):v.bind('telegram',p,p)
  self.assertIsNone(v.snapshot())

class AdditionalPendingBoundaries(unittest.TestCase):
 def test_phone_handoff_delivery_and_calendar_draft_worker_block_unrelated_binding(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock
  for attr,row in [('phone',{'handoff':{'text':'private exact notes'}}),('phone_endpoints',{'pending':{'request_id':'fixture'}}),('calendar_telegram',{'busy':True})]:
   b=Bridge(WorkspaceVoice());service=getattr(b,attr);original=service.snapshot
   try:
    service.snapshot=Mock(return_value=row);p=b.focus_session.prepare('Read chapter',25)
    with self.assertRaises(ValueError):b.execute({'command':'voice-review-bind','kind':'focus','reviewed':p})
    self.assertEqual(b.focus_session.state,'review')
   finally:service.snapshot=original;b.close()

class UnresolvedNotConfirmable(unittest.TestCase):
 def test_placeholder_blocker_itself_cannot_bind(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock
  b=Bridge(WorkspaceVoice());original=b.google_mail.snapshot
  try:
   b.google_mail.snapshot=Mock(return_value={'state':'uncertain','plan':{'payload':{'body':'fixture'}}})
   p=b.pending_voice_reviews()['mail']
   with self.assertRaises(ValueError):b.execute({'command':'voice-review-bind','kind':'mail','reviewed':p})
   self.assertIsNone(b.voice_review.snapshot())
  finally:b.google_mail.snapshot=original;b.close()

class SourceVoiceReview(unittest.TestCase):
 def test_source_confirm_cancel_exact_once_without_live_model(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock
  for action in ('confirm','cancel'):
   b=Bridge(WorkspaceVoice());p={'payload':{'note':{'name':'fixture.md','text':'Exact quote','sha256':'fixture'},'question':'One question','model':'local-fixture'},'sha256':'fixture'}
   original_snapshot=b.source_answer.snapshot;original_start=b.source_answer.start;original_stop=b.source_answer.stop
   try:
    b.source_answer.snapshot=Mock(return_value={'pending':p});b.source_answer.start=Mock();b.source_answer.stop=Mock()
    b.execute({'command':'voice-review-bind','kind':'source','reviewed':p});b.voice_action(action+' source')
    if action=='confirm':b.source_answer.start.assert_called_once_with(None,p,True)
    else:b.source_answer.start.assert_not_called();b.source_answer.stop.assert_called_once()
    b.voice_action('confirm source');self.assertLessEqual(b.source_answer.start.call_count,1)
   finally:b.source_answer.snapshot=original_snapshot;b.source_answer.start=original_start;b.source_answer.stop=original_stop;b.close()
 def test_source_ack_then_stop_mic_and_stop_during_ack_never_submits(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock
  import threading
  for kind in ('source','model-start'):
   for stopped in (False,True):
    b=Bridge(WorkspaceVoice());p={'payload':{'note':{'name':'fixture.md','text':'Quote'},'question':'Question','model':'fixture'},'sha256':'fixture'};service=b.source_answer if kind=='source'else b.managed_session;original_snapshot=service.snapshot;original_start=service.start
    runtime=Mock();runtime.generation=1;runtime.cancel=threading.Event();runtime.valid.return_value=True;runtime.enabled=True;order=[]
    try:
     service.snapshot=Mock(return_value={'pending':p});service.start=Mock(side_effect=lambda*args:order.append('start'));b.voice.runtime=runtime
     def speech(*args,**kw):
      order.append('ack')
      if stopped:runtime.cancel.set()
     runtime.speaker.speak.side_effect=speech
     b.execute({'command':'voice-review-bind','kind':kind,'reviewed':p});b.voice_action('confirm '+kind)
     self.assertEqual(order,['ack']if stopped else['ack','start'])
     if not stopped:self.assertIsNone(b.voice.runtime);service.start.assert_called_once_with(*( (None,p,True)if kind=='source'else(p,True)))
     else:service.start.assert_not_called()
    finally:service.snapshot=original_snapshot;service.start=original_start;b.close()

class ModelVoiceReview(unittest.TestCase):
 def test_exact_model_download_start_confirm_cancel_no_live_assets(self):
  from jarvis.ui_bridge import Bridge
  from jarvis.workspace_voice import WorkspaceVoice
  from unittest.mock import Mock
  for kind,attr in [('model-download','model_manager'),('model-start','managed_session')]:
   for action in ('confirm','cancel'):
    b=Bridge(WorkspaceVoice());service=getattr(b,attr);p={'id':'fixture','destination':'fixture-only','files':[{'source':'https://example.com/fixture','sha256':'fixture'}],'scope':'Exact fixture'};original_snapshot=service.snapshot;original_start=service.start;original_stop=service.stop
    try:
     service.snapshot=Mock(return_value={'pending':p});service.start=Mock();service.stop=Mock()
     b.execute({'command':'voice-review-bind','kind':kind,'reviewed':p});b.voice_action(action+' '+kind)
     if action=='confirm':service.start.assert_called_once_with(p,True)
     else:service.start.assert_not_called();service.stop.assert_called_once()
     b.voice_action('confirm '+kind);self.assertLessEqual(service.start.call_count,1)
    finally:service.snapshot=original_snapshot;service.start=original_start;service.stop=original_stop;b.close()
