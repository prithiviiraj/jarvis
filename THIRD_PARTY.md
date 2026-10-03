# Third-party ledger - Phase 0

No speech model weights are included in the Phase0 foundation. Runtime uses Python standard-library modules. Exact installer binaries and their notices must be recorded after packaging policy approval; Phase0 Windows artifact passed packaging/install tests; see README.

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
- Parakeet TDT 0.6B v3 CC BY-4.0. Not adopted: outside the blueprint MIT/Apache reuse target. Free/best selection is not evidence of a license exception. Requires a separate redistribution-policy decision if ever selected.
- Kokoro-82M weights Apache-2.0; exact voice/code/phonemizer dependencies not yet cleared.

## Experimental Phase1 source, not shipping binary yet

Whisper base model: MIT (OpenAI), converted by Systran; https://huggingface.co/Systran/faster-whisper-base , revision ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66. Silero ONNX: MIT; https://github.com/snakers4/silero-vad , revision 1e261b036686cd0017d500ee96acd1c4ba572a9d. Files download after consent and are SHA256-verified; models not bundled.

Experimental requirements pin measured versions. faster-whisper (MIT), CTranslate2 (MIT), ONNX Runtime (MIT), NumPy (BSD), sounddevice (MIT, PortAudio separately MIT), PyAV (BSD, FFmpeg binary license depends on exact wheel/build). No Phase1 EXE distribution until exact Windows wheels, transitive code, DLL licenses/source/relinking obligations and notices are audited. SAPI calls the owner-installed Windows voice; no Microsoft voice redistributed.

Candidate card licenses alone never clear the full dependency stack. See docs/speech-license-screen.md. No paid provider is enabled by default.


## Experimental workspace bridge, not binary redistribution clearance

The connected source path selects the isolated Phonemis native frontend (pinned MIT source/resources with retained JSON MIT, xsimd BSD/Boost/Sun notices) and direct Kokoro ONNX. GPL eSpeak/phonemizer are not used by this path. Five raw style matrices and model/config files are pinned to the same immutable Kokoro KMP revision and SHA256-verified. Source: https://huggingface.co/Shusek00/kokoro-kmp-models . Exact Windows DLLs, native resources, voice provenance and all distribution notices still need a complete installer manifest/audit before packaging. Source test success does not clear that gate.

## Optional local camera experimental source

OpenCV headless 4.14.0.94 is an optional source-runner dependency, not a redistributed binary or installer clearance. Verified package source: https://pypi.org/project/opencv-python-headless/4.14.0.94/ . Wrapper MIT, OpenCV Apache-2.0, wheel includes third-party libraries/notices including FFmpeg LGPLv2.1. Haar detector ships with the package. Exact Windows wheel and all transitive notices remain subject to installer redistribution review. Camera UI imports cv2 only after Enable, reports missing/unavailable device as ERROR, and never downloads a detector at camera activation. Optional ENABLE-CAMERA-DEPS.cmd installs the dependency with the owner's deliberate action; no camera starts from installation.
