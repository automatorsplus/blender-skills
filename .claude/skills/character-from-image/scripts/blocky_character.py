"""Build a blocky (voxel-style) character from a JSON spec, pose it, animate it and render it. Blender never opens.

Run:
  blender -b --factory-startup -P blocky_character.py -- --spec character.json --action wave --out renders/wave
  blender -b --factory-startup -P blocky_character.py -- --spec character.json --still --out renders/still
  blender -b --factory-startup -P blocky_character.py -- --spec character.json --action hop --preview --out renders/p

Flags:
  --spec PATH     the character, see SKILL.md for every field (only body_color is required)
  --action NAME   stand | wave | hop | run | cheer | dance (default: wave)
  --engine NAME   eevee | cycles (default: eevee, fast on a laptop)
  --frames N      default 150 (5 s at 30 fps)
  --width/--height, --pct, --samples, --only, --still, --preview   as in headless-render's scene_template.py

Every part is a softly bevelled box parented to a joint, so a pose is a set of joint rotations in degrees.
Facing: the face looks down -Y. Swinging a limb forward is a negative X rotation at shoulder or hip.
"""
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
opts = {"--out": "renders", "--spec": "", "--action": "wave", "--engine": "eevee", "--frames": "150", "--fps": "30",
        "--width": "1920", "--height": "1080", "--pct": "100", "--samples": "", "--only": ""}
flags, i = set(), 0
while i < len(argv):
    if argv[i] in ("--still", "--preview"):
        flags.add(argv[i]); i += 1
    else:
        opts[argv[i]] = argv[i + 1]; i += 2
OUT = os.path.abspath(opts["--out"])
os.makedirs(OUT, exist_ok=True)
FPS, FRAMES = int(opts["--fps"]), int(opts["--frames"])
if "--preview" in flags:
    opts["--pct"] = opts["--pct"] if opts["--pct"] != "100" else "50"
    opts["--samples"] = opts["--samples"] or "16"
    opts["--only"] = opts["--only"] or ",".join(str(1 + round(k * (FRAMES - 1) / 5)) for k in range(6))

DEFAULT = {"body_color": "#F0531F", "accent_color": None, "eye_color": "#0A0A0C", "eye_glow": False,
           "eye_style": "slots", "head": [1.42, 1.18, 1.12], "ears": "cubes", "torso": [1.0, 0.72, 0.95],
           "limb_thickness": 1.0, "roughness": 0.5, "floor_color": "#0E0E12", "backdrop_glow": None}
spec = dict(DEFAULT)
if opts["--spec"]:
    spec.update(json.load(open(opts["--spec"])))


