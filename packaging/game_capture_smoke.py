"""Windows synthetic window pixels and local HTTP vision contract. Not a real-game benchmark."""
import sys,pathlib,ctypes,io,json,threading,http.server,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from jarvis.game_companion import windows,capture,LocalGameModel
from PIL import Image
import tkinter as tk
seen=[]
class Fixture(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'models':[{'key':'synthetic-game-vision','capabilities':{'vision':True},'loaded_instances':[{'id':'synthetic-game-vision'}]}]}).encode())
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));seen.append(body);assert body['model']=='synthetic-game-vision';assert body['messages'][-1]['content'][1]['image_url']['url'].startswith('data:image/jpeg;base64,')
  self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':json.dumps({'observed':'Synthetic blue test window','comment':'Test only','confidence':'medium'})}}]}).encode())
server=http.server.ThreadingHTTPServer(('127.0.0.1',1234),Fixture);threading.Thread(target=server.serve_forever,daemon=True).start();ctypes.windll.user32.GetParent.restype=ctypes.c_void_p;ctypes.windll.user32.GetParent.argtypes=[ctypes.c_void_p];ctypes.windll.user32.SetForegroundWindow.argtypes=[ctypes.c_void_p];root=tk.Tk();root.title('JARVIS synthetic capture fixture');root.geometry('800x450+40+40');root.configure(bg='#144c9d');root.update();hwnd=ctypes.windll.user32.GetParent(root.winfo_id());ctypes.windll.user32.SetForegroundWindow(hwnd);root.update();time.sleep(.3)
try:
 target=next(x for x in windows()if x['title']=='JARVIS synthetic capture fixture')
 # Windows can reject the first focus request while desktop startup settles.
 # Bounded fixture-only readiness; production foreground checks stay strict.
 ctypes.windll.user32.GetForegroundWindow.restype=ctypes.c_void_p
 raw=None;deadline=time.monotonic()+10;attempts=0
 while raw is None and time.monotonic()<deadline:
  root.deiconify();root.lift();root.focus_force();root.update();ctypes.windll.user32.SetForegroundWindow(target['id']);root.update();attempts+=1
  if ctypes.windll.user32.GetForegroundWindow()==target['id']:raw=capture(target)
  if raw is None:time.sleep(.1)
 assert raw,('Synthetic foreground capture missing',{'selected':target['id'],'foreground':ctypes.windll.user32.GetForegroundWindow(),'attempts':attempts})
 image=Image.open(io.BytesIO(raw));assert image.width<=640 and image.height<=360
 pathlib.Path('modern-ui/ui-evidence').mkdir(parents=True,exist_ok=True);image.save('modern-ui/ui-evidence/native-selected-game-frame.png')
 center=image.convert('RGB').getpixel((image.width//2,image.height//2));assert max(abs(x-y)for x,y in zip(center,(20,76,157)))<10,'Wrong client-area capture pixels'
 m=LocalGameModel('synthetic-game-vision');row=m.analyze(raw);assert row['confidence']=='medium'and len(seen)==1
 root.iconify();root.update();assert capture(target)is None,'Minimized selected window was captured'
 print(json.dumps({'synthetic_capture':'passed','image_dimensions':image.size,'loopback_vision':'passed','scope':'Synthetic window+HTTP fixture only; not real game/model/resource test'}))
finally:root.destroy();server.shutdown();server.server_close()
