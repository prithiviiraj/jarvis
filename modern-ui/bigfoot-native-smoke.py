"""Actual copied-shell Windows UIA diagnostic. No model/download/mic/control starts."""
import os,pathlib,subprocess,time,json,importlib.util
from pywinauto import Desktop,mouse
from PIL import ImageGrab
spec=importlib.util.spec_from_file_location('native_input',pathlib.Path(__file__).with_name('native-input.py'));helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
if os.name!='nt':raise RuntimeError('Actual copied-shell diagnostic requires Windows')
exe=pathlib.Path(os.environ['JARVIS_UI_EXE']).resolve();out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True)
env=dict(os.environ,JARVIS_BIGFOOT_DIAGNOSTIC='1',JARVIS_DATA_DIR=str((out/'bigfoot-native-isolated-data').resolve()))
child=subprocess.Popen([str(exe)],env=env);checks=[]
try:
 window=Desktop(backend='uia').window(title='JARVIS / Modern workspace preview',process=child.pid);window.wait('visible',timeout=30)
 def button(name):
  control=window.child_window(title=name,control_type='Button',visible_only=True);control.wait('exists enabled',timeout=15);return control
 def visible_text(text):
  deadline=time.monotonic()+15
  while time.monotonic()<deadline:
   if any(text in c.window_text()for c in window.descendants()):return
   time.sleep(.2)
  raise AssertionError('Copied native text absent: '+text)
 visible_text('Voice');visible_text('Local speech assets');checks.append('actual first-open Voice offer')
 for name in ('Models','JARVIS','General','Voice'):
  helper.activate(button(name));time.sleep(.3);ImageGrab.grab().save(out/('native-bigfoot-'+name.lower()+'.png'));checks.append('actual native '+name+' navigation')
 # Inspect existing local controls only. Never click model/speech downloads or capture.
 visible_text('Speech input');visible_text('Automatic (multilingual)');visible_text('Test Microphone')
 for size in ((800,600),(1024,768)):
  window.move_window(width=size[0],height=size[1]);time.sleep(.4);ImageGrab.grab().save(out/('native-bigfoot-'+str(size[0])+'.png'));checks.append('native resized '+str(size))
 (out/'native-bigfoot-report.json').write_text(json.dumps({'checks':checks,'scope':'Actual Windows WebView/UIA pixels and navigation only. No model, microphone, audio, desktop task or owner-hardware proof.'},indent=2))
finally:
 subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],check=False,capture_output=True,timeout=10)
 try:child.wait(timeout=10)
 except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