def lin(hexcol):
    """#RRGGBB to linear RGB, which is what Blender's colour inputs expect."""
    h = hexcol.lstrip("#")
    c = [int(h[k:k + 2], 16) / 255 for k in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, FRAMES
scene.render.fps = FPS
scene.render.resolution_x, scene.render.resolution_y = int(opts["--width"]), int(opts["--height"])
scene.render.resolution_percentage = int(opts["--pct"])
scene.render.image_settings.file_format = "PNG"


def mat(name, color, rough=0.5, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def joint(name, parent, loc):
    o = bpy.data.objects.new(name, None)
    scene.collection.objects.link(o)
    o.parent, o.location, o.rotation_mode = parent, loc, "XYZ"
    return o


def box(name, size, loc, parent, material, bevel=0.045):
    me = bpy.data.meshes.new(name)
    sx, sy, sz = (s / 2 for s in size)
    me.from_pydata([(x, y, z) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    me.materials.append(material)
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.parent, o.location = parent, loc
    if bevel:
        mod = o.modifiers.new("Bevel", "BEVEL")
        mod.width, mod.segments = min(bevel, min(size) * 0.3), 3
    for p in me.polygons:
        p.use_smooth = True
    return o


# ---------------------------------------------------------------- the rig
body_m = mat("body", lin(spec["body_color"]), spec["roughness"])
acc_m = mat("accent", lin(spec["accent_color"]), spec["roughness"]) if spec["accent_color"] else body_m
eye_m = mat("eye", lin(spec["eye_color"]), 0.25, 6.0 if spec["eye_glow"] else 0.0)
T = spec["limb_thickness"]
hx, hy, hz = spec["head"]
tx, ty, tz = spec["torso"]

root = joint("root", None, (0, 0, 0))
body = joint("body", root, (0, 0, 1.85))
hips = joint("hips", body, (0, 0, -0.35))
spine = joint("spine", hips, (0, 0, 0.15))
neck = joint("neck", spine, (0, 0, tz))
head = joint("head", neck, (0, 0, 0.14))
J = {"root": root, "body": body, "hips": hips, "spine": spine, "neck": neck, "head": head}

box("pelvis", (tx * 0.9, ty * 0.76, 0.3), (0, 0, 0), hips, acc_m)
box("torso", (tx, ty, tz), (0, 0, tz / 2), spine, body_m, 0.06)
box("neckblock", (0.36, 0.32, 0.16), (0, 0, 0.07), neck, body_m, 0.03)
box("headbox", (hx, hy, hz), (0, 0, hz / 2), head, body_m, 0.08)
for s in (-1, 1):
    if spec["ears"] == "cubes":
        box(f"ear{s}", (0.2, 0.2, 0.3), (hx * 0.34 * s, 0.08, hz + 0.12), head, body_m, 0.035)
    elif spec["ears"] == "tall":
        box(f"ear{s}", (0.22, 0.16, 0.6), (hx * 0.3 * s, 0.05, hz + 0.27), head, body_m, 0.04)
    elif spec["ears"] == "side":
        box(f"ear{s}", (0.14, 0.3, 0.34), ((hx / 2 + 0.07) * s, 0.0, hz * 0.55), head, acc_m, 0.03)
    eye_y = -hy / 2 - 0.005
    if spec["eye_style"] == "slots":
        box(f"eye{s}", (0.19, 0.05, 0.38), (hx * 0.2 * s, eye_y, hz * 0.52), head, eye_m, 0.015)
    elif spec["eye_style"] == "square":
        box(f"eye{s}", (0.26, 0.05, 0.26), (hx * 0.21 * s, eye_y, hz * 0.55), head, eye_m, 0.015)
    elif spec["eye_style"] == "visor" and s == 1:
        box("visor", (hx * 0.7, 0.05, 0.22), (0, eye_y, hz * 0.55), head, eye_m, 0.02)

for side, s in (("l", -1), ("r", 1)):
    sh = joint(f"shoulder_{side}", spine, ((tx / 2 + 0.14) * s, 0, tz * 0.84))
    box(f"shcap_{side}", (0.36 * T, 0.42 * T, 0.36 * T), (0.03 * s, 0, -0.04), sh, acc_m)
    box(f"uarm_{side}", (0.31 * T, 0.33 * T, 0.44), (0, 0, -0.38), sh, body_m)
    el = joint(f"elbow_{side}", sh, (0, 0, -0.62))
    box(f"farm_{side}", (0.3 * T, 0.31 * T, 0.42), (0, 0, -0.22), el, body_m)
    box(f"hand_{side}", (0.37 * T, 0.34 * T, 0.33 * T), (0, -0.02, -0.58), el, acc_m)
    hp = joint(f"hip_{side}", hips, (0.24 * s, 0, -0.08))
    box(f"thigh_{side}", (0.38 * T, 0.4 * T, 0.52), (0, 0, -0.43), hp, body_m)
    kn = joint(f"knee_{side}", hp, (0, 0, -0.72))
    box(f"shin_{side}", (0.36 * T, 0.38 * T, 0.46), (0, 0, -0.2), kn, body_m)
    box(f"boot_{side}", (0.5 * T, 0.74 * T, 0.2), (0, -0.11, -0.6), kn, acc_m)
    J.update({f"shoulder_{side}": sh, f"elbow_{side}": el, f"hip_{side}": hp, f"knee_{side}": kn})

# ---------------------------------------------------------------- poses
POSED = ("body", "hips", "spine", "neck", "head", "shoulder_l", "shoulder_r", "elbow_l", "elbow_r",
         "hip_l", "hip_r", "knee_l", "knee_r")
STAND = {"shoulder_l": (0, 0, -6), "shoulder_r": (0, 0, 6), "elbow_l": (-12, 0, 0), "elbow_r": (-12, 0, 0)}
CROUCH = {"spine": (22, 0, 0), "head": (-12, 0, 0), "hip_l": (-62, 0, 0), "hip_r": (-62, 0, 0), "knee_l": (88, 0, 0),
          "knee_r": (88, 0, 0), "shoulder_l": (55, 0, -12), "shoulder_r": (55, 0, 12), "elbow_l": (-30, 0, 0), "elbow_r": (-30, 0, 0)}
LAUNCH = {"spine": (-6, 0, 0), "head": (-8, 0, 0), "hip_l": (8, 0, 0), "hip_r": (-10, 0, 0), "knee_l": (10, 0, 0),
          "knee_r": (25, 0, 0), "shoulder_l": (-160, 0, -18), "shoulder_r": (-160, 0, 18), "elbow_l": (-15, 0, 0), "elbow_r": (-15, 0, 0)}
TUCK = {"spine": (18, 0, 0), "hip_l": (-60, 0, 0), "hip_r": (-60, 0, 0), "knee_l": (80, 0, 0), "knee_r": (80, 0, 0),
        "shoulder_l": (-70, 0, -25), "shoulder_r": (-70, 0, 25), "elbow_l": (-60, 0, 0), "elbow_r": (-60, 0, 0)}
CHEER = {"spine": (-6, 0, 0), "head": (-10, 0, 0), "shoulder_l": (-165, 0, -28), "shoulder_r": (-165, 0, 28),
         "elbow_l": (-10, 0, 0), "elbow_r": (-10, 0, 0)}


def blend(a, b, u):
    return {j: tuple(x + (y - x) * u for x, y in zip(a.get(j, (0, 0, 0)), b.get(j, (0, 0, 0)))) for j in POSED}


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def wave_pose(t):
    w = math.sin(t * 10.0)
    return {"spine": (-3, 0, 2), "head": (-6, 0, 6), "shoulder_l": (0, 0, -6), "elbow_l": (-12, 0, 0),
            "shoulder_r": (0, -150, 0), "elbow_r": (0, -15 + 28 * w, 0)}


def run_pose(ph):
    s, c = math.sin(ph), math.cos(ph)
    return {"spine": (10, 0, 4 * s), "head": (-6, 0, -3 * s), "hip_l": (-38 * s - 5, 0, 0), "hip_r": (38 * s - 5, 0, 0),
            "knee_l": (12 + 62 * max(0.0, c), 0, 0), "knee_r": (12 + 62 * max(0.0, -c), 0, 0),
            "shoulder_l": (42 * s, 0, -8), "shoulder_r": (-42 * s, 0, 8), "elbow_l": (-75, 0, 0), "elbow_r": (-75, 0, 0)}


def apply(frame, angles, lift=0.0, x=0.0, turn=0.0):
    for j in POSED:
        J[j].rotation_euler = tuple(math.radians(v) for v in angles.get(j, (0, 0, 0)))
        J[j].keyframe_insert("rotation_euler", frame=frame)
    root.location = (x, 0, lift)
    root.rotation_euler = (0, 0, math.radians(turn))
    root.keyframe_insert("location", frame=frame)
    root.keyframe_insert("rotation_euler", frame=frame)


action = opts["--action"]
for f in range(1, FRAMES + 1):
    t = (f - 1) / FPS
    if action == "stand":
        apply(f, blend(STAND, {"spine": (0, 0, 2), "head": (-4, 0, 4)}, 0.5 + 0.5 * math.sin(t * 1.5)))
    elif action == "wave":
        apply(f, blend(STAND, wave_pose(t), smooth(t / 0.6)))
    elif action == "cheer":
        k = abs(math.sin(t * 4))
        apply(f, blend(STAND, CHEER, smooth(t / 0.4)), lift=0.25 * k)
    elif action == "run":
        apply(f, run_pose(t * 9.0), lift=0.06 * abs(math.sin(t * 9.0)))
    elif action == "dance":
        apply(f, {"spine": (0, 8 * math.sin(t * 6), 10 * math.sin(t * 3)), "head": (-5, 0, -12 * math.sin(t * 3)),
                  "shoulder_l": (-90 + 50 * math.sin(t * 6), 0, -30), "shoulder_r": (-90 - 50 * math.sin(t * 6), 0, 30),
                  "elbow_l": (-60, 0, 0), "elbow_r": (-60, 0, 0), "hip_l": (-10 * max(0, math.sin(t * 6)), 0, 0),
                  "hip_r": (-10 * max(0, -math.sin(t * 6)), 0, 0)}, lift=0.05 * abs(math.sin(t * 6)), turn=15 * math.sin(t * 3))
    elif action == "hop":                                    # a hop every 1.25 s: crouch, launch, tuck, land
        period = 1.25
        p = (t % period) / period
        if p < 0.2:
            pose, lift = blend(STAND, CROUCH, smooth(p / 0.2)), 0.0
        elif p < 0.35:
            pose, lift = blend(CROUCH, LAUNCH, smooth((p - 0.2) / 0.15)), 0.0
        elif p < 0.8:
            q = (p - 0.35) / 0.45
            pose, lift = blend(LAUNCH, TUCK, math.sin(math.pi * q)), 1.1 * math.sin(math.pi * q)
        else:
            pose, lift = blend(CROUCH, STAND, smooth((p - 0.8) / 0.2)), 0.0
        apply(f, pose, lift=lift)

# ---------------------------------------------------------------- studio
bpy.ops.mesh.primitive_plane_add(size=60)
floor = bpy.context.object
fm = mat("floor", lin(spec["floor_color"]), 0.18)
floor.data.materials.append(fm)
if spec["backdrop_glow"]:
    # a soft neon bar low behind the character, not a flat lit wall
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 5.5, 0.6), rotation=(math.radians(90), 0, 0))
    bar = bpy.context.object
    bar.scale = (9.0, 0.18, 1)
    bar.data.materials.append(mat("glow", lin(spec["backdrop_glow"]), 0.5, 12.0))
    gl = bpy.data.lights.new("glow", "AREA")
    gl.shape, gl.size, gl.size_y = "RECTANGLE", 9.0, 0.6
    gl.energy, gl.color = 350, lin(spec["backdrop_glow"])
    glo = bpy.data.objects.new("glow", gl)
    scene.collection.objects.link(glo)
    glo.location, glo.rotation_euler = (0, 5.3, 0.6), (math.radians(-90), 0, 0)


def area(loc, target, energy, size, color=(1, 1, 1)):
    d = bpy.data.lights.new("a", "AREA")
    d.energy, d.size, d.color = energy, size, color
    o = bpy.data.objects.new("a", d)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


C = (0, 0, 2.1)
area((-4, -4.5, 5), C, 1400, 4)                              # key
area((5, -2.5, 3), C, 500, 4, (0.7, 0.8, 1.0))               # fill
area((0, 4, 5.5), C, 1100, 3)                                # rim
scene.world = bpy.data.worlds.new("w")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.008, 0.008, 0.01, 1)

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
scene.collection.objects.link(cam)
cam.data.lens = 35
scene.camera = cam
for f in range(1, FRAMES + 1):
    u = smooth((f - 1) / max(1, FRAMES - 1))
    pos = Vector((1.6 - 1.0 * u, -11.0 + 1.6 * u, 2.9))
    cam.location = pos
    cam.rotation_euler = (Vector(C) - pos).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)

