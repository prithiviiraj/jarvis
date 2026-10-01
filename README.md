# JARVIS 0.2.0

A fresh local Windows study buddy. Author: Prithiv. Not an Omi fork.

**Current status: source prototype tested; Windows installer build still pending.**
Do not treat the source ZIP as a ready-made EXE.

## What V1 does

- Chat with a local LM Studio model in English or Tanglish.
- Ask about your primary-monitor screen after capture, preview and confirmation.
- Opt into a screen agent: one frame every 120 seconds while minimized, local nudges with a 10-minute cooldown.
- Opt into camera face-presence: local CPU checks every 2 seconds, no recognition or recordings.
- Get local popup nudges and a gentle 45-minute break check while monitoring is on.
- Get study/Maya guidance and gentle wellness suggestions, not medical diagnosis.
- Clear the short session history. Chats, activity feeds and screenshots are not saved by JARVIS.
- Optional integration with your existing Telegram bridge, preserving its network patch and local approvals. This is not installed or enabled automatically.

JARVIS does not run commands, edit Maya scenes, control the mouse, record audio,
analyze continuous video, schedule persistent reminders or act autonomously. A prompt cannot make a
small model medically reliable or resistant to every malicious screenshot.
Always review its suggestions. This version has no cloud fallback.

## Your only setup after a ready installer is supplied

1. Install LM Studio for Windows: https://lmstudio.ai/download?os=win32
2. In Discover, search `lmstudio-community/Qwen2.5-VL-3B-Instruct-GGUF`.
3. Download `Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf` and its companion
   `mmproj-model-f16.gguf`. Both are needed for vision.
4. Load the model. Start at 4096 context. If memory is tight, reduce context
   to 2048 or GPU-offloaded layers. The 6GB GPU is not a guaranteed full-offload fit.
5. Test an image inside LM Studio. In Developer, start the server on port 1234.
   Keep network serving OFF. Default no-token loopback mode works with JARVIS.
6. Install `JARVIS-Setup-0.2.0.exe`, then open the desktop shortcut.
7. Click `Check LM Studio`, then ask a short question. For screen help, type a
   question and click `Ask with screen...`. Close private windows before capture.

The installer is unsigned. It may trigger a security warning. Do not blindly
bypass Windows protection; ask for the verified source and build/checksum instead.
LM Studio itself may retain its own diagnostic logs/settings. Check its privacy settings.

## Privacy and memory

The local UI talks only to `http://127.0.0.1:1234/v1`. Proxy routing and redirects
are blocked. Screen images are reduced to at most 1280 pixels on the longer
side, used only for the current question, and not retained in JARVIS history.
Small screenshot text can be unreadable. Password/private-window detection is
not automatic. Preview and cancel if anything sensitive is visible.

The last three exchanges live in memory until you clear or close JARVIS.
`notes.txt` can hold notes you choose to save. It is plaintext and optional.
No personal, health or credential details are preloaded. Delete notes to forget them.
If several models are available, set `model` in `config.json` to the exact ID
shown by the connection check; JARVIS will not guess.

## Telegram option (not enabled by installer)

The fresh `bridge_adapter.py` can wrap the existing bridge v4. No bot token is
included. Never run two listeners for the same bot. Deploy only after confirming
the paired owner identity and approved bridge scope, then stop the original
listener and use `run_bridge.py` with the original bridge file. This developer
integration is not a one-click installed feature in V1.

`/ai question` asks locally; `/see question` requests a local screen capture;
`/aiclear` clears the local session. Every inference requires laptop approval.
Screen images do NOT go to Telegram. Generated answers are displayed locally,
then sent only after reviewing the exact answer and paired recipient together.
Telegram questions/answers still use Telegram's servers, so that interface is
not offline or fully local. The existing bridge's separately approved `/run`
commands remain outside JARVIS's AI abilities.

## Latency and laptop acceptance

No GPU throughput, first-token delay or total response time was measured on
the owner's laptop. JARVIS shows total response seconds after each answer.
First load and image encoding add work; CPU offload and running Maya at the
same time can make it much slower. This version shows a busy indicator rather
than streaming partial tokens. It does not promise instant responses.

Required before claiming working installation: Windows installer build and
EXE launch smoke test, owner-laptop text answer, image answer, preview/cancel,
private content check, clear session, server-off error, memory/latency check,
and optional bridge end-to-end test with approved owner identity.

## Developer build (not steps for the owner)

Python 3.12, Pillow and PyInstaller. `BUILD_EXE.bat` is for a Windows builder,
not an owner setup requirement. `.github/workflows/windows-build.yml` builds
on a Windows runner, runs tests, smoke-launches the EXE with a screenshot,
and compiles a per-user installer with Inno Setup. No administrator access,
auto-start task, telemetry or silent model download is added.

CI builds need repository authorization and an available runner/quota.
No paid usage or public repository is authorized by this source package.
Build dependencies are version-ranged, not a signed reproducible build.
Do not run unreviewed third-party workflows or put credentials in config/notes.

## Roadmap, not promises

- Local transcription and voice output.
- Confirmed, allowlisted Maya tasks rather than arbitrary model shell commands.
- Local memory with review/delete controls.
- Evaluate Spark-X2.5-4B as a separate text-chat option if native LM Studio runtime
  support becomes available. Not enabled, not verified by this package and not
  a substitute for the vision model.

## Verified setup/build references

- https://lmstudio.ai/docs/app
- https://lmstudio.ai/docs/developer/core/server
- https://lmstudio.ai/docs/developer/openai-compat/chat-completions
- https://huggingface.co/lmstudio-community/Qwen2.5-VL-3B-Instruct-GGUF
- https://pyinstaller.org/en/stable/operating-mode.html
- https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm

Personal settings belong only in local `config.json` and `notes.txt`; both are gitignored. Clean examples are included. Do not commit your original bridge source, tokens, owner IDs or pairing files.

## Visible monitoring controls

Both sensors start OFF every launch. Separate consent prompts explain each one.
Screen agent captures only the primary monitor, only while JARVIS is minimized,
and only once every 120 seconds. It skips parallel inference and pauses on an
inference error. A local popup shows useful nudges; dismiss or Pause all at any time.
Popups time out after 20 seconds. No proactive messages go to Telegram.

Camera samples are 320x240 CPU face-detection input. A result is stable only after
three consistent samples. "No face detected" does not prove you left the laptop.
It can miss faces or mistake objects for faces. It does not identify you, assess
emotion, attention, posture or health. Camera indicators may stay lit while ON.
Camera frames never go to the LLM. Consent of others in view is required.

Pause all stops future checks and requests camera release. Any in-flight local
model request may finish, but its proactive response is discarded. Closing stops
all session monitoring. No startup/background service is installed. Camera driver
release depends on the OS; verify the camera light goes off on your laptop.

The screen model's NO_NUDGE prompt is not a reliable private-content filter.
EVERY captured screen goes to local LM Studio. Pause before private messages,
passwords, banking, health or shared-screen work. No automatic exclusion rules.
45-minute wellness nudges are timers, never medical or behavioral assessments.
