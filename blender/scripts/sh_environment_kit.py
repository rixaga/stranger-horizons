"""Reusable procedural environment kit: terrain, rock formations, boulder scatter, light gobos.

Everything is built from a JSON set config into the "SH_Set" collection, so the same
code builds a seabed, a cave floor or a desert plateau with different numbers.
Safe to rerun: the collection is cleared and rebuilt. No third-party assets.

    blender --background --factory-startup --python blender/scripts/sh_environment_kit.py -- \
        --config episodes/EP001_ocean_prototype/scripts/ep001_set.json \
        --out episodes/EP001_ocean_prototype/blender/EP001_set.blend

Config sections (all optional except terrain):
    terrain     size_m, center_m, resolution, layers[{texture, size_m, strength}], material
    formations  [{name, location_m, height_m, base_radius_m, top_radius_m, lean_m, rings, segments,
                  roughness_m, facet_size_m, strength_m, material, snap_to_ground}]
    boulders    {count, area_m [x0, y0, x1, y1], radius_m [min, max], seed, keep_clear[[x, y, r]],
                 hero[{location_m, radius_m}], material}
    gobo        {height_m, size_m, cells, open_fraction, drift_m [dx, dy], seed}
    materials   {name: {base, base2, roughness, noise_size_m, bump}}
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector, noise

COLLECTION = "SH_Set"


# ----------------------------------------------------------------- helpers

def _collection(scene, name: str = COLLECTION):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    owned = [(o.type, o.data.name) for o in col.objects if o.data is not None]
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for kind, data_name in owned:
        store = bpy.data.meshes if kind == "MESH" else None
        block = store.get(data_name) if store is not None else None
        if block is not None and block.users == 0:
            store.remove(block)
    return col


def _new_object(col, name: str, mesh):
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    return obj


def _ensure_nodes(idblock):
    if bpy.app.version < (5, 0, 0) and not idblock.use_nodes:
        idblock.use_nodes = True


def make_material(name: str, spec: dict):
    """Rock/sediment PBR material: two-tone noise colour, roughness, procedural bump. World-scale noise."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    _ensure_nodes(mat)
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 1.0 / max(spec.get("noise_size_m", 2.0), 1e-3)
    tex.inputs["Detail"].default_value = 8.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*spec.get("base", [0.05, 0.05, 0.05]), 1)
    ramp.color_ramp.elements[1].color = (*spec.get("base2", [0.12, 0.11, 0.10]), 1)
    fine = nt.nodes.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 1.0 / max(spec.get("noise_size_m", 2.0) / 12.0, 1e-3)
    fine.inputs["Detail"].default_value = 10.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = spec.get("bump", 0.4)
    nt.links.new(coord.outputs["Object"], tex.inputs["Vector"])
    nt.links.new(coord.outputs["Object"], fine.inputs["Vector"])
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(fine.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = spec.get("roughness", 0.85)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _displace(obj, name: str, texture: str, size_m: float, strength: float, seed: int = 0):
    tex = bpy.data.textures.get(name) or bpy.data.textures.new(name, texture)
    tex.noise_scale = size_m
    if texture == "CLOUDS":
        tex.noise_depth = 4
    mod = obj.modifiers.new(name, "DISPLACE")
    mod.texture = tex
    mod.texture_coords = "GLOBAL"
    mod.direction = "Z" if obj.get("sh_kind") == "terrain" else "NORMAL"
    mod.strength = strength
    mod.mid_level = 0.5
    return mod


# ----------------------------------------------------------------- builders

def make_terrain(col, cfg: dict, materials: dict):
    sx, sy = cfg.get("size_m", [200, 200])
    cx, cy = cfg.get("center_m", [0, 0])
    n = int(cfg.get("resolution", 160))
    mesh = bpy.data.meshes.new("SH_Terrain")
    verts = [(cx + (i / n - 0.5) * sx, cy + (j / n - 0.5) * sy, 0.0) for j in range(n + 1) for i in range(n + 1)]
    faces = [(j * (n + 1) + i, j * (n + 1) + i + 1, (j + 1) * (n + 1) + i + 1, (j + 1) * (n + 1) + i)
             for j in range(n) for i in range(n)]
    mesh.from_pydata(verts, [], faces)
    mesh.shade_smooth() if hasattr(mesh, "shade_smooth") else None
    obj = _new_object(col, "SH_Terrain", mesh)
    obj["sh_kind"] = "terrain"
    for k, layer in enumerate(cfg.get("layers", [])):
        _displace(obj, f"SH_Terrain_L{k}", layer.get("texture", "CLOUDS"), layer["size_m"], layer["strength"])
    obj.data.materials.append(materials[cfg.get("material", "sediment")])
    return obj


def ground_height(terrain, x: float, y: float, default: float = 0.0) -> float:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev = terrain.evaluated_get(depsgraph)
    inv = ev.matrix_world.inverted()
    hit, loc, _n, _i = ev.ray_cast(inv @ Vector((x, y, 500.0)), Vector((0, 0, -1)))
    return (ev.matrix_world @ loc).z if hit else default


def make_formation(col, cfg: dict, materials: dict, terrain=None):
    """A tapered, leaning rock spire or mound: stacked noisy rings + faceting displacement."""
    rng = random.Random(cfg.get("seed", 1))
    rings, segs = int(cfg.get("rings", 48)), int(cfg.get("segments", 40))
    h, r0, r1 = cfg["height_m"], cfg["base_radius_m"], cfg.get("top_radius_m", cfg["base_radius_m"] * 0.3)
    lean = cfg.get("lean_m", 0.0)
    rough = cfg.get("roughness_m", r0 * 0.15)
    off = Vector((rng.uniform(0, 100), rng.uniform(0, 100), rng.uniform(0, 100)))
    bm = bmesh.new()
    ring_verts = []
    for i in range(rings):
        t = i / (rings - 1)
        z = t * h
        radius = r0 + (r1 - r0) * (t ** 0.8)
        centre = Vector((lean * t * t, 0.3 * lean * math.sin(t * 3.0), z))
        row = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            d = Vector((math.cos(a), math.sin(a), 0))
            n = noise.noise(off + Vector((d.x * 1.3, d.y * 1.3, z / max(h, 1) * 4)))
            rr = max(radius + n * rough * (1.0 - 0.5 * t), 0.2)
            row.append(bm.verts.new(centre + d * rr))
        ring_verts.append(row)
    for i in range(rings - 1):
        for j in range(segs):
            a, b = ring_verts[i][j], ring_verts[i][(j + 1) % segs]
            c, d = ring_verts[i + 1][(j + 1) % segs], ring_verts[i + 1][j]
            bm.faces.new((a, b, c, d))
    bm.faces.new(ring_verts[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(cfg["name"])
    bm.to_mesh(mesh)
    bm.free()
    obj = _new_object(col, cfg["name"], mesh)
    obj["sh_kind"] = "formation"
    x, y = cfg["location_m"][:2]
    z = ground_height(terrain, x, y) - cfg.get("sink_m", 1.5) if (terrain and cfg.get("snap_to_ground", True)) \
        else (cfg["location_m"][2] if len(cfg["location_m"]) > 2 else 0.0)
    obj.location = (x, y, z)
    obj.rotation_euler.z = math.radians(cfg.get("rotation_deg", 0.0))
    if cfg.get("strength_m", 0) > 0:
        _displace(obj, f"{cfg['name']}_Facets", "VORONOI", cfg.get("facet_size_m", 2.0), cfg["strength_m"])
    obj.data.materials.append(materials[cfg.get("material", "basalt")])
    return obj


def _boulder_mesh(name: str, seed: int):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    off = Vector((seed * 7.1, seed * 3.3, seed * 1.7))
    for v in bm.verts:
        v.co *= 1.0 + 0.28 * noise.noise(off + v.co * 1.6) + 0.08 * noise.noise(off + v.co * 5.0)
        v.co.z *= 0.62
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth() if hasattr(mesh, "shade_smooth") else None
    return mesh


def scatter_boulders(col, cfg: dict, materials: dict, terrain):
    rng = random.Random(cfg.get("seed", 7))
    variants = [_boulder_mesh(f"SH_BoulderMesh_{k}", k + 1) for k in range(cfg.get("variants", 5))]
    mat = materials[cfg.get("material", "basalt")]
    for m in variants:
        m.materials.append(mat)
    x0, y0, x1, y1 = cfg["area_m"]
    rmin, rmax = cfg.get("radius_m", [0.3, 2.0])
    clear = cfg.get("keep_clear", [])
    placed = []
    for spec in cfg.get("hero", []):
        placed.append((spec["location_m"][0], spec["location_m"][1], spec["radius_m"], spec.get("variant", 0)))
    tries = 0
    while len(placed) < cfg.get("count", 80) + len(cfg.get("hero", [])) and tries < 20000:
        tries += 1
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if any((x - cx) ** 2 + (y - cy) ** 2 < cr ** 2 for cx, cy, cr in clear):
            continue
        r = rmin + (rmax - rmin) * rng.random() ** 3  # many small, few large
        placed.append((x, y, r, rng.randrange(len(variants))))
    objs = []
    for k, (x, y, r, v) in enumerate(placed):
        obj = _new_object(col, f"SH_Boulder_{k:03d}", variants[v % len(variants)])
        obj["sh_kind"] = "boulder"
        obj.location = (x, y, ground_height(terrain, x, y) - 0.25 * r)
        obj.scale = (r, r * rng.uniform(0.8, 1.2), r)
        obj.rotation_euler = (rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), rng.uniform(0, math.tau))
        objs.append(obj)
    return objs


def make_gobo(col, cfg: dict, scene):
    """A drifting perforated sheet high in the volume: breaks a sun into volumetric light shafts.
    Invisible to the camera; it only casts shadows."""
    rng = random.Random(cfg.get("seed", 3))
    n = int(cfg.get("cells", 48))
    size = cfg.get("size_m", 160)
    z = cfg.get("height_m", 50)
    open_frac = cfg.get("open_fraction", 0.25)
    off = Vector((rng.uniform(0, 50), rng.uniform(0, 50), 0))
    cell = size / n
    verts, faces = [], []
    values = sorted(noise.noise(off + Vector((i * 0.35, j * 0.35, 0))) for j in range(n) for i in range(n))
    threshold = values[int(len(values) * (1 - open_frac))]
    for j in range(n):
        for i in range(n):
            if noise.noise(off + Vector((i * 0.35, j * 0.35, 0))) >= threshold:
                continue  # an opening: light passes here
            x, y = (i - n / 2) * cell, (j - n / 2) * cell
            b = len(verts)
            verts += [(x, y, 0), (x + cell, y, 0), (x + cell, y + cell, 0), (x, y + cell, 0)]
            faces.append((b, b + 1, b + 2, b + 3))
    mesh = bpy.data.meshes.new("SH_LightGobo")
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    obj = _new_object(col, "SH_LightGobo", mesh)
    obj["sh_kind"] = "gobo"
    for attr in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        if hasattr(obj, attr):
            setattr(obj, attr, False)
    obj.location = (0, 0, z)
    dx, dy = cfg.get("drift_m", [0.0, 0.0])
    if dx or dy:
        obj.keyframe_insert("location", frame=scene.frame_start)
        obj.location = (dx, dy, z)
        obj.keyframe_insert("location", frame=scene.frame_end)
        _linear(obj)
    return obj


def _linear(obj):
    action = obj.animation_data.action
    curves = list(getattr(action, "fcurves", []) or [])
    if not curves:
        for layer in getattr(action, "layers", []):
            for strip in layer.strips:
                for bag in getattr(strip, "channelbags", []):
                    curves.extend(bag.fcurves)
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def build_set(config: dict, scene=None) -> dict:
    scene = scene or bpy.context.scene
    scene.unit_settings.system = "METRIC"
    if "frames" in config:
        scene.frame_start, scene.frame_end = config["frames"]
    col = _collection(scene)
    materials = {name: make_material(f"SH_{name}", spec) for name, spec in config.get("materials", {}).items()}
    for default in ("sediment", "basalt"):
        materials.setdefault(default, make_material(f"SH_{default}", {}))
    terrain = make_terrain(col, config["terrain"], materials)
    formations = [make_formation(col, f, materials, terrain) for f in config.get("formations", [])]
    boulders = scatter_boulders(col, config["boulders"], materials, terrain) if "boulders" in config else []
    gobo = make_gobo(col, config["gobo"], scene) if "gobo" in config else None
    scene["sh_set"] = config.get("name", "set")
    return {"terrain": terrain.name, "formations": [f.name for f in formations], "boulders": len(boulders),
            "gobo": gobo.name if gobo else None,
            "triangles_estimate": sum(len(o.data.polygons) for o in col.objects if o.type == "MESH") * 2}


def _main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="sh_environment_kit.py")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", help="save the set as this .blend")
    args = ap.parse_args(argv)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    info = build_set(json.loads(Path(args.config).read_text(encoding="utf-8")))
    print(json.dumps(info, indent=2))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.out).resolve()))


if __name__ == "__main__":
    _main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
