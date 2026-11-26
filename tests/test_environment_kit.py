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
    sun_spec = sb["scenes"][0]["blender"]["preset_overrides"]["lights"][0]
    assert bpy.data.lights["SH_Downwelling_Sun"].diffuse_factor == pytest.approx(sun_spec["diffuse_factor"])
    assert scene.eevee.use_volume_custom_range and scene.eevee.volumetric_end == pytest.approx(220)
    assert validate_scene(scene, ep)["status"] in ("pass", "warn")


def test_gobo_open_at_forces_a_clear_opening():
    import sh_environment_kit as kit
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cfg = _small()
    cfg["gobo"].update({"cells": 48, "open_fraction": 0.0, "open_at": [[10, -20, 12]]})
    kit.build_set(cfg)
    mesh = bpy.data.objects["SH_LightGobo"].data
    centres = [p.center for p in mesh.polygons]
    assert centres                                        # solid elsewhere (open_fraction 0)
    assert all((c.x - 10) ** 2 + (c.y + 20) ** 2 >= (12 - 3.8) ** 2 for c in centres)


def test_terrain_layers_pass_texture_specific_settings():
    import sh_environment_kit as kit
    bpy.ops.wm.read_factory_settings(use_empty=True)
    kit.build_set(_small())
    layers = CFG["terrain"]["layers"]
    for k, layer in enumerate(layers):
        tex = bpy.data.textures[f"SH_Terrain_L{k}"]
        assert tex.type == layer.get("texture", "CLOUDS")
        for key in set(layer) - {"texture", "size_m", "strength"}:
            assert getattr(tex, key) == pytest.approx(layer[key])


def test_sediment_material_is_slope_aware():
    import sh_environment_kit as kit
    bpy.ops.wm.read_factory_settings(use_empty=True)
    kit.build_set(_small())
    mat = bpy.data.objects["SH_Terrain"].active_material
    kinds = {n.bl_idname for n in mat.node_tree.nodes}
    assert {"ShaderNodeNewGeometry", "ShaderNodeMapRange"} <= kinds


def test_vehicle_scale_cue_is_built_lit_aimed_and_moving():
    import math
    import sh_environment_kit as kit
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cfg = _small()
    cfg["vehicles"] = [{"name": "SH_ROV", "location_m": [-2, -38], "height_above_ground_m": 6,
                        "length_m": 2.2, "face_toward_m": [14, 0], "travel_m": 4.0,
                        "lamp_energy_w": 900, "lamp_color": [1.0, 0.93, 0.82]}]
    cfg["frames"] = [1, 300]
    info = kit.build_set(cfg)
    assert info["vehicles"] == ["SH_ROV"]
    rov = bpy.data.objects["SH_ROV"]
    terrain = bpy.data.objects["SH_Terrain"]
    bpy.context.scene.frame_set(1)
    start = rov.matrix_world.translation.copy()
    assert start.z == pytest.approx(kit.ground_height(terrain, start.x, start.y) + 6, abs=0.05)
    dims = rov.dimensions
    assert max(dims) == pytest.approx(2.2, rel=0.15)              # real-world scale: the whole point
    fwd = rov.matrix_world.to_3x3() @ __import__("mathutils").Vector((0, 1, 0))
    to_target = __import__("mathutils").Vector((14 - start.x, 0 - start.y, 0)).normalized()
    assert fwd.to_2d().normalized().dot(to_target.to_2d()) > 0.98   # faces the subject
    lamps = [o for o in bpy.data.objects if o.type == "LIGHT" and o.parent == rov]
    assert len(lamps) >= 2 and all(l.data.energy == pytest.approx(900) for l in lamps if l.data.type == "SPOT")
    bpy.context.scene.frame_set(300)
    end = rov.matrix_world.translation.copy()
    assert (end - start).length == pytest.approx(4.0, rel=0.05)    # slow, motivated travel
    assert all(o.users_collection[0].name == kit.COLLECTION for o in [rov, *lamps])


def test_vehicle_rebuild_is_rerun_safe():
    import sh_environment_kit as kit
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cfg = _small()
    cfg["vehicles"] = [{"name": "SH_ROV", "location_m": [0, 0], "length_m": 2.0}]
    kit.build_set(cfg)
    n = len(bpy.data.objects)
    kit.build_set(cfg)
    assert len(bpy.data.objects) == n
