"""Real Tk/Windows callback and draw-flush measurement, not monitor FPS.
No provider, model, microphone or speech assets used. Three visible trials/state.
"""
import json,platform,pathlib,time,tkinter as tk
from PIL import ImageGrab
from jarvis.orbs import OrbOverlay
from jarvis.experimental.animation_metrics import summarize
out=pathlib.Path('workspace-evidence');out.mkdir(exist_ok=True)
root=tk.Tk();root.geometry('700x420+10+10');root.title('JARVIS animation measurement')
tk.Label(root,text='Controlled animation timing fixture\nNo microphone, provider or model\nCallback Hz is not display FPS',font=('Segoe UI',15)).pack(pady=(140,30))
current=['JARVIS','off']; samples=[];costs=[];enabled=[False]
class MeasuredOverlay(OrbOverlay):
 def animate(self):
  t=time.perf_counter()
  super().animate()
  self.canvas.update_idletasks()
  if enabled[0]:samples.append(t);costs.append(time.perf_counter()-t)
overlay=MeasuredOverlay(root,lambda:tuple(current),lambda i:None,lambda:None)
results=[]
for state,reduced in [('off',False),('listening',False),('thinking',False),('speaking',False),('speaking',True)]:
 for trial in range(1,4):
  current[:]=['NOVA',state];overlay.reduced=reduced
  samples.clear();costs.clear();enabled[0]=False
  trial_cpu=[None];trial_wall=[None]
  def begin():
   trial_cpu[0]=time.process_time();trial_wall[0]=time.perf_counter();enabled[0]=True
  root.after(1000,begin)
  root.after(6000,root.quit);root.mainloop();enabled[0]=False
  cpu_s=time.process_time()-trial_cpu[0];wall_s=time.perf_counter()-trial_wall[0]
  results.append({'state':state,'reduced_motion':reduced,'trial':trial,'aggregate_process_cpu_s':cpu_s,'aggregate_process_cpu_pct_one_core':100*cpu_s/wall_s,**summarize(samples[:],costs[:])})
  if trial==1:ImageGrab.grab().save(out/('animation-'+state+('-reduced' if reduced else '')+'.png'))
overlay.close();root.destroy()
report={'measurement':'Tk callback cadence, high-resolution wall duration for canvas update + idle draw flush, aggregate process CPU','not_measured':['display presentation FPS','GPU/compositor latency','owner laptop','gaming load','audio lip-sync'],
 'platform':platform.platform(),'python':platform.python_version(),'warmup_s':1,'sample_window_s':5,'trials_per_state':3,'results':results}
(out/'animation-metrics.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
