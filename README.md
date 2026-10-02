# JARVIS - Phase 0 foundation

A clean foundation for the voice-first roadmap. **Not a finished hands-free assistant.**

## What works now
- Separate Windows user-data folder for settings, logs, backups and future model cache.
- Versioned settings, validation, atomic writes and a backup of valid previous settings.
- Windows Credential Manager interface for future provider keys. No plaintext key fallback.
- Small rotating diagnostic logs containing fixed event codes only, not conversations.
- A foundation window and a "Run foundation check" button. No network or sensors on launch.

## Windows installer
A new Phase 0 Setup EXE has not been built or verified yet. Do not download a source ZIP expecting software.
The existing JARVIS 0.3.0 installer is a separate push-to-talk prototype, not this foundation.
A foundation installer will use a distinct app identity so it does not replace working 0.3.0 while Phase1 voice is still being built.

## What comes next
Phase1: continuous voice, speech benchmarks and explicit user-enabled brain routing.
Phase2: polished UI, onboarding, tray and installation experience.
No later-phase agents, tools, reminders, camera verification, Game Mode or auto-update is implemented here.

## Privacy
Microphone, camera and screen capture are absent from this foundation runtime.
Cloud providers are disabled. Keys are not accepted in configuration files.
No model downloads or provider requests happen at startup.
First-run verified model downloads will be added with the selected licensed engines in the voice phase.

## Developer checks
Source: `src/jarvis`. Tests: `tests`. Packaging: `packaging`. Docs: `docs`.
Run `PYTHONPATH=src python -m unittest discover -s tests -v` in a development environment.
Run `PYTHONPATH=src python -m jarvis --check` with `JARVIS_DATA_DIR` pointing to disposable test storage.
This technical section is not an owner setup requirement.
