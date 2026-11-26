"""Shot builder and scene validator inside real Blender (skipped without bpy)."""
from __future__ import annotations

import json
import shutil

import pytest

bpy = pytest.importorskip("bpy")

from test_shpipe_core import FIXTURE  # noqa: E402


@pytest.fixture
def ep(tmp_path):
    dst = tmp_path / "EP900_fixture"
    shutil.copytree(FIXTURE, dst)
    sb = json.loads((dst / "storyboard/storyboard.json").read_text())
    sb["scenes"][1]["on_screen_label"] = "Illustrative reconstruction"
    (dst / "storyboard/storyboard.json").write_text(json.dumps(sb))
    return dst


def test_build_shot_from_storyboard(ep):
    from sh_build_shot import build_shot
    info = build_shot(ep, "S01", "preview", save=True)
    scene = bpy.context.scene
    assert (ep / "blender" / "shots" / "S01.blend").is_file()
    assert scene.frame_start == 1 and scene.frame_end == 120
    assert scene.render.resolution_x == 1280 and scene.render.fps == 30
    assert scene.camera is not None and scene.camera.data.lens == 24      # storyboard lens override
    assert scene["sh_preset"] == "deep_ocean"
    assert scene.render.filepath.endswith("renders/preview/S01/frame_")
    assert info["camera_move"] == "descent_reveal"


def test_validate_scene_passes_then_catches_drift(ep):
    from sh_build_shot import build_shot
    from sh_validate_scene import validate_scene
    build_shot(ep, "S02", "preview", save=True)
    report = validate_scene(bpy.context.scene, ep)
    assert report["status"] == "pass", report
    bpy.context.scene.frame_end = 90
    bpy.context.scene.render.resolution_x = 1920
    report = validate_scene(bpy.context.scene, ep)
    assert report["status"] == "fail"
    assert any("frame range" in e for e in report["errors"])
    assert any("resolution" in e for e in report["errors"])


def test_movement_maps_to_camera_preset(ep):
    from sh_build_shot import camera_move_for
    assert camera_move_for({"camera_preset": "lateral_track", "camera": {}}) == "lateral_track"
    assert camera_move_for({"camera": {"movement": "Slow push in"}}) == "slow_push_in"
    assert camera_move_for({"camera": {"movement": "orbit"}}) == "controlled_orbit"
    assert camera_move_for({"camera": {}}) == "slow_push_in"


def test_explicit_camera_keys_override_the_preset_move(ep):
    from sh_build_shot import build_shot
    sb = json.loads((ep / "storyboard/storyboard.json").read_text())
    sb["scenes"][0].setdefault("blender", {})["camera_keys"] = [
        {"t_s": 0, "location": [0, -30, 2], "target": [0, 0, 0], "lens_mm": 28},
        {"t_s": 3, "location": [0, -5, 1], "target": [0, 10, 0], "lens_mm": 18},
    ]
    (ep / "storyboard/storyboard.json").write_text(json.dumps(sb))
    info = build_shot(ep, "S01", "preview", save=False)
    scene = bpy.context.scene
    assert info["camera_move"] == "keyed"
    scene.frame_set(91)
    assert tuple(round(v, 3) for v in scene.camera.matrix_world.translation) == (0, -5, 1)
    assert scene.camera.data.lens == 18
