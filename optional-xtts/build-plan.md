# Separate optional XTTS runtime, not default portable

Incomplete build plan. No claim it is installed or working.

- PyPI metadata verified WindowsCPython3.12wheels: Torch2.6.0 204,120,469bytes, Torchaudio2.6.0 2,449,191bytes, coqui-tts0.27.5 universal862,766bytes. Transitive dependencies add more. These sizes prove availability, not runtime compatibility or synthesis. Use separate pinned runtime; verify CPU build has no CUDA dependency fanout before packaging.
- Build separate optional onedirEXE, not bundled into defaultJARVIS. Include all code/binary licences and source obligations. Modelweights not included.
- Keep model download inside an explicit local UI review of CPML(noncommercial model AND outputs), size, pinned hashes and targetfolder. Never setCOQUI_TOS_AGREEDwithout user's review.
- Use installed presetCraigGutsyfirst; no implicit cloning. A voice-reference workflow needs explicit rights and WAVvalidation.
- Run only127.0.0.1, fixedendpoint, no arbitrarypathorhost input. Prototypeclient prevents redirects/proxies and rejectsTamil,oversize/nonPCMresponses.
- Realengineacceptance: actualEnglishsentence -> PCM24kHz; fivevoiceprofileintent may use existingpresetmapping if verified, not pretendfiveclones; CPUfirstclause/wholeturntime and GPUmemory when relevant. Close/restart must releaseTorch/audio resources. Physicalspeaker/mic proof separate.
- User has6GBVRAM/16GBRAM from profile orientation, needs livehardwarecheckbefore choosingGPU. DefaultKokorostayssafeifXTTSoffline/unsupported; don't silentlychange engine aftererror.
- Source/docs: https://github.com/idiap/coqui-ai-TTS ; https://coqui-tts.readthedocs.io/en/latest/server.html ; https://huggingface.co/coqui/XTTS-v2/blob/main/LICENSE.txt . Model.pthaloneshows1.87GB https://huggingface.co/coqui/XTTS-v2/blob/main/model.pth .
