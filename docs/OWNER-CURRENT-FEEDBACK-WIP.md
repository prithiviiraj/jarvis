# Owner feedback work in progress

Isolated from accepted320/331 and delivered candidate dea6bc5. No replacement package yet.

Owner design approval is required before full Windows/package gates. Current-shell screenshots were sent for that gate on October15,2026 at14:20IST. They use synthetic IPC, and the browser page-layout image is visibly labeled a local test fixture, not a BrowserOS runtime screenshot.

## Implemented, still awaiting native acceptance

- Persona-specific shared-history projections, foreign-identity reply guards, and current-image-only context for explicit visual questions.
- Started/tested owned local model before cloud/optional LM Studio. Downloaded files alone do not create readiness.
- Groq speech input selection, Tamil/English automatic input, session audio-sharing review, no silent fallback. Speech output stays local Kokoro; natural Tanglish output is not verified.
- Deterministic result receipts on one existing session speaker; no model/synthesis on result playback. First voice-session build prepares27fixed clips before the microphone starts; later sessions can reuse generic clips in bounded RAM. Cold/cache preparation timing is recorded for the frozen software gate. Stop is checked between clips; a current synthesis call may finish. Actual first-start cost and audible latency remain unmeasured.
- ALL voice selection, one microphone, actual sequential persona routes/voices, explicit named-only address and Stop support.
- Ctrl+Alt edge interrupt, reuse of the current consented session, one deferred utterance while cancelled worker exits. Legacy hold adapter retained for compatibility.
- BrowserOS fixed Start with no second JSON confirmation, exact public HTTPS destinations, fixed bounded wheel steps, current-page JPEG view, observed YouTube candidate/number flow. No arbitrary scripts/refs/forms, credentials, sending, downloads or payments.
- Own completed JARVIS page history, local persistence when a normal chat archive is attached, recent/yesterday filter. No private browser import. No old pages backfilled.
- Gemma current-content vector reuse in bounded RAM; explicit note search starts optional text/code256-dim candidates if its isolated runtime exists. Exact text search stays available. No auto download/source opening/cloud sharing.
- Simpler Settings entry, explicit Windows app review access, reduced-motion-aware press/card motion. Full animation polish remains.

## Not yet complete / shipping gates

1. BrowserOS news capture/read-versus-self-read migration is implemented and fixture-tested; native pinned runtime/image/audio acceptance remains. Legacy Brave news remains separate when chosen.
2. YouTube uses a fixed single desktop-search-result anchor selector per read-only markdown call, binding the actual final href suffix independently of malicious title text. Native tests must verify current YouTube DOM layout/order. Unsupported homepage/mobile layouts, duplicates, wrong origins, unsafe or ambiguous hrefs fail closed. Generic read-links markdown is not used for effects. No native/release-ready video-selection claim yet.
3. Full native control audit, pinned BrowserOS screenshots/action checks, cancellation/timing and frozen checks have not run on this branch. No physical owner mic/Groq/Tanglish/3060acceptance.
4. First feedback preparation cost, model startup contention and ALL audio/echo behavior need measurement. No AEC claim.
5. Batch migration passes78distinct renderer scripts (77eligible workflow checks plus Settings-return), including retained copied-shell static asset checks and owner ALL/Groq/news previews. Optional face/motion fixtures are not run because their manifest is absent; see OWNER-CURRENT-RENDERER-AUDIT.json. Selected native fixtures are updated for simplified Settings, removed Laya tiles, ALL/Groq and current-shell pixels; actual Windows execution is still required. Legacy/app review coverage remains. Historical exact-candidate rerun job is untouched.
6. Current view is a screenshot, not live video or proof that BrowserOS came to the foreground. Requests that need true live foreground control need an explicit supported implementation.

No Telegram sends, invoice issuance, automatic file opening or all-features/release claims are authorized by these changes. Existing exact review gates remain except bounded BrowserOS Start/navigation requested by the owner.
