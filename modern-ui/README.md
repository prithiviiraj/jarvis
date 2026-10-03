# Modern Windows preview

Download the **JARVIS-Windows-Portable-Preview** artifact from the passing modern-ui workflow. Extract the entire ZIP, then double-click `JARVIS.exe` at the root. Keep `backend/` beside it. No Python, Node or compilation is required on your laptop.

Faces launch first. Right-click them and choose Open workspace. The backend is a fixed bundled local executable; there is no system-Python fallback and no arbitrary shell command interface. Camera and microphone start OFF. Windows 10/11 x64 and Microsoft Edge WebView2 are required. The preview is unsigned and may show a Windows publisher warning; do not disable security software.

This is not the full replacement. Local chat/judgment require LM Studio with one loaded model and its local server. Camera support is bundled, with explicit consent. Speech models, native speech frontend and optional audio dependencies are not bundled yet. Keep the working prior app until laptop acceptance.

## Acceptance

The CI builds a production Tauri executable with custom-protocol, not a dev server. It freezes the local Python bridge, tests that frozen bridge without Python in PATH, and drives the exact packaged JARVIS.exe through Windows UI Automation (WebView2). Evidence includes real window screenshots, frozen status/consent/clear checks and file digests. A green build is not proof of physical webcam/audio or real-model performance.

Developer-only build and package commands live in `.github/workflows/modern-ui.yml`. Users should not run them. The separate CI-acceptance artifact contains diagnostics, not the user app.
