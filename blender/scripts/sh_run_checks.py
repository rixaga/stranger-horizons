"""Run every environment check from inside Blender's GUI and save the reports.

Useful on macOS, where Blender launched from the Dock does not see Homebrew's PATH.
Paste into Blender's Python console (Scripting workspace):

    import runpy; runpy.run_path('/path/to/repo/blender/scripts/sh_run_checks.py')

Writes reports/environment/{blender.json, host.json, hardware.txt} in the repo.
"""
import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "reports" / "environment"
OUT.mkdir(parents=True, exist_ok=True)

for extra in ("/opt/homebrew/bin", "/usr/local/bin"):
    if extra not in os.environ.get("PATH", ""):
        os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + extra


def _run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"<{exc.__class__.__name__}>"


_saved_argv = sys.argv
try:
    sys.argv = ["blender", "--", "--json-out", str(OUT / "blender.json")]
    runpy.run_path(str(REPO / "blender" / "scripts" / "sh_env_check.py"))
    sys.argv = ["check_environment", "--json-out", str(OUT / "host.json")]
    runpy.run_path(str(REPO / "pipeline" / "check_environment.py"))["main"]()
finally:
    sys.argv = _saved_argv

hw = [
    "model: " + _run(["sysctl", "-n", "hw.model"]),
    "cpu: " + _run(["sysctl", "-n", "machdep.cpu.brand_string"]),
    "memory_bytes: " + _run(["sysctl", "-n", "hw.memsize"]),
    "cores: " + _run(["sysctl", "-n", "hw.ncpu"]),
    _run(["sw_vers"]),
    "xcode_cli_tools: " + ("yes" if _run(["xcode-select", "-p"]) else "no"),
    "python3_on_path: " + str(shutil.which("python3")),
    "ffmpeg_on_path: " + str(shutil.which("ffmpeg")),
]
(OUT / "hardware.txt").write_text("\n".join(hw) + "\n", encoding="utf-8")
print(f"Environment reports written to {OUT}")
