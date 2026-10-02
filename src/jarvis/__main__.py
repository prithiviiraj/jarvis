"""Phase 0 foundation window. Not the Phase 1 talking core."""
import argparse
import json
import os
from pathlib import Path
from .config import ConfigStore, ConfigError
from .diagnostics import Diagnostics
from .security import WindowsCredentials, CredentialError
from . import __version__

def check(root=None):
    store = ConfigStore(root)
    config = store.load()
    logs = Diagnostics(store.root)
    logs.event('foundation_check_passed'); logs.close()
    # No secrets, usernames, paths, transcript or provider calls in the result.
    return {'version': __version__, 'phase': 0, 'settings': 'valid',
            'logs': 'event-codes only', 'sensors': 'off', 'network': 'not used',
            'cloud_providers': 'disabled', 'keys': 'Windows Credential Manager only'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--voice-preview', action='store_true')
    parser.add_argument('--workspace-preview', action='store_true')
    parser.add_argument('--smoke-output')
    args = parser.parse_args()
    if args.workspace_preview:
        from .workspace import main as workspace_main
        workspace_main(); return
    if args.voice_preview:
        from .voice_preview import main as voice_main
        voice_main(); return
    if args.check:
        print(json.dumps(check(), indent=2)); return
    import tkinter as tk
    from tkinter import ttk
    store = ConfigStore()
    logs = Diagnostics(store.root)
    logs.event('startup')
    error = None
    try:
        store.load()
    except ConfigError as exc:
        logs.event('config_invalid'); error = str(exc)
    root = tk.Tk(); root.title('JARVIS - Foundation')
    root.geometry('860x600'); root.minsize(700,500)
    root.configure(bg='#101217')
    panel = tk.Frame(root, bg='#101217', padx=42, pady=38)
    panel.pack(fill='both', expand=True)
    def label(text, size=13, color='#a9b4c4'):
        widget = tk.Label(panel, text=text, fg=color, bg='#101217',
                          font=('Segoe UI', size), justify='left', anchor='w', wraplength=720)
        widget.pack(anchor='w', pady=(0,16)); return widget
    label('JARVIS', 26, '#bedfce')
    label('A clean foundation for your voice assistant.', 18, '#edf0f5')
    label('Phase 0: settings, secure key storage and private diagnostics.\nThis is not the hands-free voice build yet.')
    label('Microphone OFF   /   Camera OFF   /   Screen capture OFF', 12, '#bedfce')
    label('Your settings and model cache belong in your Windows user folder.\nAPI keys use Windows Credential Manager, never settings files.\nLogs contain event codes, not conversations or recordings.')
    state = label(error or 'Foundation ready. No network calls on launch.', 13, '#ffbdba' if error else '#bedfce')
    def run_check():
        try:
            check(store.root); state.configure(text='Check passed. Settings and private diagnostics work.')
        except Exception:
            logs.event('foundation_check_failed'); state.configure(text='Settings check failed. Your existing file was left unchanged.')
    tk.Button(panel, text='Run foundation check', command=run_check, bg='#bedfce', fg='#14251e',
              relief='flat', padx=18, pady=10).pack(anchor='w', pady=(0,18))
    label('Next: continuous voice, measured speech engines and brain routing.\nNo API key or microphone permission is needed for Phase 0.', 12)
    def close():
        logs.event('shutdown'); logs.close(); root.destroy()
    root.protocol('WM_DELETE_WINDOW', close)
    output = args.smoke_output or os.environ.get('JARVIS_SMOKE_OUTPUT')
    if output:
        def smoke():
            # Windows native screenshot helper supplied by the build harness.
            root.update()
            root.after(500, close)
        root.after(1500, smoke)
    root.mainloop()

if __name__ == '__main__':
    main()
