"""Estimate how long the full render will take, from a preview's timing.json.

Usage:
  python3 estimate.py <preview_dir> [--pct 100] [--samples 128] [--frames 150]

Render time scales roughly with pixels x samples. The estimate is deliberately rounded up by 25%: the first frame
pays for shader compilation and BVH build, and heavy frames (splashes, motion blur) run slower than calm ones.
Treat it as the number to plan around, not a promise.
"""
import argparse
import json
import os
import sys

p = argparse.ArgumentParser()
p.add_argument("preview_dir")
p.add_argument("--pct", type=int, default=100)
p.add_argument("--samples", type=int)
p.add_argument("--frames", type=int)
a = p.parse_args()

path = os.path.join(a.preview_dir, "timing.json")
if not os.path.exists(path):
    sys.exit(f"no timing.json in {a.preview_dir}; render a preview first (scene.py -- --preview)")
t = json.load(open(path))

samples = a.samples or (128 if t["engine"] == "cycles" else 64)
frames = a.frames or t["frames_in_shot"]
pixel_scale = (a.pct / t["pct"]) ** 2
sample_scale = samples / t["samples"] if t["engine"] == "cycles" else max(1.0, (samples / t["samples"]) ** 0.5)
per_frame = t["seconds_per_frame"] * pixel_scale * sample_scale * 1.25
total = per_frame * frames

def human(s):
    if s < 90:
        return f"{s:.0f} seconds"
    if s < 5400:
        return f"{s/60:.0f} minutes"
    return f"{s/3600:.1f} hours"

print(f"Preview: {t['engine']} at {t['pct']}%, {t['samples']} samples, {t['seconds_per_frame']}s a frame")
print(f"Final:   {t['engine']} at {a.pct}%, {samples} samples, {frames} frames")
print(f"Estimate: about {per_frame:.1f}s a frame, {human(total)} in total")
if total > 1800:
    print("Over 30 minutes: run it in the background (nohup ... &) and carry on, or drop samples / switch to EEVEE.")
