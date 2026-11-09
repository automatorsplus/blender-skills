"""Starting point for a headless Blender scene. Copy it, keep the plumbing, replace build_scene().

Blender never opens. Run it with:
  blender -b --factory-startup -P scene.py -- --out renders/final
  blender -b --factory-startup -P scene.py -- --out renders/preview --preview          # quick look
  blender -b --factory-startup -P scene.py -- --out renders/stills --only 1,75,150    # chosen frames

Flags (all optional):
  --out DIR        where frames go (default: renders)
  --engine NAME    eevee | cycles (default: eevee)
  --pct N          resolution percentage (default: 100)
  --samples N      render samples (default: 64 Cycles, 32 EEVEE)
  --only 1,60,120  render just these frames
  --still          render frame 1 only and save it as still.png
  --preview        shortcut for --pct 50 --samples 16 and 6 evenly spaced frames
  --width/--height output size (default 1920x1080)
  --fps N          frames per second (default 30)
  --frames N       length in frames (default 150)

Every render writes timing.json next to the frames: seconds per frame at these settings. preview-first reads it
to estimate the full render before anyone commits to it.
"""
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

# ---------------------------------------------------------------- arguments
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
opts = {"--out": "renders", "--engine": "eevee", "--pct": "100", "--samples": "", "--only": "",
        "--width": "1920", "--height": "1080", "--fps": "30", "--frames": "150"}
flags = set()
i = 0
while i < len(argv):
    if argv[i] in ("--still", "--preview"):
        flags.add(argv[i]); i += 1
    else:
        opts[argv[i]] = argv[i + 1]; i += 2

OUT = os.path.abspath(opts["--out"])
os.makedirs(OUT, exist_ok=True)
FPS, FRAMES = int(opts["--fps"]), int(opts["--frames"])
ENGINE = opts["--engine"].lower()
if "--preview" in flags:
    opts["--pct"] = opts["--pct"] if opts["--pct"] != "100" else "50"
    opts["--samples"] = opts["--samples"] or "16"
    if not opts["--only"]:
        opts["--only"] = ",".join(str(1 + round(k * (FRAMES - 1) / 5)) for k in range(6))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, FRAMES
scene.render.fps = FPS
scene.render.resolution_x, scene.render.resolution_y = int(opts["--width"]), int(opts["--height"])
scene.render.resolution_percentage = int(opts["--pct"])
scene.render.image_settings.file_format = "PNG"


# ---------------------------------------------------------------- helpers
def look_at(obj, target):
    """Point a camera or light at a world position."""
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def material(name, color, metallic=0.0, roughness=0.5, emission=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = roughness
    if emission:
        b.inputs["Emission Color"].default_value = (*emission, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def area_light(loc, target, energy, size=2.0, color=(1, 1, 1)):
    data = bpy.data.lights.new("Area", "AREA")
    data.energy, data.size, data.color = energy, size, color
    obj = bpy.data.objects.new("Area", data)
    scene.collection.objects.link(obj)
    obj.location = loc
    look_at(obj, target)
    return obj


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


# ---------------------------------------------------------------- the scene: replace this
def build_scene():
    bpy.ops.mesh.primitive_plane_add(size=40)
    bpy.context.object.data.materials.append(material("Floor", (0.02, 0.02, 0.025), roughness=0.15))

    bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, 0, 0.6))  # half its size, so it sits on the floor
    cube = bpy.context.object
    bpy.ops.object.modifier_add(type="BEVEL")
    cube.modifiers["Bevel"].width, cube.modifiers["Bevel"].segments = 0.08, 4
    cube.data.materials.append(material("Hero", (0.85, 0.35, 0.1), metallic=0.6, roughness=0.25))
    cube.rotation_euler = (0, 0, 0)
    cube.keyframe_insert("rotation_euler", frame=1)
    cube.rotation_euler = (0, 0, math.radians(360))
    cube.keyframe_insert("rotation_euler", frame=FRAMES)

    area_light((4, -3, 5), (0, 0, 0.9), 900, size=3)
    area_light((-5, -1, 3), (0, 0, 0.9), 300, size=4, color=(0.6, 0.75, 1))
    area_light((0, 5, 4), (0, 0, 0.9), 600, size=2)

    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 50
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (0, -6.5, 2.6)
    look_at(cam, (0, 0, 0.9))
    scene.camera = cam

    scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.01, 0.01, 0.012, 1)


build_scene()


# ---------------------------------------------------------------- engine
def set_engine():
    if ENGINE == "cycles":
        scene.render.engine = "CYCLES"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
                gpus = [d for d in prefs.devices if d.type != "CPU"]
                if gpus:
                    for d in prefs.devices:
                        d.use = d.type != "CPU"
                    scene.cycles.device = "GPU"
                    print(f"[render] Cycles on GPU ({kind})")
                    break
            except TypeError:
                continue
        else:
            print("[render] Cycles on CPU (no GPU found)")
        scene.cycles.samples = int(opts["--samples"] or 64)
        scene.cycles.use_denoising = True
        scene.render.use_persistent_data = True
    else:
        # The EEVEE id changed across versions: BLENDER_EEVEE_NEXT in 4.2 to 4.x, BLENDER_EEVEE before and after.
        for ident in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
            try:
                scene.render.engine = ident
                break
            except TypeError:
                continue
        scene.eevee.taa_render_samples = int(opts["--samples"] or 32)
        if hasattr(scene.eevee, "use_raytracing"):
            scene.eevee.use_raytracing = True
    scene.view_settings.view_transform = "AgX" if "AgX" in [
        t.identifier for t in type(scene.view_settings).bl_rna.properties["view_transform"].enum_items] else "Filmic"


set_engine()

# ---------------------------------------------------------------- render
if "--still" in flags:
    frames = [1]
elif opts["--only"]:
    frames = [int(f) for f in opts["--only"].split(",") if f.strip()]
else:
    frames = list(range(1, FRAMES + 1))

times = []
for f in frames:
    scene.frame_set(f)
    scene.render.filepath = os.path.join(OUT, "still.png" if "--still" in flags else f"f_{f:04d}.png")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    times.append(time.time() - t0)
    done = len(times)
    eta = (sum(times) / done) * (len(frames) - done)
    print(f"[render] frame {f} in {times[-1]:.1f}s  ({done}/{len(frames)}, about {eta/60:.1f} min left)", flush=True)

with open(os.path.join(OUT, "timing.json"), "w") as fh:
    json.dump({"engine": ENGINE, "pct": int(opts["--pct"]), "samples": int(opts["--samples"] or (64 if ENGINE == "cycles" else 32)),
               "width": int(opts["--width"]), "height": int(opts["--height"]), "frames_in_shot": FRAMES,
               "frames_rendered": frames, "seconds_per_frame": round(sum(times) / max(1, len(times)), 2)}, fh, indent=2)
print(f"[render] done: {len(frames)} frame(s) in {OUT}")
