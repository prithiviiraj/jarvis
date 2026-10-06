import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
from unittest.mock import Mock
b=Bridge(WorkspaceVoice());b.evolution.generate=Mock()
try:
 s=b.execute({'command':'chat','text':'JARVIS open the data center.'});pathlib.Path('polish-state.json').write_text(json.dumps(s))
finally:b.close()
