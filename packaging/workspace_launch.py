"""Experimental workspace executable. No auto-start, sensors or cloud on launch."""
import sys
if '--check' in sys.argv:
    from jarvis.__main__ import check
    from jarvis.native_frontend import verified_frontend
    check();verified_frontend()
else:
    from jarvis.workspace import main
    main()
