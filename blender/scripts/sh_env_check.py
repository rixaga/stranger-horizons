"""Print what this Blender build offers: version, render engines, Cycles GPU backends.

    blender --background --factory-startup --python blender/scripts/sh_env_check.py -- [--json-out path]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def cycles_backends() -> dict:
    out = {}
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except KeyError:
        return {"error": "Cycles add-on not enabled"}
    for backend in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = backend
        except TypeError:
            continue
        prefs.refresh_devices()
        devices = [d.name for d in prefs.devices if d.type != "CPU"]
        if devices:
            out[backend] = devices
    return out


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    engines = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    engines += [c.bl_idname for c in bpy.types.RenderEngine.__subclasses__() if getattr(c, "bl_idname", "")]
    engines = list(dict.fromkeys(engines))
    report = {
        "blender_version": bpy.app.version_string,
        "python": sys.version.split()[0],
        "background": bpy.app.background,
        "render_engines": engines,
        "view_transform_default": bpy.context.scene.view_settings.view_transform,
        "cycles_gpu_backends": cycles_backends(),
    }
    print(json.dumps(report, indent=2))
    if "--json-out" in argv:
        path = Path(argv[argv.index("--json-out") + 1])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


main()
