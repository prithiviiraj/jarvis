import unittest,tempfile
from unittest.mock import patch,Mock
from jarvis import voice_assets
class ProgressTests(unittest.TestCase):
 def test_voice_asset_progress_forwarded(self):
  callback=Mock();cancel=Mock()
  with tempfile.TemporaryDirectory() as folder,patch('jarvis.voice_assets.verified_http'),patch('jarvis.voice_assets.fetch_verified') as fetch:
   voice_assets.download(folder,consent=True,notify=callback,cancel=cancel)
   self.assertEqual(fetch.call_count,len(voice_assets.FILES))
   for call in fetch.call_args_list:self.assertIs(call.kwargs['notify'],callback);self.assertIs(call.kwargs['cancel'],cancel)
