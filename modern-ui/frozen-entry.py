"""Frozen local bridge entry point. No sensors start until explicit UI consent."""
from jarvis.ui_bridge import main
if __name__ == '__main__':
    import sys
    if len(sys.argv)==2 and sys.argv[1]=='--voice-self-test':
        from jarvis.voice_acceptance import run
        run()
        # Test resources are already closed/report flushed. Native model caches stay
        # process-scoped; avoid interpreter-finalization disposal stalls on Windows.
        import os
        sys.stdout.flush();sys.stderr.flush();os._exit(0)
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
