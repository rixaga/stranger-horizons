"""Procedural creatures inside real Blender (skipped without bpy)."""
from __future__ import annotations

import math

import pytest

bpy = pytest.importorskip("bpy")
from mathutils import Vector  # noqa: E402


def _fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.data.collections.new("SH_Creatures")
    bpy.context.scene.collection.children.link(col)
    return col


def test_shark_has_real_scale_fins_and_countershading():
    import sh_creatures as cr
    col = _fresh()
    shark = cr.make_shark(col, {"name": "CR_Megalodon", "length_m": 15.0, "seed": 2})
    mesh = shark["mesh"]
    bpy.context.view_layer.update()
    dims = mesh.dimensions
    assert dims.x == pytest.approx(15.0, rel=0.08)              # nose to tail tip along +X
    assert 0.12 < dims.z / dims.x < 0.45                        # tall tail fin + body depth, not a sausage
    assert mesh["sh_kind"] == "creature" and mesh["sh_label"] == "Imagined — theory, not evidence"
    names = {n.bl_idname for n in mesh.active_material.node_tree.nodes}
    assert "ShaderNodeNewGeometry" in names                     # top/belly countershading uses the normal
    for part in ("fin_dorsal", "fin_pectoral_L", "fin_pectoral_R", "fin_caudal"):
        assert part in mesh.vertex_groups or part in mesh.get("sh_parts", [])


def test_shark_rig_weights_and_swim_cycle():
    import sh_creatures as cr
    col = _fresh()
    shark = cr.make_shark(col, {"name": "CR_Megalodon", "length_m": 15.0, "bones": 8})
    rig, mesh = shark["rig"], shark["mesh"]
    assert len(rig.data.bones) == 8
    bone_groups = [g for g in mesh.vertex_groups if g.name.startswith("spine_")]
    assert len(bone_groups) == 8
    for v in list(mesh.data.vertices)[::97]:                          # every vertex fully weighted to the spine
        w = sum(g.weight for g in v.groups if mesh.vertex_groups[g.group].name.startswith("spine_"))
        assert w == pytest.approx(1.0, abs=1e-3)
    cr.swim_cycle(rig, frame_start=1, frame_end=90, fps=30, freq_hz=0.4, head_deg=2, tail_deg=16)
    scene = bpy.context.scene
    tail_y, head_y = [], []
    for f in range(1, 91, 3):                                   # one full beat at 0.4 Hz is 75 frames
        scene.frame_set(f)
        tail_y.append(rig.pose.bones["spine_7"].tail.y)
        head_y.append(rig.pose.bones["spine_1"].head.y)
    assert max(tail_y) - min(tail_y) > 0.10 * 15.0              # tail tip sweeps > 1.5 m side to side
    assert max(head_y) - min(head_y) < 0.02 * 15.0              # head stays steady (< 0.3 m)


def test_follow_path_faces_direction_of_travel():
    import sh_creatures as cr
    col = _fresh()
    shark = cr.make_shark(col, {"name": "CR_Test", "length_m": 10.0})
    rig = shark["rig"]
    pts = [(0, 40, 0), (2, 20, -1), (0, 6, 0), (-12, -2, 1), (-30, -6, 2)]
    cr.follow_path(rig, pts, frame_start=1, frame_end=120, bank_deg=25)
    scene = bpy.context.scene
    scene.frame_set(1)
    p0 = rig.matrix_world.translation.copy()
    scene.frame_set(4)
    p1 = rig.matrix_world.translation.copy()
    fwd = rig.matrix_world.to_3x3() @ Vector((1, 0, 0))
    assert fwd.normalized().dot((p1 - p0).normalized()) > 0.95  # nose points where it is going
    scene.frame_set(120)
    assert (rig.matrix_world.translation - Vector(pts[-1])).length < 0.5
