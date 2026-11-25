#!/usr/bin/env python3
"""Assemble numbered image frames with optional audio using FFmpeg."""
from __future__ import annotations
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="FFmpeg sequence pattern, e.g. frame_%05d.png")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--crf", type=int, default=18)
    args = parser.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ERROR: FFmpeg was not found on PATH.", file=sys.stderr)
        return 2
    if args.fps <= 0:
        parser.error("--fps must be positive")
    if args.audio and not args.audio.is_file():
        print(f"ERROR: Audio file not found: {args.audio}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = [ffmpeg, "-y", "-framerate", str(args.fps), "-i", args.input]
    if args.audio:
        command += ["-i", str(args.audio), "-shortest"]
    command += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(args.crf), "-preset", "medium"]
    if args.audio:
        command += ["-c:a", "aac", "-b:a", "192k"]
    command.append(str(args.output))
    return subprocess.run(command, check=False).returncode

if __name__ == "__main__":
    raise SystemExit(main())
