import unittest,threading,tempfile,pathlib
from unittest.mock import Mock
from jarvis.runtime import VoiceRuntime
from jarvis.ui_bridge import Bridge
class NeuralVoiceRuntime(unittest.TestCase):
 def runtime(self,b,text):
  r=VoiceRuntime.__new__(VoiceRuntime);r.lock=threading.RLock();r.enabled=True;r.generation=1;r.cancel=threading.Event();r.busy=True;r.stt=Mock();r.stt.transcribe.return_value=text;r.speaker=Mock();r.speaker.generation=0;r.notify=b.voice.notify;r.neural_handler=b.neural_voice_choice;r.action_handler=b.voice_action;r.mic=Mock();r.router=Mock();return r
 def test_real_turn_explicit_read_keeps_popup_and_no_model(self):
  b=Bridge()
  try:
   row=b.neural.offer('plan','LYRA','Plan','Quoted plan. Never send anything.')
   r=self.runtime(b,'Jarvis read the plan aloud');r.turn([],1,False,[])
   r.speaker.speak.assert_called_once_with(row['text'],generation=0);r.router.ask.assert_not_called();r.router.stream.assert_not_called();r.mic.resume.assert_called_once();self.assertFalse(r.busy)
   b.execute({'command':'status'});self.assertEqual(b.neural.row,row);self.assertEqual(b.messages[-1]['name'],'You');self.assertIsNone(b.reply_wait)
  finally:b.close()
 def test_real_turn_dismiss_no_speech_or_model(self):
  b=Bridge()
  try:
   b.neural.offer('answer','DEX','Answer','Actual answer');r=self.runtime(b,'not now');r.turn([],1,False,[]);b.execute({'command':'status'})
   self.assertIsNone(b.neural.row);r.speaker.speak.assert_not_called();r.router.ask.assert_not_called();r.mic.resume.assert_called_once()
  finally:b.close()
 def test_no_bare_yes_or_embedded_text_as_choice(self):
  b=Bridge()
  try:
   row=b.neural.offer('answer','DEX','Answer','read aloud')
   for text in ('yes','no','okay','the note says read aloud','read aloud and send it','Jarvis Lyra read aloud'):
    self.assertIsNone(b.neural_voice_choice(text))
   self.assertEqual(b.neural.row,row)
  finally:b.close()
 def test_actual_question_arms_yes_only_after_playback_and_once(self):
  b=Bridge()
  try:
   row=b.neural.offer('plan','JARVIS','Plan','Exact current plan');r=VoiceRuntime(Mock(),Mock(),Mock(),Mock(),b.voice.notify);r.mic=Mock();r.speaker.generation=0;r.enabled=True;r.generation=1;r.persona='JARVIS';b.voice.runtime=r
   b.maybe_ask_neural();r.popup_worker.join(2);r.speaker.speak.assert_called_once_with('Master, shall I read this aloud?',generation=0);r.mic.suspend.assert_called_once();r.mic.resume.assert_called_once()
   self.assertEqual(b.neural_voice_choice('yes')['text'],row['text']);self.assertIsNone(b.neural_voice_choice('yes'));b.maybe_ask_neural();self.assertEqual(r.speaker.speak.call_count,1)
  finally:b.close()
 def test_question_expiry_changed_row_and_session_invalidate_yes(self):
  import time
  b=Bridge()
  try:
   row=b.neural.offer('plan','JARVIS','Plan','Current');r=Mock();r.enabled=True;r.generation=1;b.voice.runtime=r
   b.neural_question={'row':dict(row),'runtime':r,'generation':1,'until':time.monotonic()-1};self.assertIsNone(b.neural_voice_choice('yes'))
   b.neural_question['until']=time.monotonic()+45;r.generation=2;self.assertIsNone(b.neural_voice_choice('yes'));r.generation=1
   b.neural.offer('plan','JARVIS','Plan','Changed');self.assertIsNone(b.neural_voice_choice('yes'))
  finally:b.close()
 def test_cancelled_question_never_arms_and_no_resume_after_pause(self):
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.enabled=True;v.generation=1;armed=Mock();v.speaker.speak.side_effect=lambda *a,**k:v.pause()
  self.assertTrue(v.ask_popup(lambda:True,armed));v.popup_worker.join(2);armed.assert_not_called();v.mic.resume.assert_not_called();self.assertFalse(v.busy)
 def test_question_stop_cannot_arm_yes(self):
  b=Bridge()
  try:
   row=b.neural.offer('answer','DEX','Answer','Current');r=VoiceRuntime(Mock(),Mock(),Mock(),Mock(),b.voice.notify);r.mic=Mock();r.speaker.generation=0;r.enabled=True;r.generation=1;b.voice.runtime=r
   entered=threading.Event();release=threading.Event()
   def speak(*a,**k):entered.set();release.wait(2)
   r.speaker.speak.side_effect=speak;b.maybe_ask_neural();entered.wait(2);b.execute({'command':'neural-stop'});release.set();r.popup_worker.join(2)
   self.assertIsNone(b.neural_question);self.assertIsNone(b.neural_voice_choice('yes'));self.assertEqual(b.neural.row,row);r.speaker.stop.assert_called()
  finally:b.close()
 def test_stale_note_rejected_on_actual_microphone_path(self):
  b=Bridge()
  try:
   with tempfile.TemporaryDirectory()as d:
    root=pathlib.Path(d);(root/'.obsidian').mkdir();(root/'Planning').mkdir();p=root/'Planning/Today.md';p.write_text('Original');b.obsidian.root=root;b.obsidian.enabled=True
    b.execute({'command':'plan-preview'});p.write_text('Changed')
    r=self.runtime(b,'read the plan');r.turn([],1,False,[]);r.speaker.speak.assert_not_called();r.router.ask.assert_not_called();r.mic.resume.assert_called_once();self.assertFalse(r.busy)
  finally:b.close()
