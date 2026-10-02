# JARVIS experimental voice workspace: device acceptance

CI is not microphone or speaker acceptance. Run these on the owner's Windows 11 RTX 3060 laptop before calling Phase 1 complete. No installer should be presented as production ready until the connected source build passes.

## Setup
- Install the audited native frontend and verified speech assets. Start LM Studio with exactly one chat model and its server on port 1234.
- Launch `python -m jarvis --workspace-preview`. Microphone, cloud, camera and workers must start OFF.
- Connect headphones. Enable microphone only after ticking session consent. This build is half-duplex: no AEC or interruption-based barge-in is claimed.
- Optional Groq: save key through Settings > Usage & Billing. Check the account's billing page for Free plan, enter a current model ID, and explicitly allow recognized text disclosure for this session. Audio stays local. A key alone is not plan proof. No paid request is authorized.

## Required measurements
- Mic/speaker: hear a reply without clipping; repeat at quiet, normal and loud speaking levels. Verify five profiles speak with their assigned voices.
- Pause, close, profile switch: mic capture stops and no late response plays. Re-enable works without duplicate capture. Closing must leave no microphone process.
- Accent: read 20 English sentences in your usual Tamil accent. Record expected vs recognized text and errors. Tamil-language support is not claimed by the English STT setup.
- Latency: measure at least 20 turns from the end of user speech to the first audible reply, separately for warm local and Groq sessions. Report p50, p95, maximum and cold start. Target 1 second is NOT passed by synthetic timing or by synthesis-only benchmarks.
- Noise: repeat with fan/background speech. Note wrong transcripts, false triggers and missed turns.
- Echo/barge-in: NOT implemented. Keep headphones/half-duplex. Do not claim these checks pass merely because playback capture is suppressed.
- Offline/local: disconnect network after models are installed; local chat works if LM Studio is running. Groq fails safely without key, consent, Free-plan confirmation, or network. No paid fallback.
- CPU/memory/gaming: measure idle/listening/responding memory and CPU while a game runs. No RTX acceleration/performance claim from CPU CI.
- UI: all views, Settings, captions and five team cards fit above the taskbar at your display scaling. Review longer transcripts and errors.

Record device, audio devices, build commit, exact model IDs, scenario, counts, timings and failures. Leave hardware-dependent items open until these results exist.
