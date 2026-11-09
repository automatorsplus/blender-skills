---
name: headless-render
description: Build and render Blender scenes without ever opening Blender and without the Blender MCP. Claude writes a Python script, Blender runs it in the background, renders the frames, and ffmpeg stitches them into an MP4. Use whenever the Blender MCP is not connected, the user says they don't want to open Blender, asks for a render or animation from a prompt, or is on a machine where the MCP addon is a hassle. This is the default route for any finished image or video.
license: MIT
metadata:
  author: https://github.com/automatorsplus
  version: "1.0.0"
  domain: blender
  role: pipeline
  triggers: render, headless, background, no MCP, don't open Blender, animation, video, mp4, script
  related-skills: preview-first, social-export, product-ad, character-from-image, rendering, lighting, materials
---

# Headless Render

Blender has a full Python API and a command-line mode. So Claude never needs to click anything, and the user
never needs to open Blender or install an addon. One script builds the whole scene; Blender renders it in the
background.

```
prompt  ->  scene.py (Claude writes it)  ->  blender -b -P scene.py  ->  frames  ->  ffmpeg  ->  video.mp4
```

## When to use this instead of the MCP

| Situation | Route |
| --- | --- |
| The user wants a finished image or video | **This skill** |
| Blender MCP is not connected, or the addon will not connect | **This skill**. Never stop and ask them to install the MCP |
| The user wants to sculpt, tweak or inspect a scene live in the Blender window | Blender MCP (the other skills' MCP sections) |
| A long render that must not block the chat | **This skill**, run in the background (see below) |

The MCP needs Blender open, an addon installed, a socket on port 9876 and the user clicking Connect. The
headless route needs Blender installed. Nothing else.

## Setup check, once per session

```bash
BLENDER=$(bash .claude/skills/headless-render/scripts/find_blender.sh) && "$BLENDER" --version | head -1
command -v ffmpeg || echo "ffmpeg missing: brew install ffmpeg (macOS) / apt install ffmpeg (Linux)"
```

If Blender is missing, tell the user it is free from blender.org (macOS: `brew install --cask blender`). Do not
proceed with a fake render.

## The workflow

1. **Copy the template.** `scripts/scene_template.py` holds the plumbing: arguments, GPU detection (Metal,
   OptiX, CUDA, HIP), EEVEE or Cycles, frame-by-frame rendering with a live time-left readout, and
   `timing.json`. Copy it into the project as `scene.py` and replace only `build_scene()`.
2. **Build everything in code.** Meshes from primitives, bmesh or profiles spun round an axis; materials as
   node trees; lights, camera and animation as keyframes. Use the specialist skills for the craft (lighting,
   materials, camera-cinematography, animation) and this skill for how it runs.
3. **Preview first.** Always: `-- --preview` renders six frames at half size with low samples. Read
   `preview-first` before any render longer than a minute. Look at the frames yourself before showing them.
4. **Final render.** Same script, no preview flag. Over 30 minutes, run it in the background:
   ```bash
   nohup "$BLENDER" -b --factory-startup -P scene.py -- --out renders/final > render.log 2>&1 &
   tail -f render.log    # [render] lines show frame time and minutes left
   ```
5. **Stitch.** `bash scripts/stitch.sh renders/final out.mp4 30 [sound.wav]`. H.264, CRF 14, yuv420p, so it
   plays everywhere and survives a social upload.
6. **Check the result.** Open the MP4 or pull a frame from the middle with ffmpeg and look at it. A render
   that exited 0 can still be black, blown out or framed wrong.

## Rules that save hours

- **`--factory-startup` every time.** The user's own Blender preferences and addons stay out of it.
- **`bpy.ops.wm.read_factory_settings(use_empty=True)` at the top of the script.** Start from nothing, not
  from the default cube, camera and light.
- **Frames as numbered PNGs, never a video straight out of Blender.** A crash at frame 140 keeps 139 frames,
  and a re-run can do just the missing ones with `--only`.
- **EEVEE for stylised, characters and anything on a laptop. Cycles for glass, liquid, metal and product
  shots.** A Cycles frame can cost 20 to 100 times an EEVEE frame. Say which and why before rendering.
- **Engine ids moved between versions.** EEVEE is `BLENDER_EEVEE_NEXT` in 4.2 to 4.x and `BLENDER_EEVEE`
  before and after; the template tries both. Input socket order on some nodes changed in Blender 5: set
  inputs by name, never by index.
- **Colours in Blender are linear.** A hex colour needs converting (`character-from-image`'s `lin()` does it)
  or every colour comes out washed pale.
- **Point things with a track quaternion**, `(target - obj.location).to_track_quat("-Z", "Y").to_euler()`,
  rather than guessing Euler angles.
- **One script, rerunnable.** Every change goes into `scene.py` and the render runs again. Never patch a
  `.blend` by hand: the script is the source.

## Scripts

| Script | What it does |
| --- | --- |
| `scripts/find_blender.sh` | Prints the Blender path on macOS, Linux or Windows (Git Bash), or install advice |
| `scripts/scene_template.py` | The starting point for every scene: flags, engine, GPU, render loop, `timing.json` |
| `scripts/stitch.sh` | Frames to MP4, optional sound track |

Related: `preview-first` (estimate before you commit), `social-export` (vertical and square cuts, sound),
`product-ad` and `character-from-image` (two complete scenes built on this route).
