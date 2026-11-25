#!/usr/bin/env python3
"""Report the tools and resources this machine has for Stranger Horizons production.

Finds Blender on PATH, in $BLENDER_BIN, or in the default macOS / Windows / Linux
install locations, and asks it for its version. Run this before any render.
Exit code 0 = everything needed for rendering found, 1 = something missing.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BLENDER_CANDIDATES = [
    "/Applications/Blender.app/Contents/MacOS/Blender",
    str(Path.home() / "Applications/Blender.app/Contents/MacOS/Blender"),
    r"C:\Program Files\Blender Foundation\Blender\blender.exe",
    "/snap/bin/blender",
    "/usr/bin/blender",
]


def find_blender() -> str | None:
    env = os.environ.get("BLENDER_BIN")
    if env and Path(env).is_file():
        return env
    on_path = shutil.which("blender")
    if on_path:
        return on_path
    return next((c for c in BLENDER_CANDIDATES if Path(c).is_file()), None)


def first_line(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (out.stdout or out.stderr).strip().splitlines()
    return text[0] if text else None


def collect() -> dict:
    blender = find_blender()
    ffmpeg = shutil.which("ffmpeg")
    usage = shutil.disk_usage(REPO)
    try:
        import jsonschema  # noqa: F401
        has_jsonschema = True
    except ImportError:
        has_jsonschema = False
    return {
        "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
        "python": sys.version.split()[0],
        "jsonschema": has_jsonschema,
        "ffmpeg": first_line([ffmpeg, "-version"]) if ffmpeg else None,
        "blender_path": blender,
        "blender": first_line([blender, "--version"]) if blender else None,
        "disk_free_gb": round(usage.free / 1e9, 1),
        "cpu_count": os.cpu_count(),
        "note": "Run blender/scripts/sh_env_check.py inside Blender for engines and GPU devices.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json-out", type=Path, help="also write the report to this file")
    args = parser.parse_args()
    report = collect()
    for key, value in report.items():
        print(f"{key:14} {value}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    ready = bool(report["blender"] and report["ffmpeg"] and report["disk_free_gb"] >= 5)
    print("READY TO RENDER" if ready else "NOT READY: Blender, FFmpeg or 5 GB free disk missing")
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
