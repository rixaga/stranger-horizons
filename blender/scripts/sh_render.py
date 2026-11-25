"""Render-profile helpers for Stranger Horizons.

Pure functions (resolve_engine, load_profile) import without Blender so they can be
unit-tested. apply_profile() and write_render_log() need bpy and run inside Blender.

Usage inside Blender:
    blender --background scene.blend --python blender/scripts/sh_render.py -- --profile preview --output //renders/frame_
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "config" / "render_config.json"

# Logical engine names used in config, mapped to identifiers seen across Blender versions.
ENGINE_ALIASES = {
    "EEVEE": ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"),
    "BLENDER_EEVEE": ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"),
    "BLENDER_EEVEE_NEXT": ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"),
    "CYCLES": ("CYCLES",),
    "BLENDER_CYCLES": ("CYCLES",),
    "WORKBENCH": ("BLENDER_WORKBENCH",),
}


def resolve_engine(name: str, available: list[str] | tuple[str, ...]) -> str:
    """Return the engine identifier the running Blender actually offers for a logical name."""
    for candidate in ENGINE_ALIASES.get(name.upper(), (name,)):
        if candidate in available:
            return candidate
    raise ValueError(f"Render engine {name!r} not available; this Blender offers {sorted(available)}")


def load_config(path: Path = CONFIG) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_profile(name: str, config: dict | None = None) -> dict:
    """Return one profile from render_config.json with the global fps merged in."""
    config = config if config is not None else load_config()
    if name not in config.get("profiles", config):
        raise KeyError(f"Unknown render profile {name!r}")
    profiles = config.get("profiles", config)
    profile = dict(profiles[name])
    profile.setdefault("fps", config.get("fps", 30))
    if "engine" not in profile and "preferred_engine" in profile:
        profile["engine"] = profile["preferred_engine"]
    return profile


# ---------------------------------------------------------------- Blender-only

def available_engines() -> list[str]:
    """Built-in engines from the RNA enum plus engines registered by add-ons (Cycles, Workbench)."""
    import bpy
    built_in = [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    registered = [cls.bl_idname for cls in bpy.types.RenderEngine.__subclasses__() if getattr(cls, "bl_idname", "")]
    return list(dict.fromkeys(built_in + registered))


def apply_profile(scene, profile: dict, output: str | None = None) -> dict:
    """Apply a profile to a bpy scene. Safe to rerun. Returns what was actually set."""
    r = scene.render
    engine = resolve_engine(profile.get("engine", "EEVEE"), available_engines())
    r.engine = engine
    r.resolution_x = int(profile["resolution_x"])
    r.resolution_y = int(profile["resolution_y"])
    r.resolution_percentage = int(profile.get("resolution_percentage", 100))
    r.fps = int(profile["fps"])
    r.fps_base = 1.0
    r.image_settings.file_format = profile.get("file_format", "PNG")
    if r.image_settings.file_format == "PNG":
        r.image_settings.color_depth = str(profile.get("color_depth", "16"))
        r.image_settings.compression = 15
    if output:
        r.filepath = output
    samples = profile.get("samples")
    if samples:
        if engine == "CYCLES":
            scene.cycles.samples = int(samples)
            scene.cycles.use_denoising = bool(profile.get("denoise", True))
        elif hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = int(samples)
    view = profile.get("color_management")
    if view:
        try:
            scene.view_settings.view_transform = view
        except TypeError:
            print(f"WARNING: view transform {view!r} not available; kept {scene.view_settings.view_transform!r}")
    if engine == "CYCLES" and profile.get("device", "GPU") == "GPU":
        _enable_gpu(scene)
    return {"engine": engine, "resolution": [r.resolution_x, r.resolution_y], "fps": r.fps,
            "samples": samples, "view_transform": scene.view_settings.view_transform, "filepath": r.filepath}


def _enable_gpu(scene) -> str:
    """Use the first available GPU backend (METAL on Apple Silicon, OPTIX/CUDA/HIP/ONEAPI elsewhere)."""
    import bpy
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for backend in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = backend
        except TypeError:
            continue
        prefs.refresh_devices()
        gpus = [d for d in prefs.devices if d.type != "CPU"]
        if gpus:
            for d in prefs.devices:
                d.use = d.type != "CPU"
            scene.cycles.device = "GPU"
            return backend
    scene.cycles.device = "CPU"
    print("WARNING: no GPU backend found; Cycles will render on CPU")
    return "CPU"


def write_render_log(scene, applied: dict, path: Path) -> None:
    """Record software version and settings next to the renders (CLAUDE.md requirement)."""
    import bpy
    log = {"written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "blender_version": bpy.app.version_string, "blend_file": bpy.data.filepath or None,
           "frame_start": scene.frame_start, "frame_end": scene.frame_end, **applied}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")


def _main(argv: list[str]) -> None:
    import argparse
    import bpy
    parser = argparse.ArgumentParser(prog="sh_render.py")
    parser.add_argument("--profile", default="preview")
    parser.add_argument("--output", help="render output path prefix, e.g. //renders/frame_")
    parser.add_argument("--render", action="store_true", help="render the animation after applying")
    args = parser.parse_args(argv)
    scene = bpy.context.scene
    applied = apply_profile(scene, load_profile(args.profile), args.output)
    print(json.dumps(applied, indent=2))
    if args.render:
        out_dir = Path(bpy.path.abspath(scene.render.filepath)).parent
        write_render_log(scene, applied, out_dir / "render_log.json")
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    _main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
