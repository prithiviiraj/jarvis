import unittest
from jarvis.speech_text import speech_text
class SpeechTextTests(unittest.TestCase):
 def test_prefix_emoji_format(self):self.assertEqual(speech_text('[NOVA] **Hello** 👋, [site](https://example.com)!'),'Hello , site!')
 def test_thinking_hidden(self):self.assertEqual(speech_text('<think>secret</think>[DEX] Ready ✅'),'Ready')
 def test_code_not_read(self):self.assertEqual(speech_text('Use this: ```python\nx=1\n```'),'Use this: Code is shown in the chat.')
 def test_speaker_receives_cleaned_only(self):
  from jarvis.experimental.kokoro_speaker import KokoroSpeaker
  from unittest.mock import Mock
  synth=Mock();synth.synthesize.return_value=([0.0],24000);output=Mock();s=KokoroSpeaker(synth,lambda sr:output);s.speak('[NOVA] **Hi** 👋');synth.synthesize.assert_called_once_with('Hi')
 def test_profile_selection_distinct(self):
  from jarvis.experimental.kokoro_speaker import KokoroSpeaker
  from unittest.mock import Mock
  a=Mock();b=Mock();s=KokoroSpeaker(a);s.profiles={'JARVIS':a,'NOVA':b};s.select_profile('NOVA');self.assertIs(s.synth,b);self.assertEqual(s.profile,'NOVA')
 def test_voice_direct_address_actual_actor(self):
  from jarvis.runtime import VoiceRuntime
  from unittest.mock import Mock
  stt=Mock();stt.transcribe.return_value='Hey NOVA are you there?';router=Mock();router.ask.return_value={'text':'Ready'};speaker=Mock();v=VoiceRuntime(Mock(),stt,router,speaker);v.mic=Mock();v.enable(True);v.turn([],v.generation,False,[]);speaker.select_profile.assert_called_once_with('NOVA');self.assertEqual(v.persona,'NOVA');self.assertIn('You are NOVA',router.ask.call_args.args[0][0]['content'])
 def test_same_runtime_two_distinct_personas(self):
  from jarvis.runtime import VoiceRuntime
  from unittest.mock import Mock
  stt=Mock();stt.transcribe.side_effect=['Hi NOVA','Hi DEX'];router=Mock();router.ask.return_value={'text':'Ready'};speaker=Mock();v=VoiceRuntime(Mock(),stt,router,speaker);v.mic=Mock();v.enable(True)
  for i in range(2):v.turn([],v.generation,False,list(v.history))
  self.assertEqual([x.args[0]for x in speaker.select_profile.call_args_list],['NOVA','DEX']);self.assertEqual(v.mic.start.call_count,1)
 def test_short_reply_prompt(self):
  from jarvis.personas import prompt
  self.assertIn('one or two short',prompt('NOVA'))
 def test_proactive_status_gates(self):
  from jarvis.proactive import ProactiveJudge
  from unittest.mock import Mock
  context=Mock();context.seq=0;context.apps=False;context.snapshot.return_value={'camera':'off'};j=ProactiveJudge(context,Mock(),clock=lambda:10000,hour=lambda:14)
  self.assertIn('Off',j.waiting_reason());j.enable(True);self.assertIn('microphone',j.waiting_reason(True));self.assertIn('allowed',j.waiting_reason());context.apps=True;self.assertIn('new presence',j.waiting_reason());j.gaming=True;self.assertIn('gaming',j.waiting_reason());j.gaming=False;j.requests.extend([0]*12);self.assertNotIn('Hourly',j.waiting_reason());j.requests.extend([9999]*12);self.assertIn('Hourly',j.waiting_reason())
