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
BT709_FRAMES = "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709"
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
                    start_number: int | None = None, audio: Path | None = None, logger=None,
                    grain: float = 0.0, dark_scene: bool = False) -> Path:
    """PNG sequence (+ optional audio) → H.264 MP4 tagged BT.709, written atomically.

    grain: temporal luma noise strength (0 = off, ~1.5–3 subtle) that dithers dark gradients so
    8-bit H.264 does not band. dark_scene: x264 adaptive quantisation tuned for dark content."""
    output = Path(output)
    tmp = atomic_output(output)
    args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(fps)]
    if start_number is not None:
        args += ["-start_number", str(start_number)]
    args += ["-i", pattern]
    if audio:
        args += ["-i", str(audio)]
    # setparams relabels the decoded frames: Blender PNGs carry sRGB transfer, which FFmpeg 9.1
    # otherwise passes through to the MP4 (seen on the owner's Mac: color_transfer=iec61966-2-1).
    vf = (f"noise=c0s={grain:g}:c0f=t," if grain > 0 else "") + BT709_FRAMES
    args += ["-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), "-preset", preset,
             *BT709, *H264_BT709_VUI]
    if dark_scene:
        args += ["-x264-params", "aq-mode=3:aq-strength=0.9:deblock=-1,-1"]
    if audio:
        args += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest"]
    args += ["-movflags", "+faststart", str(tmp)]
    try:
        run(args, logger)
        retag_bt709(tmp, logger)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    tmp.replace(output)
    return output


def retag_bt709(path: Path, logger=None) -> Path:
    """Stream-copy remux that rewrites the colour description as BT.709 in both the H.264 VUI
    (h264_metadata bitstream filter) and the MP4 'colr' box.
    FFmpeg 9.1 carried the PNG's sRGB transfer into the container even when the H.264 VUI said BT.709."""
    path = Path(path)
    tmp = path.with_name(path.stem + ".retag" + path.suffix)
    try:
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path), "-map", "0", "-c", "copy",
             *BT709, *H264_BT709_VUI, "-movflags", "+faststart+write_colr", str(tmp)], logger)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    tmp.replace(path)
    return path
