"""Bundled, manifest-verified frontend. Never execute a model-cache EXE."""
import hashlib,json,sys
from pathlib import Path

def verified_frontend():
    base=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[2]))/'native-voice'
    manifest=base/'manifest.json'
    try:
        rows=json.loads(manifest.read_text(encoding='utf-8'))
        required={'phonemis_runner.exe','en-us/lexicon_full.json','en-us/phonemizer_en_us.bin','en-us/tagger.json'}
        if set(rows)!=required:raise ValueError()
        for name,expected in rows.items():
            p=base/name
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise ValueError()
        return base/'phonemis_runner.exe',base/'en-us'
    except Exception:raise RuntimeError('Verified bundled voice frontend missing or altered. Reinstall the experimental build.') from None
