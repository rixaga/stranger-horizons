"""Runs only where Blender's Python module (bpy) is importable, e.g. `pip install bpy`
in a matching Python, or `blender --background --python-expr` with pytest available."""
from __future__ import annotations

import pytest

bpy = pytest.importorskip("bpy")


def test_cycles_is_listed_as_available_engine():
    from sh_render import available_engines
    engines = available_engines()
    assert "CYCLES" in engines
    assert any(e.startswith("BLENDER_EEVEE") for e in engines)


@pytest.mark.parametrize("profile", ["preview", "delivery", "master", "shorts"])
def test_every_profile_applies(profile):
    from sh_render import apply_profile, load_profile
    applied = apply_profile(bpy.context.scene, load_profile(profile), "//renders/frame_")
    assert applied["resolution"] == [load_profile(profile)["resolution_x"], load_profile(profile)["resolution_y"]]
    assert applied["view_transform"] == "AgX"


@pytest.mark.parametrize("name", ["deep_ocean", "antarctica", "underground", "ancient_civilizations",
                                  "uap_visualization", "space_cosmic"])
def test_preset_applies_and_reapplies_cleanly(name):
    from sh_camera import build_camera_move
    from sh_presets import COLLECTION, apply_preset, load_preset
    scene = bpy.context.scene
    build_camera_move(scene, "slow_push_in")
    first = apply_preset(scene, load_preset(name))
    count = len(bpy.data.collections[COLLECTION].objects)
    second = apply_preset(scene, load_preset(name))
    assert len(bpy.data.collections[COLLECTION].objects) == count  # rerun-safe: no duplicates
    assert first["lights"] == second["lights"]
    assert scene.view_settings.view_transform == "AgX"


def test_camera_move_is_eased_and_aimed():
    from sh_camera import _fcurves, build_camera_move
    scene = bpy.context.scene
    cam, keys = build_camera_move(scene, "descent_reveal", target=(0, 0, 0), frame_start=1)
    curves = [fc for fc in _fcurves(cam.animation_data.action) if fc.data_path == "location"]
    assert len(curves) == 3
    assert all(kp.interpolation == "BEZIER" for fc in curves for kp in fc.keyframe_points)
    assert cam.constraints["SH_Aim"].target.name == "SH_Camera_Target"
    scene.frame_set(keys[-1]["frame"])
    assert tuple(round(v, 4) for v in cam.matrix_world.translation) == keys[-1]["location"]
