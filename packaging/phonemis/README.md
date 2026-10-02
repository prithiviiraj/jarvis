# Private-runtime candidate, public reproducible source check

Pinned upstream https://github.com/IgorSwat/Phonemis revision 71eb1ce33bd586d38cbac037843b8539d7829c3b. NOT adopted by the app. No binaries, weights or voice assets shipped here.

Evaluation patch changes four missing standard headers, fixes SIMD test allocations to the actual CPU batch width, and makes English acronym article context use pronounced sounds. Tests retain their expected outputs. Linux AddressSanitizer/UndefinedBehaviorSanitizer plus leak checks: 74/74 upstream cases pass after these changes. Persistent runner uses stdin text and keeps resources loaded. Windows build must pass separately.

Upstream MIT code/resources; bundled nlohmann JSON3.12 MIT, xsimd14.2 BSD3 plus embedded Boost/Sun notices. Full notice retention and exact Windows binary/model audit are required before adoption. No GPL phonemizer/eSpeak is used by this candidate. No subjective best-voice or hardware/no-stutter claim from these checks.
