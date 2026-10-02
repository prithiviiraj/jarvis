# Phase 0 audit - 2 October 2026
Audit only. No source mutation, new foundation build or new installer yet.

## Current state
Public repository commit dc633dffe492b46da7e552f817b0564651091aad. Source is inside versioned ZIPs; root README stale. Extracted public 0.3.0 and reran suite: 32 discovered, one skipped (private bridge unavailable). This corrects prior public 41/41 shorthand.

## Reuse
- core.py: loopback client, bounded ephemeral conversation, no redirect/proxy, screenshot sizing, empty reply retry. Preserve local privacy boundary; separate provider router rather than weakening this client.
- voice.py: bounded mic capture, no files, CPU local Whisper, Windows SAPI worker and cancellation. Useful interfaces, not an always-on conversational pipeline.
- monitor.py: screen schedule generations/cooldown and local camera presence release paths. Presence is not identity verification. Neither is reboot-persistent scheduling.
- startup.py and installer.iss: explicit startup and per-user Setup EXE/shortcuts/uninstall cleanup. Reuse after upgrade/storage tests.
- app.py: consent and safety behavior, Enter binding. Replace monolithic layout/controller separation; UI is not the requested orb/tray/agents system.
- bridge_adapter.py: gated existing external bridge adapter only; not a standalone messaging tool. Exclude from Phase0/default runtime.

## Missing
Continuous VAD/endpointer, denoise/AEC/barge-in, STT benchmark, streaming TTS, provider health/failover, Credential Manager, agent registry/parallel workers, durable scheduler/memory, Obsidian, tray/hotkey/orb, telemetry/game mode, watchdog, backups/update signing, tool permission boundary. No guarantee of idle targets, no-stutter or 1s latency from existing tests.

## Foundation proposal
src/jarvis/{config,security,diagnostics,models,brain,audio,ui,agents,memory,scheduler,tools}; tests/{unit,integration,windows}; docs/{audit,roadmap,benchmarks}; THIRD_PARTY.md; packaging/. One stable Setup EXE naming scheme, roadmap phases separate from old app versions.
Per-user writable state in LocalAppData, not beside installed EXE. Versioned config with migrations/validation, safe defaults; separate model cache; Windows Credential Manager adapter and fake test backend; redacted rotating logs (no transcripts, audio, screenshots, keys by default). Verified resumable first-run downloader with atomic rename/checksum/retry, no TLS bypass. Scope current local server separately from future user-enabled cloud providers and data disclosure.

## License gate
Top-level MIT package names do not establish transitive binary/model rights. Existing PyAV embeds FFmpeg; exact binaries/options and LGPL obligations need inventory. PyInstaller is GPL with a bootloader exception, not MIT/Apache, so packaging exception recorded under the owner free+best delegation. Preserve original attribution; do not rewrite dependency licenses. No new STT/TTS package adopted. openWakeWord stock/feature datasets NC-SA cannot pass permissive-only gate. PocketSphinx BSD/MIT candidate is permitted by the free+best delegation but not adopted before testing.

## Completion gate
Owner adopted the roadmap and public Phase0 source work on 2026-10-02. Phase0 complete only after accepted source-tree migration + config/secrets/logging tests + clean Windows launch and usable new EXE artifact. Existing 0.3.0 artifact is not a Phase0 foundation build. Hardware benchmarks and voice/language samples belong to Phase1, asked one at a time.
