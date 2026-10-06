import sys,json,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from jarvis.ui_bridge import Bridge
from jarvis.workspace_voice import WorkspaceVoice
b=Bridge(WorkspaceVoice());b.browser_enabled=True
try:
 request=json.loads(sys.argv[1])if len(sys.argv)>1 else {'command':'chat','text':'JARVIS open the browser.','audio':False}
 state=b.execute(request)
 if request['command']=='chat':assert state['browser']['pending']=={'command':'open-window','value':''}and b.browser is None
 if len(sys.argv)>1:print(json.dumps(state))
 else:pathlib.Path('bridge-state.json').write_text(json.dumps(state),encoding='utf-8')
finally:b.close()
