"""Make a sound track for a render in plain Python: no samples to download, no libraries.

Usage:
  python3 sfx.py <out.wav> <seconds> <cue> [<cue> ...]

A cue is kind@seconds, for example:
  python3 sfx.py track.wav 10 whoosh@0.2 pop@1.5 pop@2.5 chime@9.4 hum@0

Kinds:
  pop     short bright blip (a landing, a button, a UI element appearing)
  thud    low soft hit (something heavy landing)
  whoosh  filtered noise sweep (a fast move, a camera push, a reveal)
  chime   two-note bell (the end card, a success moment)
  riser   rising tone over 1.5s (build-up before a reveal)
  hum     low bed under the whole shot from that point on

Cue times come from frame numbers: seconds = (frame - 1) / fps.
"""
import math
import random
import struct
import sys
import wave

RATE = 44100


def env(t, attack, decay):
    return min(1.0, t / attack) * math.exp(-t / decay) if attack > 0 else math.exp(-t / decay)


def pop(n):
    return [0.6 * env(i / RATE, 0.002, 0.05) * math.sin(2 * math.pi * (880 - 400 * i / n) * i / RATE) for i in range(n)]


def thud(n):
    return [0.8 * env(i / RATE, 0.003, 0.12) * math.sin(2 * math.pi * (90 - 40 * i / n) * i / RATE) for i in range(n)]


def whoosh(n):
    rnd, out, lp = random.Random(1), [], 0.0
    for i in range(n):
        u = i / n
        k = 0.02 + 0.25 * math.sin(math.pi * u)          # filter opens then closes
        lp += k * (rnd.uniform(-1, 1) - lp)
        out.append(0.9 * math.sin(math.pi * u) * lp)
    return out


def chime(n):
    out = []
    for i in range(n):
        t = i / RATE
        a = math.sin(2 * math.pi * 1046.5 * t) * env(t, 0.004, 0.6)
        b = math.sin(2 * math.pi * 1568.0 * max(0, t - 0.12)) * env(max(0, t - 0.12), 0.004, 0.7) if t > 0.12 else 0
        out.append(0.35 * (a + b))
    return out


def riser(n):
    phase, out = 0.0, []
    for i in range(n):
        u = i / n
        phase += 2 * math.pi * (200 + 900 * u * u) / RATE
        out.append(0.3 * u * math.sin(phase))
    return out


def hum(n):
    return [0.12 * min(1, i / (RATE * 0.8)) * (math.sin(2 * math.pi * 55 * i / RATE) + 0.5 * math.sin(2 * math.pi * 110 * i / RATE)) for i in range(n)]


LENGTHS = {"pop": 0.25, "thud": 0.5, "whoosh": 0.7, "chime": 2.0, "riser": 1.5}
KINDS = {"pop": pop, "thud": thud, "whoosh": whoosh, "chime": chime, "riser": riser, "hum": hum}

if len(sys.argv) < 4:
    sys.exit(__doc__)
out_path, seconds = sys.argv[1], float(sys.argv[2])
track = [0.0] * int(seconds * RATE)
for cue in sys.argv[3:]:
    kind, at = cue.split("@")
    start = int(float(at) * RATE)
    n = len(track) - start if kind == "hum" else int(LENGTHS[kind] * RATE)
    for i, v in enumerate(KINDS[kind](n)):
        if start + i < len(track):
            track[start + i] += v

peak = max(1e-9, max(abs(v) for v in track))
gain = min(1.0, 0.89 / peak)                               # keep below -1 dBFS, never clip
with wave.open(out_path, "w") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(b"".join(struct.pack("<h", int(v * gain * 32767)) for v in track))
print(f"wrote {out_path}: {seconds}s, {len(sys.argv) - 3} cues")
