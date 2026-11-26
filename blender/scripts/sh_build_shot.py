"""Build one shot .blend from one storyboard scene. Safe to rerun.

    blender --background --factory-startup --python blender/scripts/sh_build_shot.py -- \
        --episode episodes/EP000_ocean_prototype --scene S01 --mode preview

Sets frame range and fps from the storyboard, applies the render profile, the
environment preset and the camera move, records metadata on the scene, sets the
output path to <episode>/renders/<mode>/<scene>/frame_####, and saves
<episode>/blender/shots/<scene>.blend. Hero geometry comes from the scene's
optional "blender.template" .blend; without one the shot is environment-only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
for p in (HERE, REPO / "pipeline"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import bpy  # noqa: E402

from sh_camera import build_camera_move, build_keyed_camera  # noqa: E402
from sh_presets import _deep_merge, apply_preset, load_preset  # noqa: E402
from sh_render import apply_profile, load_profile  # noqa: E402
from shpipe import storyboard as sb_mod  # noqa: E402
from shpipe.paths import Episode  # noqa: E402

MOVEMENT_WORDS = [("descent", "descent_reveal"), ("aerial", "aerial_reveal"), ("rise", "rise_reveal"),
                  ("orbit", "controlled_orbit"), ("track", "lateral_track"), ("lateral", "lateral_track"),
                  ("shoulder", "over_shoulder_reveal"), ("static", "static_hold"), ("hold", "static_hold"),
                  ("push", "slow_push_in")]
PROFILE_FOR_MODE = {"preview": "preview", "final": "delivery", "master": "master"}


def camera_move_for(scene_spec: dict) -> str:
    if scene_spec.get("camera_preset"):
        return scene_spec["camera_preset"]
    movement = scene_spec.get("camera", {}).get("movement", "").lower()
    return next((preset for word, preset in MOVEMENT_WORDS if word in movement), "slow_push_in")


def build_shot(episode_root, scene_id: str, mode: str = "preview", save: bool = True,
               profile: str | None = None) -> dict:
    ep = Episode(Path(episode_root))
    sb = sb_mod.load(ep)
    spec = next((s for s in sb["scenes"] if s["scene_id"] == scene_id), None)
    if spec is None:
        raise KeyError(f"Scene {scene_id} not in {ep.storyboard}")
    row = next(r for r in sb_mod.timeline(sb) if r["scene_id"] == scene_id)
    hints = spec.get("blender", {})

    template = hints.get("template")
    if template:
        bpy.ops.wm.open_mainfile(filepath=str(REPO / template))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = int(sb["fps"])
    scene.frame_start, scene.frame_end = 1, row["frames"]

    out_prefix = ep.render_dir(mode, scene_id) / "frame_"
    profile = profile or hints.get("render_profile") or PROFILE_FOR_MODE[mode]
    applied = apply_profile(scene, load_profile(profile), str(out_prefix))
    if hints.get("camera_keys"):  # explicit path (e.g. a fly-in that ends as a vehicle POV) wins over presets
        move = "keyed"
        build_keyed_camera(scene, hints["camera_keys"])
    else:
        move = camera_move_for(spec)
        build_camera_move(scene, move, target=tuple(hints.get("target_m", (0.0, 0.0, 2.0))), frame_start=1,
                          duration_s=spec["duration_seconds"], lens_mm=spec.get("camera", {}).get("lens_mm"))
    merged = _deep_merge(load_preset(spec.get("environment_preset", "base")), hints.get("preset_overrides", {}))
    preset = apply_preset(scene, merged)
    cam_spec = spec.get("camera", {})
    if "dof" in cam_spec and scene.camera:  # storyboard wins over the preset for depth of field
        scene.camera.data.dof.use_dof = cam_spec["dof"]
        scene.camera.data.dof.focus_object = bpy.data.objects.get("SH_Camera_Target")
        scene.camera.data.dof.aperture_fstop = cam_spec.get("fstop", 4.0)

    scene["sh_episode"] = ep.episode_id
    scene["sh_scene"] = scene_id
    scene["sh_mode"] = mode
    scene["sh_profile"] = profile
    scene["sh_reconstruction_status"] = spec["reconstruction_status"]
    scene["sh_on_screen_label"] = spec.get("on_screen_label", "")
    blend = ep.shot_blend(scene_id)
    if save:
        blend.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    return {"scene": scene_id, "mode": mode, "frames": row["frames"], "camera_move": move,
            "preset": preset["preset"], "profile": profile, "render": applied,
            "blend": str(blend) if save else None}


def _main(argv: list[str]) -> None:
    import argparse
    ap = argparse.ArgumentParser(prog="sh_build_shot.py")
    ap.add_argument("--episode", required=True)
    ap.add_argument("--scene", required=True, nargs="+")
    ap.add_argument("--mode", choices=sorted(PROFILE_FOR_MODE), default="preview")
    ap.add_argument("--profile", help="render profile override, e.g. preview_hd")
    args = ap.parse_args(argv)
    for sid in args.scene:
        print(json.dumps(build_shot(args.episode, sid, args.mode, profile=args.profile), indent=2, default=str))


if __name__ == "__main__":
    _main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
