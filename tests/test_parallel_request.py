import unittest,threading
from unittest.mock import Mock
from jarvis.parallel_request import split
from jarvis.ui_bridge import Bridge
from jarvis.runtime import VoiceRuntime
class Parallel(unittest.TestCase):
 def test_exact_bounded_split(self):
  p=split('Jarvis open the browser and tell me what Iron Man is');self.assertEqual(p['proposal']['command'],'open-window');self.assertEqual(p['question'],'what Iron Man is')
  self.assertEqual(split('browser search for Iron Man while explain his history')['proposal']['command'],'search')
 def test_not_general_chain_or_model_action(self):
  for t in ('open browser then search Iron Man','do not open browser and tell me why','open browser and delete files','how do I open browser and tell me why','kill Notepad and tell me why','open browser and search Iron Man'):
   self.assertIsNone(split(t),t)
 def test_bridge_submits_before_independent_question_without_wait(self):
  b=Bridge();b.laya_active=True;b.browser_enabled=True;b.browser=Mock();b.browser.cancel.is_set.return_value=False;b.browser.snapshot.return_value={'state':'working'};b.voice.send_text=Mock()
  try:
   order=[];b.browser.submit.side_effect=lambda **k:order.append('command');b.voice.send_text.side_effect=lambda *a,**k:order.append('answer')
   b.execute({'command':'chat','text':'open browser and tell me who Iron Man is'})
   self.assertEqual(order,['command','answer']);b.browser.submit.assert_called_once_with(command='open-window',value='',confirmed=True);b.voice.send_text.assert_called_once_with('who Iron Man is',auto_pick=True)
  finally:b.close()
 def test_off_still_answers_without_browser(self):
  b=Bridge();b.voice.send_text=Mock()
  try:
   b.execute({'command':'chat','text':'open browser and tell me who Iron Man is'});self.assertIsNone(b.browser);b.voice.send_text.assert_called_once();self.assertEqual(b.reo_log[-1]['state'],'blocked')
  finally:b.close()
 def test_actual_voice_turn_dispatch_does_not_wait_for_browser_ready(self):
  b=Bridge();b.laya_active=True;b.browser_enabled=True;b.browser=Mock();b.browser.cancel.is_set.return_value=False;b.browser.snapshot.return_value={'state':'working'}
  r=VoiceRuntime.__new__(VoiceRuntime);r.lock=threading.RLock();r.enabled=True;r.generation=1;r.cancel=threading.Event();r.busy=True;r.stt=Mock();r.stt.transcribe.return_value='open browser and tell me who Iron Man is';r.speaker=Mock();r.speaker.generation=0;r.notify=Mock();r.action_handler=b.voice_action;r.mic=Mock();r.router=Mock();r.router.ask.return_value={'text':'Independent answer'};r.streaming=False;r.reasoning_off=False;r.persona='JARVIS';r.vision=None;r.shared_context=None;r.record_turn=None
  try:
   order=[];b.browser.submit.side_effect=lambda **k:order.append('command');r.router.ask.side_effect=lambda *a,**k:(order.append('answer')or {'text':'Independent answer'})
   r.turn([],1,False,[]);self.assertEqual(order,['command','answer']);self.assertEqual(r.router.ask.call_args.args[0][-1]['content'],'who Iron Man is');r.speaker.speak.assert_called_once();r.mic.resume.assert_called_once()
  finally:b.close()
