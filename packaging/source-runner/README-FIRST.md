# JARVIS EXPERIMENTAL source runner

Personal testing build, not a frozen EXE or finished installer. Python 3.12 is required on Windows 11 x64. Packages are installed on your own machine from PyPI; this ZIP does not contain their DLLs/wheels. Native Phonemis frontend/resources and notices are bundled and hash-verified. Voice models download only during setup. No key, microphone, cloud, camera or agent worker starts automatically.

1. Extract the whole ZIP to a writable folder, not inside the ZIP viewer.
2. Double-click SETUP.cmd. It creates a private .venv, installs dependencies and downloads about 500 MB of checksum-verified models to your Windows user-data folder. Wait for "Setup finished".
3. Double-click LAUNCH.cmd. It opens the floating faces first. Right-click a face and choose Open workspace for setup/chat/settings. Use headphones. No AEC or barge-in is implemented; this is half-duplex.
4. Local option: start LM Studio, load exactly one chat model, start its server on port 1234. Voice setup: allow microphone this session, leave Groq OFF, then Enable voice.
5. Groq option: Settings > Usage & Billing > Manage Groq API key. Enter your key there and Save securely. Never put keys in chat, this README, scripts or config files. Check your account at console.groq.com is on the Free plan. In Voice setup, allow recognized text disclosure to Groq and confirm Free plan. Groq model selection is Automatic, choosing an active production chat model from a bounded allowlist (GPT-OSS120B first, then GPT-OSS20B, then listed Llama3.1/3.3 chat IDs). It never infers billing from model access. Optional manual override is hidden: open it, paste an active ID, press Enter to lock; unlock or hide it to return to Automatic. Test Groq text connection sends only a fixed greeting; then tick microphone consent and Enable voice.

## Say this to test
- "Hello, who are you?"
- "Tell me a short joke."
- Switch to NOVA, KAI, LYRA and DEX and repeat. Each uses a different locked voice.
- Press Pause all during a reply. Audio and capture must stop. Closing must release the microphone.

Groq sends recognized text, not microphone audio. Cloud consent is session-only. The app does not automatically verify billing and will not select a paid fallback. Real Groq replies require your own key and account; CI synthetic replies are not proof of a live provider.

## Network problems (including Jio)
Setup uses bounded pip/download retries and resumes checksum-bound model partials. After a failed model download it retries with certifi trusted roots instead of Windows default roots. TLS certificate checks stay ON. If a certificate/network error remains, rerun SETUP.cmd or use a different network/hotspot. Do not use --trusted-host, disable TLS, or paste secrets into a terminal command. Downloads never install a file whose pinned hash fails.

## Honest limits
Source tests and controlled Windows pixels verify software mechanics, not your microphone, speakers, Tamil accent, game performance or one-second audible response. Local typed Chat, team rounds, bounded banter and declared-activity timer are implemented below. No independent background jobs/tools, screen/camera sensing, hands-free agent-name switching, AEC or barge-in are complete. Phase1 is OPEN. Use docs/on-device-acceptance.md and report results without keys.

## If the Groq connection test fails

Both GROQ-DIAG.cmd and GROQ-DIAG.py are included beside LAUNCH.cmd. Double-click GROQ-DIAG.cmd after setup. Diagnostic v4: confirm Free plan and type YES to allow one models lookup and at most one fixed greeting using an automatically selected listed production chat model. It prints only sanitized categories, count and known/selected chat IDs, never raw response/key. Omitted active fields are supported; explicit inactive models are rejected. App and diagnostic use the same descriptive JARVIS User-Agent. Send only the printed result codes, never the key. Sanitized codes are also saved to %LOCALAPPDATA%\JARVIS\logs\groq-diagnostic.json. A successful diagnostic proves a text reply, not microphone/audio acceptance. If you exposed a key in a video or chat, revoke it at the Groq console and save a replacement only in app Settings.

This build includes automatic-model selection and an optional hidden manual override. A freshly pasted key stays visible after Save with Saved status, until the dialog closes. Stored keys are never read back into the field. Keep keys out of screenshots/videos.

GPT-OSS requests use low reasoning effort and a bounded1024 total completion-token cap, including reasoning. Reasoning text is excluded and never displayed/spoken as an answer. The text-test button shows Testing, then full success/failure feedback. This text test does not speak or start the microphone.

Download models opens a visible window: Starting/cache checksum checks, an activity meter and current-file received MiB, then Ready or Failed/Cancelled. It is not an overall-percent meter. Only missing files download; verified caches are reused. Cancel keeps verified files and eligible partial downloads.

Session setup choices are remembered across voice profiles in memory only. Switching stops/releases the previous microphone/runtime; press Enable voice to start the selected voice. It does not start recording automatically. Pause all or closing the app clears remembered permission; next launch starts OFF. JARVIS keeps the team-leader identity but does not claim real background delegation/tools.

Local Whisper uses a short roster-name prompt (JARVIS/NOVA/KAI/LYRA/DEX) as a transcription hint. This is not a guarantee for accent/name accuracy; captions remain the actual transcript. Team profiles know the roster and ask for clarification for garbled names instead of inventing a person.

