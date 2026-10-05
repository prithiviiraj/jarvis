# Optional-engine experiments - October 6, 2026

The CI118 Windows candidate is unchanged. These experiments are not UI features or accepted laptop behavior.

## Gate results

- Model2Vec potion-base-4M: MIT model card; pinned assets 15.80MB. Linux CPU load191ms and six easy English search queries6/6. Harder negation/secrecy/Tamil fixture3/6, bothTamil queries wrong. Optional adapter is English-only and returns candidates, never permissions, actions or automatic answers. No private vault data used. No automatic download/import dependency. Exact vault search remains default.
- LFM2.5-350M Q4_K_M:229.31MB, CPU load314ms; tiny classifier2/7correct. Rejected for routing/default use. LFM Open License v1.0 has a $10Mcommercial-revenue restriction; not plain Apache. No model packaged.
- SmolVLM2-256M Video Instruct: Apache2.0. Default image splitting attempt killed before inference reply. Bounded512px one-frame repeat61.2seconds for12tokens, guessed an absent white outline. Fails live1fpsgoal here. This is a synthetic frame smoke, not a video-understanding accuracy benchmark, live camera or owner-laptop evidence. No vision engine adopted.
- Maya MCP0.6.1: MIT. Pinned upstream source593dry-runtests passed;81real-Maya tests deselected. Actual stdio protocol handshake,71tools and offline health confirmed. No Autodesk Maya installed/session/scene tested. Raw-script tools advertised despite disabled execution; adapter rejects them, file operations/deletion/import/export and unlisted tools independently. Allowlisted effects require exact one-use review; adapter returns reviewed parameters and executes nothing itself.
- PocketTTS: MIT code; official weight catalog gated, pinned weight request401without authenticated access. Deliberately omitted pending user's model-access/terms decision. No bypass, community mirror or voice cloning performed.

## Sources

https://huggingface.co/minishlab/potion-base-4M
https://github.com/MinishLab/model2vec
https://huggingface.co/LiquidAI/LFM2.5-350M-GGUF
https://docs.liquid.ai/lfm/models/lfm2-350m
https://huggingface.co/HuggingFaceTB/SmolVLM2-256M-Video-Instruct
https://huggingface.co/blog/smolvlm2
https://github.com/GimbalGoats/GG_MayaMCP
https://github.com/kyutai-labs/pocket-tts
https://huggingface.co/kyutai/pocket-tts

All numbers above are this environment's small research fixtures, not user's laptop measurements. Physical audio/Tamil/AEC/provider latency gates remain open.
