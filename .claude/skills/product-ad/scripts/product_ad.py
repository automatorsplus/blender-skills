"""A product ad in one script: your label on a can or bottle, turning in a dark studio while ice and droplets burst
around it in slow motion. Strip lights down the sides, a coloured glow behind, a slow camera push. Cycles.

Run (Blender never opens):
  blender -b --factory-startup -P product_ad.py -- --label label.png --out renders/preview --preview
  blender -b --factory-startup -P product_ad.py -- --label label.png --out renders/final

Flags:
  --label PATH      the label artwork, a PNG. It wraps once around the product. 2:1 or wider looks right on a can.
  --product NAME    can | bottle (default: can)
  --accent R,G,B    colour of the warm strip light and the backdrop glow, 0-1 (default: 1,0.55,0.25 orange)
  --burst NAME      ice | droplets | none (default: ice, which brings droplets with it)
  --condensation    on | off (default: on)
  --frames N        length in frames (default 150, 5 seconds at 30 fps)
  --width/--height  output size (default 1920x1080; 1080x1920 renders a true vertical, re-framed for it)
  --pct, --samples, --only, --preview   as in headless-render's scene_template.py

Writes timing.json beside the frames, for preview-first's estimate.py.
"""
import json
import math
import os
import random
import sys
import time

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
opts = {"--out": "renders", "--label": "", "--product": "can", "--accent": "1,0.55,0.25", "--burst": "ice",
        "--condensation": "on", "--frames": "150", "--fps": "30", "--width": "1920", "--height": "1080",
        "--pct": "100", "--samples": "", "--only": ""}
flags, i = set(), 0
while i < len(argv):
    if argv[i] == "--preview":
        flags.add(argv[i]); i += 1
    else:
        opts[argv[i]] = argv[i + 1]; i += 2

OUT = os.path.abspath(opts["--out"])
os.makedirs(OUT, exist_ok=True)
FPS, FRAMES = int(opts["--fps"]), int(opts["--frames"])
W, H = int(opts["--width"]), int(opts["--height"])
VERTICAL = H > W
ACCENT = tuple(float(x) for x in opts["--accent"].split(","))
if "--preview" in flags:
    opts["--pct"] = opts["--pct"] if opts["--pct"] != "100" else "50"
    opts["--samples"] = opts["--samples"] or "16"
    opts["--only"] = opts["--only"] or ",".join(str(1 + round(k * (FRAMES - 1) / 5)) for k in range(6))
SAMPLES = int(opts["--samples"] or 96)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, FRAMES
scene.render.fps = FPS
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.render.resolution_percentage = int(opts["--pct"])
scene.render.image_settings.file_format = "PNG"
rnd = random.Random(4)


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def math_(nt, op, a, b=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for idx, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[idx].default_value = v
        else:
            nt.links.new(v, n.inputs[idx])
    return n.outputs[0]


# ---------------------------------------------------------------- the product, spun from a profile (radius, height)
PROFILES = {
    "can": ([(0.0, 0.035), (0.12, 0.04), (0.2, 0.03), (0.245, 0.008), (0.27, 0.0), (0.295, 0.006), (0.318, 0.03),
             (0.33, 0.09), (0.33, 1.14), (0.326, 1.18), (0.3, 1.235), (0.276, 1.29), (0.268, 1.315), (0.273, 1.333),
             (0.27, 1.347), (0.258, 1.352), (0.25, 1.336), (0.245, 1.326), (0.0, 1.326)], 0.09, 1.14, 0.68),
    "bottle": ([(0.0, 0.0), (0.27, 0.0), (0.3, 0.03), (0.31, 0.1), (0.31, 0.95), (0.29, 1.08), (0.22, 1.22),
                (0.13, 1.36), (0.11, 1.5), (0.11, 1.62), (0.125, 1.64), (0.125, 1.7), (0.0, 1.7)], 0.18, 0.92, 0.85),
}
profile, LABEL_Z0, LABEL_Z1, MID = PROFILES[opts["--product"]]
me = bpy.data.meshes.new("product")
bm = bmesh.new()
vs = [bm.verts.new((r, 0, z)) for r, z in profile]
for a, b in zip(vs, vs[1:]):
    bm.edges.new((a, b))
bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi, steps=160,
               use_duplicate=False)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(me)
