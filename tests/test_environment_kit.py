"""Environment kit inside real Blender (skipped without bpy)."""
from __future__ import annotations

import json

import pytest

bpy = pytest.importorskip("bpy")

from conftest import REPO  # noqa: E402

CFG = json.loads((REPO / "episodes/EP001_ocean_prototype/scripts/ep001_set.json").read_text())


def _small():
    cfg = json.loads(json.dumps(CFG))
    cfg["terrain"]["resolution"] = 40
    cfg["boulders"]["count"] = 10
    cfg["gobo"]["cells"] = 16
    return cfg


def test_build_set_is_rerun_safe():
    import sh_environment_kit as kit
    bpy.ops.wm.read_factory_settings(use_empty=True)
    first = kit.build_set(_small())
    n = len(bpy.data.collections[kit.COLLECTION].objects)
    second = kit.build_set(_small())
    assert len(bpy.data.collections[kit.COLLECTION].objects) == n
    assert first["formations"] == second["formations"] == ["SH_Subject_Pinnacle", "SH_Ridge_Left", "SH_Seamount_Far"]
    assert second["boulders"] == 10 + len(CFG["boulders"]["hero"])


def test_formations_sit_on_terrain_and_gobo_is_camera_invisible():
    import sh_environment_kit as kit
    bpy.ops.wm.read_factory_settings(use_empty=True)
    kit.build_set(_small())
    terrain = bpy.data.objects["SH_Terrain"]
    pin = bpy.data.objects["SH_Subject_Pinnacle"]
    ground = kit.ground_height(terrain, pin.location.x, pin.location.y)
    assert abs(pin.location.z - (ground - 1.5)) < 1e-3
    gobo = bpy.data.objects["SH_LightGobo"]
    assert gobo.visible_camera is False and gobo.visible_shadow is True
    assert gobo.animation_data is not None           # drifts for shimmering shafts


def test_ep001_shot_builds_and_validates(tmp_path):
    import shutil
    import sh_environment_kit as kit
    from sh_build_shot import build_shot
    from sh_validate_scene import validate_scene
    ep = tmp_path / "EP001_ocean_prototype"
    shutil.copytree(REPO / "episodes/EP001_ocean_prototype", ep, ignore=shutil.ignore_patterns("renders", "final", "*.blend"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    kit.build_set(_small())
    tpl = REPO / "episodes/EP001_ocean_prototype/blender/EP001_set.blend"
    sb = json.loads((ep / "storyboard/storyboard.json").read_text())
    tmp_tpl = tmp_path / "set.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(tmp_tpl))
    sb["scenes"][0]["blender"]["template"] = str(tmp_tpl.relative_to(REPO)) if tmp_tpl.is_relative_to(REPO) else str(tmp_tpl)
    (ep / "storyboard/storyboard.json").write_text(json.dumps(sb))
    info = build_shot(ep, "S01", "preview", save=False)
    scene = bpy.context.scene
    assert info["profile"] == "preview_hd" and scene.render.resolution_x == 1920
    assert scene.frame_end == 300 and scene.camera.data.dof.use_dof
    assert scene.camera.data.dof.focus_object.name == "SH_Camera_Target"
    assert bpy.data.lights["SH_Downwelling_Sun"].diffuse_factor == pytest.approx(0.3)
    assert scene.eevee.use_volume_custom_range and scene.eevee.volumetric_end == pytest.approx(220)
    assert validate_scene(scene, ep)["status"] in ("pass", "warn")
