"""Shared fixtures for Stranger Horizons pipeline tests."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PIPELINE = REPO / "pipeline"
sys.path.insert(0, str(PIPELINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(REPO / "blender" / "scripts"))

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg not installed")


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=cwd)


@pytest.fixture
def frames(tmp_path: Path) -> Path:
    """30 tiny PNG frames named frame_00001.png ..."""
    if shutil.which("ffmpeg") is None:
        pytest.skip("FFmpeg not installed")
    out = tmp_path / "frames"
    out.mkdir()
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=30",
         "-frames:v", "30", "-start_number", "1", str(out / "frame_%05d.png")],
        check=True,
    )
    return out
