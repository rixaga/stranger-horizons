from __future__ import annotations

import json

import jsonschema
import pytest

from conftest import REPO

PRESET_DIR = REPO / "config" / "presets"
TOPICS = ["deep_ocean", "antarctica", "underground", "ancient_civilizations", "uap_visualization", "space_cosmic"]
SCHEMA = json.loads((REPO / "schemas" / "environment_preset.schema.json").read_text())


@pytest.mark.parametrize("name", ["base", *TOPICS])
def test_preset_file_matches_schema(name):
    data = json.loads((PRESET_DIR / f"{name}.json").read_text())
    assert [e.message for e in jsonschema.Draft202012Validator(SCHEMA).iter_errors(data)] == []


@pytest.mark.parametrize("name", TOPICS)
def test_merged_preset_keeps_shared_identity(name):
    from sh_presets import load_preset
    p = load_preset(name)
    assert p["color_management"]["view_transform"] == "AgX"
    assert p["color_management"]["look"] == "Medium High Contrast"
    assert -1.0 <= p["color_management"]["exposure"] <= 1.0
    assert p["palette"]["abyss_navy"] == "#0B1622"
    assert p["accent"] in ("signal_cyan", "ember_amber")
    assert p["editorial_rules"], "every topic must carry editorial rules"
    # base editorial rules are inherited, topic rules appended
    assert any("CGI is illustration" in r for r in p["editorial_rules"])


def test_merge_is_deep_and_topic_wins():
    from sh_presets import load_preset
    p = load_preset("deep_ocean")
    assert p["camera"]["lens_mm"] == 24          # topic override
    assert p["camera"]["clip_start_m"] == 0.05   # inherited from base
    assert p["volume"]["kind"] == "water"


def test_vacuum_has_no_volume_or_particles():
    from sh_presets import load_preset
    p = load_preset("space_cosmic")
    assert p["volume"]["kind"] == "none"
    assert p["particles"]["kind"] == "none"


def test_unknown_preset_raises():
    from sh_presets import load_preset
    with pytest.raises(FileNotFoundError):
        load_preset("atlantis")


def test_camera_keyframes_ease_and_hold():
    from sh_camera import compute_keyframes
    keys = compute_keyframes("descent_reveal", target=(0, 0, 0), fps=30, frame_start=1)
    frames = [k["frame"] for k in keys]
    assert frames[0] == 1
    assert frames == sorted(frames)
    # final framing is held: last two keys share a location
    assert keys[-1]["location"] == keys[-2]["location"]
    assert keys[-1]["frame"] - keys[-2]["frame"] == 60  # 2.0 s hold at 30 fps
    assert keys[0]["location"] == (0, -6, 18)


def test_camera_duration_override():
    from sh_camera import compute_keyframes
    keys = compute_keyframes("slow_push_in", target=(1, 2, 3), fps=30, frame_start=101, duration_s=4)
    assert keys[0]["frame"] == 101 and keys[-1]["frame"] == 101 + 4 * 30
    assert keys[0]["location"] == (1, -12, 5.5)


def test_orbit_keyframes_stay_on_radius():
    from sh_camera import compute_keyframes
    import math
    keys = compute_keyframes("controlled_orbit", target=(0, 0, 0), fps=30, frame_start=1)
    for k in keys:
        x, y, _ = k["location"]
        assert math.isclose(math.hypot(x, y), 15, rel_tol=1e-6)


@pytest.mark.parametrize("move", json.loads((REPO / "config" / "camera_presets.json").read_text())["moves"])
def test_every_camera_move_builds(move):
    from sh_camera import compute_keyframes
    assert len(compute_keyframes(move, target=(0, 0, 0), fps=30, frame_start=1)) >= 2
