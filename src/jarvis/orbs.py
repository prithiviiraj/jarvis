"""Five-orb view driven only by real workspace state. No inferred activity."""
import math,time
ROSTER=[('JARVIS','#5bc8b2'),('NOVA','#aa8be9'),('KAI','#ec9d65'),('LYRA','#e287b5'),('DEX','#79a9e8')]
def radius(name,selected,state,elapsed,reduced=False):
    speaking=name==selected and state=='speaking'
    return 21+(7+(0 if reduced else 2*math.sin(elapsed*6)) if speaking else 0)
class OrbOverlay:
    def __init__(self,root,state,select,pause):
        import tkinter as tk
        self.tk=tk
        self.root=root;self.state=state;self.select=select;self.started=time.monotonic();self.reduced=False;self.job=None
        self.window=tk.Toplevel(root);self.window.title('JARVIS - Five orbs');self.window.geometry('390x128+20+20');self.window.attributes('-topmost',True);self.window.configure(bg='#101013');self.window.resizable(False,False)
        self.canvas=tk.Canvas(self.window,width=390,height=83,bg='#101013',highlightthickness=0);self.canvas.pack();self.items={}
        for i,(name,color) in enumerate(ROSTER):
            x=39+i*78;orb=self.canvas.create_oval(x-21,14,x+21,56,fill=color,outline='');label=self.canvas.create_text(x,72,text=name,fill='#eeeeF1',font=('Segoe UI',8));self.items[name]=(x,orb,label)
            self.canvas.tag_bind(orb,'<Button-1>',lambda e,n=i:self.select(n));self.canvas.tag_bind(label,'<Button-1>',lambda e,n=i:self.select(n))
        row=tk.Frame(self.window,bg='#101013');row.pack(fill='x');self.status=tk.Label(row,text='OFF',fg='#96969f',bg='#101013',font=('Segoe UI',8));self.status.pack(side='left',padx=8)
        for text,command in [('Open',root.lift),('Pause',pause),('Motion',self.toggle_motion),('Close',self.close)]:tk.Button(row,text=text,command=command,relief='flat',bg='#19191e',fg='#eeeeF1',font=('Segoe UI',8),bd=0).pack(side='right',padx=2)
        self.window.protocol('WM_DELETE_WINDOW',self.close);self.animate()
    def toggle_motion(self):self.reduced=not self.reduced
    def animate(self):
        if not self.window.winfo_exists():return
        selected,state=self.state();elapsed=time.monotonic()-self.started
        for name,(x,orb,label) in self.items.items():
            r=radius(name,selected,state,elapsed,self.reduced);self.canvas.coords(orb,x-r,35-r,x+r,35+r);self.canvas.itemconfigure(orb,outline='#eeeeF1' if name==selected else '',width=2)
        self.status.configure(text=(selected+' / '+state.upper())[:27]);self.job=self.window.after(16,self.animate)
    def close(self):
        if self.job:
            try:self.window.after_cancel(self.job)
            except self.tk.TclError:pass
        self.job=None;self.window.destroy()