bm.free()
body = bpy.data.objects.new("product", me)
scene.collection.objects.link(body)
for p in me.polygons:
    p.use_smooth = True
root = bpy.data.objects.new("product_root", None)            # turns about its own middle
scene.collection.objects.link(root)
body.parent = root
body.location = (0, 0, -MID)

# Material: label inside the band, bare metal (can) or glass (bottle) outside it.
mat = bpy.data.materials.new("product")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.remove(nt.nodes["Principled BSDF"])
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], sep.inputs[0])
ang = math_(nt, "ARCTAN2", sep.outputs["Y"], sep.outputs["X"])
u = math_(nt, "FRACT", math_(nt, "ADD", math_(nt, "DIVIDE", ang, 2 * math.pi), 0.75))   # seam at the back
v = math_(nt, "DIVIDE", math_(nt, "SUBTRACT", sep.outputs["Z"], LABEL_Z0), LABEL_Z1 - LABEL_Z0)
uvv = nt.nodes.new("ShaderNodeCombineXYZ")
nt.links.new(u, uvv.inputs[0])
nt.links.new(v, uvv.inputs[1])
lab = nt.nodes.new("ShaderNodeBsdfPrincipled")
if opts["--label"]:
    img = nt.nodes.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(os.path.abspath(opts["--label"]))
    img.extension = "EXTEND"
    nt.links.new(uvv.outputs[0], img.inputs["Vector"])
    nt.links.new(img.outputs["Color"], lab.inputs["Base Color"])
else:
    lab.inputs["Base Color"].default_value = (*ACCENT, 1)
frost = node(nt, "ShaderNodeTexNoise", Scale=380.0, Detail=2.0)
bump = node(nt, "ShaderNodeBump", Strength=0.12)
nt.links.new(frost.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], lab.inputs["Normal"])
lab.inputs["Metallic"].default_value = 0.55 if opts["--product"] == "can" else 0.0
lab.inputs["Roughness"].default_value = 0.32
lab.inputs["Coat Weight"].default_value = 0.6
lab.inputs["Coat Roughness"].default_value = 0.12
outside = nt.nodes.new("ShaderNodeBsdfPrincipled")
if opts["--product"] == "can":
    outside.inputs["Base Color"].default_value = (0.82, 0.82, 0.85, 1)
    outside.inputs["Metallic"].default_value = 1.0
    outside.inputs["Roughness"].default_value = 0.17
else:
    outside.inputs["Base Color"].default_value = (0.75, 0.9, 0.8, 1)
    outside.inputs["Transmission Weight"].default_value = 1.0
    outside.inputs["IOR"].default_value = 1.5
    outside.inputs["Roughness"].default_value = 0.02
inside = math_(nt, "MULTIPLY", math_(nt, "GREATER_THAN", sep.outputs["Z"], LABEL_Z0),
               math_(nt, "LESS_THAN", sep.outputs["Z"], LABEL_Z1))