Automatic prefers listed GPT-OSS120B for answer quality; listed20B is used when120B is absent. No speed/quality guarantee. When listed20B is available, a transient timeout/rate-limit/server failure on120B before any answer text may fall back once to20B. The actual responding model is reported. No failover after text starts, no model mixing, and no fallback for permission/auth/model/empty-token errors. Diagnostic sends one greeting only and never retries it. Optional manual override lets the owner explicitly choose listed20B for comparison.

Reopening Settings checks Windows Credential Manager for key presence and its saved timestamp, without decoding/displaying the stored secret. Saved key present / no re-paste needed is distinct from an empty entry field. Only a newly pasted key stays visible. Saving never enables cloud or microphone automatically.

Shared conversation: completed profile-labelled turns are bounded and RAM-only. Profile switches keep it; Pause all/close clear it. With cloud session consent, recent shared conversation can be disclosed with recognized text. It does not observe your screen/game/camera. There are no independent workers.

Provider pool candidate: up to5 slots from your own legitimate Groq/Gemini/NIM accounts or LM Studio. Per-profile primary/fallback routes and exact model IDs are session-only. No account is created and no call starts on Save. Confirm disclosure of shared recent conversation and Free access for each cloud slot, then explicitly Enable the selected voice. Keys use allowlisted Windows Credential Manager targets. Pauseall clears pool routes/consents, not saved keys. Fallback is pre-text only, stops for nonretryable auth/permission errors, never mixes answers. Same-project Gemini keys share quota; no quota multiplication/evasion. NIM developer APIs are prototyping access. Gemini free-tier data-use policy may differ from paid. Models/account access and billing have NOT been live tested. Original local/Groq setup remains available.
Docs: https://ai.google.dev/gemini-api/docs/openai ; https://ai.google.dev/gemini-api/docs/rate-limits ; https://ai.google.dev/gemini-api/docs/pricing ; https://docs.api.nvidia.com/nim/re/docs/product ; https://docs.api.nvidia.com/nim/reference/llm-apis

Save notes + clear: explicitly pauses voice, lets you choose a private local folder, saves Markdown conversation plus a short extractive recap, flushes and atomically finishes the file, then clears shared app context. A failed/cancelled save preserves memory. This is not an AI factual summary, automatic Obsidian sync, unlimited memory, or a command to clear LM Studio's own server cache. Notes contain private conversation: choose the folder with that in mind.

Floating faces: Mini orb hides the workspace and opens five transparent borderless faces. Left-click selects a profile; middle-drag moves; right-click offers Open/Pause/Reduced motion/Close. Idle/listening/thinking/speaking states animate the eyes/mouth and enlarge the selected speaking face. These are app states, not detected emotions or real lip-sync. Deadline pacing targets60Hz; CI callback timing is not measured display FPS or laptop performance.

Typed local chat: pause voice, open Chat, type and Send local. Requires exactly one loaded LM Studio chat model and its local server. No microphone, speech assets, cloud key or provider request is used. Team Room shows completed shared conversation, bounded in RAM; Pause all/close clear it. A cancelled/profile-switched reply is discarded. Not background work or sensing.

Browser proposal foundation (experimental, not connected to workspace): model-free contract accepts at most20 supplied nonsensitive controls from a15-second snapshot under an exact HTTPS host scope. Model output can only select observed offered click/scroll/wait/done/blocked choices; cannot supply selectors/code/text or execute. All proposals require review and DONE is not proof of completion. No browser driver, sensing or model is loaded. Laya quality/hardware and a separate reviewed executor remain untested/unimplemented.

Multi-profile round: Team Room lets you choose2-5profiles and Start round. UI order is JARVIS, NOVA, KAI, LYRA, DEX. Each uses the same local LM Studio model with its own persona, sees actual prior replies, and records only when the entire round succeeds. These are text replies, not distinct live workers or audible voices. No background/autonomous rounds.

Session timer panel: OFF on launch. Session timer opens a separate local panel; declare gaming/working/watching videos, choose15-180minutes, check session consent, Start timer. Suggestions stay in this panel as text, deferred while quiet/voice busy/workspace minimized. Stop, closing the panel, Pause all or closing app clear it. No popup/audio/cloud/screen detection. This is a declared-activity timer, not proactive agents observing you.


Bounded local banter: Team Room > Banter session. OFF until you enter a topic, select2-5personas, allow session consent and Start. Default2short turns with3-second gaps; typical use2-4turns. Bounds2-12turns and2-30seconds. Keep it short. Session checks a120second limit; a local in-flight request may take its timeout to return, then is discarded if stopped/expired. One local model, text only, shared supplied context, no mic/cloud/tools/screen/game/camera. Stop/panel-close/Pause/profile-switch/app-close discard all staged session turns. Success saves the full session. No autonomous24/7activity or audible speech is claimed.


Glass-dark polish: lightweight dark-blue surfaces, window-wide97percent opacity and eased button hover transitions. No live backdrop blur, GPU compositor or new graphics dependencies are added. Native window shadows depend on Windows; no shadow/render-performance guarantee. Reduced motion applies to floating face expressions.

Typed Chat moderator: default Pick one relevant persona. Direct address at the start selects a name; otherwise bounded keyword rules choose one specialist, with mixed/general topics going to JARVIS. One local request only. Uncheck to keep the selected persona. This is deterministic text routing, not human-level intent understanding or voice auto-switching.
