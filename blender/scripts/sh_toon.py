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
