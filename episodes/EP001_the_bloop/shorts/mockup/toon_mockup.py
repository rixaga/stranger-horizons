"""Promo Short style mockup: S022 megalodon + ROV in the toon look, one vertical still (1080x1920).

Run in background Blender (via launch_shot.py with {"script": ...}) or:
    blender --background --factory-startup --python toon_mockup.py -- [--engine BLENDER_EEVEE] [--out PATH]
Saves toon_mockup.blend and render/toon_mockup_3d.png next to this file. The HUD / text cards are
added afterwards as a separate overlay layer (make_overlay.py), so the 3D render stays clean.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "blender" / "scripts"))
import sh_template  # noqa: E402
from sh_toon import apply_toon  # noqa: E402

FRAME = 300
NAVY = (0.010, 0.022, 0.055)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--engine", default="BLENDER_EEVEE")
ap.add_argument("--out", default=str(HERE / "render" / "toon_mockup_3d.png"))
ap.add_argument("--percent", type=int, default=100)
args = ap.parse_args(argv)

cfg = json.loads((REPO / "episodes/EP001_the_bloop/blender/templates/S022.json").read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
sh_template.build_template(cfg, 495, None)
scene = bpy.context.scene
scene.frame_set(FRAME)

for name in ("SH_Terrain", "SH_LightGobo"):
    ob = bpy.data.objects.get(name)
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
for ob in list(bpy.data.objects):
    if ob.type == "LIGHT":
        bpy.data.objects.remove(ob, do_unlink=True)

rig = bpy.data.objects["CR_Megalodon_Rig"]
shark = bpy.data.objects["CR_Megalodon"]
rov = bpy.data.objects["SH_ROV"]
m = rig.matrix_world
nose = m.translation.copy()
fwd = (m.to_3x3() @ Vector((1, 0, 0))).normalized()
side = fwd.cross(Vector((0, 0, 1))).normalized()       # shark's right
mid = nose - fwd * 6.0

# ROV just below the snout, at about the shark's distance from camera: 2.8 m vs 15 m reads as scale
up = Vector((0, 0, 1))
rov.animation_data_clear()
rov.location = nose - fwd * 3.5 + side * 4.0 - up * 7.5
to_head = nose - rov.location
rov.rotation_euler = (0, 0, math.atan2(-to_head.x, to_head.y))

cam_data = bpy.data.cameras.new("SH_Camera")
cam_data.lens = 30
cam = bpy.data.objects.new("SH_Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = mid + side * 23.0 + fwd * 2.0 - up * 3.5
target = mid - fwd * 2.0 - up * 2.2
q = (target - cam.location).to_track_quat("-Z", "Y")
from mathutils import Quaternion  # noqa: E402
roll = Quaternion((target - cam.location).normalized(), math.radians(16))  # dutch angle: diagonal in 9:16
cam.rotation_euler = (roll @ q).to_euler()
scene.camera = cam


def sun(name, rot_deg, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "SUN")
    d.energy, d.color, d.angle = energy, color, math.radians(3)
    ob = bpy.data.objects.new(name, d)
    ob.rotation_euler = [math.radians(a) for a in rot_deg]
    scene.collection.objects.link(ob)


sun("SH_Key", (25, 0, -60), 6.0)
sun("SH_Rim", (120, 0, 160), 3.5, (0.55, 0.85, 1.0))

world = bpy.data.worlds.new("SH_ToonWorld")
world.use_nodes = True
wn = world.node_tree
tc = wn.nodes.new("ShaderNodeTexCoord")
sep = wn.nodes.new("ShaderNodeSeparateXYZ")
wramp = wn.nodes.new("ShaderNodeValToRGB")  # darker below, lighter towards the surface
wramp.color_ramp.elements[0].position, wramp.color_ramp.elements[0].color = 0.35, (0.004, 0.010, 0.028, 1)
wramp.color_ramp.elements[1].position, wramp.color_ramp.elements[1].color = 0.85, (0.020, 0.085, 0.150, 1)
mr = wn.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -1.0, 1.0
wn.links.new(tc.outputs["Generated"], sep.inputs[0])
wn.links.new(sep.outputs["Z"], mr.inputs["Value"])
wn.links.new(mr.outputs["Result"], wramp.inputs["Fac"])
wn.links.new(wramp.outputs["Color"], wn.nodes["Background"].inputs["Color"])
scene.world = world

apply_toon([shark], colors={"CR_Megalodon": {"top": (0.36, 0.47, 0.58), "belly": (0.86, 0.88, 0.84)}},
           outline_m=0.06)
apply_toon([rov], colors={"SH_ROV": (1.0, 0.62, 0.12)}, outline_m=0.02)
for slot in rov.material_slots[1:-1]:  # frame/float/lens slots: keep them on the channel's amber accent
    if slot.material.name.startswith("SH_Toon_"):
        slot.material = rov.material_slots[0].material

# marine snow: tiny unlit specks between camera and shark
import bmesh  # noqa: E402
import random  # noqa: E402
rng = random.Random(7)
snow_bm = bmesh.new()
for _ in range(170):
    t = rng.uniform(7.0, 32.0)
    d = (mid - cam.location).normalized()
    right = d.cross(up).normalized()
    p = cam.location + d * t + right * rng.uniform(-0.45, 0.45) * t + up * rng.uniform(-0.8, 0.8) * t
    bmesh.ops.create_icosphere(snow_bm, subdivisions=1, radius=rng.uniform(0.015, 0.045),
                               matrix=__import__("mathutils").Matrix.Translation(p))
snow_me = bpy.data.meshes.new("SH_MarineSnow")
snow_bm.to_mesh(snow_me)
snow = bpy.data.objects.new("SH_MarineSnow", snow_me)
scene.collection.objects.link(snow)
sm = bpy.data.materials.new("SH_MarineSnow")
sm.use_nodes = True
sm.node_tree.nodes.clear()
se = sm.node_tree.nodes.new("ShaderNodeEmission")
se.inputs["Color"].default_value = (0.75, 0.9, 1.0, 1)
se.inputs["Strength"].default_value = 1.2
so = sm.node_tree.nodes.new("ShaderNodeOutputMaterial")
sm.node_tree.links.new(se.outputs[0], so.inputs[0])
snow_me.materials.append(sm)

# stylised lamp beam: soft additive cone from the ROV nose
bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.05, radius2=1.0, depth=5)
beam = bpy.context.active_object
beam.name = "SH_ToonBeam"
aim = (nose - fwd * 2.5 - up * 0.8) - rov.location
start = rov.location + aim.normalized() * 1.4
beam.location = start + aim.normalized() * 2.5
beam.rotation_euler = aim.to_track_quat("Z", "Y").to_euler()
bm = bpy.data.materials.new("SH_ToonBeam")
bm.use_nodes = True
nt = bm.node_tree
nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.85, 0.5, 1)
em.inputs["Strength"].default_value = 0.18
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
add = nt.nodes.new("ShaderNodeAddShader")
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs[0], add.inputs[0])
nt.links.new(tr.outputs[0], add.inputs[1])
nt.links.new(add.outputs[0], out.inputs[0])
if hasattr(bm, "surface_render_method"):
    bm.surface_render_method = "BLENDED"
beam.data.materials.append(bm)

r = scene.render
r.engine = args.engine
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, args.percent
r.film_transparent = False
scene.view_settings.view_transform = "Standard"      # keep the flat palette (AgX would desaturate it)
scene.view_settings.look = "None"
if args.engine == "BLENDER_EEVEE":
    scene.eevee.taa_render_samples = 32
r.image_settings.file_format = "PNG"
r.filepath = args.out
Path(args.out).parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "toon_mockup.blend"))
bpy.ops.render.render(write_still=True)
print("TOON_MOCKUP_DONE", args.out)
