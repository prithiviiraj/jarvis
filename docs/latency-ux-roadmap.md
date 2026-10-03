# Reply latency UX requirements, not implemented claims

Priorities for future work:
- Stream persona replies so useful text appears as generated.
- Offer a narrowly consented local-model prewarm, without disclosing private conversation or enabling a cloud route.
- Keep floating face listening/thinking feedback visible during generation, with cancellation and stop.

Current state: local typed Chat uses one selected/routed persona and sends thinking state; non-streaming local request. No model request/prewarm starts at launch. Face state is not actual display FPS or audible latency measurement. No cloud request may be introduced as a hidden warmup. Streaming must discard cancelled generations, avoid late saves and preserve real provider/model labels.

Normal messages should receive ONE relevant reply. Full-team banter is separate, rare, short and opt-in. Default2turns; typical2-4. No screen/game/camera observation is implied.
