import unittest,json,tempfile,pathlib
from unittest.mock import Mock
from jarvis.chat_history import ChatHistory
from jarvis.ui_bridge import Bridge
from jarvis.brain_settings import BrainSettings
class LargeHistoryIPC(unittest.TestCase):
 def test_full_unicode_archive_fits_native_status_contract(self):
  with tempfile.TemporaryDirectory()as t:
   h=ChatHistory(pathlib.Path(t)/'chat.sqlite');i=h.new();rows=[{'name':'You'if n%2==0 else'JARVIS','text':'தமிழ்'*800}for n in range(200)];h.save(i,rows)
   voice=Mock();voice.busy=False;voice.runtime=None;voice.events.get_nowait.side_effect=__import__('queue').Empty;voice.tts_engine='kokoro';voice.name='JARVIS';voice.reply_actor='JARVIS'
   b=Bridge(voice=voice,brains=BrainSettings(store=Mock()),history=h)
   data=b.execute({'command':'status'});raw=json.dumps({'ok':True,'data':data},ensure_ascii=True).encode();self.assertGreater(len(raw),100000);self.assertLess(len(raw),8_000_000);self.assertEqual(len(data['messages']),200)
   self.assertIn('reply.len()>8_000_000',(pathlib.Path(__file__).parents[1]/'modern-ui/src-tauri/src/main.rs').read_text());h.close()
