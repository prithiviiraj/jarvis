# Speech screening - 2026-10-02

Selected for experimental pipeline: faster-whisper base multilingual CPU INT8 (measured clean fixture only), Silero VAD current MIT ONNX model, Windows installed SAPI emergency voice (no voice redistribution). No final TTS winner. No paid/cloud STT.

| Candidate | Verified source | Finding and status |
|---|---|---|
| Kokoro-82M | https://huggingface.co/hexgrad/Kokoro-82M ; https://github.com/hexgrad/kokoro ; https://github.com/hexgrad/misaki | Apache weights/code do not clear the whole Windows stack. English phonemizer supports an eSpeak fallback; eSpeak is not silently approved/bundled. Need voices/transitive audit and real listening test. |
| Chatterbox Turbo | https://huggingface.co/ResembleAI/chatterbox-turbo | MIT card, CUDA examples. Full Windows dependency + seed voice rights audit not done. No GPU benchmark run on available CPU-only cloud host. |
| Qwen3-TTS 0.6B | https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice | Apache-2.0 card, CUDA examples. No run or memory-fit guarantee. |
| Piper current | https://github.com/OHF-Voice/piper1-gpl | GPLv3 code. Not adopted as emergency fallback; SAPI avoids introducing this redistribution issue. Voices each require separate license check. |
| Silero VAD | https://github.com/snakers4/silero-vad ; https://raw.githubusercontent.com/snakers4/silero-vad/master/LICENSE | MIT. Current ONNX tested in streaming 512-sample frames. This is VAD, not acoustic echo cancellation or noise suppression. |
| Parakeet TDT v3 | https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3 | CC BY-4.0. Not adopted; no owner policy exception inferred. No run on current host. |

Current loop is half-duplex: it suspends microphone processing while the brain and installed voice reply. Headphones required for first hardware test. Barge-in/AEC/noise suppression are incomplete, so Phase1 is not done. The cloud fixture endpointer splits at internal pauses; sentence-aware turn detection is unproven.
