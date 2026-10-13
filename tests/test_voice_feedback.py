import unittest
from unittest.mock import Mock
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
from jarvis.runtime import VoiceRuntime
from jarvis.voice_meter import VoiceMeter
class Feedback(unittest.TestCase):
 def test_prefix_only_stream_then_real_reply_not_false_error(self):
  b=Bridge(WorkspaceVoice());v=VoiceRuntime(Mock(),Mock(),Mock(),Mock(),b.voice.notify);v.mic=Mock();v.stt.transcribe.return_value='hi';v.streaming=True
  v.router.stream.return_value=iter([{'text':'[JARVIS]','provider':'local','model':'fixture'},{'text':' Hello master.','provider':'local','model':'fixture'}])
  try:
   v.enable(True);v.turn([0],v.generation,False,[]);s=b.execute({'command':'status'});self.assertEqual(s['error'],'');self.assertEqual(s['messages'][-1]['text'],'Hello master.');self.assertEqual(s['voice_turn_diagnostic']['result'],'completed');self.assertEqual(s['voice_turn_diagnostic']['model'],'fixture')
  finally:v.close();b.close()
 def test_true_final_empty_and_stale_partial(self):
  b=Bridge(WorkspaceVoice())
  try:
   b.voice.notify('turn-start',{'turn_id':'new'});b.voice.notify('answer',{'text':'old','turn_id':'old','partial':True});b.voice.notify('answer',{'text':'','turn_id':'new','partial':True});s=b.execute({'command':'status'});self.assertEqual(s['error'],'');self.assertEqual(s['messages'],[])
   b.voice.notify('answer',{'text':'','turn_id':'new','partial':False});s=b.execute({'command':'status'});self.assertIn('empty',s['error'])
  finally:b.close()
 def test_actual_empty_runtime_failure_preserved(self):
  events=[];v=VoiceRuntime(Mock(),Mock(),Mock(),Mock(),lambda *e:events.append(e));v.mic=Mock();v.stt.transcribe.return_value='hi';v.streaming=True;v.router.stream.return_value=iter([{'text':'[JARVIS]','provider':'local','model':'fixture'}])
  try:
   v.enable(True);v.turn([0],v.generation,False,[]);self.assertTrue(any(k=='turn-result'and d['category']=='empty-final'for k,d in events));self.assertTrue(any(k=='error'and 'failed' in d for k,d in events));self.assertEqual(v.history,[])
  finally:v.close()
 def test_level_silence_loud_stale_clear(self):
  now=[1.];m=VoiceMeter(lambda:now[0]);m.feed([0]*512);self.assertEqual(m.snapshot()['level'],0);m.feed([.25]*512);self.assertAlmostEqual(m.snapshot()['level'],.25);self.assertAlmostEqual(m.snapshot()['peak'],.25);now[0]+=1;self.assertEqual(m.snapshot()['level'],0);m.feed([.5]);m.clear();self.assertEqual(m.snapshot()['level'],0);m.feed([float('nan')]);self.assertEqual(m.snapshot()['level'],0)

class Honesty(unittest.TestCase):
 def runtime(self,text):
  v=VoiceRuntime(Mock(),Mock(),Mock(),Mock());v.mic=Mock();v.stt.transcribe.return_value=text;v.router.ask.return_value={'text':'useful answer'};v.enable(True);return v
 def test_vision_not_ready_spoken_without_model_or_image(self):
  from jarvis.vision import LocalVision
  v=self.runtime('Jarvis what do you see?');v.vision=LocalVision(lambda:None)
  try:v.turn([0],v.generation,False,[]);v.router.ask.assert_not_called();self.assertIn('cannot see',v.speaker.speak.call_args.args[0])
  finally:v.close()
 def test_exact_model_echo_not_spoken_or_committed(self):
  for streaming in (False,True):
   v=self.runtime('What is two plus two?');v.streaming=streaming;v.router.ask.return_value={'text':'What is two plus two?'};v.router.stream.return_value=iter([{'text':'What is two plus two?','provider':'local','model':'fixture'}])
   try:v.turn([0],v.generation,False,[]);self.assertEqual(v.history,[]);self.assertNotIn('What is two plus two?',str(v.speaker.speak.call_args_list));self.assertIn('repeated your question',str(v.speaker.speak.call_args_list))
   finally:v.close()
 def test_useful_quote_not_rejected(self):
  from jarvis.voice_feedback import echo_reply,safe_route
  self.assertFalse(echo_reply('You asked what is two plus two. The answer is four.','what is two plus two'));self.assertEqual(safe_route({'model':'sk-secret with spaces','provider':'local','slot':'slot1','key':'private'}),{'provider':'local','slot':'slot1'})

class CurrentCaption(unittest.TestCase):
 def test_next_turn_and_stop_never_show_prior_chat_as_current_voice(self):
  b=Bridge(WorkspaceVoice())
  try:
   b.messages=[{'name':'You','text':'old private text'},{'name':'JARVIS','text':'old answer'}];b.voice.notify('turn-start',{'turn_id':'a'});b.voice.notify('transcript','new question');b.voice.notify('answer',{'turn_id':'a','partial':True,'text':'new answer','profile':'LYRA'});s=b.execute({'command':'status'});self.assertEqual(s['voice_current_caption'],{'you':'new question','name':'LYRA','text':'new answer'})
   b.voice.notify('turn-start',{'turn_id':'b'});s=b.execute({'command':'status'});self.assertEqual(s['voice_current_caption']['text'],'');b.execute({'command':'voice-off'});b.voice.notify('answer',{'turn_id':'a','partial':False,'text':'late old reply'});s=b.execute({'command':'status'});self.assertEqual(s['voice_current_caption']['you'],'');self.assertNotIn('late old reply',str(s['messages']))
  finally:b.close()
 def test_route_secret_prefixes_not_exposed(self):
  from jarvis.voice_feedback import safe_route
  for secret in ('sk-private','gsk_abcdefgh','AIzaabcdef','https://x@y'):
   self.assertEqual(safe_route({'model':secret}),{})
