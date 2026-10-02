import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jarvis.config import ConfigStore, ConfigError, DEFAULT, migrate
from jarvis.paths import ensure_layout, data_root
from jarvis.diagnostics import Diagnostics
from jarvis.security import WindowsCredentials, CredentialError
from jarvis.__main__ import check

class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def test_user_layout(self):
        ensure_layout(self.root)
        for n in ('models','logs','backups'): self.assertTrue((self.root/n).is_dir())
    def test_data_override(self):
        with patch.dict(os.environ, {'JARVIS_DATA_DIR':str(self.root)}): self.assertEqual(data_root(),self.root.resolve())
    def test_defaults(self):
        s=ConfigStore(self.root); self.assertEqual(s.load(),DEFAULT)
        self.assertEqual(json.loads(s.path.read_text()),DEFAULT)
    def test_config_roundtrip_and_backup(self):
        s=ConfigStore(self.root);s.load();v=dict(DEFAULT,theme='light');s.save(v)
        self.assertEqual(s.load()['theme'],'light')
        self.assertEqual(json.loads((self.root/'backups/config.previous.json').read_text()),DEFAULT)
    def test_legacy_migration(self):
        self.assertEqual(migrate({'base_url':'http://127.0.0.1:1234/v1','model':'local'})['local_model'],'local')
    def test_bad_json_unchanged(self):
        s=ConfigStore(self.root);s.path.write_text('{broken')
        with self.assertRaises(ConfigError):s.load()
        self.assertEqual(s.path.read_text(),'{broken')
    def test_future_schema_unchanged(self):
        s=ConfigStore(self.root);v=dict(DEFAULT,schema_version=9);s.path.write_text(json.dumps(v));old=s.path.read_bytes()
        with self.assertRaises(ConfigError):s.load()
        self.assertEqual(old,s.path.read_bytes())
    def test_secret_rejected_before_write(self):
        s=ConfigStore(self.root);s.load();old=s.path.read_bytes()
        with self.assertRaises(ConfigError):s.save(dict(DEFAULT,api_key='private-test'))
        self.assertEqual(old,s.path.read_bytes());self.assertFalse((self.root/'backups/config.previous.json').exists())
    def test_cloud_disabled(self):
        with self.assertRaises(ConfigError):migrate(dict(DEFAULT,cloud_providers_enabled=['grok']))
    def test_remote_and_redirectlike_urls_rejected(self):
        for u in ('https://example.com/v1','http://localhost:1234/v1','http://user:pass@127.0.0.1:1234/v1','http://127.0.0.1:1234/v1?key=x'):
            with self.assertRaises(ConfigError):migrate(dict(DEFAULT,local_base_url=u))
    def test_logs_reject_free_text(self):
        d=Diagnostics(self.root)
        try:
            with self.assertRaises(ValueError):d.event('secret transcript body')
            d.event('startup')
        finally:d.close()
        self.assertNotIn('secret', (self.root/'logs/events.log').read_text())
    def test_rotating_logs_bounded(self):
        d=Diagnostics(self.root,max_bytes=150,backup_count=2)
        for _ in range(40):d.event('startup')
        d.close();self.assertLessEqual(len(list((self.root/'logs').glob('*'))),3)
    def test_nonwindows_no_key_fallback(self):
        with patch('jarvis.security.os.name','posix'):
            with self.assertRaises(CredentialError):WindowsCredentials()
    def test_provider_targets(self):
        self.assertEqual(WindowsCredentials.target('nim'),'JARVIS/provider/nim')
        with self.assertRaises(CredentialError):WindowsCredentials.target('unverified')
    def test_start_check_no_network_or_sensors(self):
        j=check(self.root);self.assertEqual(j['network'],'not used');self.assertEqual(j['sensors'],'off')
        self.assertFalse(any(self.root.glob('*.wav')))
if __name__=='__main__':unittest.main()
