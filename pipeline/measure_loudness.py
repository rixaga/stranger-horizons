#!/usr/bin/env python3
"""Measure integrated loudness and true peak (ITU-R BS.1770 via FFmpeg ebur128) and
compare with the delivery targets in config/render_config.json (audio section).

Exit code 0 = within target, 1 = outside target, 2 = could not measure.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULTS = {"integrated_lufs_target": -14.0, "integrated_lufs_tolerance": 1.0, "true_peak_max_dbtp": -1.0}


def load_targets() -> dict:
    try:
        cfg = json.loads((REPO / "config" / "render_config.json").read_text(encoding="utf-8"))
        return {**DEFAULTS, **cfg.get("audio", {})}
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULTS)


def measure(path: Path) -> dict:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg was not found on PATH")
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true:framelog=quiet",
         "-f", "null", "-"], capture_output=True, text=True)
    summary = proc.stderr.rsplit("Summary:", 1)[-1]
    i = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", summary)
    lra = re.search(r"LRA:\s+(-?[\d.]+) LU", summary)
    tp = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)
    if proc.returncode != 0 or not i or not tp:
        raise RuntimeError(f"Could not measure loudness of {path}: {proc.stderr.strip()[-400:]}")
    to_f = lambda m: float("-inf") if m.group(1) == "-inf" else float(m.group(1))
    return {"integrated_lufs": to_f(i), "loudness_range_lu": float(lra.group(1)) if lra else None,
            "true_peak_dbtp": to_f(tp)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("media", type=Path)
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args()
    targets = load_targets()
    try:
        m = measure(args.media)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    lufs_ok = abs(m["integrated_lufs"] - targets["integrated_lufs_target"]) <= targets["integrated_lufs_tolerance"]
    peak_ok = m["true_peak_dbtp"] <= targets["true_peak_max_dbtp"]
    report = {**m, "targets": targets, "lufs_ok": lufs_ok, "true_peak_ok": peak_ok, "pass": lufs_ok and peak_ok}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Integrated: {m['integrated_lufs']:.1f} LUFS (target {targets['integrated_lufs_target']} "
              f"±{targets['integrated_lufs_tolerance']}) {'OK' if lufs_ok else 'OUT'}")
        print(f"True peak:  {m['true_peak_dbtp']:.1f} dBTP (max {targets['true_peak_max_dbtp']}) {'OK' if peak_ok else 'OUT'}")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
