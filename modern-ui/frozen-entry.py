"""Frozen local bridge entry point. No sensors start until explicit UI consent."""
from jarvis.ui_bridge import main
if __name__ == '__main__':
    import sys
    if len(sys.argv)==2 and sys.argv[1]=='--real-speed-test':
        from jarvis.owner_speed import run
        run(confirm=True)
    elif len(sys.argv)==2 and sys.argv[1]=='--groq-stt-self-test':
        from jarvis.groq_stt_acceptance import run
        run()
    elif len(sys.argv)==2 and sys.argv[1]=='--bundle-self-test':
        from jarvis.bundle_acceptance import run
        run()
    elif len(sys.argv)==2 and sys.argv[1]=='--desktop-input-fixture':
        from jarvis.desktop_acceptance import fixture
        fixture()
    elif len(sys.argv)==2 and sys.argv[1]=='--desktop-self-test':
        from jarvis.desktop_acceptance import run
        run()
    elif len(sys.argv)==2 and sys.argv[1]=='--telegram-self-test':
        from jarvis.telegram_acceptance import run
        run()
    elif len(sys.argv)==2 and sys.argv[1]=='--google-self-test':
        from jarvis.google_acceptance import run
        run()
    elif len(sys.argv)==2 and sys.argv[1]=='--draft-self-test':
        from jarvis.draft_acceptance import run
        run()
    elif len(sys.argv)==2 and sys.argv[1]=='--phone-self-test':
        from jarvis.phone_acceptance import run
        run()
        import os
        sys.stdout.flush();sys.stderr.flush();os._exit(0)
    elif len(sys.argv)==2 and sys.argv[1]=='--voice-self-test':
        import os,traceback
        from jarvis.voice_acceptance import run
        code=0
        try:run()
        except BaseException:
            traceback.print_exc();code=1
        # Test-only process. Preserve failure code/log, avoid native finalization hang.
        sys.stdout.flush();sys.stderr.flush();os._exit(code)
    elif len(sys.argv)==2 and sys.argv[1]=='--search-self-test':
        from jarvis.search_acceptance import run
        run()
        import os
        sys.stdout.flush();sys.stderr.flush();os._exit(0)
    elif len(sys.argv)==2 and sys.argv[1]=='--turn-self-test':
        from jarvis.turn_acceptance import run
        run()
        import os
        sys.stdout.flush();sys.stderr.flush();os._exit(0)
    elif len(sys.argv)==2 and sys.argv[1]=='--laya-self-test':
        from jarvis.laya_acceptance import run
        run()
        import os
        sys.stdout.flush();sys.stderr.flush();os._exit(0)
    else:main()
