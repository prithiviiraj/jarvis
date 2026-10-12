# Bigfoot-derived companion

Upstream: https://github.com/jhmeel/bigfoot
Pinned revision:95f7ffdb29ff49efe321a96c9caa3e5c8c94a1e6
Original author:jhmeel. License:GPL-3.0-or-later.

JARVIS adaptations in modern-ui/src/bigfoot/geometry.ts are derived from src/renderer/overlay.js spring-follow logic and src/renderer/overlay-draw.js smoothPath. The native integration, React view, bounded stroke storage and controls are JARVIS changes. Original spring constants and curve construction are retained, with input limits, screen-edge clamping and reduced-motion behavior added.

No Bigfoot autonomous shell, plugin, file, network, mouse/keyboard agent or wake-word path is imported. The companion starts only through explicit local controls. Drawing is temporary in memory and not sent to a model. Closing clears it. These components are not proof of the other Bigfoot feature claims.

The combined source on this integration branch is distributed under GPL-3.0-or-later. Keep this notice and the full license. Earlier278candidate has not been changed by this branch.
