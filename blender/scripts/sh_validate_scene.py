"""Validate a shot .blend against its storyboard scene before rendering.

    blender --background episodes/EP001_x/blender/shots/S01.blend \
        --python blender/scripts/sh_validate_scene.py -- --episode episodes/EP001_x

Exit code 1 if any check fails. Writes <episode>/qc/blender_<scene>.json.
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

from sh_render import available_engines, load_profile, resolve_engine  # noqa: E402
from shpipe import storyboard as sb_mod  # noqa: E402
from shpipe.paths import Episode  # noqa: E402

PROFILE_FOR_MODE = {"preview": "preview", "final": "delivery", "master": "master"}
FOOTAGE = {"documentary_footage", "licensed_archival_footage", "original_footage"}


def validate_scene(scene, episode_root) -> dict:
    ep = Episode(Path(episode_root))
    errors, warnings = [], []
    sid, mode = scene.get("sh_scene"), scene.get("sh_mode", "preview")
    if not sid:
        return {"status": "fail", "errors": ["scene has no sh_scene metadata; build it with sh_build_shot.py"]}
    sb = sb_mod.load(ep)
    spec = next((s for s in sb["scenes"] if s["scene_id"] == sid), None)
    if spec is None:
        return {"status": "fail", "errors": [f"{sid} is not in the storyboard"]}
    row = next(r for r in sb_mod.timeline(sb) if r["scene_id"] == sid)
    profile_name = scene.get("sh_profile") or PROFILE_FOR_MODE.get(mode, "preview")
    profile = load_profile(profile_name)
    r = scene.render

    if scene.camera is None:
        errors.append("no active camera")
    if (scene.frame_start, scene.frame_end) != (1, row["frames"]):
        errors.append(f"frame range {scene.frame_start}-{scene.frame_end}, storyboard needs 1-{row['frames']}")
    if r.fps != int(sb["fps"]) or r.fps_base != 1.0:
        errors.append(f"fps {r.fps}/{r.fps_base}, storyboard needs {sb['fps']}")
    if (r.resolution_x, r.resolution_y, r.resolution_percentage) != (profile["resolution_x"], profile["resolution_y"], 100):
        errors.append(f"resolution {r.resolution_x}x{r.resolution_y}@{r.resolution_percentage}% "
                      f"≠ {profile_name} profile {profile['resolution_x']}x{profile['resolution_y']}")
    try:
        if r.engine != resolve_engine(profile["engine"], available_engines()):
            errors.append(f"engine {r.engine} ≠ {profile_name} profile {profile['engine']}")
    except ValueError as exc:
        errors.append(str(exc))
    expected_out = ep.render_dir(mode, sid)
    actual_out = Path(bpy.path.abspath(r.filepath)).parent
    if actual_out.resolve() != expected_out.resolve():
        errors.append(f"output path {actual_out} ≠ {expected_out}")
    if scene.view_settings.view_transform != "AgX":
        errors.append(f"view transform {scene.view_settings.view_transform}, style guide requires AgX")
    if spec["reconstruction_status"] not in FOOTAGE and not scene.get("sh_on_screen_label"):
        errors.append("reconstruction shot without on-screen label metadata")
    if "sh_preset" not in scene:
        warnings.append("no environment preset recorded")
    missing = [img.name for img in bpy.data.images
               if img.source == "FILE" and not img.packed_file and img.filepath
               and not Path(bpy.path.abspath(img.filepath)).is_file()]
    if missing:
        errors.append("missing image files: " + ", ".join(missing))
    libs = [lib.filepath for lib in bpy.data.libraries if not Path(bpy.path.abspath(lib.filepath)).is_file()]
    if libs:
        errors.append("missing linked libraries: " + ", ".join(libs))
    if bpy.data.is_dirty:
        warnings.append("unsaved changes in the .blend")
    return {"status": "fail" if errors else ("warn" if warnings else "pass"), "scene": sid, "mode": mode,
            "blender": bpy.app.version_string, "errors": errors, "warnings": warnings}


def _main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="sh_validate_scene.py")
    ap.add_argument("--episode", required=True)
    args = ap.parse_args(argv)
    report = validate_scene(bpy.context.scene, args.episode)
    print(json.dumps(report, indent=2))
    if report.get("scene"):
        out = Episode(Path(args.episode)).qc_dir / f"blender_{report['scene']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []))
