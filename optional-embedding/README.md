# Shared local retrieval runtime

Isolated from working Laya because EmbeddingGemma requires Transformers 5. Source setup: use Python 3.12 in a separate environment, install requirements.txt with a matched Torch2.8.0/torchvision0.23.0/torchaudio2.8.0 CPU or CUDA build, set JARVIS_EMBEDDING_PYTHON to that interpreter. CI builds an isolated Windows runtime, then includes it beside JARVIS.exe as embedding-runtime/jarvis-embedding.exe in the main portable package. No separate interpreter setup is needed for that package. No listener or open network port.

Reviewed model setup downloads 1,525,787,092 bytes pinned to 914f7f89142e33e77833254d9c9b90c3cef7303b with SHA256 and byte checks. Google declares Apache 2.0 in the model card and developer guide; the model repo contains no separate LICENSE. Model weights are not bundled. It may use substantially more RAM/VRAM than phone quantized claims. The optional CI artifact uses CPU Torch; RTX3060 CUDA speed is not established by that artifact.

Inputs: one selected local folder, maximum100 chunks, hidden/symlink paths skipped, text first24kchars in6kchunks, media at most100MB. Default full768dimensions. 128d multimodal quality is weaker; compare before reducing. Model8K context limits media coverage. Current audio is first30seconds mono16kHz; video first30seconds/up to29sampled frames. Long video moment indexing is NOT yet implemented: this adapter provides clip-level candidates, not timestamps. Audio processor expects mono16kHz. No automatic private-data indexing, cloud context handoff or graph-note writes. Similarity links are suggestions, not explicit wiki links.

Keep the working exact and English static vault search until real owner-data comparisons pass. Tamil/Tanglish acceptance needs real inference and a labeled local corpus; synthetic adapter tests prove request/data mechanics, not language quality.

Sources:
https://huggingface.co/google/embeddinggemma-2
https://developers.googleblog.com/en/embeddinggemma-2-the-developer-guide/
https://pypi.org/pypi/sentence-transformers/6.1.0/json
