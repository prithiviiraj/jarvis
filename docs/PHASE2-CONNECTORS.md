# Phase2 connector route and remaining setup

Verified official sources,8October2026. These are implementation requirements, not connected accounts or permission to send.

## Google Calendar and Gmail

Use an installed desktop OAuth client with local loopback callback and local protected refresh-token storage. Never reuse another application's tokens, copy browser cookies or put client secrets/refresh tokens in the repository. Explicit account identity must be shown in every preview. Read-only and write grants are separate.

Calendar free/busy is enough for conflict checks when event details are not needed. Read events only with calendar.events.readonly; request calendar.events.owned for approved writes on owned calendars rather than global calendar administration. Recheck free/busy at commit and show the final calendar, date, time, timezone, place, attendees and invitation behavior. A local Markdown calendar is not an external event.

Gmail sent-history/body matching needs gmail.readonly, which is a restricted scope. Sending uses gmail.send, a sensitive scope. Do not request full mail.google.com or delete privileges. Broad public distribution requires Google verification unless an exception applies. Google's personal-use exception may fit a sole-user installed app, but does not remove explicit OAuth consent or organization restrictions. Server access to restricted data can require a security assessment. Account setup is an actual dependency, not a fake Connect button.

Sources:
- https://developers.google.com/workspace/calendar/api/auth
- https://developers.google.com/workspace/gmail/api/auth/scopes
- https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification

## Telegram

Bot API can send completion text and voice and receive commands by long polling. A bot cannot start a conversation with a user; the owner must start the bot first. Pair using a single-use random code and show the resulting chat identity for approval; never trust an arbitrary chat_id supplied in an external message. Bot token is a persistent secret, collected locally into protected storage. Existing webhook ownership must be checked before switching to getUpdates. Keep messages scoped to reviewed task output; a bot does not inherit microphone, calendar, mail or spending access. Voice is sendVoice-compatible audio, not a telephone call.

Sources:
- https://core.telegram.org/bots
- https://core.telegram.org/bots/api

## Implementation order

1. Pure workflow state and transport contracts with fixture tests: explicit account/source provenance, review-bound action digest, duplicate-mail exact history warning, uncertain-send reconciliation, Stop.
2. Read-only Calendar/Gmail adapters and Telegram pairing. No real outbound fixture messages.
3. Installed OAuth and local secret protection plus clear Settings status. User chooses which live accounts to connect.
4. Actual approved read tests, then approved exact writes with server readback.
5. Phone calling separately: Telegram audio is not telephony, and provider cost/number registration needs research before any claim.

No claim that these routes are free without limits. No externally connected service, live send or booking has been completed by this document.
