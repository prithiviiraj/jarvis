# Next packaging milestone: standalone Windows app

User target: an installable/double-clickable Windows app without Python setup on the laptop. A frozen executable/installer is the next packaging milestone after current UI/banter verification, not an accomplished deliverable.

Current source runner still requires Python3.12 and SETUP.cmd. Keep this distinction in reports/download labels. No installer readiness claim from a source-runner ZIP.

Plan: audit bundled dependency/model/native licenses and redistribution obligations; build a packaging-friendly frozen app with no exotic new dependencies; verify on a clean Windows environment with no system Python, install/launch/uninstall, model setup and saved credentials, then owner-laptop audio/provider acceptance. Preserve the existing working build until acceptance. A standalone launcher may still need verified model downloads; file size and offline expectations must be stated from the final package.
