#!/usr/bin/env bash
set -euo pipefail
curl -fL https://download.blender.org/release/Blender4.2/blender-4.2.9-linux-x64.tar.xz -o /tmp/blender.tar.xz
echo 'dfbc127a7d28f9c2175b23bf9d6701b2855f31eedfb391f9a6e60adb24572846  /tmp/blender.tar.xz' | sha256sum -c -
tar -xf /tmp/blender.tar.xz -C /tmp
/tmp/blender-4.2.9-linux-x64/blender -b -t 2 --python modern-ui/art/render-faces.py -- --out modern-ui/public/faces
