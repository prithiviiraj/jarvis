# Free phone route: prepared core, transport not implemented

Owner8October2026 11:58:35 said phone calls important. 11:59:10 said implement/use free option only. No paid providers or numbers.

Candidate: phone browser/app to running laptop, private internet voice, local Whisper/Kokoro/LM Studio. No purchased number or voice provider minutes. Same-network first; outside-network route remains an availability/security problem, not assumed free or reliable. Need owner-authenticated one-time pairing, explicit local listener activation, TLS trusted on phone, expiring/revokable phone session, bounded audio, no raw transcript/audio storage by default, shared conversation priority and Stop; proper capture/decode/playback interruption tests. Need runtime/network/audio library audit and Windows packaging before implementation. Do not expose the main stdio bridge or all agent commands over LAN. Phone transport cannot turn a claimed user identity into consent for sending or paying.

Limits: not JARVIS's own mobile telephone number, not free restaurant/business PSTN calling. Self-hosted LiveKit is a candidate for media transport, not a free PSTN provider; do not add server now merely because template exists. Existing same-machine screen loop needs no WebRTCserver. Microsoft Phone Link uses paired phone/Bluetooth and existing mobile plan; no verified programmatic audio feed to JARVIS. Need clarify if incoming real-phone alerts vs internet JARVIS call matters to owner, but do not ask unnecessary question before preparing workable free choice.

Sources inspected/discovered8October2026:
- https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia : mic capture requires secure context; plain LAN HTTP fails.
- https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Signaling_and_video_calling : peer-to-peer media needs signaling/negotiation.
- https://docs.livekit.io/telephony/start/providers/ : SIPprovider needed fortraditionalnetworks.
- https://docs.livekit.io/telephony/making-calls/outbound-trunk/ : purchased phone number/provider configuration.
- https://docs.livekit.io/transport/self-hosting/ : selfhostmedia option, not carrier.
- https://www.twilio.com/en-us/voice/pricing/in : paidusage, notzero-costPSTN.
- https://support.microsoft.com/topic/setting-up-calls-in-the-phone-link-c7e75908-c65d-bd42-fcb2-ea4d5fb783f1 : Androidphone/BluetoothcallsfromPC.

Prepared modules: phone_session.py, phone_audio.py and phone_controller.py. They provide local review-bound pairing, expiring/revokable session, bounded WAV, local Whisper/brain/Kokoro processing and async Stop. No listener, phone browser capture, TLS trust, outside-network access, PSTN or live phone acceptance exists. Unit tests use injected speech/model adapters. phone_acceptance.py is a frozen real-engine software test with a controlled loopback brain fixture, not phone/device evidence. Main deferred trusted transport selection until the core is ready. No network exposure is authorized by this ledger.

Transport prep update8October2026: phone_transport.py now prepares a private IPv4 TLS listener bound to an exact reviewed interface/origin/port and certificate fingerprint. It starts only after exact review and separate phone-trust confirmation; auto-stops/revokes at15minutes. No trust store edits, firewall changes, tunnel or startup listener. Actual isolated loopback TLS fixture tests verify static no-store serving, local approval pairing/token delivery and Stop revocation. This is not a trusted physical-phone test. Product UI does not yet expose listener start until the transport/trust route is settled. The self-signed localhost fixture certificate is not installed or distributed.
