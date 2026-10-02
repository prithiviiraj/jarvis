"""Windows UI bridge smoke with synthetic runtime. No physical audio claim."""
import tkinter as tk,pathlib,json,time
from unittest.mock import Mock,patch
from PIL import ImageGrab
from jarvis.workspace import Workspace
from jarvis.workspace_voice import WorkspaceVoice,VOICES
out=pathlib.Path('workspace-evidence');out.mkdir(exist_ok=True)
created=[]
def factory(name,notify,*args):
 runtime=Mock();runtime.enabled=False
 def enable(**kw):
  assert kw['consent'];runtime.enabled=True;notify('transcript','And so my fellow Americans ask not what your country can do for you, ask what you can do for your country.');notify('answer',{'text':'Hello. I am '+name+'. This is a synthetic CI reply, not a live model response.'})
 def close():runtime.enabled=False
 runtime.enable.side_effect=enable;runtime.close.side_effect=close;created.append((name,runtime));return runtime
root=tk.Tk();controller=WorkspaceVoice(factory);app=Workspace(root,controller)
rows=[];failed=[False]
def capture(name):
 root.update();time.sleep(.25);root.update();ImageGrab.grab().save(out/(name+'.png'))
def voices():
 for i,name in enumerate(VOICES):
  app.select(i);controller.start(True).join(3);app.poll_voice();root.update()
  assert controller.runtime.enabled
  assert name in app.response
  capture(name+'-active');rows.append({'profile':name,'voice':VOICES[name],'synthetic_runtime_connected':True})
 app.select(0);capture('voice');app.set_view('Team Room');capture('team');app.set_view('Chat');capture('chat')
 app.settings();capture('settings');app.settings_window.destroy()
 app.voice_setup();capture('onboarding')
 assert not app.manual_model_entry.winfo_ismapped()
 app.manual_model_toggle.invoke();app.manual_model_entry.insert(0,'llama-3.1-8b-instant');app.manual_model_lock()
 assert app.manual_model_entry.cget('state')=='disabled';capture('manual-model-locked')

 for window in root.winfo_children():
  if isinstance(window,tk.Toplevel):window.destroy()
 app.groq_key();capture('key-onboarding')
 with patch('jarvis.security.WindowsCredentials') as store:
  assert app.groq_key_entry.get()==''
  app.groq_key_entry.insert(0,'SYNTHETIC-NOT-A-REAL-KEY');app.groq_key_save()
  store.return_value.set.assert_called_once_with('groq','SYNTHETIC-NOT-A-REAL-KEY');store.return_value.get.assert_not_called()
  assert app.groq_key_entry.get()=='SYNTHETIC-NOT-A-REAL-KEY'
  assert 'Saved' in app.groq_key_status.cget('text');capture('key-saved-visible')

 for window in root.winfo_children():
  if isinstance(window,tk.Toplevel):window.destroy()
 app.open_mini();capture('mini');app.mini.destroy();app.edit_profile();capture('profile')
 app.pause();assert controller.runtime is None
 result={'profiles':rows,'sensors_on_launch':False,'test':'Synthetic controller to actual Tk UI; not real mic, model, or playback','unrun':['physical audio','AEC','barge-in','owner accent','1s end-to-first-audible','installer']}
 (out/'bridge-check.json').write_text(json.dumps(result,indent=2));app.close()
def guarded():
 try:voices()
 except Exception:
  import traceback
  traceback.print_exc();failed[0]=True;root.destroy()
root.after(800,guarded);root.mainloop()

if failed[0]:raise SystemExit(1)
