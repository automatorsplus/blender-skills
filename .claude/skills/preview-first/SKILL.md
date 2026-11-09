---
name: preview-first
description: Never start a long Blender render blind. Render six quick preview stills, build a contact sheet, estimate the full render time from them, get a yes, then run the final in the background. Use before any render over a minute, any Cycles animation, any time the user is waiting on a render, or when they ask how long a render will take.
license: MIT
metadata:
  author: https://github.com/automatorsplus
  version: "1.0.0"
  domain: blender
  role: pipeline
  triggers: preview, how long, render time, estimate, contact sheet, stills, check before render, waiting
  related-skills: headless-render, rendering, social-export
---

# Preview First

The expensive mistake in Blender is not a bad render. It is a bad render you waited 40 minutes for. A preview
costs seconds and catches the wrong camera, the blown highlight, the missing label and the object floating
above the floor before the long render starts.

## The loop

```
1. preview   six frames, half size, 16 samples           seconds
2. look      contact sheet, checked by Claude first      before the user sees it
3. estimate  full-render time from the preview's timing  one line
4. decide    user says go, or one change and back to 1
5. final     in the background, with time-left readout   the chat stays free
```

### 1. Preview

Every script built on `headless-render`'s template, `product-ad` or `character-from-image` takes `--preview`:
six evenly spaced frames at 50% size with 16 samples.

```bash
"$BLENDER" -b --factory-startup -P scene.py -- --out renders/preview --preview
```

### 2. Look

```bash
python3 .claude/skills/preview-first/scripts/contact_sheet.py renders/preview
```

Open `contact-sheet.png` and check it yourself before showing it. Check, in this order:

- **Framing:** is the subject whole and in frame on every frame? Heads and feet are what get cut.
- **Contact:** does everything that should touch the floor touch it? Floating objects are the commonest miss.
- **Exposure:** any frame blown to white or crushed to black? Emissive surfaces blow out first.
- **The brief:** is every thing the user asked for visible (the label, the second character, the logo)?
- **Motion:** across the six frames, does the movement read? A turntable that barely turns looks static.

Fix anything you find and preview again. Show the user the sheet only once it passes your own check, and say
what you changed.

### 3. Estimate

```bash
python3 .claude/skills/preview-first/scripts/estimate.py renders/preview --pct 100 --samples 128
```

It reads the preview's `timing.json` and scales by pixels and samples, then adds 25% for the heavy frames.
Tell the user the number before the final starts: *about 35 minutes for 150 frames in Cycles.*

### 4. Decide

Too long? Offer the cheapest fix first:

| Lever | Typical saving | Cost to the look |
| --- | --- | --- |
| Cycles samples 128 to 64 (denoiser on) | about half | small |
| EEVEE instead of Cycles | 10 to 50 times | glass, liquid and caustics lose realism |
| 1080p instead of 4K | 4 times | depends where it goes |
| 5 seconds instead of 10 | half | the shot is shorter |
| Motion blur off | 10 to 30% | fast motion looks steppy |

### 5. Final, in the background

```bash
nohup "$BLENDER" -b --factory-startup -P scene.py -- --out renders/final > render.log 2>&1 &
```

Carry on with the next thing. `tail render.log` shows each frame's time and the minutes left. If a render
dies part way, re-render only what is missing with `--only` and the frame numbers.

## Rule

**No render over five minutes starts without an estimate the user has seen.** If they said *just do it*, still
state the estimate in one line as you start it.

## Scripts

| Script | What it does |
| --- | --- |
| `scripts/contact_sheet.py` | Tiles preview frames 3 across with frame numbers (Pillow; falls back to ffmpeg) |
| `scripts/estimate.py` | Full-render time from a preview's `timing.json` |
