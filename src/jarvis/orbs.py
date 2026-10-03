"""Five-orb view driven only by real workspace state. No inferred activity."""
import math,time
ROSTER=[('JARVIS','#5bc8b2'),('NOVA','#aa8be9'),('KAI','#ec9d65'),('LYRA','#e287b5'),('DEX','#79a9e8')]
def radius(name,selected,state,elapsed,reduced=False):
    speaking=name==selected and state=='speaking'
    return 21+(7+(0 if reduced else 2*math.sin(elapsed*6)) if speaking else 0)
def face_pose(name,selected,state,elapsed,reduced=False):
    speaking=name==selected and state=='speaking'
    blink=(not reduced and (elapsed+next(i for i,(n,_) in enumerate(ROSTER) if n==name)*.65)%4.5<.12)
    mode=state if name==selected else 'off'
    return {'mode':mode,'eye':.025 if blink or mode=='off' else .11,'mouth':(.07 if reduced else .07+.055*(1+math.sin(elapsed*14))) if speaking else .025}
def ease(current,target,dt,reduced=False):
    """Time-based easing, independent of callback frequency."""
    if reduced:return target
    return current+(target-current)*(1-math.exp(-min(.1,max(0,dt))/0.09))
def next_frame_delay(deadline,now):
    """A missed frame is skipped, not replayed in a catch-up burst."""
    deadline+=1/60
    if deadline<=now:deadline=now+1/60
    return deadline,max(1,int((deadline-now)*1000))
