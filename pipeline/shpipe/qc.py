"""Quality Control: run every available check for an episode and write a report.

Checks that cannot run yet (no renders, no audio, no final video) are reported as
'skip', never as 'pass'. Final mode also requires every approval gate.
"""
from __future__ import annotations

import datetime as _dt
import importlib
import struct
import sys
from pathlib import Path

from . import assets, config, ffmpeg, research, script, storyboard
from .errors import ShError
from .paths import GATES, Episode

sys.path.insert(0, str(config.REPO / "pipeline"))
STATUS_ORDER = {"pass": 0, "skip": 0, "warn": 1, "fail": 2}


def _png_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def check_structure(ep: Episode) -> dict:
    validate_episode = importlib.import_module("validate_episode")
    profile = "prototype" if ep.meta.get("status") == "prototype" else "episode"
    errors, warnings = validate_episode.validate_episode(ep.root, profile)
    return {"status": "fail" if errors else "pass", "profile": profile, "errors": errors, "warnings": warnings}


def check_renders(ep: Episode, mode: str) -> dict:
    if not (ep.root / "renders" / mode).is_dir():
        return {"status": "skip", "reason": f"no renders/{mode} yet"}
    sb = storyboard.load(ep)
    profile = config.render_config()["preview" if mode == "preview" else "delivery"]
    expected_size = (profile["resolution_x"], profile["resolution_y"])
    scenes, errors, warnings = {}, [], []
    for row in storyboard.timeline(sb):
        folder = ep.render_dir(mode, row["scene_id"])
        frames = sorted(folder.glob("frame_*.png")) if folder.is_dir() else []
        sizes = {_png_size(f) for f in frames[:1] + frames[-1:]}
        scene_size = expected_size
        log = folder / "render_log.json"
        if log.is_file():  # a scene may use a profile override (e.g. preview_hd)
            res = config.load_json(log).get("resolution")
            if res:
                scene_size = tuple(res)
        ok = len(frames) == row["frames"]
        scenes[row["scene_id"]] = {"expected": row["frames"], "found": len(frames), "ok": ok,
                                   "size": sorted(s for s in sizes if s)}
        if not ok:
            errors.append(f"{row['scene_id']}: {len(frames)}/{row['frames']} frames")
        if frames and sizes != {scene_size}:
            warnings.append(f"{row['scene_id']}: frame size {sorted(sizes)} differs from expected {scene_size}")
        if frames and not (folder / "render_log.json").is_file():
            warnings.append(f"{row['scene_id']}: render_log.json missing")
    return {"status": "fail" if errors else ("warn" if warnings else "pass"), "scenes": scenes,
            "errors": errors, "warnings": warnings}


def check_audio(ep: Episode) -> dict:
    mix = ep.root / "audio" / "mix" / "final_mix.wav"
    if not mix.is_file():
        return {"status": "skip", "reason": "audio/mix/final_mix.wav not present yet"}
    try:
        measure = importlib.import_module("measure_loudness")
        m, t = measure.measure(mix), measure.load_targets()
    except (RuntimeError, ShError) as exc:
        return {"status": "fail", "errors": [str(exc)]}
    errors = []
    if abs(m["integrated_lufs"] - t["integrated_lufs_target"]) > t["integrated_lufs_tolerance"]:
        errors.append(f"integrated {m['integrated_lufs']:.1f} LUFS, target {t['integrated_lufs_target']}")
    if m["true_peak_dbtp"] > t["true_peak_max_dbtp"]:
        errors.append(f"true peak {m['true_peak_dbtp']:.1f} dBTP above {t['true_peak_max_dbtp']}")
    return {"status": "fail" if errors else "pass", **m, "errors": errors}


def check_final_video(ep: Episode) -> dict:
    video = ep.root / "final" / f"{ep.episode_id}.mp4"
    if not video.is_file():
        return {"status": "skip", "reason": f"final/{video.name} not present yet"}
    try:
        info = ffmpeg.probe(video)
    except ShError as exc:
        return {"status": "fail", "errors": [str(exc)]}
    errors = []
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if v is None:
        errors.append("no video stream")
    else:
        tags = {k: v.get(k) for k in ("color_space", "color_primaries", "color_transfer")}
        if set(tags.values()) != {"bt709"}:
            errors.append(f"video not fully tagged BT.709 ({tags})")
        if (v.get("width"), v.get("height")) not in {(1920, 1080), (3840, 2160)}:
            errors.append(f"unexpected delivery size {v.get('width')}x{v.get('height')}")
    if a is None:
        errors.append("no audio stream")
    expected = storyboard.timeline(storyboard.load(ep))[-1]["end_seconds"]
    duration = float(info["format"]["duration"])
    if abs(duration - expected) > 0.5:
        errors.append(f"duration {duration:.2f}s differs from storyboard {expected:.2f}s")
    return {"status": "fail" if errors else "pass", "duration": duration, "errors": errors}


def check_approvals(ep: Episode, final: bool) -> dict:
    approvals = ep.meta.get("approvals", {})
    missing = [g for g in GATES if not approvals.get(g)]
    status = ("fail" if final else "warn") if missing else "pass"
    return {"status": status, "missing": missing,
            "errors" if final else "warnings": [f"gates not yet approved: {', '.join(missing)}"] if missing else []}


def run(ep: Episode, final: bool = False) -> dict:
    checks = [("structure", lambda: check_structure(ep)), ("research", lambda: research.coverage(ep)),
              ("script", lambda: script.check(ep)), ("storyboard", lambda: storyboard.check(ep)),
              ("assets", lambda: assets.check()), ("renders_preview", lambda: check_renders(ep, "preview")),
              ("renders_final", lambda: check_renders(ep, "final")), ("audio", lambda: check_audio(ep)),
              ("final_video", lambda: check_final_video(ep)), ("approvals", lambda: check_approvals(ep, final))]
    results = []
    for name, fn in checks:
        try:
            r = fn()
        except Exception as exc:  # a broken check must show up in the report, not abort QC
            r = {"status": "fail", "errors": [f"{exc.__class__.__name__}: {exc}"]}
        summary = {k: v for k, v in r.items() if k not in ("sections", "timeline")}
        results.append({"name": name, **summary})
    overall = max((c["status"] for c in results), key=STATUS_ORDER.get)
    report = {"episode_id": ep.episode_id, "mode": "final" if final else "working",
              "generated": _dt.datetime.now().isoformat(timespec="seconds"), "status": overall, "checks": results}
    config.write_json(ep.qc_dir / "qc_report.json", report)
    (ep.qc_dir / "qc_report.md").write_text(to_markdown(report), encoding="utf-8")
    return report


def to_markdown(report: dict) -> str:
    icon = {"pass": "✅", "warn": "⚠️", "fail": "❌", "skip": "⏭️"}
    lines = [f"# QC report — {report['episode_id']} ({report['mode']})", "",
             f"Generated {report['generated']}. Overall: **{report['status'].upper()}**", "",
             "| Check | Status | Notes |", "|---|---|---|"]
    for c in report["checks"]:
        notes = "; ".join(c.get("errors", []) + c.get("warnings", [])) or c.get("reason", "")
        lines.append(f"| {c['name']} | {icon[c['status']]} {c['status']} | {notes.replace('|', '/')} |")
    return "\n".join(lines) + "\n"
