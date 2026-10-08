# JARVIS local workspace

Release work is still open. This branch is source, not a final all-features Windows delivery. CI204 passed the packaged Windows regression at `0988a3276c3b090ddb3ffc4462a757e806540abd`; newer Gmail and calendar changes need their own acceptance. No new EXE is delivered just because a diagnostic build exists.

## Active team and local data

JARVIS is the leader, with LYRA and DEX. Legacy profiles are inactive, not deleted. Existing chats, vault notes, model caches and provider credentials are preserved. Kokoro is the selectable local speech engine. No gesture feature is included.

Team room stays focused on conversation and one Activate team button. Tool setup and detailed controls stay in Settings. The four Tools cards are Laya activate, Camera awareness, Proactive and Live screen share. Camera, microphone, cloud use and tool sessions require their own permission.

## Current software

- Typed and consented local voice conversation, JARVIS/LYRA/DEX voices, chat history and Stop.
- Local Brain of Brain notes, source-backed search and captured note reading, linked depth/flat knowledge views, local Obsidian canvas and sync.
- Isolated Edge browser control and bounded foreground-bound Windows mouse/keyboard input. Unknown targets and consequential effects are not silently executed. These are not arbitrary-app completion guarantees.
- News uses a chosen page and captured source text, not an invented default feed. Long local read-aloud is chunked and stoppable.
- Google Desktop OAuth preparation: PKCE, explicit account/scopes, verified email identity, temporary loopback callback, Windows Credential Manager token storage, refresh and local disconnect. No plaintext token fallback.
- Explicit bounded Gmail listing and UTF-8 plain-text reads. HTML, attachments and ambiguous headers make capture completeness false.
- Exact reviewed new Gmail messages with account, To, CC, subject and body together. No replies, BCC or attachments. Partial sent-history checks block sends. Unknown send outcomes persist across restart and cannot be retried until reconciled.
- Exact reviewed solo primary-calendar events with explicit offset timestamps, private visibility, live identity/free-busy checks and stored readback. No invitations, reminders, video links, recurrence or changes to existing events. Conflicts block creation. Unknown event outcomes remain blocked across restart.
- Inert phone voice preparation: one-use pairing, laptop review, bounded audio, revokable session and Stop. No network listener starts. Trusted transport has not been chosen.

## Account setup and limits

Google access needs the owner's registered Desktop OAuth client and Google account consent. Client credentials belong in secure credential storage, never chat or a committed file. Google apps left in Testing can require reconnecting after seven days. Local disconnect removes the saved token; server permission must also be removed from the Google account when desired.

Connecting is not permission to send mail, change an event or disclose data. Incoming mail, web pages and notes are untrusted content, not instructions. The app does not send or create events from model text. Final recipient/words or account/event review is required at the action control.

Telegram pairing and other connector foundations are not yet a live connected-product completion claim. An unlimited mobile plan does not establish a usable carrier calling/audio path. Dialing, internet voice and speaking into a carrier call are different features. JARVIS cannot yet call a person and speak to them through the owner's mobile recharge.

## Acceptance boundaries

CI204 verified actual Windows Tauri/WebView2 startup, native input against a synthetic Windows edit window, exact three-profile restart with unchanged archived data, source retrieval pixels, frozen speech software and credential/loopback flow. Google token/identity replies and model replies were controlled fixtures. Phone pairing screenshots are renderer fixtures, not physical phone proof.

Still unrun: owner Google client/login and real connector data, physical microphone/speaker/echo, physical phone/browser capture and playback, trusted TLS/LAN/outside-network transport, carrier/PSTN speech, arbitrary desktop/model goal completion, and long-run resource behavior. The project does not ask the owner to carry our regression testing. Genuine account registration, consent and transport choices remain owner decisions.

Do not treat passing software fixtures, a diagnostic artifact or this source ZIP as the final requested release. Preserve the existing installed package until a complete, tested release is explicitly delivered.
