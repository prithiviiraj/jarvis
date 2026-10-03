# Replaceable face pack v1

Render each persona from Maya/Blender with the same camera and lighting across states. Square512x512 transparent PNG RGBA is recommended;64-1024px is accepted. Alpha edges should be clean, with no baked background, ground shadow, labels or controls. Keep the face inside80% of the canvas, centred, with matching placement across frames.

Folders: JARVIS/, NOVA/, KAI/, LYRA/, DEX/. Each has idle/, thinking/, speaking/. Looping PNG frame sequences or a static/animated WebP clip are accepted. A clip can have1-120 images at1-30fps. Recommended24fps,2-4seconds. A WebP loop uses one frame path in the manifest; its own internal frame timing is authoritative. Entire pack under60MB.

At the pack root put manifest.json:

```json
{"version":1,"width":512,"height":512,"personas":{"JARVIS":{"idle":{"fps":24,"frames":["JARVIS/idle/0000.png","JARVIS/idle/0001.png"]},"thinking":{"fps":24,"frames":["JARVIS/thinking/0000.png"]},"speaking":{"fps":24,"frames":["JARVIS/speaking/0000.png"]}}}}
```

Repeat all3 states for all5 personas. Frame paths are relative to the folder, no external URLs or parent paths. In the app: Settings > Load3D face pack folder. The importer reads image files only, never executes content. This first importer lasts for the current app session; persistent installation is the next increment. Original .blend files are optional authoring sources, not runtime dependencies. In a bundled pack, files live under faces/ and the same manifest loads them.

States are activity indicators, not audio phoneme/lip-sync: idle when waiting/listening, thinking during STT/model processing, speaking during playback. Reduced-motion handling may freeze sequences later; keep a readable first frame.
