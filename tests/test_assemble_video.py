from __future__ import annotations

import json
import subprocess
from pathlib import Path

from conftest import PIPELINE, needs_ffmpeg, run

SCRIPT = str(PIPELINE / "assemble_video.py")


def probe(path: Path) -> dict:
    # Full -show_streams, not -show_entries: ffprobe 9.1 omits color_primaries/color_transfer
    # from a -show_entries selection even when the stream carries them.
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)["streams"][0]


def test_help_does_not_crash():
    result = run(SCRIPT, "--help")
    assert result.returncode == 0, result.stderr
    assert "frame_%05d.png" in result.stdout


@needs_ffmpeg
def test_output_is_tagged_bt709(frames: Path, tmp_path: Path):
    out = tmp_path / "out.mp4"
    result = run(SCRIPT, "--input", str(frames / "frame_%05d.png"), "--output", str(out))
    assert result.returncode == 0, result.stderr
    info = probe(out)
    assert info["color_space"] == "bt709"
    assert info["color_primaries"] == "bt709"
    assert info["color_transfer"] == "bt709"
    assert info["nb_frames"] == "30"


@needs_ffmpeg
def test_missing_frames_gives_clear_error(tmp_path: Path):
    out = tmp_path / "out.mp4"
    result = run(SCRIPT, "--input", str(tmp_path / "nothing_%05d.png"), "--output", str(out))
    assert result.returncode == 2
    assert "no frames" in result.stderr.lower()
    assert not out.exists()


@needs_ffmpeg
def test_failed_encode_leaves_no_partial_output(frames: Path, tmp_path: Path):
    out = tmp_path / "out.mp4"
    # An unknown x264 preset makes FFmpeg fail after it has started.
    result = run(SCRIPT, "--input", str(frames / "frame_%05d.png"), "--output", str(out), "--preset", "not_a_preset")
    assert result.returncode != 0
    assert not out.exists()
    assert not list(tmp_path.glob("*.partial*"))
