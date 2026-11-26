#!/usr/bin/env python3
"""Assemble numbered image frames (and optional audio) into an H.264 MP4 using FFmpeg.

The output is tagged BT.709 so players do not guess the colour matrix, and it is
written to a temporary file that is only renamed into place when FFmpeg succeeds,
so a stopped or failed encode never leaves a short file that still plays.
"""
from __future__ import annotations

import argparse
import glob
import re
import shutil
import subprocess
import sys
from pathlib import Path

BT709 = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
# Also write the tags into the H.264 VUI so they do not depend on FFmpeg version behaviour.
H264_BT709_VUI = ["-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1"]


def pattern_has_frames(pattern: str) -> bool:
    """True if at least one file matches a printf-style pattern such as frame_%05d.png."""
    as_glob = re.sub(r"%0?\d*d", "*", pattern)
    return any(Path(p).is_file() for p in glob.glob(as_glob))


def build_command(ffmpeg: str, args: argparse.Namespace, output: Path) -> list[str]:
    command = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
               "-framerate", str(args.fps)]
    if args.start_number is not None:
        command += ["-start_number", str(args.start_number)]
    command += ["-i", args.input]
    if args.audio:
        command += ["-i", str(args.audio)]
    command += ["-vf", "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(args.crf), "-preset", args.preset, *BT709, *H264_BT709_VUI]
    if args.audio:
        command += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest"]
    command += ["-movflags", "+faststart", "-f", "mp4", str(output)]
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="FFmpeg sequence pattern, e.g. frame_%%05d.png")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--start-number", type=int, help="first frame number (default: FFmpeg auto-detects 0-4)")
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--preset", default="medium", help="x264 preset; use veryfast for quick previews")
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ERROR: FFmpeg was not found on PATH.", file=sys.stderr)
        return 2
    if args.fps <= 0:
        parser.error("--fps must be positive")
    if not pattern_has_frames(args.input):
        print(f"ERROR: No frames match {args.input}", file=sys.stderr)
        return 2
    if args.audio and not args.audio.is_file():
        print(f"ERROR: Audio file not found: {args.audio}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    partial = args.output.with_name(args.output.name + ".partial.mp4")
    result = subprocess.run(build_command(ffmpeg, args, partial), check=False)
    if result.returncode != 0:
        partial.unlink(missing_ok=True)
        print(f"ERROR: FFmpeg exited with code {result.returncode}", file=sys.stderr)
        return result.returncode
    partial.replace(args.output)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