mix = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(inside, mix.inputs[0])
nt.links.new(outside.outputs[0], mix.inputs[1])
nt.links.new(lab.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
me.materials.append(mat)

# ---------------------------------------------------------------- water
water = bpy.data.materials.new("water")
water.use_nodes = True
wb = water.node_tree.nodes["Principled BSDF"]
wb.inputs["Base Color"].default_value = (1, 1, 1, 1)
wb.inputs["Transmission Weight"].default_value = 1.0
wb.inputs["IOR"].default_value = 1.333
wb.inputs["Roughness"].default_value = 0.0

if opts["--condensation"] == "on":
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.0)
    drop = bpy.context.active_object
    drop.scale = (1, 1, 0.45)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_smooth()
    drop.data.materials.append(water)
    drop.hide_render = drop.hide_viewport = True
    g = bpy.data.node_groups.new("condensation", "GeometryNodeTree")
    g.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi, go = g.nodes.new("NodeGroupInput"), g.nodes.new("NodeGroupOutput")
    dist = g.nodes.new("GeometryNodeDistributePointsOnFaces")
    dist.inputs["Density"].default_value = 900.0
    sepz = g.nodes.new("ShaderNodeSeparateXYZ")
    g.links.new(g.nodes.new("GeometryNodeInputPosition").outputs[0], sepz.inputs[0])
    c1 = g.nodes.new("FunctionNodeCompare")
    c1.data_type, c1.operation = "FLOAT", "GREATER_THAN"
    c1.inputs["B"].default_value = LABEL_Z0 + 0.04
    g.links.new(sepz.outputs["Z"], c1.inputs["A"])
    c2 = g.nodes.new("FunctionNodeCompare")
    c2.data_type, c2.operation = "FLOAT", "LESS_THAN"
    c2.inputs["B"].default_value = LABEL_Z1 - 0.02
    g.links.new(sepz.outputs["Z"], c2.inputs["A"])
    band = g.nodes.new("FunctionNodeBooleanMath")
    band.operation = "AND"
    g.links.new(c1.outputs[0], band.inputs[0])
    g.links.new(c2.outputs[0], band.inputs[1])
    g.links.new(gi.outputs[0], dist.inputs["Mesh"])
    g.links.new(band.outputs[0], dist.inputs["Selection"])
    oi = g.nodes.new("GeometryNodeObjectInfo")
    oi.inputs["Object"].default_value = drop
    iop = g.nodes.new("GeometryNodeInstanceOnPoints")
    align = g.nodes.new("FunctionNodeAlignRotationToVector")
    align.axis = "Z"
    g.links.new(dist.outputs["Normal"], align.inputs["Vector"])
    rs = g.nodes.new("FunctionNodeRandomValue")
    rs.data_type = "FLOAT"
    for sk in rs.inputs:                                      # socket order moved in Blender 5, so pick by name and type
        if sk.type == "VALUE" and sk.name in ("Min", "Max"):
            sk.default_value = 0.0 if sk.name == "Min" else 1.0
    pw = g.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 3.0
    g.links.new(next(o for o in rs.outputs if o.type == "VALUE"), pw.inputs[0])
    sc = g.nodes.new("ShaderNodeMath")
    sc.operation = "MULTIPLY_ADD"
    sc.inputs[1].default_value, sc.inputs[2].default_value = 0.026, 0.006
    g.links.new(pw.outputs[0], sc.inputs[0])
    g.links.new(dist.outputs["Points"], iop.inputs["Points"])
    g.links.new(oi.outputs["Geometry"], iop.inputs["Instance"])
    g.links.new(align.outputs[0], iop.inputs["Rotation"])
    g.links.new(sc.outputs[0], iop.inputs["Scale"])
    join = g.nodes.new("GeometryNodeJoinGeometry")
    g.links.new(gi.outputs[0], join.inputs[0])
    g.links.new(iop.outputs[0], join.inputs[0])
    g.links.new(join.outputs[0], go.inputs[0])
    body.modifiers.new("condensation", "NODES").node_group = g

