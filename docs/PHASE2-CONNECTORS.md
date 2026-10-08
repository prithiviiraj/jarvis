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

## Drive/Sheets reviewed read track

Implemented optional drive.metadata.readonly (restricted) and spreadsheets.readonly (sensitive). Both stay unchecked by default. Drive returns a maximum20file metadata page; Sheets reads an explicit finite A1 rectangle up to1000cells. These scopes cover all metadata/spreadsheets in the connected account, not just the request. No file download, edit, upload or share is implemented. Exact account/request confirmation, bounded responses, Stop and stale-result suppression are required. Live client registration and owner OAuth consent remain dependencies; fixture acceptance is not real-account access.

Official API/scope sources checked8October2026:
- https://developers.google.com/workspace/drive/api/guides/api-specific-auth
- https://developers.google.com/workspace/sheets/api/scopes
- https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list
- https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/get

## GitHub/Notion reviewed read track

Separate dedicated local tokens, exact GitHub login or Notion token-bot UUID verification, no silent reconnect. A saved token must be explicitly re-verified each session. GitHub reads at most20open issues/pull requests or one UTF8source file up to100KB at a reviewed branch/commit. Notion reads one20block direct-child page; nested children are not expanded. All responses are untrusted data, never tool instructions or model input. No write, background sync or external code execution. Provider token scopes cannot be reduced by client code; use fine-grained selected-repository read scopes / read-content selected Notion pages. Local removal does not revoke provider access.

Sources checked8October2026:
- https://docs.github.com/en/rest/users/users#get-the-authenticated-user
- https://docs.github.com/en/rest/repos/contents#get-repository-content
- https://developers.notion.com/reference/get-self
- https://developers.notion.com/reference/get-block-children

## Current bounded write additions,8October evening

The earlier read-track paragraphs describe their first implementation, not the current complete surface. Current optional reviewed actions add:

- GitHub: one issue at exact verified login/repository/title/body, separate Issues-write token permission, repository notification warning,120second review, POST plus GET readback. No PR/code change.
- Notion: replace one existing plain leaf paragraph, exact bot/block/parent/prior edit/prior/new words. Separate update-content capability. No rich text, nested content, creation, deletion or append.
- Sheets: finite100cell/8KBRAW text overwrite, exact account/spreadsheet/tab numeric ID/prior/new cells, separate broad spreadsheets write grant. Empty strings clear; formula-looking strings remain text. Live prior recheck then PUT/GET. Concurrent write after recheck remains possible and is disclosed.
- Drive: one small UTF8.txt at verified unshared owned My Drive root, separate drive.file and restricted metadata grants, preallocated ID and owner-only permissions/checksum readback. No shared folder, existing-file overwrite, arbitrary laptop upload or automatic opening. Actual root metadata/permissions availability under grants remains unverified, fail closed.
- Calendar to Telegram: explicit live recheck of exact completed solo event, account/title/dates/location only, notes omitted, then existing exact bot/chat/words draft review. No automatic output, voice, background trigger, Zapier account or restaurant/business booking proof.

All write outcomes are durable and uncertain outcomes block automatic retries. Corrupt evidence ledgers stay blocked rather than breaking unrelated status. Actual connected account setup and live consent/read/write acceptance remain dependencies. Controlled frozen Windows fixtures prove software contracts, not provider access or owner hardware.

Official write API sources:
https://docs.github.com/en/rest/issues/issues
https://developers.notion.com/reference/update-a-block
https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/update
https://developers.google.com/workspace/drive/api/reference/rest/v3/files/create
