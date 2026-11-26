"""Build a shot template .blend from a JSON description: environment set + creatures + props.

sh_build_shot.py then opens this template (storyboard scene → blender.template) and adds the
camera move, environment preset, render profile and metadata. Safe to rerun.

Template JSON:
    {"set": <sh_environment_kit config>,            optional; terrain, gobo, vehicles, ...
     "creatures": [{"type": "shark", "cfg": {...},  see sh_creatures.make_shark
                    "path": [[x, y, z], ...],       world-space points, travelled at constant speed
                    "path_span": [0.0, 1.0],        fraction of the shot the path occupies
                    "bank_deg": 20,
                    "swim": {"freq_hz": 0.3, "head_deg": 2, "tail_deg": 16}}]}

    blender --background --factory-startup --python blender/scripts/sh_template.py -- \
        --config episodes/EP001_the_bloop/blender/templates/S022.json --frames 495 \
        --out episodes/EP001_the_bloop/blender/templates/S022.blend
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import bpy  # noqa: E402

import sh_creatures as cr  # noqa: E402
import sh_environment_kit as kit  # noqa: E402

CREATURES = "SH_Creatures"
MAKERS = {"shark": cr.make_shark}


def build_template(cfg: dict, frames: int, out: Path | None = None) -> dict:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, int(frames)
    info: dict = {"frames": int(frames)}
    if "set" in cfg:
        set_cfg = dict(cfg["set"])
        set_cfg["frames"] = [1, int(frames)]
        info["set"] = kit.build_set(set_cfg, scene)
    col = bpy.data.collections.get(CREATURES) or bpy.data.collections.new(CREATURES)
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    made = []
    for spec in cfg.get("creatures", []):
        maker = MAKERS[spec["type"]]
        parts = maker(col, spec.get("cfg", {}))
        rig = parts["rig"]
        a, b = spec.get("path_span", [0.0, 1.0])
        f0 = 1 + round(a * (frames - 1))
        f1 = 1 + round(b * (frames - 1))
        if spec.get("path"):
            cr.follow_path(rig, spec["path"], f0, f1, bank_deg=spec.get("bank_deg", 20.0))
        swim = spec.get("swim")
        if swim:
            cr.swim_cycle(rig, 1, int(frames), scene.render.fps, swim.get("freq_hz", 0.3),
                          swim.get("head_deg", 2.0), swim.get("tail_deg", 16.0))
        made.append({"name": parts["mesh"].name, "label": parts["mesh"]["sh_label"]})
    info["creatures"] = made
    scene["sh_template"] = cfg.get("name", "template")
    if out:
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()))
        info["blend"] = str(out)
    return info


def _main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="sh_template.py")
    ap.add_argument("--config", required=True)
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    print(json.dumps(build_template(json.loads(Path(a.config).read_text(encoding="utf-8")), a.frames, Path(a.out)),
                     indent=2))


if __name__ == "__main__":
    _main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
