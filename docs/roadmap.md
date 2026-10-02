# Roadmap adopted for phase planning

0. Audit/foundation: source layout, settings, credential storage, logs, ledger and clean startup.
1. Talking core: opt-in continuous listening, VAD, measured STT/TTS, provider routing, blind voice test.
2. UI/installer: voice orb, captions, onboarding, tray and shortcuts.
3. Agent identities: create/edit/name routing/voices.
4. Parallel teams: task board, leader delegation and spoken reports.
5. Local memory and owner-selected Obsidian connector.
6. Durable scheduler and event-driven proactivity.
7. Optional local camera/face verification.
8. Consent-gated tools and integrations.
9. Reliability, Game Mode, watchdog, backup/update and 72-hour soak.
10. Further polish and reviewed component adoption.

Never skip phase completion or call an untested prototype finished. Local and cloud data boundaries, provider costs, exact engine/model licenses and platform permissions must be explicit. Benchmarks run in authorized cloud environments, not on the owner's laptop; cloud scores are not laptop guarantees. Phase names are independent from existing 0.3.0 prototype version.

## October 2 evening scope

Groq workspace onboarding/diagnostics is the current live-provider path; real authenticated reply acceptance is an owner on-device step, not proved by synthetic CI. Keys only enter the app's Windows Credential Manager Settings screen, never chat. LM Studio remains the local default. Gemini and NVIDIA NIM have backend presets but no workspace integration/onboarding acceptance; schedule that after experimental installer clearance, not tonight.

Installer work paused: exact Windows runtime review found missing notice coverage and vendor-linked CTranslate2/Intel/CUDA inputs. Continue CPU-only backend build plus transitive notice review before redistribution. Phase 1 stays open. No 1-second audible-latency claim: software fixture measured 1.53-1.70s to first WAV write with a synthetic brain.
