"""Toon 3D plates for the EP001 wordless Short (vertical 1080x1920, 30 fps, EEVEE).

    blender --background --factory-startup --python build_short_3d.py -- --plate all
    ... -- --plate iceberg --frames 1,90,200      (check stills only)

Writes render/<plate>/frame_####.png and render/tracks/<plate>.json (per-frame pixel anchors for
overlay callouts), plus render/<plate>.blend for editing. Frame counts come from short.json.
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
EP = HERE.parents[1]
sys.path.insert(0, str(REPO / "blender" / "scripts"))
from sh_toon import apply_toon, flat_material, marine_snow, project_track, toon_world  # noqa: E402

SHORT = json.loads((HERE / "short.json").read_text())
FPS = SHORT["fps"]
UP = Vector((0, 0, 1))
AMBER, ORANGE, TEAL = (1.0, 0.62, 0.12), (1.0, 0.42, 0.10), (0.35, 0.86, 0.92)


def frames_for(plate):
    if plate == "backdrop":
        return 1
    return sum(round(s["duration_s"] * FPS) for s in SHORT["shots"] if s["plate"] == plate)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return settings(bpy.context.scene)


def settings(sc):
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = SHORT["width"], SHORT["height"], 100
    r.fps = FPS
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    return sc


def camera(sc, loc, target, lens=32, name="SH_Camera"):
    cam = bpy.data.objects.get(name) or bpy.data.objects.new(name, bpy.data.cameras.new(name))
    if cam.name not in sc.collection.objects:
        sc.collection.objects.link(cam)
    cam.data.lens = lens
    cam.data.clip_start = 0.1
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    return cam


def key_cam(cam, frame, loc, target):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=frame)
    cam.keyframe_insert("rotation_euler", frame=frame)


def sun(sc, name, rot_deg, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "SUN")
    d.energy, d.color, d.angle = energy, color, math.radians(3)
    ob = bpy.data.objects.new(name, d)
    ob.rotation_euler = [math.radians(a) for a in rot_deg]
    sc.collection.objects.link(ob)
    return ob


def lights(sc):
    sun(sc, "SH_Key", (25, 0, -60), 6.0)
    sun(sc, "SH_Rim", (120, 0, 160), 3.5, (0.55, 0.85, 1.0))


def mesh_obj(sc, name, op, **kw):
    getattr(bpy.ops.mesh, op)(**kw)
    ob = bpy.context.active_object
    ob.name = name
    return ob


def rough(ob, strength, size=2.0, seed=0, levels=4, boxy=False):
    sub = ob.modifiers.new("sub", "SUBSURF")
    sub.levels = sub.render_levels = levels
    if boxy:  # keep straight cliffs and a flat top (tabular ice)
        sub.subdivision_type = "SIMPLE"
    tex = bpy.data.textures.new(f"{ob.name}_n", "CLOUDS")
    tex.noise_scale = size
    tex.noise_depth = 1
    d = ob.modifiers.new("disp", "DISPLACE")
    d.texture, d.strength = tex, strength
    d.texture_coords = "GLOBAL"
    ob.modifiers.new("smooth", "SMOOTH").factor = 0.4
    return ob


def rings(sc, center, normal, n, start, every, life, r1, color=TEAL, name="SH_Ring"):
    """Expanding thin rings (sound waves), each living `life` frames."""
    mat = flat_material(f"{name}_mat", color, 1.4, alpha=0.65)
    out = []
    for i in range(n):
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.025, major_segments=96, minor_segments=6)
        ob = bpy.context.active_object
        ob.name = f"{name}_{i}"
        ob.location = center
        ob.rotation_euler = Vector(normal).to_track_quat("Z", "Y").to_euler()
        ob.data.materials.append(mat)
        f0 = start + i * every
        for f, s, show in ((f0 - 1, 0.01, False), (f0, 0.3, True), (f0 + life, r1, True), (f0 + life + 1, r1, False)):
            ob.scale = (s, s, s)
            ob.keyframe_insert("scale", frame=f)
            ob.hide_render = not show
            ob.keyframe_insert("hide_render", frame=f)
        out.append(ob)
    return out


# ------------------------------------------------------------------ plates

def plate_ocean_descent(sc, n):
    toon_world(sc)
    cam = camera(sc, (0, 0, 0), (0, 10, -1.8), lens=28)
    key_cam(cam, 1, (0, 0, 0), (0, 10, -1.8))
    key_cam(cam, n, (0, 1.5, -6), (0, 11.5, -8.2))
    marine_snow(sc, (0, 9, -3), 14, count=520, seed=3)
    return {}


def plate_hydrophone(sc, n):
    toon_world(sc)
    lights(sc)
    floor = mesh_obj(sc, "SH_Seafloor", "primitive_plane_add", size=120)
    floor.location.z = -0.2
    rough(floor, 1.6, size=6.0, levels=6)
    anchor = mesh_obj(sc, "SH_Anchor", "primitive_cube_add", size=0.9, location=(0, 0, 0.35))
    cable = mesh_obj(sc, "SH_Cable", "primitive_cylinder_add", radius=0.03, depth=8.2, location=(0, 0, 4.4))
    inst = mesh_obj(sc, "SH_Hydrophone", "primitive_cylinder_add", radius=0.2, depth=1.3, location=(0, 0, 5.0))
    tip = mesh_obj(sc, "SH_Hydrophone_Tip", "primitive_uv_sphere_add", radius=0.21, location=(0, 0, 4.3))
    flt = mesh_obj(sc, "SH_Float", "primitive_uv_sphere_add", radius=0.65, location=(0, 0, 8.9))
    apply_toon([floor], {"SH_Seafloor": (0.15, 0.21, 0.27)}, outline_m=0.0)
    apply_toon([anchor, cable, tip], {"SH_Anchor": (0.25, 0.28, 0.33), "SH_Cable": (0.2, 0.22, 0.26),
                                      "SH_Hydrophone_Tip": (0.12, 0.13, 0.16)}, outline_m=0.02)
    apply_toon([inst], {"SH_Hydrophone": AMBER}, outline_m=0.025)
    apply_toon([flt], {"SH_Float": ORANGE}, outline_m=0.03)
    rings(sc, (-34, 14, 5), (0.35, -1, 0.0), n=5, start=8, every=24, life=70, r1=38)
    cam = camera(sc, (7.5, -13, 4.2), (0, 0, 4.8), lens=34)
    key_cam(cam, 1, (7.5, -13, 4.2), (0, 0, 4.8))
    key_cam(cam, n, (5.8, -10.2, 4.6), (0, 0, 5.0))
    marine_snow(sc, (0, -2, 5), 12, count=260, seed=5)
    return {"hydrophone": project_track(sc, inst, range(1, n + 1))}


def plate_megalodon(sc, n):
    import sh_template
    cfg = json.loads((EP / "blender/templates/S022.json").read_text())
    sh_template.build_template(cfg, 495, None)  # (starts a fresh file)
    sc = settings(bpy.context.scene)
    for name in ("SH_Terrain", "SH_LightGobo"):
        ob = bpy.data.objects.get(name)
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)
    for ob in list(bpy.data.objects):
        if ob.type == "LIGHT":
            bpy.data.objects.remove(ob, do_unlink=True)
    start = 200  # S022 timeline: the approach and close pass
    sc.frame_start, sc.frame_end = start, start + n - 1
    sc.frame_set(300)
    rig, shark, rov = (bpy.data.objects[k] for k in ("CR_Megalodon_Rig", "CR_Megalodon", "SH_ROV"))
    m = rig.matrix_world
    nose = m.translation.copy()
    fwd = (m.to_3x3() @ Vector((1, 0, 0))).normalized()
    side = fwd.cross(UP).normalized()
    mid = nose - fwd * 6.0
    rov.animation_data_clear()
    rov.location = nose - fwd * 3.5 + side * 4.0 - UP * 7.5
    to_head = nose - rov.location
    rov.rotation_euler = (0, 0, math.atan2(-to_head.x, to_head.y))
    cam = camera(sc, mid + side * 19.0 + fwd * 2.0 - UP * 3.0, mid - fwd * 1.0 - UP * 2.2, lens=28)
    from mathutils import Quaternion
    look = (mid - fwd * 1.0 - UP * 2.2) - cam.location
    cam.rotation_euler = (Quaternion(look.normalized(), math.radians(16)) @ look.to_track_quat("-Z", "Y")).to_euler()
    # camera drifts with the shark (75% of its travel) so it stays in frame for the whole shot
    base = cam.location.copy()
    for f in list(range(start, start + n, 10)) + [start + n - 1]:
        sc.frame_set(f)
        cam.location = base + (rig.matrix_world.translation - nose) * 0.75
        cam.keyframe_insert("location", frame=f)
    sc.frame_set(300)
    toon_world(sc)
    lights(sc)
    apply_toon([shark], {"CR_Megalodon": {"top": (0.36, 0.47, 0.58), "belly": (0.86, 0.88, 0.84)}}, outline_m=0.06)
    apply_toon([rov], {"SH_ROV": AMBER}, outline_m=0.02)
    for slot in rov.material_slots[1:-1]:
        slot.material = rov.material_slots[0].material
    marine_snow(sc, mid + side * 12, 13, count=300, seed=7)
    frames = range(start, start + n)
    return {"shark": project_track(sc, rig, frames, offset=(-6.0, 0, 0)),
            "rov": project_track(sc, rov, frames)}


def plate_iceberg(sc, n):
    toon_world(sc, bottom=(0.30, 0.42, 0.52), top=(0.62, 0.78, 0.90))
    sun(sc, "SH_Key", (40, 0, -35), 5.0)
    sun(sc, "SH_Rim", (115, 0, 150), 2.5, (0.7, 0.9, 1.0))
    water = mesh_obj(sc, "SH_Water", "primitive_plane_add", size=400)
    apply_toon([water], {"SH_Water": (0.06, 0.27, 0.38)}, outline_m=0.0)
    # tabular Antarctic-style berg: flat top, steep cliffs, split down the middle
    def slab(name, loc, dims, seed):
        ob = mesh_obj(sc, name, "primitive_cube_add", size=1, location=loc)
        ob.scale = dims
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return rough(ob, 0.45, 3.0, seed=seed, levels=5, boxy=True)
    a = slab("SH_Ice_A", (-4.7, 0, 2.6), (9.2, 8, 9), 0)
    b = slab("SH_Ice_B", (4.7, 0, 2.1), (9.2, 7.6, 8.2), 1)
    ice = {"top": (0.90, 0.97, 1.0), "belly": (0.45, 0.70, 0.86)}
    apply_toon([a, b], {"SH_Ice_A": ice, "SH_Ice_B": ice}, outline_m=0.08)
    crack_f = 75
    for ob, rot, dx, dz in ((a, -3, -0.6, -0.3), (b, 13, 3.0, -2.2)):
        ob.keyframe_insert("location", frame=crack_f)
        ob.keyframe_insert("rotation_euler", frame=crack_f)
        ob.location.x += dx
        ob.location.z += dz
        ob.rotation_euler.y = math.radians(rot)
        ob.keyframe_insert("location", frame=crack_f + 55)
        ob.keyframe_insert("rotation_euler", frame=crack_f + 55)
    glow = mesh_obj(sc, "SH_Crack", "primitive_plane_add", size=1, location=(0.1, -5.2, 3.5))
    glow.rotation_euler = (math.radians(90), 0, 0)
    glow.data.materials.append(flat_material("SH_CrackGlow", (1.0, 0.95, 0.75), 3.0, alpha=0.9))
    for f, s in ((crack_f - 8, 0.0), (crack_f, 1.0), (crack_f + 30, 0.0)):
        glow.scale = (0.5 * s, 7 * max(s, 0.01), 1)
        glow.keyframe_insert("scale", frame=f)
    rings(sc, (0.2, 0, 0.05), (0, 0, 1), n=4, start=crack_f, every=14, life=90, r1=60, color=(0.85, 0.97, 1.0))
    cam = camera(sc, (0, -40, 1.6), (0, 0, 2.6), lens=30)
    key_cam(cam, 1, (0, -40, 2.2), (0, 0, 4.6))
    key_cam(cam, n, (-2.5, -34, 1.8), (0.5, 0, 4.2))
    crack_pt = bpy.data.objects.new("SH_CrackPoint", None)
    crack_pt.location = (0, -5, 4.0)
    sc.collection.objects.link(crack_pt)
    return {"iceberg": project_track(sc, crack_pt, range(1, n + 1))}


def plate_backdrop(sc, n):
    toon_world(sc)
    camera(sc, (0, 0, 0), (0, 10, 0), lens=30)
    marine_snow(sc, (0, 10, 0), 9, count=160, seed=11)
    return {}


PLATES = {"ocean_descent": plate_ocean_descent, "hydrophone": plate_hydrophone, "megalodon": plate_megalodon,
          "iceberg": plate_iceberg, "backdrop": plate_backdrop}


def run(plate, engine, frames=None, samples=16):
    sc = reset()
    n = frames_for(plate)
    sc.frame_start, sc.frame_end = 1, n
    tracks = PLATES[plate](sc, n)
    sc = bpy.context.scene  # a plate may have started a fresh file
    r = sc.render
    r.engine = engine
    if engine == "BLENDER_EEVEE":
        sc.eevee.taa_render_samples = samples
    out = HERE / "render" / plate
    out.mkdir(parents=True, exist_ok=True)
    (HERE / "render" / "tracks").mkdir(parents=True, exist_ok=True)
    if tracks:
        (HERE / "render" / "tracks" / f"{plate}.json").write_text(json.dumps(
            {k: {str(i + 1): v[f] for i, f in enumerate(sorted(v))} for k, v in tracks.items()}))
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "render" / f"{plate}.blend"))
    r.image_settings.file_format = "PNG"
    first = sc.frame_start
    todo = [first + f - 1 for f in frames if f <= n] if frames else range(sc.frame_start, sc.frame_end + 1)
    for f in todo:
        sc.frame_set(f)
        r.filepath = str(out / f"frame_{f - first + 1:04d}.png")
        bpy.ops.render.render(write_still=True)
    print(f"PLATE_DONE {plate} {len(list(todo))} frames", flush=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--plate", default="all")
    ap.add_argument("--frames", default="")
    ap.add_argument("--engine", default="BLENDER_EEVEE")
    ap.add_argument("--samples", type=int, default=16)
    a = ap.parse_args(argv)
    fr = [int(x) for x in a.frames.split(",") if x]
    for p in (PLATES if a.plate == "all" else a.plate.split(",")):
        run(p, a.engine, fr or None, a.samples)
    print("SHORT_3D_DONE", flush=True)