# ---------------------------------------------------------------- engine and render
if opts["--engine"] == "cycles":
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            if any(d.type != "CPU" for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type != "CPU"
                scene.cycles.device = "GPU"
                break
        except TypeError:
            continue
    scene.cycles.samples = int(opts["--samples"] or 64)
    scene.cycles.use_denoising = True
else:
    for ident in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = ident
            break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = int(opts["--samples"] or 32)
    if hasattr(scene.eevee, "use_raytracing"):
        scene.eevee.use_raytracing = True
scene.view_settings.view_transform = "AgX"

frames = [1] if "--still" in flags else ([int(x) for x in opts["--only"].split(",")] if opts["--only"] else list(range(1, FRAMES + 1)))
times = []
for f in frames:
    scene.frame_set(f)
    scene.render.filepath = os.path.join(OUT, "still.png" if "--still" in flags else f"f_{f:04d}.png")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    times.append(time.time() - t0)
    print(f"[render] frame {f} in {times[-1]:.1f}s ({len(times)}/{len(frames)})", flush=True)
with open(os.path.join(OUT, "timing.json"), "w") as fh:
    json.dump({"engine": opts["--engine"], "pct": int(opts["--pct"]),
               "samples": int(opts["--samples"] or (64 if opts["--engine"] == "cycles" else 32)),
               "width": int(opts["--width"]), "height": int(opts["--height"]), "frames_in_shot": FRAMES,
               "frames_rendered": frames, "seconds_per_frame": round(sum(times) / max(1, len(times)), 2)}, fh, indent=2)
print(f"[render] done: {len(frames)} frame(s) in {OUT}")
