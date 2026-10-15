"""Actual Windows unified workspace navigation/pixels. No sensor or live account task."""
import os,pathlib,subprocess,time,json,importlib.util
from pywinauto import Desktop
from pywinauto.controls.uiawrapper import UiaMeta,UIAWrapper
UiaMeta.control_type_to_cls.setdefault(None,UIAWrapper)
spec=importlib.util.spec_from_file_location('native_input',pathlib.Path(__file__).with_name('native-input.py'));helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
out=pathlib.Path('ui-evidence');out.mkdir(exist_ok=True);os.environ['JARVIS_DATA_DIR']=str((out/'unified-isolated-data').resolve());p=subprocess.Popen([os.environ['JARVIS_UI_EXE']]);checks=[]
try:
 w=Desktop(backend='uia').window(process=p.pid,title='JARVIS');w.wait('visible',timeout=30);w.set_focus();time.sleep(1)
 def button(name):
  b=w.child_window(title=name,control_type='Button',visible_only=True);b.wait('exists enabled',timeout=15);return b
 def click(name):helper.activate(button(name));time.sleep(.2)
 # Onboarding never permits sensors. Dismiss only this disposable fixture guide.
 guide=w.child_window(title='Skip setup guide',control_type='Button')
 if guide.exists():helper.activate(guide)
 for name in ['Home','JARVIS','Models','Voice settings','General','Terminal','Settings','Computer tools','Start listening','Camera off','Screen share off','Connect browser','Stop']:button(name);checks.append('visible '+name)
 w.capture_as_image().save(out/'native-unified-home.png')
 profile=w.child_window(title='Speaking profile',control_type='ComboBox');profile.wait('visible',timeout=15);profile.wrapper_object().select('ALL team');time.sleep(.2);button('Start ALL voice');checks.append('ALL selected without microphone start')
 profile.wrapper_object().select('JARVIS');time.sleep(.2);click('Settings');button('Choose connection');button('Set up voice');button('Explore tools');w.capture_as_image().save(out/'native-unified-settings-home.png');click('Choose connection');button('Back to Home');w.capture_as_image().save(out/'native-unified-settings-connections.png')
 for name in ['Connections','Voice','Privacy','Tools','More']:
  click(name);button('Back to Home');checks.append('category '+name)
 click('Voice')
 route=w.child_window(title='Recognition route',control_type='ComboBox');route.wait('visible',timeout=15)
 language=w.child_window(title='Input language',control_type='ComboBox');language.wait('visible',timeout=15)
 click('Set up Groq speech input');button('Cancel Groq setup')
 enable=w.child_window(title='Enable Groq speech input',control_type='Button');enable.wait('exists',timeout=10);assert not enable.wrapper_object().is_enabled(),'Groq sharing/free-tier gates bypassed'
 w.capture_as_image().save(out/'native-unified-groq-consent.png');click('Cancel Groq setup');checks.append('Groq route/language and Cancel; unchecked sharing/free gates remain disabled')
 click('All settings')
 for name in ['Appearance','Memory','Team options','Live screen share','Search engine','Chats','Advanced']:
  click(name);button('Back to Home');checks.append('detail '+name)
 click('Back to Home');w.child_window(title='Message draft',control_type='Edit').wait('visible',timeout=15)
 click('More');click('My notes');button('Connect or manage my notes');w.capture_as_image().save(out/'native-unified-notes.png');click('Connect or manage my notes');button('Back to Home');click('Back to Home')
 # Real resized work-area pixels, no separate copied-shell fixture.
 for width,height in [(1024,768),(940,680)]:
  helper.place_in_work_area(w,width,height);time.sleep(.35);w.capture_as_image().save(out/('native-unified-'+str(width)+'x'+str(height)+'.png'));button('Home');button('Settings');checks.append('current shell resized '+str(width)+'x'+str(height))
 click('Stop');w.capture_as_image().save(out/'native-unified-stopped.png')
 (out/'unified-native-result.json').write_text(json.dumps({'checks':checks,'scope':'Actual Win32/WebView2 UIA, disposable profile; no microphone/camera/screenshare/browser enabled by this fixture'},indent=2))
 print('Actual unified Windows pane/controls/pixels: passed')
finally:p.terminate();p.wait(timeout=15)
