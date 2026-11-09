"""Tile a folder of rendered frames into one contact sheet, 3 across, frame numbers on each.

Usage:
  python3 contact_sheet.py <frames_dir> [out.png]

Needs Pillow (pip install pillow). Without it, falls back to ffmpeg's tile filter with no labels.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

if len(sys.argv) < 2:
    sys.exit(__doc__)
d = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(d, "contact-sheet.png")
files = sorted(glob.glob(os.path.join(d, "f_*.png")))
if not files:
    sys.exit(f"no f_*.png frames in {d}")
cols, w, pad = 3, 640, 8
rows = (len(files) + cols - 1) // cols

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    tmp = tempfile.mkdtemp()
    for i, f in enumerate(files):
        shutil.copy(f, os.path.join(tmp, f"{i:03d}.png"))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "1", "-i", os.path.join(tmp, "%03d.png"),
                    "-vf", f"scale={w}:-2,tile={cols}x{rows}:padding={pad}:margin={pad}:color=black",
                    "-frames:v", "1", out], check=True)
    shutil.rmtree(tmp)
    print(f"wrote {out} ({len(files)} frames, no labels: pip install pillow for frame numbers)")
    sys.exit(0)

thumbs = []
for f in files:
    im = Image.open(f).convert("RGB")
    im = im.resize((w, round(im.height * w / im.width)))
    thumbs.append((re.sub(r"\D", "", os.path.basename(f)).lstrip("0") or "0", im))
h = thumbs[0][1].height
sheet = Image.new("RGB", (cols * w + (cols + 1) * pad, rows * h + (rows + 1) * pad), "black")
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.load_default(size=24)
except TypeError:
    font = ImageFont.load_default()
for i, (num, im) in enumerate(thumbs):
    x, y = pad + (i % cols) * (w + pad), pad + (i // cols) * (h + pad)
    sheet.paste(im, (x, y))
    label = f"frame {num}"
    box = draw.textbbox((x + 12, y + 10), label, font=font)
    draw.rectangle((box[0] - 6, box[1] - 4, box[2] + 6, box[3] + 4), fill=(0, 0, 0))
    draw.text((x + 12, y + 10), label, fill="white", font=font)
sheet.save(out)
print(f"wrote {out} ({len(files)} frames)")
