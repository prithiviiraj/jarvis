"""Writable per-user state, separate from the installed executable."""
import os
from pathlib import Path

def data_root():
    override = os.environ.get('JARVIS_DATA_DIR')
    if override:
        return Path(override).expanduser().resolve()
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA')
        if not base:
            raise RuntimeError('Windows user data folder is unavailable. No files were saved.')
        return Path(base) / 'JARVIS'
    return Path.home() / '.local' / 'share' / 'jarvis'

def ensure_layout(root=None):
    root = Path(root) if root is not None else data_root()
    for folder in ('logs', 'models', 'backups'):
        (root / folder).mkdir(parents=True, exist_ok=True)
    return root
