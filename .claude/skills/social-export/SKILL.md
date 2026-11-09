---
name: social-export
description: Turn a Blender render into post-ready files for every platform, with a sound track made in code. 16:9 for YouTube, LinkedIn and X, 9:16 for Reels, TikTok and Shorts, 1:1 for feeds, at sizes each platform accepts, plus pops, whooshes, chimes and hums generated in plain Python and placed on the frames where things happen. Use when the user wants a render as a Reel, TikTok, Short or post, wants sound on a render, or asks what size to export.
license: MIT
metadata:
  author: https://github.com/automatorsplus
  version: "1.0.0"
  domain: blender
  role: pipeline
  triggers: reel, tiktok, shorts, vertical, 9:16, square, instagram, export for social, sound effects, sfx
  related-skills: headless-render, preview-first, product-ad, compositing
---

# Social Export

A render is not a post until it is the right shape, the right size and makes a sound.

## Formats

| Where | Shape | Size | Watch out for |
| --- | --- | --- | --- |
| YouTube, LinkedIn, X | 16:9 | 1920x1080 | X limits video length and file size by account type; check before a long render |
| Instagram Reels, TikTok, YouTube Shorts | 9:16 | 1080x1920 | Keep the subject out of the bottom fifth: captions and buttons sit there |
| Instagram feed, LinkedIn feed | 1:1 or 4:5 | 1080x1080, 1080x1350 | |

## Two ways to get a vertical

1. **Re-render it vertical (best).** Render again at `--width 1080 --height 1920`. `product-ad` re-frames its
   camera for it; for your own scene, move the camera back or lower the focal length so the subject fills the
   height. Costs a second render. Looks designed for the platform.
2. **Cut it from the 16:9 (fast).**
   ```bash
   bash .claude/skills/social-export/scripts/export.sh ad.mp4 exports          # centre crop
   bash .claude/skills/social-export/scripts/export.sh ad.mp4 exports fill     # whole shot over a blurred copy
   ```
   Centre crop keeps the middle 32% of the width: fine for one centred object, wrong for anything wide.
   `fill` keeps the whole shot and fills above and below with a blurred copy of it.

`export.sh` writes 16:9, 9:16 and 1:1 at once and prints each file's size and dimensions.

## Sound, made in code

```bash
python3 .claude/skills/social-export/scripts/sfx.py track.wav 5 hum@0 whoosh@0.1 pop@1.2 pop@2.45 chime@4.2
bash .claude/skills/headless-render/scripts/stitch.sh renders/final ad.mp4 30 track.wav
```

Kinds: `pop` (a landing, a button), `thud` (something heavy), `whoosh` (a fast move or reveal), `chime` (end
card, success), `riser` (build-up), `hum` (a low bed from that point on). No downloads, no licences, nothing
to credit.

**Place the sounds from the animation, never by ear.** Every event in the script has a frame: the landing of
a hop, a button lighting, the camera's fastest move. Seconds = (frame - 1) / fps. Read the frame numbers out
of the script and build the cue list from them, so each sound lands on its frame.

The track is normalised below -1 dBFS so it never clips. For music, the user adds their own in an editor; do
not pull tracks from the web.

## Check before handing over

- Play or pull a frame from each export. A crop can cut the subject in half.
- Instagram rejects some files over the platform's limits; `export.sh` prints sizes, so check them.
- The 9:16 subject sits in the top four fifths.
