"""Wordless promo Shorts: shot list validation and overlay element timing."""
from __future__ import annotations

import pytest

LEDGER = {"claims": [{"claim_id": "C01"}, {"claim_id": "C47"}]}


def short(**over):
    s = {"short_id": "S01", "fps": 30, "width": 1080, "height": 1920,
         "shots": [{"id": "SH01", "duration_s": 2.0, "elements": [
             {"type": "pill", "text": "1997 · PACIFIC", "claims": ["C01"], "in_s": 0.5, "out_s": 1.5},
             {"type": "tag", "text": "IMAGINED — NOT EVIDENCE", "claims": []}]},
                   {"id": "SH02", "duration_s": 1.0, "elements": []}]}
    s.update(over)
    return s


def test_valid_short_has_no_problems_and_timeline_adds_up():
    from shpipe.shorts import shot_ranges, validate_short
    s = short()
    assert validate_short(s, LEDGER) == []
    assert shot_ranges(s) == [("SH01", 0, 60), ("SH02", 60, 90)]


def test_unknown_claim_and_untagged_number_are_problems():
    from shpipe.shorts import validate_short
    s = short()
    s["shots"][0]["elements"].append({"type": "pill", "text": "OVER 5,000 km", "claims": []})
    s["shots"][0]["elements"].append({"type": "pill", "text": "x", "claims": ["C99"]})
    probs = validate_short(s, LEDGER)
    assert any("5,000" in p for p in probs)      # digits on screen need a claim (or "design": true)
    assert any("C99" in p for p in probs)


def test_element_alpha_fades_in_and_out():
    from shpipe.shorts import element_alpha
    el = {"in_s": 1.0, "out_s": 2.0}
    assert element_alpha(el, 0.9, shot_s=3.0) == 0.0
    assert element_alpha(el, 1.1, shot_s=3.0) == pytest.approx(0.5)   # 0.2 s fade
    assert element_alpha(el, 1.5, shot_s=3.0) == 1.0
    assert element_alpha(el, 2.05, shot_s=3.0) == pytest.approx(0.75)
    assert element_alpha({}, 0.0, shot_s=3.0) == 1.0                   # default: whole shot, no fade at t=0


def test_hud_and_meter_values_are_checked_too():
    from shpipe.shorts import validate_short
    s = short()
    s["shots"][1]["elements"] = [{"type": "hud", "speed": "16x FASTER", "pitch": "9–28 Hz", "claims": []},
                                 {"type": "meter", "label": "HEARD FROM", "value": "OVER 5,000 km", "claims": []}]
    probs = validate_short(s, LEDGER)
    assert len(probs) == 2


def test_locate_frame_gives_shot_and_local_time():
    from shpipe.shorts import locate_frame
    s = short()
    assert locate_frame(s, 0) == ("SH01", 0, 0.0)
    assert locate_frame(s, 61) == ("SH02", 1, pytest.approx(1 / 30))
    with pytest.raises(IndexError):
        locate_frame(s, 90)


def test_wave_envelope_peaks(tmp_path):
    import math
    import struct
    import wave
    from shpipe.shorts import wave_envelope
    p = tmp_path / "t.wav"
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(1000)
        data = [int(10000 * (i / 1000) * math.sin(i)) for i in range(2000)]  # louder over time
        w.writeframes(struct.pack(f"<{len(data)}h", *data))
    env = wave_envelope(p, 0.0, 2.0, bins=20)
    assert len(env) == 20 and max(env) == pytest.approx(1.0)
    assert env[-1] > env[2] > 0                                             # rising loudness


def test_render_frame_size_and_hidden_elements(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    from shpipe.shorts_render import render_frame
    plate = Image.new("RGB", (1080, 1920), (10, 20, 40))
    shot = {"id": "SH01", "duration_s": 2.0, "elements": [{"type": "big", "text": "HELLO", "y": 900, "in_s": 1.0}]}
    before = render_frame(plate, shot, 0.5, tracks={}, frame=15, fonts=None)
    assert before.size == (1080, 1920) and before.tobytes() == plate.tobytes()
    after = render_frame(plate, shot, 1.6, tracks={}, frame=48, fonts=None)
    assert after.tobytes() != plate.tobytes()
