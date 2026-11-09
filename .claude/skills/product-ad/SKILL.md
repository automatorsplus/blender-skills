---
name: product-ad
description: A finished 3D product commercial from a label image and one sentence. The product (a can or bottle, wrapped in the user's own label) turns in a dark studio while ice and droplets burst around it in slow motion, with strip lights, a coloured glow and a slow camera push, rendered in Cycles without opening Blender. Use when the user wants a product ad, a drink ad, a packshot, a commercial, a hero shot of a product, or asks what kind of 3D work brands pay for.
license: MIT
metadata:
  author: https://github.com/automatorsplus
  version: "1.0.0"
  domain: blender
  role: specialist
  triggers: product ad, commercial, packshot, hero shot, drink, can, bottle, label, brand, advert
  related-skills: headless-render, preview-first, social-export, lighting, materials, rendering
---

# Product Ad

The 3D job businesses actually pay for: their product, looking expensive, five seconds long, in every format
their socials need. `scripts/product_ad.py` builds the whole thing from a label PNG.

## What it makes

- The product spun from a real profile (a 330ml can, or a glass bottle), the label wrapped once around it
- Condensation beaded over the label band, instanced with geometry nodes
- A slow-motion burst of rounded ice cubes and water droplets that refract for real
- Two strip lights carving highlights down the sides (one in the brand's accent colour), a top soft box, a key
- A dark backdrop with the accent colour glowing behind
- A slow camera push and drift, depth of field on the product, motion blur
- Cycles on the GPU, AgX colour, 1920x1080 or a true 1080x1920 vertical

## Run it

```bash
S=.claude/skills/product-ad/scripts/product_ad.py
"$BLENDER" -b --factory-startup -P $S -- --label label.png --out renders/preview --preview
python3 .claude/skills/preview-first/scripts/contact_sheet.py renders/preview
python3 .claude/skills/preview-first/scripts/estimate.py renders/preview --samples 96
"$BLENDER" -b --factory-startup -P $S -- --label label.png --out renders/final        # after a yes
bash .claude/skills/headless-render/scripts/stitch.sh renders/final ad.mp4 30
```

Vertical for Reels and TikTok: render again with `--width 1080 --height 1920`. The camera re-frames for it.
That beats cropping the 16:9, which cuts the burst off at both sides.

| Flag | Default | Notes |
| --- | --- | --- |
| `--label` | none (plain accent colour) | PNG, wraps once around; 2:1 or wider for a can |
| `--product` | `can` | `can` or `bottle` |
| `--accent` | `1,0.55,0.25` | strip light and glow colour, RGB 0 to 1. Pick it from the label |
| `--burst` | `ice` | `ice` (ice and droplets), `droplets`, `none` |
| `--condensation` | `on` | `off` for a dry product |
| `--frames` | `150` | 5 s at 30 fps |
| `--samples` | `96` | 64 is fine with the denoiser; 16 for previews |

## The label

- **Keep the logo and name in the middle third of the label's width.** The front of the product shows about a
  third of the wrap; the rest turns away. A word spread across the full width gets cut off.
- **No label yet?** Make one: a 2048x1024 PNG with the brand colour, the name large in the middle and a band
  of contrast behind it. Pillow, an HTML page screenshotted, or an image model all work. Use the brand's real
  colours and a real font; never invent a logo for a real brand.
- The seam sits at the back, so it never shows.

## Changing it

The script is a starting point, not a cage. Common asks and where they live:

- **Different product shape:** add a profile to `PROFILES`, a list of (radius, height) points from the base
  up, plus where the label band starts and ends. Jars, tubes and cosmetics bottles are all profiles.
- **Fruit or garnish in the burst:** add pieces to `pieces` with their own material (a sliced citrus is a
  thin cylinder with a radial pattern; a leaf is a bent plane).
- **Brand colour backdrop instead of dark:** change the backdrop ramp's second colour and raise its strength.
- **Logo end card:** hold the last 30 frames and add an emissive text object (`bpy.ops.object.text_add`) in
  front of the product, or add the end card in an editor.

## Time on a laptop

On an Apple silicon MacBook the preview frames took 1 to 3 seconds each, and `estimate.py` put a full 1080p
frame at 96 samples at about 50 seconds: roughly two hours for the 5-second ad. Your machine will differ, so
always run the estimate, and always run the final in the background (`preview-first`).

## Why it sells

A brand pays for this because it replaces a studio shoot: no product samples to ship, no photographer, a
version for every flavour by swapping the label PNG and the accent colour. Same script, new label, new ad.
