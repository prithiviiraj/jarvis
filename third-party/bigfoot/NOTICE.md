# Bigfoot-derived companion

Upstream: https://github.com/jhmeel/bigfoot
Pinned revision:95f7ffdb29ff49efe321a96c9caa3e5c8c94a1e6
Original author:jhmeel. License:GPL-3.0-or-later.

JARVIS adaptations in modern-ui/src/bigfoot/geometry.ts are derived from src/renderer/overlay.js spring-follow logic and src/renderer/overlay-draw.js smoothPath. The native integration, React view, bounded stroke storage and controls are JARVIS changes. Original spring constants and curve construction are retained, with input limits, screen-edge clamping and reduced-motion behavior added.

No Bigfoot autonomous shell, plugin, file, network, mouse/keyboard agent or wake-word path is imported. The companion starts only through explicit local controls. Drawing is temporary in memory and not sent to a model. Closing clears it. These components are not proof of the other Bigfoot feature claims.

The combined source on this integration branch is distributed under GPL-3.0-or-later. Keep this notice and the full license. Earlier278candidate has not been changed by this branch.

Additional interface source is copied from the same pinned revision into modern-ui/public/bigfoot-ui: app.html, styles.css, settings.css, app.css, local-ai.css, ui.js, app.js, home.js, local-ai.js, terminal-pane.js, assets and fonts. This is faithful source preparation for the owner's requested UI, not a completed or enabled interface migration. The original Electron bridge, terminal shells and autonomous effects are not active. A JARVIS-specific adapter must preserve reviewed actions, accurate readiness and existing owner data before this becomes the default.

Managed-model research uses local/catalog.js and hardware.js concepts in src/jarvis/local_models.py plus pinned catalogJSON. Original manager/runtime/download code is retained as study source in local-reference/, not executed. JARVIS download_checked/extract_runtime adds exact verification and extraction bounds; automatic retired-model deletion is not imported. The Inter font remains SIL-OFL1.1, notice in INTER-OFL.txt. llama.cpp source is MIT, notice in LLAMA-MIT.txt. Exact binary transitive notices remain unverified before redistribution.

Additional adaptations: optional synthesized UI sound tone/SOUNDS source in modern-ui/public/bigfoot-ui/jarvis-sounds.js derives from renderer/engine.js. Prepared acknowledgement pattern in src/jarvis/fast_ack.py and runtime integration derives from main/audio.js/kokoro.js/controller.js. Voice clips are generated locally from separately verified Kokoro assets during explicit voice setup, not copied from an unverified binary soundpack. Avatar artist terms and credits remain with assets/voices/CREDITS.txt. These paths remain subject to actual Windows audio and integrated acceptance.
