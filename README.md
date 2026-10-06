# JARVIS modern workspace - review candidate

This is the modern local-first workspace, not the old Phase 0 foundation installer. This directory is an isolated source review candidate, not a new ready-to-install EXE. Do not install a source ZIP expecting an app.

## What this candidate adds
- Plan, visual vault map and local calendar reviews in the conversation, with exact confirm/cancel rather than a forced trip to Settings.
- A news-page flow with no default source: choose a public HTTPS page, review its exact URL, open it through separately enabled browser control, then review up to 4000 characters of observed visible page text. Quoted text may include navigation or ads, not only headlines. Capture time is shown. This is a reviewed snapshot, not live news; recapture for changes. A separate confirmation reads the exact quote with an already installed local voice. No microphone, chat model, cloud fallback or model download starts from news reading.
- Calendar-request handoff preserves the original request and an explicit place phrase. Relative date/time and missing title/end/timezone remain unresolved; fill and review exact fields before saving a local Obsidian event note.
- Brain of Brain orientation links the visual map, Today plan and local calendar. Other data areas are editable work notes, not live bookings or routes. Editing notes cannot grant permissions or execute tools.

## Tested here
New backend control-logic tests, including actual Bridge dispatch with fake browser/voice, renderer fixtures and inspected screenshots. Front review, News, calendar draft and orientation builds passed on this Linux test host. These results are not a Windows packaged-app pass or physical-device proof.

Source137/CI155 already has separate Windows fixture evidence for the prior workspace and local calendar/canvas. That evidence does not certify these new changes and is not proof on the owner's laptop. No passed CI has been rerun for this candidate.

## Before a night test
1. Use only the exact modern-workspace artifact selected and verified for this candidate after its new CI. No new candidate EXE exists yet. Do not confuse old Phase 0, prototype, source ZIP and modern portable artifacts.
2. Keep microphone, camera, browser control, cloud and automatic work off until their own reviewed setup is accepted.
3. Check local model connection and installed voice separately. Asset installation is explicit, never hidden in a news action.
4. Create the reviewed Brain of Brain vault. If Obsidian asks, select that folder as its vault. Existing edited notes must remain intact.
5. Start with typed plan/map/calendar reviews and cancel first. Test exact confirm only when the displayed destination/event is right.
6. News requires your chosen page URL. Opening and reading are separate reviews. Stop reading and change page tests should come before using long text.
7. Record what actually works on the laptop. Do not infer audio, capture, GPU performance or firewall enforcement from these screenshots.

## Not yet proven
Owner-laptop microphone/speaker/echo, game capture, GPU/latency, current installation behavior, native News browser/voice path and the new packaged UI. Relative-date language is a draft handoff, not an automatic scheduler. No reminders, calendar conflict checking, invitations or Google sync. KAI Google sync is next phase. Wake word and Windows auto-start remain planned.

LiveKit v3 is parked as a separate review-only experiment with unresolved cancellation/handle-ownership diagnostics. It is not promoted, enabled, or bundled by these changes. Windows containment has not been proved; the withdrawn blanket Block plus loopback Allow recipe must not be used.

## Release state
Delivery HOLD remains. Main review and a new candidate CI are needed before any source promotion or artifact delivery decision. No artifact has been deleted, no app published, and no hardware claim is made by this README. Older source137 README is preserved as README-original137.md for review.
