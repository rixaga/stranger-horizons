from __future__ import annotations

import json
import subprocess
from pathlib import Path

from conftest import PIPELINE, needs_ffmpeg, run


@needs_ffmpeg
def test_loudness_report_flags_too_quiet_audio(tmp_path: Path):
    wav = tmp_path / "tone.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=5,volume=-30dB", str(wav)], check=True)
    result = run(str(PIPELINE / "measure_loudness.py"), str(wav), "--json")
    assert result.returncode == 1, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["integrated_lufs"] < -20
    assert report["pass"] is False


@needs_ffmpeg
def test_loudness_report_passes_on_target(tmp_path: Path):
    wav = tmp_path / "tone.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=8", "-af", "loudnorm=I=-14:TP=-2:LRA=7", "-ar", "48000",
                    str(wav)], check=True)
    result = run(str(PIPELINE / "measure_loudness.py"), str(wav), "--json")
    report = json.loads(result.stdout)
    assert abs(report["integrated_lufs"] - -14) <= 1.0, report
    assert result.returncode == 0, report


def test_environment_check_reports_core_tools(tmp_path: Path):
    out = tmp_path / "env.json"
    result = run(str(PIPELINE / "check_environment.py"), "--json-out", str(out))
    assert result.returncode in (0, 1), result.stderr
    data = json.loads(out.read_text())
    for key in ("python", "ffmpeg", "blender", "disk_free_gb", "platform"):
        assert key in data
