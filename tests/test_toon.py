"""Toon (cel-shaded + outline) look for promo Shorts."""
from __future__ import annotations

import pytest

bpy = pytest.importorskip("bpy")


def _cube(name):
    bpy.ops.mesh.primitive_cube_add()
    ob = bpy.context.active_object
    ob.name = name
    return ob


def test_apply_toon_gives_cel_material_and_outline():
    from sh_toon import apply_toon
    bpy.ops.wm.read_factory_settings(use_empty=True)
    a, b = _cube("A"), _cube("B")
    apply_toon([a, b], colors={"A": (1.0, 0.7, 0.1)}, outline_m=0.03)
    for ob in (a, b):
        mats = [s.material for s in ob.material_slots]
        assert mats[0].name.startswith("SH_Toon")
        types = {n.type for n in mats[0].node_tree.nodes}
        assert {"SHADERTORGB", "VALTORGB"} <= types
        ramp = next(n for n in mats[0].node_tree.nodes if n.type == "VALTORGB")
        assert ramp.color_ramp.interpolation == "CONSTANT"        # hard cel bands
        outline = ob.modifiers["SH_Outline"]
        assert outline.type == "SOLIDIFY" and outline.use_flip_normals
        assert outline.thickness == pytest.approx(-0.03) or outline.thickness == pytest.approx(0.03)
        assert mats[outline.material_offset].use_backface_culling   # inverted hull shows only the rim
    ramp_a = next(n for n in a.material_slots[0].material.node_tree.nodes if n.type == "VALTORGB")
    assert tuple(ramp_a.color_ramp.elements[-1].color)[:3] == pytest.approx((1.0, 0.7, 0.1))


def test_apply_toon_is_safe_to_rerun():
    from sh_toon import apply_toon
    bpy.ops.wm.read_factory_settings(use_empty=True)
    a = _cube("A")
    apply_toon([a])
    apply_toon([a])
    assert [m.name for m in a.modifiers].count("SH_Outline") == 1
    assert len(a.material_slots) == 2


def test_apply_toon_keeps_extra_material_slots_like_eyes():
    from sh_toon import apply_toon
    bpy.ops.wm.read_factory_settings(use_empty=True)
    a = _cube("Shark")
    skin, eye = bpy.data.materials.new("skin"), bpy.data.materials.new("eye")
    eye.diffuse_color = (0.01, 0.01, 0.01, 1)
    a.data.materials.append(skin)
    a.data.materials.append(eye)
    a.data.polygons[3].material_index = 1
    apply_toon([a], colors={"Shark": {"top": (0.4, 0.5, 0.6), "belly": (0.9, 0.9, 0.85)}})
    names = [s.material.name for s in a.material_slots]
    assert len(names) == 3 and names[-1] == "SH_ToonOutline"
    assert a.data.polygons[3].material_index == 1             # eye polygons stay on their own slot
    eye_ramp = next(n for n in a.material_slots[1].material.node_tree.nodes if n.type == "VALTORGB")
    assert max(eye_ramp.color_ramp.elements[-1].color[:3]) < 0.05  # eye toon colour comes from the original
    skin_nodes = a.material_slots[0].material.node_tree.nodes
    assert sum(n.type == "VALTORGB" for n in skin_nodes) == 2    # top + belly bands (countershading)


def test_toon_world_marine_snow_and_projected_track():
    from mathutils import Vector
    from sh_toon import marine_snow, project_track, toon_world
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
    w = toon_world(scene, bottom=(0, 0, 0.02), top=(0.02, 0.08, 0.15))
    assert scene.world is w and any(n.type == "VALTORGB" for n in w.node_tree.nodes)
    snow = marine_snow(scene, Vector((0, 0, 0)), 5.0, count=40, seed=1)
    assert len(snow.data.polygons) == 40 * 20       # one icosphere (20 faces) per speck
    cam = bpy.data.objects.new("C", bpy.data.cameras.new("C"))
    scene.collection.objects.link(cam)
    cam.location = (0, -10, 0)
    cam.rotation_euler = (1.5707963, 0, 0)          # looking along +Y
    scene.camera = cam
    target = bpy.data.objects.new("T", None)
    scene.collection.objects.link(target)
    pts = project_track(scene, target, [1, 2])
    assert pts[1] == pytest.approx((540, 960), abs=1)   # straight ahead = frame centre (pixels, y down)
