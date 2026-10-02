"""Allowlisted rotating events. Never accept free text, transcripts or secrets."""
import logging
from logging.handlers import RotatingFileHandler
from .paths import ensure_layout

EVENTS = {'startup', 'shutdown', 'config_invalid', 'credentials_unavailable',
          'foundation_check_passed', 'foundation_check_failed'}

class Diagnostics:
    def __init__(self, root=None, max_bytes=65536, backup_count=3):
        root = ensure_layout(root)
        self.logger = logging.Logger('jarvis.foundation', logging.INFO)
        self.handler = RotatingFileHandler(root / 'logs' / 'events.log', maxBytes=max_bytes,
                                           backupCount=backup_count, encoding='utf-8')
        self.handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        self.logger.addHandler(self.handler)
    def event(self, name):
        if name not in EVENTS:
            raise ValueError('Only approved diagnostic event codes can be logged.')
        self.logger.info(name)
    def close(self):
        self.handler.close()
        self.logger.removeHandler(self.handler)
