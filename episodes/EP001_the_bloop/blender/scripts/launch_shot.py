"""Start run_shot.py for one EP001 scene in a separate background Blender, from Blender's Python console.

The GUI stays responsive; progress goes to logs/run_shot.log and renders/preview/progress.json.

    import runpy; runpy.run_path('<repo>/episodes/EP001_the_bloop/blender/scripts/launch_shot.py')

Arguments for run_shot.py go in launch_args.json next to this file, e.g. ["--scene", "S022", "--tag", "proto1"].
A dict {"script": "<path relative to the episode>", "args": [...]} runs another script instead.
"""
import json
import subprocess
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "blender" / "scripts"))
from sh_launch import build_command  # noqa: E402

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
args_file = HERE / "launch_args.json"
extra = json.loads(args_file.read_text()) if args_file.is_file() else []
log_path = EP / "logs" / "blender_background.log"
log_path.parent.mkdir(parents=True, exist_ok=True)
cmd = build_command(bpy.app.binary_path, HERE, extra)
proc = subprocess.Popen(cmd, stdout=log_path.open("w"), stderr=subprocess.STDOUT, start_new_session=True)
(EP / "logs" / "launch.json").write_text(json.dumps({"pid": proc.pid, "cmd": cmd}, indent=2))
print(f"EP001 background Blender started (pid {proc.pid}). Log: {log_path}", file=sys.stderr)
