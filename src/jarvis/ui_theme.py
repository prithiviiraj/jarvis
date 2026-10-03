"""Lightweight dark-glass treatment. No blur engine, GPU dependency or sensing."""
BG='#11161d';RAIL='#141c25';PANEL='#1d2733';LINE='#2b3b4b';TEXT='#eef3f8';MUTED='#9faebd'
def glass(window):
    # Window-wide alpha, not expensive live backdrop blur. Opaque fallback.
    try:window.attributes('-alpha',.97);return True
    except Exception:return False

def mix(a,b,t):
    t=max(0,min(1,t));a=a.lstrip('#');b=b.lstrip('#')
    return '#'+''.join('%02x'%round(int(a[i:i+2],16)*(1-t)+int(b[i:i+2],16)*t) for i in (0,2,4))
def hover(widget,base,highlight=LINE):
    import time
    state={'job':None,'color':base}
    def transition(target):
        if state['job'] is not None:
            try:widget.after_cancel(state['job'])
            except Exception:pass
        initial=state['color'];start=time.monotonic()
        def step():
            if not widget.winfo_exists():return
            t=min(1,(time.monotonic()-start)/.11);state['color']=mix(initial,target,1-(1-t)**3);widget.configure(bg=state['color'])
            state['job']=widget.after(16,step) if t<1 else None
        step()
    widget.bind('<Enter>',lambda e:transition(highlight));widget.bind('<Leave>',lambda e:transition(base))
