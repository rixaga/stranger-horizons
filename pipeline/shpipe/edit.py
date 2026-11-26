"""Video Editor: subtitles from the storyboard, per-scene clips, concat, final mux.

Follows the one-clip-per-scene pattern: each scene's image sequence is encoded once
with identical settings, clips are joined with the concat demuxer without
re-encoding, and the final mix is muxed with the video stream copied.
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

from . import config, ffmpeg
from .errors import ShError
from .paths import Episode
from .storyboard import load, timeline

MAX_CHARS, MAX_LINES = 42, 2


def _srt_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _cues(text: str) -> list[str]:
    lines = textwrap.wrap(" ".join(text.split()), MAX_CHARS)
    return ["\n".join(lines[i:i + MAX_LINES]) for i in range(0, len(lines), MAX_LINES)]


def write_srt(ep: Episode, out: Path | None = None) -> Path:
    """One or more cues per scene, timed proportionally to characters within the scene."""
    sb = load(ep)
    rows = {r["scene_id"]: r for r in timeline(sb)}
    blocks, n = [], 0
    for scene in sb["scenes"]:
        cues = _cues(scene.get("narration", ""))
        if not cues:
            continue
        row = rows[scene["scene_id"]]
        start, span = row["start_seconds"], row["end_seconds"] - row["start_seconds"]
        total = sum(len(c) for c in cues)
        for cue in cues:
            dur = span * len(cue) / total
            n += 1
            blocks.append(f"{n}\n{_srt_time(start)} --> {_srt_time(start + dur)}\n{cue}\n")
            start += dur
    out = Path(out or ep.root / "final" / f"{ep.episode_id}.srt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(blocks), encoding="utf-8")
    return out


def frame_pattern(folder: Path) -> tuple[str, int]:
    """Return (printf pattern, first frame number) for frame_0001.png-style sequences."""
    frames = sorted(folder.glob("frame_*.png"))
    if not frames:
        raise ShError(f"No frames (frame_*.png) in {folder}")
    m = re.fullmatch(r"frame_(\d+)\.png", frames[0].name)
    digits = len(m.group(1))
    return str(folder / f"frame_%0{digits}d.png"), int(m.group(1))


def encode_scene_clip(ep: Episode, scene_id: str, mode: str = "preview", logger=None) -> Path:
    sb = load(ep)
    enc = config.render_config().get("encode", {})
    pattern, first = frame_pattern(ep.render_dir(mode, scene_id))
    crf = enc.get("crf_preview", 23) if mode == "preview" else enc.get("crf_delivery", 18)
    preset = "veryfast" if mode == "preview" else "medium"
    return ffmpeg.encode_sequence(pattern, ep.clip(mode, scene_id), fps=int(sb["fps"]), crf=crf, preset=preset,
                                  start_number=first, logger=logger)


def concat(clips: list[Path], out: Path, logger=None) -> Path:
    """Join clips with identical encoding settings without re-encoding."""
    out = Path(out)
    tmp = ffmpeg.atomic_output(out)
    listing = out.with_suffix(".concat.txt")
    listing.write_text("".join(f"file '{Path(c).resolve()}'\n" for c in clips), encoding="utf-8")
    try:
        ffmpeg.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(listing), "-c", "copy", "-movflags", "+faststart", str(tmp)], logger)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    finally:
        listing.unlink(missing_ok=True)
    tmp.replace(out)
    return out


def mux(video: Path, audio: Path, out: Path, logger=None) -> Path:
    """Add the final mix to the edited video; the video stream is copied, not re-encoded."""
    out = Path(out)
    tmp = ffmpeg.atomic_output(out)
    try:
        ffmpeg.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video), "-i", str(audio),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart", str(tmp)], logger)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    tmp.replace(out)
    return out
