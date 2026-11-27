"""Toon look for Stranger Horizons promo Shorts: hard cel bands + inverted-hull outline (EEVEE).

Reusable on any mesh built by the kit (creatures, ROV, terrain). Safe to rerun.
The long-form episode stays realistic; this is a separate style for vertical promos.
"""
from __future__ import annotations

import bpy

OUTLINE_MAT = "SH_ToonOutline"
DEFAULT_COLOR = (0.55, 0.62, 0.70)
SHADOW_TINT = (0.04, 0.07, 0.16)  # navy, so shadows stay on-palette instead of grey


def _outline_material(color=(0.01, 0.015, 0.03)):
    mat = bpy.data.materials.get(OUTLINE_MAT) or bpy.data.materials.new(OUTLINE_MAT)
    mat.use_nodes = True
    mat.use_backface_culling = True
    nt = mat.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    return mat


def _ramp(nt, color, bands):
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "CONSTANT"
    shadow = tuple(c * 0.35 + t * 0.65 for c, t in zip(color, SHADOW_TINT))
    mid = tuple(c * 0.72 + t * 0.28 for c, t in zip(color, SHADOW_TINT))
    cr.elements[0].position, cr.elements[0].color = 0.0, (*shadow, 1)
    cr.elements[1].position, cr.elements[1].color = bands[1], (*color, 1)
    e = cr.elements.new(bands[0])
    e.color = (*mid, 1)
    return ramp


def toon_material(name: str, color=DEFAULT_COLOR, belly=None, bands=(0.18, 0.5)):
    """Diffuse -> Shader to RGB -> constant ramp (shadow / mid / lit) -> emission.

    With belly, a second ramp is used where the surface faces down (countershading)."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = (1, 1, 1, 1)
    s2rgb = nt.nodes.new("ShaderNodeShaderToRGB")
    nt.links.new(diff.outputs[0], s2rgb.inputs[0])
    top = _ramp(nt, color, bands)
    nt.links.new(s2rgb.outputs["Color"], top.inputs["Fac"])
    col = top.outputs["Color"]
    if belly is not None:
        low = _ramp(nt, belly, bands)
        nt.links.new(s2rgb.outputs["Color"], low.inputs["Fac"])
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        step = nt.nodes.new("ShaderNodeMath")
        step.operation = "LESS_THAN"
        step.inputs[1].default_value = -0.25
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        nt.links.new(geo.outputs["Normal"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], step.inputs[0])
        nt.links.new(step.outputs[0], mix.inputs["Factor"])
        nt.links.new(top.outputs["Color"], mix.inputs["A"])
        nt.links.new(low.outputs["Color"], mix.inputs["B"])
        col = mix.outputs["Result"]
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(col, em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs[0])
    return mat


def apply_toon(objects, colors: dict | None = None, outline_m: float = 0.03):
    """Swap each mesh's materials for toon versions (slot by slot) and add an outline hull.

    colors[name] is an RGB tuple or {"top": rgb, "belly": rgb} for the first slot; other slots
    (eyes, lamps...) take their colour from the original material's viewport colour."""
    colors = colors or {}
    outline = _outline_material()
    for ob in objects:
        if ob.type != "MESH":
            continue
        originals = [m for m in ob.data.materials if m and m.name != OUTLINE_MAT]
        if not originals or all(m.name.startswith("SH_Toon_") for m in originals):
            originals = originals or [None]
        toons = []
        for i, orig in enumerate(originals):
            if orig is not None and orig.name.startswith("SH_Toon_"):
                toons.append(orig)
                continue
            spec = colors.get(ob.name) if i == 0 else None
            if isinstance(spec, dict):
                top, belly = spec["top"], spec.get("belly")
            elif spec is not None:
                top, belly = spec, None
            else:
                top = tuple(orig.diffuse_color[:3]) if (orig is not None and i > 0) else DEFAULT_COLOR
                belly = None
            toons.append(toon_material(f"SH_Toon_{ob.name}_{i}", top, belly))
        idx = [p.material_index for p in ob.data.polygons]
        ob.data.materials.clear()  # (this also resets polygon material indices)
        for m in toons:
            ob.data.materials.append(m)
        ob.data.materials.append(outline)
        last = len(toons) - 1
        for poly, i in zip(ob.data.polygons, idx):
            poly.material_index = min(i, last)
        mod = ob.modifiers.get("SH_Outline") or ob.modifiers.new("SH_Outline", "SOLIDIFY")
        mod.thickness = outline_m
        mod.offset = 1.0
        mod.use_flip_normals = True
        mod.use_rim = False
        mod.material_offset = len(toons)  # hull faces land on (or clamp to) the outline slot
        while ob.modifiers[-1] != mod:  # outline goes last, after armature/subdivision
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.modifier_move_down(modifier=mod.name)
    return objects


def toon_world(scene, bottom=(0.004, 0.010, 0.028), top=(0.020, 0.085, 0.150), name="SH_ToonWorld"):
    """Flat vertical gradient background (darker below), no volumetrics."""
    world = bpy.data.worlds.get(name) or bpy.data.worlds.new(name)
    world.use_nodes = True
    wn = world.node_tree
    wn.nodes.clear()
    tc = wn.nodes.new("ShaderNodeTexCoord")
    sep = wn.nodes.new("ShaderNodeSeparateXYZ")
    mr = wn.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -1.0, 1.0
    ramp = wn.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.35, (*bottom, 1)
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.85, (*top, 1)
    bg = wn.nodes.new("ShaderNodeBackground")
    out = wn.nodes.new("ShaderNodeOutputWorld")
    wn.links.new(tc.outputs["Generated"], sep.inputs[0])
    wn.links.new(sep.outputs["Z"], mr.inputs["Value"])
    wn.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    wn.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    wn.links.new(bg.outputs[0], out.inputs[0])
    scene.world = world
    return world


def flat_material(name, color, strength=1.0, alpha=None):
    """Unlit colour (emission); with alpha it is blended (beams, rings, glows)."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if alpha is None:
        nt.links.new(em.outputs[0], out.inputs[0])
    else:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = alpha
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs[0])
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
    return mat


def marine_snow(scene, center, radius, count=200, seed=7, size=(0.015, 0.045), name="SH_MarineSnow"):
    """Tiny unlit specks scattered in a sphere: one icosphere each, in a single mesh."""
    import random

    import bmesh
    from mathutils import Matrix, Vector
    rng = random.Random(seed)
    bm = bmesh.new()
    for _ in range(count):
        while True:
            v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
            if v.length <= 1:
                break
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rng.uniform(*size),
                                   matrix=Matrix.Translation(Vector(center) + v * radius))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    me.materials.append(flat_material("SH_MarineSnow", (0.75, 0.9, 1.0), 1.2))
    return ob


def project_track(scene, obj, frames, offset=(0.0, 0.0, 0.0)):
    """{frame: (x, y)} pixel position (y down) of obj (+ local offset) through the active camera."""
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    w, h = scene.render.resolution_x, scene.render.resolution_y
    out = {}
    for f in frames:
        scene.frame_set(f)
        p = world_to_camera_view(scene, scene.camera, obj.matrix_world @ Vector(offset))
        out[f] = (round(p.x * w, 1), round((1 - p.y) * h, 1))
    return out
