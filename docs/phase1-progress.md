# Phase1 work in progress
Code additions: provider failover controller; conversation state controller; Silero ONNX adapter; bounded continuous microphone worker/endpointer; local STT; installed Windows SAPI; half-duplex runtime; first-run pinned hash-verified downloads; optional provider presets and local model discovery.

Linux suite: 72 discovered, 71 pass/1 Windows-only skip. Real localhost HTTP success/429/redirect-refusal tested. Download hash/consent logic tested, actual pinned HTTPS model downloads passed in this cloud host. Real ONNX VAD inference and Whisper INT8 transcriptions measured, JSON under benchmarks. These are clean English fixtures, not the owner's hardware/accent.

No blind human voice preference test, noise suppression, echo cancellation, physical barge-in, provider-key onboarding, final voice preference or installed Windows voice acceptance yet. Mic/SAPI untested here, so Phase1 is NOT complete. Advanced UI and agents have not begun. Streaming SSE/clauses are now implemented with bounded queues and tested against a localhost synthetic server; audible streaming on physical hardware remains unrun.

Half-duplex test mode suspends mic processing during the brain response and local speech so the assistant cannot transcribe its own reply. This is NOT echo cancellation and not the roadmap's final barge-in feature. Headphones required for first hardware test. No recordings saved. Model downloads require explicit approval; verified files survive retry. Partial-file resume is not implemented yet.

Cloud only: owner's laptop untouched. Router tests prove control flow/HTTP handling, not Gemini/NIM/Grok live access. No provider keys used. Grok paid credits must not be enabled without an owner cost decision. Models are not bundled.

Windows baseline run2: https://github.com/prithiviiraj/jarvis/actions/runs/36998317529 passed 49 source/OS tests, real SAPI synthetic-file generation, preview launch/pixel inspection, pinned downloads and Whisper/Silero fixture inference. It did not prove default physical playback or mic. Streaming additions postdate that baseline and require their own Windows rerun.
