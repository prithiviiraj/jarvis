"""Frozen local bridge entry point. No sensors start until explicit UI consent."""
from jarvis.ui_bridge import main
if __name__ == '__main__':
    import sys
    if len(sys.argv)==2 and sys.argv[1]=='--voice-self-test':
        from jarvis.voice_acceptance import run
        run()
    else:main()
