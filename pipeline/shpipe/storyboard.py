"""Storyboard Generator checks: schema, timeline, requirements, shot list.

Storyboards are drafted as JSON (Claude from the approved script, owner approves).
This module turns them into frame-accurate timing and a list of what production needs.
"""
from __future__ import annotations

import csv
from pathlib import Path

from . import config
from .paths import Episode

WORDS_PER_SECOND = 145 / 60
FOOTAGE = {"documentary_footage", "licensed_archival_footage", "original_footage"}


def timecode(frame_index: int, fps: int) -> str:
    """0-based frame index → HH:MM:SS:FF."""
    s, f = divmod(frame_index, fps)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def load(ep: Episode) -> dict:
    return config.load_json(ep.storyboard)


def timeline(sb: dict) -> list[dict]:
    fps = int(sb["fps"])
    out, cursor = [], 0
    for scene in sb["scenes"]:
        frames = round(scene["duration_seconds"] * fps)
        out.append({"scene_id": scene["scene_id"], "frames": frames, "shot_frame_start": 1, "shot_frame_end": frames,
                    "start_frame_edit": cursor + 1, "start_timecode": timecode(cursor, fps),
                    "start_seconds": cursor / fps, "end_seconds": (cursor + frames) / fps})
        cursor += frames
    return out


def check(ep: Episode) -> dict:
    if not ep.storyboard.is_file():
        return {"status": "fail", "errors": ["storyboard/storyboard.json is missing"]}
    sb = load(ep)
    errors = [f"schema: {e}" for e in config.validate(sb, "storyboard")]
    if errors:
        return {"status": "fail", "errors": errors}
    presets_known = set(config.environment_presets())
    moves_known = set(config.camera_moves())
    register = config.REPO / "assets" / "asset_register.json"
    assets_known = {a["id"] for a in config.load_json(register).get("assets", [])} if register.is_file() else set()

    presets, moves, asset_ids, no_label, too_long = set(), set(), set(), [], []
    for s in sb["scenes"]:
        sid = s["scene_id"]
        if p := s.get("environment_preset"):
            presets.add(p)
            if p not in presets_known:
                errors.append(f"{sid}: unknown environment_preset {p!r}")
        if m := s.get("camera_preset"):
            moves.add(m)
            if m not in moves_known:
                errors.append(f"{sid}: unknown camera_preset {m!r}")
        for a in s.get("asset_ids", []):
            asset_ids.add(a)
            if a not in assets_known:
                errors.append(f"{sid}: asset {a} is not in assets/asset_register.json")
        if s["reconstruction_status"] not in FOOTAGE and not s.get("on_screen_label"):
            no_label.append(sid)
        words = len(s.get("narration", "").split())
        if words > s["duration_seconds"] * WORDS_PER_SECOND:
            too_long.append(sid)
    ids = [s["scene_id"] for s in sb["scenes"]]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        errors.append("duplicate scene_id: " + ", ".join(dupes))
    if no_label:
        errors.append("non-footage scenes without on_screen_label: " + ", ".join(no_label))
    warnings = ["narration longer than scene at 145 wpm: " + ", ".join(too_long)] if too_long else []
    tl = timeline(sb)
    return {
        "status": "fail" if errors else ("warn" if warnings else "pass"),
        "timeline": tl,
        "total_seconds": tl[-1]["end_seconds"] if tl else 0,
        "presets": sorted(presets),
        "camera_moves": sorted(moves),
        "asset_ids": sorted(asset_ids),
        "missing_on_screen_label": no_label,
        "narration_too_long": too_long,
        "errors": errors,
        "warnings": warnings,
    }


def write_shot_list(ep: Episode, out: Path) -> Path:
    sb = load(ep)
    rows = {r["scene_id"]: r for r in timeline(sb)}
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["scene_id", "start_timecode", "duration_seconds", "frames", "reconstruction_status", "on_screen_label",
              "environment_preset", "camera_preset", "shot_size", "movement", "lens_mm", "visual_intent", "narration"]
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for s in sb["scenes"]:
            cam = s.get("camera", {})
            w.writerow({"scene_id": s["scene_id"], "start_timecode": rows[s["scene_id"]]["start_timecode"],
                        "duration_seconds": s["duration_seconds"], "frames": rows[s["scene_id"]]["frames"],
                        "reconstruction_status": s["reconstruction_status"], "on_screen_label": s.get("on_screen_label", ""),
                        "environment_preset": s.get("environment_preset", ""), "camera_preset": s.get("camera_preset", ""),
                        "shot_size": cam.get("shot_size", ""), "movement": cam.get("movement", ""),
                        "lens_mm": cam.get("lens_mm", ""), "visual_intent": s["visual_intent"],
                        "narration": s.get("narration", "")})
    return out
