"""Actual Windows pixels, navigation/modal/mini-orb smoke; no sensor starts."""
import tkinter as tk,pathlib,sys
from PIL import ImageGrab
from jarvis.workspace import Workspace
out=pathlib.Path('workspace-evidence');out.mkdir(exist_ok=True)
root=tk.Tk();app=Workspace(root)
def capture(name):
 root.update();ImageGrab.grab().save(out/(name+'.png'))
def step1():
 capture('voice');app.set_view('Team Room');root.after(400,step2)
def step2():
 capture('team');app.set_view('Chat');root.after(400,step3)
def step3():
 capture('chat');app.settings();root.after(400,step4)
def step4():
 capture('settings');app.settings_window.destroy();app.open_mini();root.after(400,step5)
def step5():
 capture('mini');app.mini.destroy();app.edit_profile();root.after(400,step6)
def step6():
 capture('profile');root.destroy()
root.after(800,step1);root.mainloop()
