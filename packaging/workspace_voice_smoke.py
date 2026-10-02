"""Windows UI bridge smoke with synthetic runtime. No physical audio claim."""
import tkinter as tk,pathlib,json,time,threading,tempfile
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
 app.session_setup={'mic':True,'cloud':True,'free':True,'model':''}
 app.select(1);app.voice_setup();assert app.session_mic_var.get() and app.groq_cloud_consent.get();capture('session-consent-NOVA')
 for window in root.winfo_children():
  if isinstance(window,tk.Toplevel):window.destroy()
 app.select(0);app.voice_setup();assert app.session_mic_var.get() and app.groq_cloud_consent.get();capture('session-consent-JARVIS')
 for window in root.winfo_children():
  if isinstance(window,tk.Toplevel):window.destroy()
 app.pause();assert not any(app.session_setup[k] for k in ['mic','cloud','free']);app.voice_setup();capture('onboarding')

 app.groq_cloud_consent.set(True);app.groq_free_confirmation.set(True)
 with patch('jarvis.brain_check.check_groq',return_value={'model':'openai/gpt-oss-20b','reply':'Hello. I am ready when you are.','first_text_s':0.65}), patch('jarvis.workspace.messagebox.showinfo') as success:
  app.groq_test_button.invoke()
  for _ in range(40):root.update();time.sleep(.01)
  app.poll_voice();root.update()
  assert success.called;assert 'Reply:' in app.groq_test_status.cget('text');assert app.groq_test_button.cget('state')=='normal';capture('groq-test-success')
 with patch('jarvis.workspace.messagebox.showerror') as error:
  app.groq_test_finished({'ok':False,'error':'Synthetic failure. No provider request.'});assert error.called;capture('groq-test-failure')

 assert not app.manual_model_entry.winfo_ismapped()
 # Actual progress UI, synthetic downloads only. No owner network/provider calls.
 released=threading.Event();began=threading.Event();bytes_sent=threading.Event();finish=threading.Event()
 def fake_download(*args,**kw):
  began.set();assert released.wait(10);kw['notify']('model.bin',12582912);bytes_sent.set();assert finish.wait(10)
 with patch('jarvis.workspace.messagebox.askyesno',return_value=True),patch('jarvis.models.download',side_effect=fake_download),patch('jarvis.voice_assets.download'):
  app.start_model_download();assert began.wait(1);assert app.model_download_button.cget('state')=='disabled'
  capture('model-download-starting');released.set()
  assert bytes_sent.wait(2)
  for _ in range(15):root.update();time.sleep(.01)
  assert '12.00 MiB' in app.model_download_label.cget('text')
  capture('model-download-bytes');finish.set()
  for _ in range(60):root.update();time.sleep(.01)
  assert 'Ready:' in app.model_download_label.cget('text');capture('model-download-ready');app.model_download_window.destroy()
 with patch('jarvis.workspace.messagebox.askyesno',return_value=True),patch('jarvis.models.download',side_effect=RuntimeError('SYNTHETIC failure')):
  app.start_model_download()
  for _ in range(30):root.update();time.sleep(.01)
  assert 'failed' in app.model_download_label.cget('text');capture('model-download-failed');app.model_download_window.destroy()
 app.manual_model_toggle.invoke();app.manual_model_entry.insert(0,'llama-3.1-8b-instant');app.manual_model_lock()
 assert app.manual_model_entry.cget('state')=='disabled';capture('manual-model-locked')

 for window in root.winfo_children():
  if isinstance(window,tk.Toplevel):window.destroy()
 app.groq_key();capture('key-onboarding')
 with patch('jarvis.security.WindowsCredentials') as store:
  store.return_value.status.return_value={'present':True,'saved_at':'2026-10-03T00:00:00+05:30'}
  assert app.groq_key_entry.get()==''
  app.groq_key_entry.insert(0,'SYNTHETIC-NOT-A-REAL-KEY');app.groq_key_save()
  store.return_value.set.assert_called_once_with('groq','SYNTHETIC-NOT-A-REAL-KEY');store.return_value.get.assert_not_called()
  assert app.groq_key_entry.get()=='SYNTHETIC-NOT-A-REAL-KEY'
  assert 'Saved' in app.groq_key_status.cget('text');capture('key-saved-visible')
  for window in root.winfo_children():
   if isinstance(window,tk.Toplevel):window.destroy()
  app.groq_key();assert app.groq_key_entry.get()=='';assert 'No re-paste needed' in app.groq_key_status.cget('text');store.return_value.get.assert_not_called();capture('key-reopened-saved-state')

 for window in root.winfo_children():
  if isinstance(window,tk.Toplevel):window.destroy()
 app.voice.memory.append('JARVIS','synthetic question','synthetic answer')
 with tempfile.TemporaryDirectory() as folder,patch('tkinter.filedialog.askdirectory',return_value=folder),patch('jarvis.workspace.messagebox.showinfo') as info:
  app.save_notes();assert not app.voice.memory.messages();assert len(list(pathlib.Path(folder).glob('*.md')))==1;assert info.called
 app.provider_pool();capture('provider-pool-empty')
 for sid,kind,model,on,consent,free in app.pool_rows:
  if sid=='slot1':on.set(True);model.insert(0,'synthetic-local-model')
 app.pool_routes['NOVA'].insert(0,'slot1');app.pool_apply();assert 'Nothing started' in app.pool_status.cget('text');capture('provider-pool-routes');app.pool_window.destroy();app.voice.pool_config=None
 app.open_mini();capture('mini');assert app.mini.attributes('-topmost');app.select(1);root.update();app.voice.notify('state','speaking');app.poll_voice();capture('five-orbs-NOVA-speaking');assert app.orb_overlay.status.cget('text')=='NOVA / SPEAKING';app.voice.notify('state','off');app.poll_voice();capture('five-orbs-off');assert app.orb_overlay.status.cget('text')=='NOVA / OFF';assert app.mini.overrideredirect();assert app.mini.winfo_rgb(app.mini.attributes('-transparentcolor'))==app.mini.winfo_rgb('#ff00fe');app.voice.notify('state','thinking');app.poll_voice();capture('floating-faces-thinking');app.voice.notify('state','listening');app.poll_voice();capture('floating-faces-listening');root.withdraw();capture('floating-faces-desktop');root.deiconify();app.orb_overlay.close();app.edit_profile();capture('profile')
 app.pause();assert controller.runtime is None
 for window in root.winfo_children():
  if isinstance(window,tk.Toplevel):window.destroy()
 local_router=Mock();local_router.ask.return_value={'text':'Synthetic local reply: JARVIS said hello earlier. No screen observation.','provider':'local'};controller.text_factory=Mock(return_value=local_router)
 app.set_view('Chat');app.chat_entry.insert(0,'Synthetic typed question with microphone off.');app.send_chat()
 for _ in range(20):root.update();time.sleep(.01)
 app.poll_voice();assert controller.runtime is None;assert not local_router.ask.call_args.kwargs['cloud_consent'];assert len(controller.memory.snapshot())==1;capture('typed-local-chat')
 app.set_view('Team Room');capture('shared-team-room');assert 'Synthetic local reply' in app.team_transcript.get('1.0','end');app.pause();app.update_team_transcript();assert not controller.memory.snapshot()
 local_router.ask.side_effect=[{'text':'Synthetic NOVA: our supplied conversation invites a playful team reply.','provider':'local'},{'text':'Synthetic JARVIS: I heard NOVA. This is conversation only, not game sensing.','provider':'local'}]
 app.round_entry.insert(0,'Playful banter about our actual conversation, no screen claims.');app.start_team_round()
 for _ in range(20):root.update();time.sleep(.01)
 app.poll_voice();assert len(controller.memory.snapshot())==2;assert '[NOVA]' in local_router.ask.call_args.args[0][-2]['content'];capture('local-team-round');app.pause()


 result={'profiles':rows,'sensors_on_launch':False,'test':'Synthetic controller to actual Tk UI; not real mic, model, or playback','unrun':['physical audio','AEC','barge-in','owner accent','1s end-to-first-audible','installer']}
 (out/'bridge-check.json').write_text(json.dumps(result,indent=2));app.close()
def guarded():
 try:voices()
 except Exception:
  import traceback
  traceback.print_exc();failed[0]=True;root.destroy()
root.after(800,guarded);root.mainloop()

if failed[0]:raise SystemExit(1)
