"""Environment look presets for Stranger Horizons.

load_preset() is pure Python (testable without Blender). apply_preset() builds or
rebuilds everything inside the "SH_Environment" collection, so it is safe to rerun:
world, volume domain, lights, particles, colour management, engine volume settings
and the active camera's lens settings.

    blender --background shot.blend --python blender/scripts/sh_presets.py -- --preset deep_ocean [--save]

Light coordinates: world space, except lights with "parent_to_camera": true, whose
location/rotation are local to the active camera (lights shine along their -Z, as
the camera looks along its -Z).
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PRESET_DIR = REPO / "config" / "presets"
COLLECTION = "SH_Environment"
CONCAT_LISTS = {"editorial_rules"}


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        elif key in CONCAT_LISTS and isinstance(out.get(key), list):
            out[key] = out[key] + [v for v in value if v not in out[key]]
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_preset(name: str, preset_dir: Path = PRESET_DIR) -> dict:
    path = preset_dir / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"No preset {name!r} in {preset_dir}")
    data = json.loads(path.read_text(encoding="utf-8"))
    parent = data.get("extends")
    return _deep_merge(load_preset(parent, preset_dir), data) if parent else data


def list_presets(preset_dir: Path = PRESET_DIR) -> list[str]:
    return sorted(p.stem for p in preset_dir.glob("*.json") if p.stem != "base")


# ---------------------------------------------------------------- Blender-only

def _collection(bpy, scene):
    col = bpy.data.collections.get(COLLECTION)
    if col is None:
        col = bpy.data.collections.new(COLLECTION)
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    owned = [(type(o.data).__name__, o.data.name) for o in col.objects if o.data is not None]
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    stores = {"Mesh": bpy.data.meshes, "PointLight": bpy.data.lights, "SpotLight": bpy.data.lights,
              "SunLight": bpy.data.lights, "AreaLight": bpy.data.lights}
    for kind, name in owned:
        store = stores.get(kind)
        block = store.get(name) if store is not None else None
        if block is not None and block.users == 0:
            store.remove(block)
    return col


def _link(col, obj):
    col.objects.link(obj)
    return obj


def _set_input(node, names, value):
    for n in names if isinstance(names, (list, tuple)) else [names]:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return True
    return False


def _ensure_nodes(idblock):
    """Node trees are always on from Blender 5.0; only older versions need use_nodes set."""
    import bpy
    if bpy.app.version < (5, 0, 0) and not idblock.use_nodes:
        idblock.use_nodes = True


def _rgba(rgb):
    return (*rgb, 1.0)


def _world(bpy, scene, cfg):
    world = bpy.data.worlds.get("SH_World") or bpy.data.worlds.new("SH_World")
    _ensure_nodes(world)
    nt = world.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg.inputs["Color"].default_value = _rgba(cfg.get("color", [0, 0, 0]))
    bg.inputs["Strength"].default_value = cfg.get("strength", 1.0)
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    scene.world = world


def _volume_material(bpy, cfg):  # noqa: C901 (linear node build)
    mat = bpy.data.materials.get("SH_Volume") or bpy.data.materials.new("SH_Volume")
    _ensure_nodes(mat)
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = _rgba(cfg.get("scatter_color", [0.8, 0.8, 0.8]))
    pv.inputs["Anisotropy"].default_value = cfg.get("anisotropy", 0.0)
    _set_input(pv, ["Absorption Color"], _rgba([1, 1, 1]))

    # density = base * height falloff * noise
    density = nt.nodes.new("ShaderNodeValue")
    density.outputs[0].default_value = cfg.get("density", 0.01)
    current = density.outputs[0]
    hf = cfg.get("height_falloff", {})
    if hf.get("enabled"):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.clamp = True
        mr.inputs["From Min"].default_value = hf.get("z_full", 0.0)
        mr.inputs["From Max"].default_value = hf.get("z_zero", 10.0)
        mr.inputs["To Min"].default_value = 1.0
        mr.inputs["To Max"].default_value = 0.0
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(current, mul.inputs[0])
        nt.links.new(mr.outputs["Result"], mul.inputs[1])
        current = mul.outputs[0]
    amount = cfg.get("noise_amount", 0.0)
    if amount > 0:
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = cfg.get("noise_scale", 0.1)
        drift = cfg.get("noise_drift_m_s")
        if drift:
            coord = nt.nodes.new("ShaderNodeTexCoord")
            mapping = nt.nodes.new("ShaderNodeMapping")
            nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
            nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
            scene = bpy.context.scene
            seconds = (scene.frame_end - scene.frame_start) / max(scene.render.fps, 1)
            loc = mapping.inputs["Location"]
            loc.default_value = (0, 0, 0)
            loc.keyframe_insert("default_value", frame=scene.frame_start)
            loc.default_value = tuple(-d * seconds for d in drift)
            loc.keyframe_insert("default_value", frame=scene.frame_end)
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = 1.0 - amount
        mr.inputs["To Max"].default_value = 1.0 + amount
        nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(current, mul.inputs[0])
        nt.links.new(mr.outputs["Result"], mul.inputs[1])
        current = mul.outputs[0]
    nt.links.new(current, pv.inputs["Density"])

    shader = pv.outputs["Volume"]
    if cfg.get("absorption_density", 0) > 0:
        absorb = nt.nodes.new("ShaderNodeVolumeAbsorption")
        absorb.inputs["Color"].default_value = _rgba(cfg.get("absorption_color", [1, 1, 1]))
        absorb.inputs["Density"].default_value = cfg["absorption_density"]
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(pv.outputs["Volume"], add.inputs[0])
        nt.links.new(absorb.outputs["Volume"], add.inputs[1])
        shader = add.outputs["Shader"]
    nt.links.new(shader, out.inputs["Volume"])
    return mat


def _cube(bpy, name, bounds, center):
    mesh = bpy.data.meshes.new(name)
    hx, hy, hz = (b / 2 for b in bounds)
    verts = [(sx * hx, sy * hy, sz * hz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    mesh.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = center
    return obj


def _volume(bpy, col, cfg):
    if cfg.get("kind", "none") == "none":
        return None
    obj = _link(col, _cube(bpy, "SH_VolumeDomain", cfg.get("bounds_m", [100, 100, 30]), cfg.get("center_m", [0, 0, 0])))
    obj.data.materials.append(_volume_material(bpy, cfg))
    obj.display_type = "BOUNDS"
    return obj


def _lights(bpy, scene, col, lights):
    made = []
    for spec in lights:
        data = bpy.data.lights.new(spec["name"], spec["type"])
        data.color = spec["color"]
        data.energy = spec["energy"]
        if hasattr(data, "volume_factor"):
            data.volume_factor = spec.get("volume_factor", 1.0)
        for key in ("diffuse_factor", "specular_factor"):
            if key in spec and hasattr(data, key):
                setattr(data, key, spec[key])
        if spec["type"] == "SUN":
            data.angle = math.radians(spec.get("angle_deg", 0.53))
        if spec["type"] == "SPOT":
            data.spot_size = math.radians(spec.get("spot_size_deg", 45))
            data.spot_blend = spec.get("spot_blend", 0.3)
        if spec["type"] in ("SPOT", "POINT"):
            data.shadow_soft_size = spec.get("size_m", 0.1)
        if spec["type"] == "AREA":
            data.size = spec.get("size_m", 1.0)
        obj = _link(col, bpy.data.objects.new(spec["name"], data))
        obj.location = spec.get("location", [0, 0, 10])
        obj.rotation_euler = [math.radians(a) for a in spec.get("rotation_deg", [0, 0, 0])]
        if spec.get("parent_to_camera") and scene.camera:
            obj.parent = scene.camera
        made.append(obj.name)
    return made


def _particles(bpy, col, cfg):
    if cfg.get("kind", "none") == "none" or cfg.get("count", 0) == 0:
        return None
    grain_mesh = bpy.data.meshes.new("SH_ParticleGrain")
    # an octahedron is enough at these sizes and keeps memory low
    grain_mesh.from_pydata([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)], [],
                           [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)])
    grain = _link(col, bpy.data.objects.new("SH_ParticleGrain", grain_mesh))
    grain.location = (0, 0, -10000)  # parked out of shot; instances are placed by the particle system
    mat = bpy.data.materials.get("SH_Particle") or bpy.data.materials.new("SH_Particle")
    _ensure_nodes(mat)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = _rgba(cfg.get("color", [0.8, 0.8, 0.8]))
        bsdf.inputs["Roughness"].default_value = 0.6
        if cfg.get("emission", 0) > 0:
            _set_input(bsdf, ["Emission Color", "Emission"], _rgba(cfg.get("color", [1, 1, 1])))
            _set_input(bsdf, ["Emission Strength"], cfg["emission"])
    grain_mesh.materials.append(mat)

    emitter = _link(col, _cube(bpy, "SH_ParticleEmitter", cfg.get("bounds_m", [20, 20, 10]), cfg.get("center_m", [0, 0, 0])))
    emitter.display_type = "BOUNDS"
    emitter.show_instancer_for_render = False
    emitter.show_instancer_for_viewport = False
    mod = emitter.modifiers.new("SH_Particles", "PARTICLE_SYSTEM")
    ps = mod.particle_system.settings
    ps.count = cfg["count"]
    ps.frame_start = -1.0
    ps.frame_end = -1.0
    ps.lifetime = 100000
    ps.emit_from = "VOLUME"
    ps.distribution = "RAND"
    ps.use_emit_random = True
    ps.physics_type = "NEWTON"
    ps.normal_factor = 0.0
    ps.object_align_factor = cfg.get("drift_m_s", [0, 0, 0])
    ps.brownian_factor = cfg.get("brownian", 0.0)
    ps.effector_weights.gravity = 0.0
    ps.render_type = "OBJECT"
    ps.instance_object = grain
    ps.particle_size = cfg.get("size_m", 0.005)
    ps.size_random = cfg.get("size_random", 0.5)
    ps.use_rotations = True
    ps.rotation_factor_random = 1.0
    ps.display_percentage = 10
    mod.particle_system.seed = 7
    return emitter


def _color_management(scene, cfg):
    vs = scene.view_settings
    try:
        vs.view_transform = cfg.get("view_transform", "AgX")
    except TypeError:
        print(f"WARNING: view transform {cfg.get('view_transform')!r} unavailable")
    look = cfg.get("look")
    if look:
        for candidate in (look, f"{vs.view_transform} - {look}"):
            try:
                vs.look = candidate
                break
            except TypeError:
                continue
        else:
            print(f"WARNING: look {look!r} unavailable for {vs.view_transform}; kept {vs.look!r}")
    vs.exposure = cfg.get("exposure", 0.0)
    vs.gamma = cfg.get("gamma", 1.0)


def _engine_settings(scene, eevee, cycles):
    ev = getattr(scene, "eevee", None)
    if ev is not None and "volumetric_end_m" in eevee and hasattr(ev, "use_volume_custom_range"):
        ev.use_volume_custom_range = True  # Blender 5.x ignores volumetric_end without it
    if ev is not None:
        for attr, key in (("volumetric_tile_size", "volumetric_tile_size"), ("volumetric_samples", "volumetric_samples"),
                          ("volumetric_end", "volumetric_end_m"), ("use_volumetric_shadows", "volumetric_shadows")):
            if key in eevee and hasattr(ev, attr):
                setattr(ev, attr, eevee[key])
    cy = getattr(scene, "cycles", None)
    if cy is not None:
        for attr in ("volume_bounces", "max_bounces", "volume_step_rate"):
            if attr in cycles and hasattr(cy, attr):
                setattr(cy, attr, cycles[attr])


def _camera(scene, cfg):
    cam = scene.camera
    if cam is None:
        return
    c = cam.data
    c.lens = cfg.get("lens_mm", c.lens)
    c.sensor_width = cfg.get("sensor_mm", c.sensor_width)
    c.clip_start = cfg.get("clip_start_m", c.clip_start)
    c.clip_end = cfg.get("clip_end_m", c.clip_end)
    c.dof.use_dof = cfg.get("dof", False)
    c.dof.aperture_fstop = cfg.get("fstop", 4.0)
    if "motion_blur_shutter" in cfg:
        scene.render.motion_blur_shutter = cfg["motion_blur_shutter"]


def apply_preset(scene, preset: dict) -> dict:
    """Apply a merged preset to a scene. Rebuilds the SH_Environment collection each call."""
    import bpy
    col = _collection(bpy, scene)
    _world(bpy, scene, preset.get("world", {}))
    volume = _volume(bpy, col, preset.get("volume", {}))
    lights = _lights(bpy, scene, col, preset.get("lights", []))
    particles = _particles(bpy, col, preset.get("particles", {}))
    _color_management(scene, preset.get("color_management", {}))
    _engine_settings(scene, preset.get("eevee", {}), preset.get("cycles", {}))
    _camera(scene, preset.get("camera", {}))
    scene["sh_preset"] = preset["name"]
    return {"preset": preset["name"], "volume": volume.name if volume else None, "lights": lights,
            "particles": particles.name if particles else None, "view_transform": scene.view_settings.view_transform,
            "look": scene.view_settings.look, "exposure": scene.view_settings.exposure}


def _main(argv: list[str]) -> None:
    import argparse
    import bpy
    parser = argparse.ArgumentParser(prog="sh_presets.py")
    parser.add_argument("--preset", required=True, choices=list_presets())
    parser.add_argument("--save", action="store_true", help="save the .blend after applying")
    args = parser.parse_args(argv)
    print(json.dumps(apply_preset(bpy.context.scene, load_preset(args.preset)), indent=2))
    if args.save and bpy.data.filepath:
        bpy.ops.wm.save_mainfile()


if __name__ == "__main__":
    _main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
