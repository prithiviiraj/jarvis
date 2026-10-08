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
