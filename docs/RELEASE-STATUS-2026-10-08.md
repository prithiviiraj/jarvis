# Overnight release status,8October2026

This is a scoped evidence ledger, not an all-features completion claim or permission to ship a final EXE. No new public release is made by this document.

## Current software source and checks

Latest product source a0464e314108f501cd2405a7f5f8160211b9278b.1139local tests,5skipped. Frontend build and controlled renderer reviews passed on the preceding product revision; latest change only rejects cloud-marked replies in local source-answer/brain-switch results. This latest guard still needs Windows acceptance.

Native232 and full233 run at c6ee6bcb3e4bd2744a32f24550895ef5e8c82d4f, before that guard. They were active at the last hourly check. Newer docs-only revisions do not change their product coverage.

- Native232: https://github.com/prithiviiraj/jarvis/actions/runs/37815915085
- Full233: https://github.com/prithiviiraj/jarvis/actions/runs/37816036596
- Native231 atb021e68 completed successfully: https://github.com/prithiviiraj/jarvis/actions/runs/37808297282
-231evidence: https://github.com/prithiviiraj/jarvis/actions/runs/37808297282/artifacts/11565040902
- Full230 failed before post-native heavy software tests, on obsolete offscreen Sheets-read UIA lookup: https://github.com/prithiviiraj/jarvis/actions/runs/37804359316

231passed the entire actual Windows Tauri/WebView2 sequence at its revision, including controlled frozen connector contracts and actual synthetic foreground desktop input/readback/revoke/resize refusal. It does not cover the subsequent phone-to-desktop, local design and cancellation hardening. Some native screenshots show clipped lower controls; native assertions are separate evidence, not proof that every control is visible in a single image.

## Prepared capability versus remaining outcome

| Area | Prepared software | Not yet established |
| --- | --- | --- |
| JARVIS/LYRA/DEX chat | Typed routing, streaming, local/cloud settings, custom face/settings preservation | Sustained owner-laptop model quality, latency and resource use |
| Local speech | Kokoro/Whisper runtime packaging, explicit asset/microphone gates | Latest full frozen software chain and owner mic/output acceptance |
| Phone internet voice | Trusted private TLS review, pairing, local bounded speech/context, Stop/expiry, exact recent-text unsent desktop handoff | Physical phone trust/network/capture/playback/local-model conversation |
| Carrier/business calling | Reviewed dial contract only, no dispatch | Supported companion/audio route, phone model/platform, destination tariff, exact call approval, real call completion |
| Desktop control | Selected foreground-window exact bounded mouse/literal-key plan, Stop/stale geometry refusal | Arbitrary semantic business-app completion or ad-spend/publication permission |
| Gmail/calendar/Telegram | Exact account/recipient/words reviews, live rechecks, durable uncertainty, solo event draft handoff | Actual registered client/owner account grants and approved live acceptance; Telegram output held |
| GitHub/Notion/Sheets/Drive | Narrow separate read/write workflows, live prior/readback/restart guards | Actual provider grants and live acceptance; broad connector parity |
| Canva | Local editable SVG text-poster alternative | Registered approved Canva integration/account sync and broader design workflow |
| Zapier | Explicit calendar-to-Telegram reviewed draft handoff alternative | Zapier account/background automations |
| Knowledge/modes | Source-grounded local draft, graph focus, exact local brain switch, Watch/focus/reflex | Real model/sensor quality, calibrated fast routing and full reference outcome parity |
| Invoice | Exact fact/total HTML local draft review/save | Issuing, delivery and payment requests intentionally excluded |

## Boundaries

No live Telegram/mail output, account changes, carrier calls, payments, invoice issue/delivery or automatic file opening were performed in this rebuild work. Local model IDs, source hashes, successful API fixtures or generated draft labels are not factual correctness or hardware acceptance. A preview or diagnostic artifact must never be relabelled final/all-features without closing the missing outcomes and the owner's requested scope.

Phone physical acceptance checklist: PHONE-DEVICE-ACCEPTANCE.md. Carrier setup boundaries: PHONE-CARRIER-DIAL.md. Connector shape and official sources: PHASE2-CONNECTORS.md.
