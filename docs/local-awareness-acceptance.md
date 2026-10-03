# Local awareness foundation: acceptance and limits

Camera and app awareness start OFF. Open Camera controls or right-click the faces -> Local awareness. Install the optional source-only camera dependency with ENABLE-CAMERA-DEPS.cmd first. This is not a standalone installer or binary license clearance.

Enable local camera opts in for this session. A separate topmost indicator appears before acquisition and remains while the workspace is hidden. OFF stops all sensing and clears local context. Closing the controls, Pause all and app exit stop sensing. Reopening the app does not resume it. Camera acquisition/read errors mean ERROR/unknown, never absent or asleep. A stop may briefly show STOPPING until the device thread unwinds; starting again is blocked until then.

Camera frames are transient RAM inputs to a local OpenCV frontal Haar face detector. Sample at roughly one second, resize to 320x240, debounce three consecutive samples. Any detected frontal face means presence, not the owner's verified identity. False positives/negatives, poor lighting, side profiles and multiple people need real laptop tests. Camera device may retain internal buffers; the app does not encode, write or upload frames. No screen capture or audio starts from these controls.

Foreground-process awareness has its own opt-in. Window titles require another explicit checkbox since titles may include private names or text. Snapshot/events are capped at 24, RAM-only. Clearing/off removes app/title history. No files, model/provider requests, automatic speech, scripted reminders or persistent notes are generated from these observations. A bounded structured snapshot is the future persona-context boundary, not enabled model judgment. Titles are inert untrusted data, not instructions. Sharing this context with cloud or local models remains a later separately controlled step.

## Laptop checklist

- Off launch does not light webcam LED or capture app titles. Missing optional dependency gives ERROR instead of starting an install.
- Enable: indicator and webcam LED visible, face detected under normal lighting; step away and return with debounce.
- OFF/close controls/Pause all: camera LED goes off, context cleared, no delayed presence or restart.
- Hide workspace: indicator stays visible and OFF still works. Closing indicator stops all sensing.
- Permission denied/unplug camera: ERROR/unknown, not sleep/absence. Restart only after capture thread exits.
- App detection shows expected process; titles empty unless separately enabled. Disable titles clears prior private titles. Turn app detection off clears current app/title.
- Monitor CPU/power and sleep/lock/resume. No 24/7 reliability or health/sleep inference claim until soak/accuracy acceptance.

CI uses real Windows foreground APIs and real detector loading/blank-image inference. Presence lifecycle/indicator tests use a synthetic capture adapter, not a physical camera or the owner. Pixels are evidence of UI, not evidence of webcam accuracy. Cloud vision, live game commentary and persona-driven proactive speech remain unimplemented.
