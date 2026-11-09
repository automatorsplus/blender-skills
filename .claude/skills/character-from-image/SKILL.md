---
name: character-from-image
description: Turn a picture of a character, mascot or logo creature into a jointed 3D blocky (voxel-style) character that can wave, hop, run, cheer and dance, rendered without opening Blender. Claude reads the image, writes a small JSON spec of colours and proportions, and one script builds, rigs, animates and renders it. Use when the user drops an image of a mascot or character and wants it in 3D, animated, or as a brand mascot video.
license: MIT
metadata:
  author: https://github.com/automatorsplus
  version: "1.0.0"
  domain: blender
  role: specialist
  triggers: mascot, character from image, picture to 3D, voxel character, blocky, animate my character, wave, hop, dance
  related-skills: headless-render, preview-first, character-artist, voxel-style, lowpoly-style, animation, rigging
---

# Character From Image

Most people's first 3D wish is *my mascot, in 3D, moving*. A full sculpt and rig is days of work. A blocky
character, every part a softly bevelled box on a joint, reads instantly as the same character, animates
cleanly from code and renders in seconds in EEVEE.

## The workflow

1. **Read the image.** Note the main body colour, any accent colour (hands, feet, belt, armour), the eyes
   (slots, square, a visor, glowing or not), the ears or horns, and the proportions (big head, chunky limbs).
2. **Write the spec** as `character.json`. Only `body_color` is required:

   ```json
   {
     "body_color": "#3A7BFF",
     "accent_color": "#1B2A4A",
     "eye_color": "#7CF3FF",
     "eye_glow": true,
     "eye_style": "visor",
     "ears": "side",
     "head": [1.42, 1.18, 1.12],
     "torso": [1.0, 0.72, 0.95],
     "limb_thickness": 1.0,
     "backdrop_glow": "#3A7BFF"
   }
   ```

   | Field | Options | Default |
   | --- | --- | --- |
   | `body_color` | hex | `#F0531F` |
   | `accent_color` | hex or null (hands, feet, shoulder caps, belt) | null, all body colour |
   | `eye_color`, `eye_glow` | hex, true/false | near-black, false |
   | `eye_style` | `slots`, `square`, `visor` | `slots` |
   | `ears` | `cubes` (small on top), `tall` (bunny), `side` (headphone-like), `none` | `cubes` |
   | `head`, `torso` | [width, depth, height] in metres | [1.42, 1.18, 1.12], [1.0, 0.72, 0.95] |
   | `limb_thickness` | 0.7 slim to 1.4 chunky | 1.0 |
   | `floor_color` | hex | `#0E0E12` |
   | `backdrop_glow` | hex or null: a neon bar behind the character | null |

3. **Preview, then render.**

   ```bash
   S=.claude/skills/character-from-image/scripts/blocky_character.py
   "$BLENDER" -b --factory-startup -P $S -- --spec character.json --still --out renders/still
   "$BLENDER" -b --factory-startup -P $S -- --spec character.json --action wave --preview --out renders/p
   python3 .claude/skills/preview-first/scripts/contact_sheet.py renders/p
   "$BLENDER" -b --factory-startup -P $S -- --spec character.json --action wave --out renders/wave
   bash .claude/skills/headless-render/scripts/stitch.sh renders/wave wave.mp4 30
   ```

4. **Compare with the image.** Put the still beside the original. Wrong colour? The spec takes hex and the
   script converts to linear; check the hex itself. Wrong proportions? Adjust `head` and `torso` and render
   the still again (two seconds).

## Actions

| Action | What happens | Good for |
| --- | --- | --- |
| `stand` | idle sway | backgrounds, end cards |
| `wave` | raises the right arm and waves from the elbow | intros, *hi* moments |
| `hop` | crouch, launch, tuck, land, every 1.25 s | energy, transitions |
| `run` | run cycle on the spot | *on the way* moments; add a moving floor for travel |
| `cheer` | both arms up, bouncing | wins, announcements |
| `dance` | arm pumps, hip sway, turn | celebration, social clips |

## Going further

The rig is a set of joint empties: `root`, `body`, `hips`, `spine`, `neck`, `head`, `shoulder_l/r`,
`elbow_l/r`, `hip_l/r`, `knee_l/r`. A pose is a dict of degrees per joint; `blend(a, b, u)` mixes two poses.
New moves are new pose dicts keyed over time. Facing is -Y: a limb swings forward with a negative X rotation.

- **A scene, not a studio:** replace the floor with a world from `environment-artist` or a genre skill.
- **Several characters:** build the rig twice with different specs and offset each `root`.
- **More detail:** extra boxes parented to the right joint (a hat on `head`, a backpack on `spine`).
- **Smoother look:** `--engine cycles` for soft shadows and real reflections, at many times the render time.

## Honest limits

This is blocky by design. It nails mascots, robots, game characters and logo creatures. It is the wrong tool
for a realistic human or an organic animal; use `character-artist` or `creature-artist` with the MCP for
those, and tell the user why.
