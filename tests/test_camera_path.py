"""Keyed camera paths: explicit location/target keys, optionally relative to a moving object (e.g. ROV POV)."""
from __future__ import annotations

import pytest


def test_path_keyframes_convert_seconds_to_frames():
    from sh_camera import compute_path_keyframes
    keys = compute_path_keyframes([
        {"t_s": 0, "location": [0, -10, 2], "target": [0, 0, 0], "lens_mm": 24},
        {"t_s": 4.5, "location": [1, 2, 3], "target": [0, 5, 0], "relative_to": "SH_ROV"},
    ], fps=30, frame_start=1)
    assert [k["frame"] for k in keys] == [1, 136]
    assert keys[0]["lens"] == 24 and keys[1]["lens"] == 24          # lens carries forward
    assert keys[1]["relative_to"] == "SH_ROV" and keys[0]["relative_to"] is None


def test_path_keyframes_reject_unsorted_times():
    from sh_camera import compute_path_keyframes
    with pytest.raises(ValueError):
        compute_path_keyframes([{"t_s": 2, "location": [0, 0, 0], "target": [0, 1, 0]},
                                {"t_s": 1, "location": [0, 0, 0], "target": [0, 1, 0]}], fps=30)


def test_keyed_camera_rides_a_moving_object():
    bpy = pytest.importorskip("bpy")
    from mathutils import Vector
    from sh_camera import build_keyed_camera
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 60
    scene.render.fps = 30
    rov = bpy.data.objects.new("SH_ROV", None)
    scene.collection.objects.link(rov)
    rov.rotation_euler = (0, 0, 1.0)
    rov.location = (10, 0, -5)
    rov.keyframe_insert("location", frame=1)
    rov.location = (13, 0, -5)
    rov.keyframe_insert("location", frame=60)

    cam, keys = build_keyed_camera(scene, [
        {"t_s": 0, "location": [0, -20, 0], "target": [10, 0, -5], "lens_mm": 35},
        {"t_s": 1, "location": [0, 1.5, 0.6], "target": [0, 40, -2], "relative_to": "SH_ROV", "lens_mm": 18},
        {"t_s": 59 / 30, "location": [0, 1.5, 0.6], "target": [0, 40, -2], "relative_to": "SH_ROV"},
    ])
    assert scene.camera is cam and cam.name == "SH_Camera"
    for frame in (31, 60):
        scene.frame_set(frame)
        want = rov.matrix_world @ Vector((0, 1.5, 0.6))
        assert (cam.matrix_world.translation - want).length < 1e-3
        look = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
        aim = (rov.matrix_world @ Vector((0, 40, -2)) - want).normalized()
        assert look.dot(aim) > 0.999
    assert cam.data.lens == pytest.approx(18)