class OrbOverlay:
    def __init__(self,root,state,select,pause):
        import tkinter as tk
        self.tk=tk
        self.root=root;self.state=state;self.select=select;self.started=time.monotonic();self.reduced=False;self.job=None;self.next_frame=time.monotonic();self.last_frame=self.next_frame;self.smooth={}
        self.window=tk.Toplevel(root);self.window.title('JARVIS - Five orbs');self.window.geometry('390x83+30+25');self.window.overrideredirect(True);self.window.attributes('-topmost',True);self.window.configure(bg='#ff00fe');self.window.attributes('-transparentcolor','#ff00fe');self.window.resizable(False,False)
        self.canvas=tk.Canvas(self.window,width=390,height=83,bg='#ff00fe',highlightthickness=0);self.canvas.pack();self.items={};self.faces={}
        for i,(name,color) in enumerate(ROSTER):
            x=39+i*78;orb=self.canvas.create_oval(x-21,14,x+21,56,fill=color,outline='');label=self.canvas.create_text(x,72,text='',fill='#eeeeF1',font=('Segoe UI',8));self.items[name]=(x,orb,label)
            face={}
            for part,fill in [('hair','#26313c'),('left','#11151c'),('right','#11151c'),('mouth','#25313b'),('cheekL','#ffe1cf'),('cheekR','#ffe1cf')]:face[part]=self.canvas.create_oval(0,0,1,1,fill=fill,outline='')
            face['detail']=self.canvas.create_line(0,0,1,1,fill='#f4ebd4',width=2)
            # White sclera and highlights make expressions readable at small size.
            face['whiteL']=self.canvas.create_oval(0,0,1,1,fill='#fff4e7',outline='');face['whiteR']=self.canvas.create_oval(0,0,1,1,fill='#fff4e7',outline='')
            self.canvas.tag_lower(face['whiteL'],face['left']);self.canvas.tag_lower(face['whiteR'],face['right'])
            face['browL']=self.canvas.create_line(0,0,1,1,fill='#27313b',width=2,smooth=True);face['browR']=self.canvas.create_line(0,0,1,1,fill='#27313b',width=2,smooth=True)
            self.faces[name]=face
            for item in face.values():self.canvas.tag_bind(item,'<Button-1>',lambda e,n=i:self.select(n))
            self.canvas.tag_bind(orb,'<Button-1>',lambda e,n=i:self.select(n));self.canvas.tag_bind(label,'<Button-1>',lambda e,n=i:self.select(n))
        self.status=tk.Label(self.window,text='OFF') # Diagnostic state only, not packed.
        self.menu=tk.Menu(self.window,tearoff=False)
        for text,command in [('Open workspace',self.show_workspace),('Pause all',pause),('Reduced motion',self.toggle_motion),('Close overlay',self.close)]:self.menu.add_command(label=text,command=command)
        self.canvas.bind('<Button-3>',lambda e:self.menu.tk_popup(e.x_root,e.y_root))
        self.canvas.bind('<ButtonPress-2>',lambda e:setattr(self,'drag',(e.x_root,e.y_root,self.window.winfo_x(),self.window.winfo_y())))
        self.canvas.bind('<B2-Motion>',self.move)
        self.window.protocol('WM_DELETE_WINDOW',self.close);self.animate()
    def show_workspace(self):
        self.root.deiconify();self.root.lift()
    def move(self,e):
        if hasattr(self,'drag'):
            sx,sy,x,y=self.drag;self.window.geometry('+%d+%d'%(x+e.x_root-sx,y+e.y_root-sy))
    def toggle_motion(self):self.reduced=not self.reduced
    def animate(self):
        if not self.window.winfo_exists():return
        selected,state=self.state();now=time.monotonic();elapsed=now-self.started;dt=now-self.last_frame;self.last_frame=now
        for name,(x,orb,label) in self.items.items():
            target=radius(name,selected,state,elapsed,self.reduced);previous=self.smooth.get(name,{'radius':21,'eye':.025,'mouth':.025});r=ease(previous['radius'],target,dt,self.reduced);self.canvas.coords(orb,x-r,35-r,x+r,35+r);self.canvas.itemconfigure(orb,outline='#eeeeF1' if name==selected else '',width=2)
            pose=face_pose(name,selected,state,elapsed,self.reduced)
            pose['eye']=ease(previous['eye'],pose['eye'],dt,self.reduced);pose['mouth']=ease(previous['mouth'],pose['mouth'],dt,self.reduced)
            self.smooth[name]={'radius':r,'eye':pose['eye'],'mouth':pose['mouth']};f=self.faces[name];y=35
            for side,dx in [('left',-.32),('right',.32)]:
                ey=pose['eye']*r;ex=x+dx*r+(.035*r if pose['mode']=='thinking' else 0);self.canvas.coords(f[side],ex-.07*r,y-.12*r-ey,ex+.07*r,y-.12*r+ey)
            for side,dx in [('L',-.32),('R',.32)]:
                ex=x+dx*r;ey=pose['eye']*r;self.canvas.coords(f['white'+side],ex-.16*r,y-.12*r-ey,ex+.16*r,y-.12*r+ey)
                self.canvas.coords(f['brow'+side],ex-.16*r,y-.34*r,ex,y-(.44 if pose['mode']=='thinking' else .38)*r,ex+.16*r,y-.34*r)
            for part,dx in [('cheekL',-.49),('cheekR',.49)]:self.canvas.coords(f[part],x+dx*r-.1*r,y+.08*r,x+dx*r+.1*r,y+.18*r)
            h=pose['mouth']*r;self.canvas.coords(f['mouth'],x-.22*r,y+.35*r-h,x+.22*r,y+.35*r+h)
            hair={'JARVIS':(-.72,-.9,.72,-.58),'NOVA':(-.88,-.85,-.05,-.45),'KAI':(-.55,-.98,.55,-.72),'LYRA':(.05,-.85,.88,-.45),'DEX':(-.8,-.83,.8,-.65)}[name]
            self.canvas.coords(f['hair'],x+hair[0]*r,y+hair[1]*r,x+hair[2]*r,y+hair[3]*r)
            if pose['mode']=='thinking':self.canvas.itemconfigure(f['detail'],fill='#fff4cc')
            else:self.canvas.itemconfigure(f['detail'],fill='#f4ebd4')
            if name=='DEX':self.canvas.coords(f['detail'],x-.5*r,y-.12*r,x+.5*r,y-.12*r)
            elif name=='JARVIS':self.canvas.coords(f['detail'],x-.25*r,y+.6*r,x+.25*r,y+.6*r)
            else:self.canvas.coords(f['detail'],x-.12*r,y-.9*r,x+.12*r,y-.75*r)
        self.status.configure(text=(selected+' / '+state.upper())[:27])
        # Deadline pacing avoids adding each draw duration to every16ms delay.
        self.next_frame,delay=next_frame_delay(self.next_frame,time.monotonic())
        self.job=self.window.after(delay,self.animate)
    def close(self):
        if self.job:
            try:self.window.after_cancel(self.job)
            except self.tk.TclError:pass
        self.job=None;self.window.destroy();self.show_workspace()
