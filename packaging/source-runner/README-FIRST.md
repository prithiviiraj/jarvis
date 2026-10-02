# JARVIS EXPERIMENTAL source runner

Personal testing build, not a frozen EXE or finished installer. Python 3.12 is required on Windows 11 x64. Packages are installed on your own machine from PyPI; this ZIP does not contain their DLLs/wheels. Native Phonemis frontend/resources and notices are bundled and hash-verified. Voice models download only during setup. No key, microphone, cloud, camera or agent worker starts automatically.

1. Extract the whole ZIP to a writable folder, not inside the ZIP viewer.
2. Double-click SETUP.cmd. It creates a private .venv, installs dependencies and downloads about 500 MB of checksum-verified models to your Windows user-data folder. Wait for "Setup finished".
3. Double-click LAUNCH.cmd. Use headphones. No AEC or barge-in is implemented; this is half-duplex.
4. Local option: start LM Studio, load exactly one chat model, start its server on port 1234. Voice setup: allow microphone this session, leave Groq OFF, then Enable voice.
5. Groq option: Settings > Usage & Billing > Manage Groq API key. Enter your key there and Save securely. Never put keys in chat, this README, scripts or config files. Check your account at console.groq.com is on the Free plan. In Voice setup, allow recognized text disclosure to Groq and confirm Free plan. Groq model selection is Automatic, choosing an active production chat model from a bounded allowlist (GPT-OSS20B first, then GPT-OSS120B, then listed Llama3.1/3.3 chat IDs). It never infers billing from model access. Optional manual override is hidden: open it, paste an active ID, press Enter to lock; unlock or hide it to return to Automatic. Test Groq text connection sends only a fixed greeting; then tick microphone consent and Enable voice.

## Say this to test
- "Hello, who are you?"
- "Tell me a short joke."
- Switch to NOVA, KAI, LYRA and DEX and repeat. Each uses a different locked voice.
- Press Pause all during a reply. Audio and capture must stop. Closing must release the microphone.

Groq sends recognized text, not microphone audio. Cloud consent is session-only. The app does not automatically verify billing and will not select a paid fallback. Real Groq replies require your own key and account; CI synthetic replies are not proof of a live provider.

## Network problems (including Jio)
Setup uses bounded pip/download retries and resumes checksum-bound model partials. After a failed model download it retries with certifi trusted roots instead of Windows default roots. TLS certificate checks stay ON. If a certificate/network error remains, rerun SETUP.cmd or use a different network/hotspot. Do not use --trusted-host, disable TLS, or paste secrets into a terminal command. Downloads never install a file whose pinned hash fails.

## Honest limits
125+ source tests and cloud fixtures prove software mechanics, not your microphone, speakers, Tamil accent, game performance or 1-second response. Prior fixture first WAV write was 1.53-1.70s with a synthetic brain. No live provider or audible latency acceptance is claimed. No background agent jobs/tools, hands-free agent-name switching, typed chat, tray/autostart or AEC/barge-in are complete. Phase 1 is OPEN. Follow docs/on-device-acceptance.md and report results without keys.


## If the Groq connection test fails

Both GROQ-DIAG.cmd and GROQ-DIAG.py are included beside LAUNCH.cmd. Double-click GROQ-DIAG.cmd after setup. Diagnostic v4: confirm Free plan and type YES to allow one models lookup and at most one fixed greeting using an automatically selected listed production chat model. It prints only sanitized categories, count and known/selected chat IDs, never raw response/key. Omitted active fields are supported; explicit inactive models are rejected. App and diagnostic use the same descriptive JARVIS User-Agent. Send only the printed result codes, never the key. Sanitized codes are also saved to %LOCALAPPDATA%\JARVIS\logs\groq-diagnostic.json. A successful diagnostic proves a text reply, not microphone/audio acceptance. If you exposed a key in a video or chat, revoke it at the Groq console and save a replacement only in app Settings.

This build includes automatic-model selection and an optional hidden manual override. A freshly pasted key stays visible after Save with Saved status, until the dialog closes. Stored keys are never read back into the field. Keep keys out of screenshots/videos.

GPT-OSS requests use low reasoning effort and a bounded1024 total completion-token cap, including reasoning. Reasoning text is excluded and never displayed/spoken as an answer. The text-test button shows Testing, then full success/failure feedback. This text test does not speak or start the microphone.

Download models opens a visible window: Starting/cache checksum checks, an activity meter and current-file received MiB, then Ready or Failed/Cancelled. It is not an overall-percent meter. Only missing files download; verified caches are reused. Cancel keeps verified files and eligible partial downloads.

Session setup choices are remembered across voice profiles in memory only. Switching stops/releases the previous microphone/runtime; press Enable voice to start the selected voice. It does not start recording automatically. Pause all or closing the app clears remembered permission; next launch starts OFF. JARVIS keeps the team-leader identity but does not claim real background delegation/tools.

Local Whisper uses a short roster-name prompt (JARVIS/NOVA/KAI/LYRA/DEX) as a transcription hint. This is not a guarantee for accent/name accuracy; captions remain the actual transcript. Team profiles know the roster and ask for clarification for garbled names instead of inventing a person.
