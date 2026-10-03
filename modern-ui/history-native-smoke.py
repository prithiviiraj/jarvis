"""Separate history phase native restart acceptance; only synthetic local data."""
import os,json,pathlib,subprocess,tempfile,time,ctypes
from pywinauto import Desktop
with tempfile.TemporaryDirectory()as folder:
 from jarvis.chat_history import ChatHistory
 store=ChatHistory(pathlib.Path(folder)/'chat-history.sqlite');chat=store.new();store.save(chat,[{'name':'You','text':'Local restart test greeting'},{'name':'JARVIS','text':'History survives restart.'}]);store.close()
 env=dict(os.environ,JARVIS_DATA_DIR=folder);exe=os.environ['JARVIS_UI_EXE']
 for cycle in range(2):
  p=subprocess.Popen([exe],env=env)
  try:
   faces=Desktop(backend='uia').window(title='JARVIS / Floating faces');faces.wait('visible',timeout=30);faces.child_window(title='Reopen workspace',control_type='Button').wrapper_object().invoke()
   main=Desktop(backend='uia').window(title='JARVIS / Modern workspace preview');main.wait('visible',timeout=20);main.child_window(title='Connect local core',control_type='Button').wrapper_object().invoke();time.sleep(1)
   text=' '.join(x.window_text()for x in main.descendants());assert 'History survives restart.'in text
   main.child_window(title='Chat history',control_type='Button').wrapper_object().invoke();time.sleep(.6);main.capture_as_image().save('ui-evidence/history-native-restart-'+str(cycle)+'.png')
   assert 'Local restart test greeting'in ' '.join(x.window_text()for x in main.descendants())
  finally:
   ctypes.windll.user32.PostMessageW(faces.handle,0x0010,0,0)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
 pathlib.Path('ui-evidence/history-native-checks.json').write_text(json.dumps({'two_actual_UI_process_launches':True,'restored_chat_text':True,'past_chat_list':True,'synthetic_data_only':True}))
