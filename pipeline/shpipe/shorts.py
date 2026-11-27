"""Wordless promo Shorts: shot list (short.json) checks and overlay element timing.

A short is a list of shots; each shot has a 3D/background plate and timed overlay elements
(text cards, HUD, callouts). Text that states a fact must name the claim(s) it rests on, so a
Short can never say more than the episode's claim ledger supports.
"""
from __future__ import annotations

import re

FADE_S = 0.2
_DIGIT = re.compile(r"\d")


def shot_ranges(short: dict) -> list[tuple[str, int, int]]:
    """[(shot_id, first_frame, end_frame_exclusive)] on the Short's timeline."""
    fps, start, out = short["fps"], 0, []
    for shot in short["shots"]:
        n = round(shot["duration_s"] * fps)
        out.append((shot["id"], start, start + n))
        start += n
    return out


def validate_short(short: dict, ledger: dict) -> list[str]:
    known = {c["claim_id"] for c in ledger.get("claims", ledger if isinstance(ledger, list) else [])}
    problems = []
    for shot in short["shots"]:
        for el in shot.get("elements", []):
            text = " ".join(str(el.get(k, "")) for k in ("text", "title", "sub", "speed", "pitch", "label", "value"))
            for cid in el.get("claims", []):
                if cid not in known:
                    problems.append(f"{shot['id']}: '{text}' cites unknown claim {cid}")
            if _DIGIT.search(text) and not el.get("claims") and not el.get("design"):
                problems.append(f"{shot['id']}: '{text}' shows a number but cites no claim")
            if el.get("out_s", shot["duration_s"]) > shot["duration_s"] + 1e-6:
                problems.append(f"{shot['id']}: '{text}' ends after the shot")
    return problems


def element_alpha(el: dict, t: float, shot_s: float) -> float:
    """Opacity of an element at time t (seconds into its shot): 0.2 s fades at its own in/out."""
    t_in, t_out = el.get("in_s", 0.0), el.get("out_s", shot_s)
    if t < t_in:
        return 0.0
    a = 1.0
    if t_in > 0:
        a = min(a, (t - t_in) / FADE_S)
    if t_out < shot_s and t >= t_out:
        a = min(a, 1.0 - (t - t_out) / FADE_S)
    return max(0.0, min(1.0, a))


def locate_frame(short: dict, frame: int) -> tuple[str, int, float]:
    """Short timeline frame -> (shot_id, frame within the shot, seconds within the shot)."""
    for sid, a, b in shot_ranges(short):
        if a <= frame < b:
            return sid, frame - a, (frame - a) / short["fps"]
    raise IndexError(f"frame {frame} is past the end of the Short")


def wave_envelope(path, from_s: float, dur_s: float, bins: int = 400) -> list[float]:
    """Peak amplitude per bin of a mono/stereo 16-bit WAV segment, normalised to 1."""
    import struct
    import wave
    with wave.open(str(path), "rb") as w:
        rate, ch, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        if width != 2:
            raise ValueError("expected 16-bit PCM")
        w.setpos(min(int(from_s * rate), w.getnframes()))
        n = min(int(dur_s * rate), w.getnframes() - w.tell())
        raw = w.readframes(n)
    samples = struct.unpack(f"<{len(raw) // 2}h", raw)[::ch]
    step = max(1, len(samples) // bins)
    peaks = [max((abs(x) for x in samples[i * step:(i + 1) * step]), default=0) for i in range(bins)]
    top = max(peaks) or 1
    return [p / top for p in peaks]
