# Existing mobile plan: separate dial track, not working carrier voice AI

Original authenticated owner messages8October2026:12:47:21 asks whether "call my brother then tell this" will act realistically;12:48:10 reports an unlimited-call recharge and asks whether the phone can connect. These messages are context, not approval to place any actual call or permission to guess a contact.

Supported design candidate: a small paired Android companion asks for CALL_PHONE permission and uses ACTION_CALL after exact laptop recipient/number review. ACTION_DIAL opens the dialer and needs a phone tap. Background/locked-phone behavior, OEM restrictions and actual call-state readback need companion/device tests. Do not imply every Android device supports unattended dialing. The user has not yet supplied the phone model/platform or accepted companion setup.

Dial-only phase must say it does not deliver the reviewed words. TTS-to-carrier audio through Windows Bluetooth HFP is unverified. Android normally blocks third-party capture of carrier call audio; a Bluetooth audio test is not proof of two-way AI calling. No fake listening, successful message delivery or conversation completion claims.

An unlimited plan does not prove international/premium/roaming calls are covered. Final number and cost need current plan verification before a call. Preserve existing internet-call track, which is local voice to JARVIS without a mobile number.

Sources inspected:
- https://developer.android.com/guide/components/intents-common : ACTION_DIAL/ACTION_CALL and CALL_PHONE.
- https://developer.android.com/media/platform/sharing-audio-input : voice-call audio capture requires special/privileged access.
- https://support.microsoft.com/en-us/windows/apps/phonelink/setting-up-calls-in-the-phone-link : paired Bluetooth phone calling, not a supported automation API.

phone_dial.py prepares an exact reviewed request but never executes it. No companion, call listener or carrier transport installed.

## Current platform limits checked8October evening

Android VOICE_CALL, VOICE_UPLINK and VOICE_DOWNLINK capture requires CAPTURE_AUDIO_OUTPUT, reserved for privileged system components, unavailable to ordinary third-party companion apps. An accessibility microphone permission is not full carrier-call audio access. iOS CallKit provides system UI for the app's own VoIP communication; it does not supply another app's or cellular call audio.

Phone Link supports Bluetooth calling on Windows/phone, but this alone does not establish a supported JARVIS audio/control route or AI speech delivery. Microsoft support pages disagree on iOS minimum15versus16; actual phone/app compatibility must be checked. Phone Link call troubleshooting says Bluetooth headset relay is not supported and dual SIM is not selectable. No unattended dialing or audio-injection guarantee can be made.

No companion, privileged permission workaround, root, call recording or native pairing has been installed. Platform/model and owner-selected transport remain unresolved.

Sources fetched:
https://developer.android.com/media/platform/sharing-audio-input
https://developer.android.com/reference/android/media/MediaRecorder.AudioSource
https://developer.apple.com/documentation/callkit
https://developer.apple.com/forums/thread/841340
https://support.microsoft.com/en-us/windows/apps/phonelink/setting-up-calls-in-the-phone-link
https://support.microsoft.com/en-us/windows/apps/phonelink/phone-link-requirements-and-setup
https://support.microsoft.com/en-us/Windows/Apps/PhoneLink/troubleshooting-calls-in-the-Phone-Link
