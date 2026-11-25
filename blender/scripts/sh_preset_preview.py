"""Render one look-dev still per environment preset on a neutral test set.

Use it to compare presets side by side after changing them. Not production imagery.

    blender --background --factory-startup --python blender/scripts/sh_preset_preview.py -- \
        --out renders/lookdev --engine CYCLES --samples 32 --width 640
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402

from sh_camera import build_camera_move  # noqa: E402
from sh_presets import apply_preset, list_presets, load_preset  # noqa: E402
from sh_render import available_engines, resolve_engine  # noqa: E402


def neutral_set() -> None:
    """Ground plane, scattered boulders and one tall block as a scale cue. Mid-grey, rough."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    mat = bpy.data.materials.new("SH_LookdevGrey")
    if bpy.app.version < (5, 0, 0):
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.18, 0.18, 0.18, 1)
    bsdf.inputs["Roughness"].default_value = 0.85

    def add(obj):
        scene.collection.objects.link(obj)
        obj.data.materials.append(mat)
        return obj

    ground = bpy.data.meshes.new("SH_Ground")
    n, size = 40, 160.0
    rng = random.Random(3)
    verts = [((i / n - 0.5) * size, (j / n - 0.5) * size, rng.uniform(-0.15, 0.15)) for j in range(n + 1) for i in range(n + 1)]
    faces = [(j * (n + 1) + i, j * (n + 1) + i + 1, (j + 1) * (n + 1) + i + 1, (j + 1) * (n + 1) + i) for j in range(n) for i in range(n)]
    ground.from_pydata(verts, [], faces)
    add(bpy.data.objects.new("SH_Ground", ground))
    for k in range(14):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rng.uniform(0.4, 1.6),
                                              location=(rng.uniform(-14, 14), rng.uniform(-6, 22), 0))
        rock = bpy.context.active_object
        rock.scale = (1, rng.uniform(0.7, 1.3), rng.uniform(0.4, 0.8))
        rock.data.materials.append(mat)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 6, 3))
    block = bpy.context.active_object
    block.scale = (2.0, 1.2, 6.0)
    block.data.materials.append(mat)


def main(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="sh_preset_preview.py")
    ap.add_argument("--out", default="renders/lookdev")
    ap.add_argument("--engine", default="CYCLES")
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--presets", nargs="*")
    args = ap.parse_args(argv)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    for name in args.presets or list_presets():
        neutral_set()
        scene = bpy.context.scene
        scene.render.engine = resolve_engine(args.engine, available_engines())
        scene.render.resolution_x = args.width
        scene.render.resolution_y = round(args.width * 9 / 16)
        scene.render.fps = 30
        if scene.render.engine == "CYCLES":
            scene.cycles.samples = args.samples
            scene.cycles.use_denoising = True
        else:
            scene.eevee.taa_render_samples = args.samples
        build_camera_move(scene, "slow_push_in", target=(0, 6, 2.5))
        applied = apply_preset(scene, load_preset(name))
        scene.frame_set(scene.frame_start + 60)
        scene.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        report[name] = applied
        print(f"rendered {name}")
    (out / "lookdev_report.json").write_text(json.dumps(report, indent=2) + "\n")


main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
