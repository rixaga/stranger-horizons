"""Find and run FFmpeg/ffprobe with clear errors; shared encoding settings."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .errors import CommandFailed, ToolMissing

# macOS apps launched from the Dock do not inherit Homebrew's PATH.
EXTRA_DIRS = ("/opt/homebrew/bin", "/usr/local/bin")
BT709 = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
# Belt and braces: also write the tags straight into the H.264 VUI, so they survive any
# change in how FFmpeg versions pass output colour options to the encoder.
H264_BT709_VUI = ["-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1"]
INSTALL_HINT = "Install it with `brew install ffmpeg` (macOS) or your package manager, then retry."


def find(tool: str = "ffmpeg") -> str:
    found = shutil.which(tool)
    if found:
        return found
    for d in EXTRA_DIRS:
        candidate = Path(d) / tool
        if candidate.is_file():
            return str(candidate)
    raise ToolMissing(f"{tool} was not found. {INSTALL_HINT}")


def run(args: list[str], logger=None) -> subprocess.CompletedProcess:
    cmd = [find(args[0]), *args[1:]]
    if logger:
        logger.debug("run: %s", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-6:])
        raise CommandFailed(f"{args[0]} failed (exit {proc.returncode}):\n{tail}")
    return proc


def probe(path: Path) -> dict:
    out = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)])
    return json.loads(out.stdout)


def atomic_output(final: Path) -> Path:
    """Temporary sibling path that still ends in the real extension (players reject odd suffixes)."""
    final = Path(final)
    final.parent.mkdir(parents=True, exist_ok=True)
    return final.with_name(final.stem + ".partial" + final.suffix)


def encode_sequence(pattern: str, output: Path, fps: int = 30, crf: int = 18, preset: str = "medium",
                    start_number: int | None = None, audio: Path | None = None, logger=None) -> Path:
    """PNG sequence (+ optional audio) → H.264 MP4 tagged BT.709, written atomically."""
    output = Path(output)
    tmp = atomic_output(output)
    args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(fps)]
    if start_number is not None:
        args += ["-start_number", str(start_number)]
    args += ["-i", pattern]
    if audio:
        args += ["-i", str(audio)]
    args += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), "-preset", preset, *BT709, *H264_BT709_VUI]
    if audio:
        args += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest"]
    args += ["-movflags", "+faststart", str(tmp)]
    try:
        run(args, logger)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    tmp.replace(output)
    return output