pieces = []
if opts["--burst"] in ("ice", "droplets"):
    if opts["--burst"] == "ice":
        ice = bpy.data.materials.new("ice")
        ice.use_nodes = True
        ib = ice.node_tree.nodes["Principled BSDF"]
        ib.inputs["Base Color"].default_value = (0.9, 0.96, 1.0, 1)
        ib.inputs["Transmission Weight"].default_value = 1.0
        ib.inputs["IOR"].default_value = 1.31
        ib.inputs["Roughness"].default_value = 0.06
        inz = node(ice.node_tree, "ShaderNodeTexNoise", Scale=5.0, Detail=10.0)
        ibump = node(ice.node_tree, "ShaderNodeBump", Strength=0.35)
        ice.node_tree.links.new(inz.outputs["Fac"], ibump.inputs["Height"])
        ice.node_tree.links.new(ibump.outputs["Normal"], ib.inputs["Normal"])
        bpy.ops.mesh.primitive_cube_add(size=1)
        shape = bpy.context.active_object
        bv = shape.modifiers.new("B", "BEVEL")
        bv.width, bv.segments = 0.12, 4
        bpy.ops.object.modifier_apply(modifier="B")
        bpy.ops.object.shade_smooth()
        shape.data.materials.append(ice)
        cube_mesh = shape.data
        bpy.data.objects.remove(shape)
        for _ in range(14):
            o = bpy.data.objects.new("ice", cube_mesh)
            scene.collection.objects.link(o)
            a = rnd.uniform(0, 2 * math.pi)
            d = Vector((math.cos(a) * 1.3, -abs(math.sin(a)) * 0.9 - 0.2, rnd.uniform(-0.55, 0.75))).normalized()
            pieces.append((o, d, rnd.uniform(0.85, 1.45), rnd.uniform(0.17, 0.26),
                           Vector([rnd.uniform(-1.6, 1.6) for _ in range(3)]), Vector([rnd.uniform(0, 6.28) for _ in range(3)])))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=1.0)
    sphere = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    sphere.data.materials.append(water)
    sphere_mesh = sphere.data
    bpy.data.objects.remove(sphere)
    for _ in range(140):
        o = bpy.data.objects.new("droplet", sphere_mesh)
        scene.collection.objects.link(o)
        a = rnd.uniform(0, 2 * math.pi)
        d = Vector((math.cos(a), rnd.uniform(-1.0, 0.3), rnd.uniform(-0.4, 0.9))).normalized()
        pieces.append((o, d, rnd.uniform(1.2, 2.4), rnd.uniform(0.008, 0.03), Vector((0, 0, 0)), Vector((0, 0, 0))))

# ---------------------------------------------------------------- animation: slow turn, slow-motion burst
for f in range(1, FRAMES + 1):
    t = (f - 1) / FPS
    uu = t / (FRAMES / FPS)
    root.location = (0, 0, MID + 0.04 * math.sin(t * 1.3))
    root.rotation_euler = (math.radians(6), math.radians(-8 + 4 * uu), math.radians(-28 + 56 * smooth(uu)))
    root.keyframe_insert("location", frame=f)
    root.keyframe_insert("rotation_euler", frame=f)
    k = t + 0.35                                              # the burst started just before frame one
    for (o, d, speed, s, spin, rot0) in pieces:
        r = 0.42 + speed * 0.95 * (1 - math.exp(-k * 0.42))
        o.location = Vector((0, 0.15, MID)) + d * r + Vector((0, 0, -0.05 * k * k))
        o.scale = (s, s, s * 0.9)
        o.rotation_euler = tuple(rot0 + spin * k * 0.4)
        o.keyframe_insert("location", frame=f)
        o.keyframe_insert("rotation_euler", frame=f)
        o.keyframe_insert("scale", frame=f)

