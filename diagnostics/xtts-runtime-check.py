"""Dependency compatibility only. No model download, license acceptance or synthesis."""
import pathlib,json,importlib.metadata,os
assert not os.environ.get('COQUI_TOS_AGREED'),'No implicit model terms acceptance'
import torch,torchaudio
from TTS.api import TTS
from TTS.tts.models.xtts import Xtts
from TTS.tts.configs.xtts_config import XttsConfig
config=XttsConfig()
assert 'ta'not in config.languages
report={'scope':'optional CPU XTTS runtime import/config compatibility only','versions':{x:importlib.metadata.version(x)for x in ('torch','torchaudio','coqui-tts','transformers')},'cuda_build':torch.version.cuda,'model_downloaded':False,'model_synthesis':False,'languages':config.languages,'requires_owner_CPML_review_before_model_setup':True}
assert torch.version.cuda is None
pathlib.Path('optional-engine-evidence').mkdir(exist_ok=True);pathlib.Path('optional-engine-evidence/xtts-runtime.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
