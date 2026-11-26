from __future__ import annotations

import json
import subprocess
from pathlib import Path

from conftest import PIPELINE, needs_ffmpeg, run
from test_shpipe_core import ep  # noqa: F401


def _frames(d: Path, n: int, color: str):
    d.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c={color}:s=320x180:r=30",
                    "-frames:v", str(n), "-start_number", "1", str(d / "frame_%04d.png")], check=True)


def _probe(p: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,color_space,color_primaries,color_transfer",
                          "-of", "json", str(p)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


@needs_ffmpeg
def test_clips_concat_and_mux(ep):
    from shpipe import edit
    from shpipe.paths import Episode
    e = Episode(ep)
    _frames(e.render_dir("preview", "S01"), 120, "navy")
    _frames(e.render_dir("preview", "S02"), 60, "gray")
    clips = [edit.encode_scene_clip(e, s, "preview") for s in ("S01", "S02")]
    assert all(c.is_file() for c in clips)
    joined = edit.concat(clips, e.root / "edit" / "joined.mp4")
    info = _probe(joined)
    assert abs(float(info["format"]["duration"]) - 6.0) < 0.1
    v = info["streams"][0]
    assert (v.get("color_space"), v.get("color_primaries"), v.get("color_transfer")) == ("bt709",) * 3
    wav = e.root / "audio" / "mix.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=220:duration=6", str(wav)], check=True)
    final = edit.mux(joined, wav, e.root / "final" / "EP900.mp4")
    kinds = sorted(s["codec_type"] for s in _probe(final)["streams"])
    assert kinds == ["audio", "video"]


@needs_ffmpeg
def test_render_check_counts_frames(ep):
    from shpipe import qc
    from shpipe.paths import Episode
    e = Episode(ep)
    _frames(e.render_dir("preview", "S01"), 120, "navy")
    _frames(e.render_dir("preview", "S02"), 30, "gray")      # short by 30 frames
    r = qc.check_renders(e, "preview")
    assert r["scenes"]["S01"]["ok"] is True
    assert r["scenes"]["S02"]["found"] == 30 and r["scenes"]["S02"]["ok"] is False
    assert r["status"] == "fail"


def test_cli_smoke(ep):
    result = run(str(PIPELINE / "sh.py"), "storyboard", str(ep))
    assert result.returncode == 1                      # fixture has storyboard errors
    assert "S02" in result.stdout
    result = run(str(PIPELINE / "sh.py"), "--help")
    assert result.returncode == 0
    for cmd in ("episode-new", "approve", "research", "script", "storyboard", "assets", "srt", "clip", "concat", "mux", "qc"):
        assert cmd in result.stdout
