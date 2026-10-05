# Phase1 work in progress
Code additions: provider failover controller; conversation state controller; Silero ONNX adapter; bounded continuous microphone worker/endpointer; local STT; installed Windows SAPI; half-duplex runtime; first-run pinned hash-verified downloads; optional provider presets and local model discovery.

Linux suite current: 102 discovered, 101 pass/1 Windows-only skip. Public Windows streaming baseline remains 72 cases at https://github.com/prithiviiraj/jarvis/actions/runs/36999121719 . Native G2P evaluation passed MSVC and 74 upstream tests separately at https://github.com/prithiviiraj/jarvis/actions/runs/37001910971 . Neither test count measures full product completion. Real localhost HTTP success/429/redirect-refusal tested. Download hash/consent logic tested, actual pinned HTTPS model downloads passed in this cloud host. Real ONNX VAD inference and Whisper INT8 transcriptions measured, JSON under benchmarks. These are clean English fixtures, not the owner's hardware/accent.

No blind human voice preference test, noise suppression, echo cancellation, physical barge-in, provider-key onboarding, final voice preference or installed Windows voice acceptance yet. Mic/SAPI untested here, so Phase1 is NOT complete. Advanced UI and agents have not begun. Streaming SSE/clauses are now implemented with bounded queues and tested against a localhost synthetic server; audible streaming on physical hardware remains unrun.

Half-duplex test mode suspends mic processing during the brain response and local speech so the assistant cannot transcribe its own reply. This is NOT echo cancellation and not the roadmap's final barge-in feature. Headphones required for first hardware test. No recordings saved. Model downloads require explicit approval; verified files survive retry. Bound hash/URL/cap partial-file resume added; exact206 offset/full SHA validated. Live immutable HTTPS tokenizer resumed from100000 bytes with206 and full hash match.

Cloud only: owner's laptop untouched. Router tests prove control flow/HTTP handling, not Gemini/NIM/Groq live access. No provider keys used. Groq is the owner's intended free provider, not xAI Grok. Groq requires a verified Free-tier account-plan gate; key presence alone does not prove free billing. No paid credits or upgrades allowed. Models are not bundled.

Historical Windows baseline run2: https://github.com/prithiviiraj/jarvis/actions/runs/36998317529 passed 49 source/OS tests, real SAPI synthetic-file generation, preview launch/pixel inspection, pinned downloads and Whisper/Silero fixture inference. It did not prove default physical playback or mic. Streaming additions passed source checks and fixture run3: https://github.com/prithiviiraj/jarvis/actions/runs/36999121719 . Actual native Kokoro five WAV evaluation passed https://github.com/prithiviiraj/jarvis/actions/runs/37002579214 . Windows no-PyAV fork source/fixture passed87 cases at https://github.com/prithiviiraj/jarvis/actions/runs/37003009067 . Optional cancellable candidate speaker is unit tested only; physical output remains unrun. Candidate not chosen or installed.

Build 72 adds truthful local-vault search boundaries: deterministic sorted
visible Markdown traversal, at most 500 scanned notes, 30 results and 0.75s.
The bridge/UI reports scanned count, unreadable/oversized skips and partial
reasons. No matches in a partial scan never means the note is absent. Hidden
and linked notes remain excluded even on complete scans. Disconnect clears
these results. Search/reads still never enter chat-model context automatically.

Build 74 replaces native browser-confirm dialogs for vault connection and new
notes with visible in-app exact-folder/name/text reviews and Confirm/Cancel.
Changing fields invalidates their review; disconnect clears it. The backend
still checks the exact current vault/name/text and uses exclusive create, so
existing notes cannot be overwritten. Native Windows acceptance operates only
on a temporary test vault, never the owner's files.

Build 79 replaces browser permission/command browser dialogs with visible
in-app review and Confirm/Cancel. Every exact prepared destination/search/scroll
is still reviewed; changed pending command or command text invalidates its
review. Stop browser clears review. No typing/sending/payment/upload action.
Native acceptance tests permission and command cancellation without navigation;
frozen connector acceptance retains actual isolated Edge observed-link proof.

Build80 gives the selected voice engine a visible download review: Kitten
about28MB voice assets plus shared recognition if missing, Kokoro roughly500MB
total. Exact reviewed_engine is checked by the bridge; engine selection is
locked during setup. Review/Cancel starts no mic or download. Native acceptance
cancels both engine reviews, restores Kokoro, captures native browser reviews.

Build83 fixes stale speech readiness: changing engine invalidates previous
Ready state without checking/downloading or starting mic. Explicit checks name
the selected engine plus shared assets. Ready means checksum-verified assets,
not physical playback or complete voice-runtime acceptance.

Build84 binds reviewed scroll commands to an existing ready public HTTPS page.
No page/no ready state refuses preparation. A page URL change before execution
refuses scrolling; observed-link navigation still rechecks link membership.
Exact current page is displayed in review. This is a URL binding, not a content
freeze: a page can change its content at the same URL.

Build85 adds cooperative STT cancellation before/between yielded segments and
closes the segment iterator. Pause discards cancelled recognition before a model
or action handler. A running native inference call is not force-interrupted.
CI diagnostic60second timer is now scoped to each voice turn, not cumulative
model downloads+five turns, so its stackdump cannot imply a long single turn
just because the full acceptance run took a minute.

Build86 consumes explicit browser requests locally when mode is OFF or the
operation is unsupported. Unsupported vault writes/incomplete read/search
commands stay local too; no silent model fallback. Vault commands recognize
allfive addressed personas and preserve exact Markdown paths. Ordinary
conversation about a browser/vault is not reclassified as an action.

Build87 connects an experimental local Laya proposal client, session opt-in,
loopback127.0.0.1:8000. This build does NOT install a Laya model or server.
Goals/host/up to20 observed link labels go only to that explicitly enabled local
server; no screenshot/page text/accountkeys. Link/scroll proposals map into
existing exact review, never autonomous execution. Stop and page/link changes
reject late replies; deterministic commands override outstanding suggestions.
Model DONE/WAIT/BLOCKED is not task completion. Typing/forms/payment/upload
remain unavailable. Endpoint fixtures validate wiring, not actualmodelquality.

Build90 prepared from laptop feedback: one-button account key/save/test remains;
empty-unsaved-key or active mic/reply blocks test with visible prerequisite.
Gemini Omni/video/audio IDs are refused for text greeting and excluded from
Automatic. HTTP429 shows rate-limit OR quota, no daily-reset/billing inference.
User0.5s first-audio goal remains unproven. Balanced endpoint800ms and Fast480ms
precede telemetry's STT/model/PCM timings; PCM write is not sound heard.
OptionalCPUruntime packaging removes only two upstreamNumPy test maps omitted
by artifact uploader, then computes the actual shipped-file manifest.
Actual laptop screenshot recognized "Hey, Kai. Can you hear me?" while previous
DEX replied. Build90 parses punctuation after Hey/Hi/Hello and tests this exact
transcript so the explicit KAI address overrides previous DEX.
