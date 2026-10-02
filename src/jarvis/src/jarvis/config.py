"""Versioned settings; no API keys, chat, sensor consent or auto-start grants."""
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit
from .paths import ensure_layout

DEFAULT = {'schema_version': 1, 'project_name': 'JARVIS',
           'local_base_url': 'http://127.0.0.1:1234/v1', 'local_model': '',
           'theme': 'dark', 'cloud_providers_enabled': []}

class ConfigError(ValueError):
    pass

def validate(value):
    if not isinstance(value, dict) or value.get('schema_version') != 1:
        raise ConfigError('Settings version is not supported. Your file was left unchanged.')
    if set(value) != set(DEFAULT):
        raise ConfigError('Unknown or missing settings. Secrets must use Windows Credential Manager.')
    if value['project_name'] != 'JARVIS' or value['theme'] not in ('dark', 'light'):
        raise ConfigError('Invalid app name or theme.')
    if not isinstance(value['local_model'], str) or len(value['local_model']) > 300:
        raise ConfigError('Invalid local model name.')
    if value['cloud_providers_enabled'] != []:
        raise ConfigError('Cloud providers are not enabled in Phase 0.')
    try:
        u = urlsplit(value['local_base_url'])
        valid = (u.scheme == 'http' and u.hostname == '127.0.0.1' and u.port
                 and u.path == '/v1' and not u.username and not u.password
                 and not u.query and not u.fragment)
    except (ValueError, TypeError, AttributeError):
        valid = False
    if not valid:
        raise ConfigError('Use a local address: http://127.0.0.1:PORT/v1.')
    return dict(value)

def migrate(value):
    if not isinstance(value, dict):
        raise ConfigError('Settings file must contain an object.')
    if 'schema_version' not in value:
        if set(value) - {'project_name', 'base_url', 'model'}:
            raise ConfigError('Legacy settings contain unknown fields; original file was left unchanged.')
        value = dict(DEFAULT, local_base_url=value.get('base_url', DEFAULT['local_base_url']),
                     local_model=value.get('model', ''))
    return validate(value)

class ConfigStore:
    def __init__(self, root=None):
        self.root = ensure_layout(root)
        self.path = self.root / 'config.json'
    def load(self):
        if not self.path.exists():
            self.save(DEFAULT)
            return dict(DEFAULT)
        try:
            return migrate(json.loads(self.path.read_text(encoding='utf-8')))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigError('Cannot read settings. Original file was left unchanged.') from None
    def save(self, value):
        value = validate(value)
        # Validate before touching either the file or its backup.
        if self.path.exists():
            old = self.path.read_bytes()
            # Only back up validated, secret-free settings, never arbitrary legacy bytes.
            try:
                safe = migrate(json.loads(old))
            except (ValueError, UnicodeDecodeError):
                safe = None
            if safe is not None:
                (self.root / 'backups' / 'config.previous.json').write_text(json.dumps(safe, indent=2), encoding='utf-8')
        fd, name = tempfile.mkstemp(prefix='settings-', suffix='.tmp', dir=self.root)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(value, f, indent=2)
                f.flush(); os.fsync(f.fileno())
            os.replace(name, self.path)
        finally:
            Path(name).unlink(missing_ok=True)