# ---------------------------------------------------------------- studio
back_m = bpy.data.materials.new("backdrop")
back_m.use_nodes = True
bt = back_m.node_tree
bt.nodes.remove(bt.nodes["Principled BSDF"])
grad = bt.nodes.new("ShaderNodeTexGradient")
grad.gradient_type = "SPHERICAL"
mp = bt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (2.6, 4.0, 1)
bt.links.new(bt.nodes.new("ShaderNodeTexCoord").outputs["Object"], mp.inputs["Vector"])
bt.links.new(mp.outputs[0], grad.inputs["Vector"])
ramp = bt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
ramp.color_ramp.elements[1].color = (ACCENT[0] * 0.05, ACCENT[1] * 0.05, ACCENT[2] * 0.05, 1)
bt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
em = node(bt, "ShaderNodeEmission", Strength=1.0)
bt.links.new(ramp.outputs["Color"], em.inputs["Color"])
bt.links.new(em.outputs[0], bt.nodes["Material Output"].inputs["Surface"])
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 6, MID), rotation=(math.radians(90), 0, 0))
back = bpy.context.active_object
back.scale = (18, 11, 1)
back.data.materials.append(back_m)


def strip(loc, target, energy, sx, sy, color):
    bpy.ops.object.light_add(type="AREA", location=loc)
    lo = bpy.context.active_object
    lo.data.shape = "RECTANGLE"
    lo.data.size, lo.data.size_y = sx, sy
    lo.data.energy, lo.data.color = energy, color
    lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    lo.visible_camera = False


C = (0, 0, MID)
strip((-2.3, 1.2, MID + 0.1), C, 420, 0.22, 4.0, ACCENT)                  # accent strip, left
strip((2.3, 1.1, MID + 0.1), C, 480, 0.22, 4.0, (0.75, 0.85, 1.0))        # cool strip, right
strip((0, 0.4, MID + 2.9), C, 160, 2.0, 2.0, (1.0, 0.97, 0.92))           # top soft box
strip((-1.8, -3.8, MID + 1.2), C, 110, 2.4, 2.4, (1.0, 0.93, 0.85))       # soft key
scene.world = bpy.data.worlds.new("w")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)

# ---------------------------------------------------------------- camera: slow push and drift
bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.data.lens = 60
cam.data.sensor_fit = "HORIZONTAL"                            # the product fills the width in either orientation
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 2.8
cam.data.dof.focus_object = root
scene.camera = cam
back_off = 0.62 if VERTICAL else 1.0
for f in range(1, FRAMES + 1):
    uu = smooth(((f - 1) / FPS) / (FRAMES / FPS))
    pos = Vector((0.9 - 1.3 * uu, (-5.7 + 0.9 * uu) * back_off, MID + 0.17 + 0.2 * uu))
    cam.location = pos
    cam.rotation_euler = (Vector(C) - pos).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)

# ---------------------------------------------------------------- Cycles, GPU when there is one
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
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 10
scene.cycles.transmission_bounces = 10
scene.cycles.glossy_bounces = 6
scene.cycles.caustics_reflective = scene.cycles.caustics_refractive = False
scene.cycles.blur_glossy = 1.0
scene.render.use_persistent_data = True
scene.render.use_motion_blur = True
scene.render.motion_blur_shutter = 0.5
scene.view_settings.view_transform = "AgX"
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass

frames = [int(x) for x in opts["--only"].split(",")] if opts["--only"] else list(range(1, FRAMES + 1))
times = []
for f in frames:
    scene.frame_set(f)
    scene.render.filepath = os.path.join(OUT, f"f_{f:04d}.png")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    times.append(time.time() - t0)
    eta = sum(times) / len(times) * (len(frames) - len(times))
    print(f"[render] frame {f} in {times[-1]:.1f}s  ({len(times)}/{len(frames)}, about {eta/60:.1f} min left)", flush=True)
with open(os.path.join(OUT, "timing.json"), "w") as fh:
    json.dump({"engine": "cycles", "pct": int(opts["--pct"]), "samples": SAMPLES, "width": W, "height": H,
               "frames_in_shot": FRAMES, "frames_rendered": frames,
               "seconds_per_frame": round(sum(times) / max(1, len(times)), 2)}, fh, indent=2)
print(f"[render] done: {len(frames)} frame(s) in {OUT}")
