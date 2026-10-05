import unittest,queue,tempfile
from pathlib import Path
from unittest.mock import Mock
from jarvis.vault_voice import parse_voice
from jarvis.ui_bridge import Bridge
from jarvis.brain_settings import BrainSettings
class VaultVoice(unittest.TestCase):
 def bridge(self):
  v=Mock();v.runtime=None;v.busy=False;v.events.get_nowait.side_effect=queue.Empty;v.name='JARVIS';v.reply_actor='JARVIS';v.tts_engine='kokoro'
  return Bridge(voice=v,brains=BrainSettings(store=Mock()))
 def test_explicit_and_exact(self):
  self.assertEqual(parse_voice('Jarvis obsidian search வணக்கம்'),{'command':'vault-search','query':'வணக்கம்'})
  self.assertEqual(parse_voice('vault read Work/Note.md'),{'command':'vault-read','note_name':'Work/Note.md'})
  for s in ['search my notes','read Work/Note.md','my vault read x.md']:self.assertIsNone(parse_voice(s))
 def test_disconnected_consumes_no_chat_fallback(self):
  b=self.bridge();self.assertTrue(b.voice_action('vault read secret.md'));b.voice.send_text.assert_not_called();b.voice.notify.assert_called_with('error','Local vault command failed. Check the connected vault and exact Markdown note path in Settings > Memory.')
 def test_connected_read_search_no_write_or_chat(self):
  b=self.bridge()
  with tempfile.TemporaryDirectory()as t:
   p=Path(t);(p/'.obsidian').mkdir();(p/'n.md').write_text('local private வணக்கம்',encoding='utf-8')
   b.execute({'command':'vault-connect','consent':True,'vault_folder':t})
   self.assertTrue(b.voice_action('obsidian search வணக்கம்'));self.assertEqual(b.vault_results[0]['name'],'n.md')
   self.assertTrue(b.voice_action('vault read n.md'));self.assertEqual(b.vault_note,'local private வணக்கம்')
   self.assertTrue(b.voice_action('vault read ../other.md'));b.voice.send_text.assert_not_called();self.assertEqual((p/'n.md').read_text(encoding='utf-8'),'local private வணக்கம்')
 def test_long_query_consumed_locally(self):
  b=self.bridge();self.assertTrue(b.voice_action('obsidian search '+'x'*101));b.voice.send_text.assert_not_called()

 def test_typed_preview_exact_same_parser(self):
  b=self.bridge()
  with self.assertRaises(ValueError):b.execute({'command':'vault-preview','text':'obsidian read x.md'})
  with self.assertRaises(ValueError):b.execute({'command':'vault-preview','text':'obsidian create x.md'})
 def test_runtime_stays_local(self):
  import threading
  from jarvis.runtime import VoiceRuntime
  b=self.bridge();r=VoiceRuntime.__new__(VoiceRuntime);r.lock=threading.RLock();r.enabled=True;r.generation=1;r.cancel=threading.Event();r.busy=True;r.stt=Mock();r.stt.transcribe.return_value='obsidian read secret.md';r.speaker=Mock();r.speaker.generation=0;r.notify=Mock();r.action_handler=b.voice_action;r.mic=Mock();r.router=Mock()
  r.turn([],1,False,[])
  r.router.ask.assert_not_called();r.router.stream.assert_not_called();r.speaker.speak.assert_not_called();r.mic.resume.assert_called_once();self.assertFalse(r.busy)

 def test_all_persona_prefixes_keep_exact_path(self):
  for name in ['JARVIS','NOVA','KAI','LYRA','DEX']:
   self.assertEqual(parse_voice('Hey '+name+', vault read Work/Note.md'),{'command':'vault-read','note_name':'Work/Note.md'})
 def test_unsupported_spoken_write_is_consumed_without_chat(self):
  b=self.bridge()
  for text in ['obsidian create x.md','Lyra vault delete x.md','vault read']:
   self.assertTrue(b.voice_action(text));b.voice.send_text.assert_not_called()
 def test_disabled_and_unsupported_commands_never_route_or_speak(self):
  import threading
  from jarvis.runtime import VoiceRuntime
  b=self.bridge()
  for text in ['Nova browser open example.com','Lyra vault delete secret.md','Dex vault read secret.md']:
   r=VoiceRuntime.__new__(VoiceRuntime);r.lock=threading.RLock();r.enabled=True;r.generation=1;r.cancel=threading.Event();r.busy=True;r.stt=Mock();r.stt.transcribe.return_value=text;r.speaker=Mock();r.speaker.generation=0;r.notify=Mock();r.action_handler=b.voice_action;r.mic=Mock();r.router=Mock()
   r.turn([],1,False,[]);r.router.ask.assert_not_called();r.router.stream.assert_not_called();r.speaker.speak.assert_not_called();self.assertFalse(r.busy)
