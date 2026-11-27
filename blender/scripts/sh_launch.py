"""Command line for a background Blender run, from an episode's launch_args.json.

A list is the argument list for run_shot.py (the shot pipeline). A dict {"script": <path relative to
the episode folder>, "args": [...]} runs any other script, e.g. a Shorts mockup.
"""
from __future__ import annotations

from pathlib import Path


def build_command(binary: str, here: Path, spec) -> list[str]:
    here = Path(here)
    if isinstance(spec, dict):
        script = here.parents[1] / spec["script"]
        extra = list(spec.get("args", []))
    else:
        script = here / "run_shot.py"
        extra = list(spec or [])
    return [binary, "--background", "--factory-startup", "--python", str(script), "--", *extra]
