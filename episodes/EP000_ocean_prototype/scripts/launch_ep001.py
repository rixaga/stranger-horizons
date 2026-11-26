"""Start the EP001 pipeline in a separate background Blender, from Blender's Python console.

The GUI stays responsive; progress goes to logs/run_ep001.log and renders/preview/progress.json.

    import runpy; runpy.run_path('<repo>/episodes/EP000_ocean_prototype/scripts/launch_ep001.py')

Extra arguments for run_ep001.py can be put in scripts/launch_args.json as a list, e.g.
["--resolution", "720"]. Without that file the full pipeline runs with --resolution auto.
"""
import json
import subprocess
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
EP = HERE.parent
args_file = HERE / "launch_args.json"
extra = json.loads(args_file.read_text()) if args_file.is_file() else []
log_path = EP / "logs" / "blender_background.log"
log_path.parent.mkdir(parents=True, exist_ok=True)
cmd = [bpy.app.binary_path, "--background", "--factory-startup", "--python", str(HERE / "run_ep001.py"), "--", *extra]
proc = subprocess.Popen(cmd, stdout=log_path.open("w"), stderr=subprocess.STDOUT, start_new_session=True)
(EP / "logs" / "launch.json").write_text(json.dumps({"pid": proc.pid, "cmd": cmd}, indent=2))
print(f"EP001 pipeline started in background (pid {proc.pid}). Log: {log_path}", file=sys.stderr)
