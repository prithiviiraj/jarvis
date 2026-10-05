# Reply latency UX requirements, not implemented claims

Priorities for future work:
- Stream persona replies so useful text appears as generated.
- Offer a narrowly consented local-model prewarm, without disclosing private conversation or enabling a cloud route.
- Keep floating face listening/thinking feedback visible during generation, with cancellation and stop.

Current state: local typed Chat uses one selected/routed persona and sends thinking state; non-streaming local request. No model request/prewarm starts at launch. Face state is not actual display FPS or audible latency measurement. No cloud request may be introduced as a hidden warmup. Streaming must discard cancelled generations, avoid late saves and preserve real provider/model labels.

Normal messages should receive ONE relevant reply. Full-team banter is separate, rare, short and opt-in. Default2turns; typical2-4. No screen/game/camera observation is implied.

## Build 68: explicit local-model warmup
Settings > Brain & APIs now has Warm local model. Each click reviews the exact
fixed greeting ("Say ready in one word.") before sending it to the loaded local
LM Studio chat model. It never runs at startup, never uses history or cloud,
and never reads provider keys. It shares the local inference gate with chat
and team. Stop voice first; if the gate is busy the request fails rather than
queueing behind a reply. Pause all cancels it. The displayed seconds measure
only that fixed local inference, not STT, TTS, or audible response latency.
A warmed model may help avoid a later cold load, but no laptop speed improvement
is claimed without the owner's real-model measurement. Restart loses the status.

## Build 71: stage diagnostics, not an audible-latency promise
Session-only last voice turn timings now survive the bridge and appear in
Settings > Voices. STT, first model text, first queued clause, and whole software
turn are measured from the end of an utterance delivered by the microphone.
First PCM output write is recorded only after the output adapter's first write
succeeds. It is not sound heard at the physical speaker and does not include the
VAD endpoint wait. Paused/stale turns do not publish timing; missing output
callbacks show Not measured. Pause all clears the session result. No conversation
text/audio is added to these numeric diagnostics and they are not stored on disk.
The frozen five-voice acceptance uses real STT/Kokoro synthesis with test input
and output adapters; real hardware, owner accent and real-model speed stay open.

Build 77 exposes session-only end-of-utterance silence presets: Balanced800ms
unchanged default, Fast480ms, Deliberate1216ms (32ms frame quantization).
Change only while microphone/voice is stopped. Fast may split a natural pause;
owner accent and hardware must be tested. These are silence thresholds, not
response-time promises. Voice processing metrics begin after endpoint detection,
so do not include this wait. No microphone starts or settings persist at launch.
