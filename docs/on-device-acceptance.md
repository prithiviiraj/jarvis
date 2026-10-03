# JARVIS experimental candidate: laptop acceptance

Source runner, not a finished installer. CI and synthetic UI replies do not prove your microphone, speakers, accent, live providers or audible latency. Keep the working build until this candidate passes on your Windows 11 x64 laptop. Python 3.12 required.

## Setup and privacy
1. Extract the whole source-runner ZIP to a writable folder. Run SETUP.cmd and wait for "Setup finished". Setup downloads verified voice assets as needed.
2. Run LAUNCH.cmd with headphones. Confirm microphone, cloud, camera and worker controls start OFF.
3. For local Chat/rounds/banter, load exactly one chat model in LM Studio and start its local server on port 1234. No cloud key or microphone consent is needed for local typed interaction.
4. For voice, open session setup and explicitly allow microphone. Half-duplex only: AEC and barge-in are not implemented.
5. Optional Groq: save the key only in app Settings. Reopen to see saved presence/timestamp, not the stored secret. Check the account billing page yourself. Automatic model selection is default; manual override is optional. Explicitly allow recognized/shared text disclosure for this session. A key alone is not Free-plan proof. No paid fallback is authorized.
6. Provider pool slots/routes are session-scoped. Saving does not start recording or model calls. Verify exact live model IDs, access, quota and billing. Never put keys in screenshots, reports or chat.

## New feature checks
- Typed Chat with Mic OFF: selected-profile reply, local-server error, cancellation and no late saved reply.
- Team Room: completed shared history, correct persona labels, long transcript scrolling, Pause all/close clear RAM history.
- Team rounds: 2 then 5 selected personas, ordered prior-reply context. Failure/switch/Pause/close must save no partial round.
- Banter session: OFF/default unchecked consent; topic, 2-12 turns, 2-30s gaps, maximum120seconds; local text only. Stop/close/switch/Pause must discard staged session. An in-flight local request can finish but may not save after Stop. These are personas on one model, not separate workers or sensed context.
- Notes: save to a private folder; inspect Markdown/recap before trusting cleared context. Cancel/failure must preserve history. No automatic Obsidian sync or LM Studio cache clearing.
- Mini orb: five borderless faces only; select, middle-drag, right-click restore/Pause/reduced-motion/close. Animation is voice state, not emotion or audio lip-sync.
- Timer: OFF by default. Declare activity, consent, interval15-180minutes. Real elapsed reminder while idle/visible; quiet/busy/hidden defer. Stop/panel-close/Pause/app-close clear. No game/screen/camera sensing.
- UI at your normal display scaling: all rail controls above taskbar, longer errors/captions/transcripts readable.

## Voice and performance measurements
- Mic/output: quiet, normal and loud levels. Hear all5assigned voices without clipping.
- Pause/close/switch: capture stops; no late audio; re-enable without duplicate capture; app close releases microphone.
- Accent: 20 English sentences in your normal Tamil accent. Record expected/recognized text and errors. English STT is not proof of Tamil-language support.
- Latency: at least20turns per route, end of speech to first audible reply; warm local and live Groq separately. Report p50/p95/max/cold-start. First WAV write or synthetic brain timing is not audible latency.
- Noise: fan/background speech, false triggers, missed turns and wrong transcripts.
- Game load: idle/listening/responding CPU/memory and responsiveness. Windows CI callback Hz is not display FPS or laptop gaming performance.
- Offline: after assets install, local routes with LM Studio should work without network. Cloud fails safely without access/consent/network; no paid fallback.

Record hardware/audio devices, commit, model IDs, route, scenario, turn count, timings, resource use and failures. Keep hardware-dependent checks OPEN until results exist. No camera/screen/browser executor/Laya model/background24/7work is active in this candidate.
