# Third-party ledger - Phase 0

No new third-party runtime packages or speech model weights are included in the Phase0 foundation. Runtime uses Python standard-library modules. Exact installer binaries and their notices must be recorded after packaging policy approval; no Windows artifact yet.

## Selected runtime/build platform
| Component | Use | License/source | Status |
| --- | --- | --- | --- |
| Python runtime | Packaged application language runtime | PSF license, https://docs.python.org/3/license.html | Selected PSF runtime; retain LICENSE.txt and bundled component notices |
| Tcl/Tk | Temporary Phase0 foundation window | Tcl/Tk permissive terms, https://www.tcl-lang.org/software/tcltk/license.html | Selected permissive runtime; retain license.terms; not the final UI |
| PyInstaller | Existing installer build route | GPL with bootloader exception, https://github.com/PyInstaller/PyInstaller/blob/develop/COPYING.txt | Selected with owner free+best delegation; retain GPL/exception notice |
| Inno Setup | Existing Setup EXE compiler | https://github.com/jrsoftware/issrc/blob/main/license.txt | Verified terms allow free use, alteration and distribution with attribution preservation; retain exact compiler license in artifact |

## Existing prototype is NOT automatically approved for new roadmap
Pillow/customtkinter/OpenCV/faster-whisper/sounddevice/PyAV/FFmpeg/ONNX/CTranslate2 and all model assets require full exact-version notices and transitive audit before reintroduction. Existing passing installer tests do not establish permissive-only compliance. No wholesale project copies.

## Voice candidates, not adopted
- openWakeWord code Apache-2.0 but stock models and default training features CC BY-NC-SA-4.0: excluded under permissive-only target.
- PocketSphinx code/model BSD-class, permitted BSD-class candidate under owner delegation; not adopted pending accuracy test.
- Parakeet TDT 0.6B v3 CC BY-4.0, CC BY exception permitted by owner free+best delegation; not adopted pending benchmark.
- Kokoro-82M weights Apache-2.0; exact voice/code/phonemizer dependencies not yet cleared.
