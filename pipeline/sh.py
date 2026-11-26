#!/usr/bin/env python3
"""Stranger Horizons production CLI. One subcommand per pipeline step.

Episodes can be given as a folder path or an ID (EP002). Exit code 0 = pass/warn,
1 = check failed, 2 = tool or usage error. Everything is logged to
<episode>/logs/pipeline.log as well as the console.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shpipe import assets, edit, qc, research, script, storyboard  # noqa: E402
from shpipe.errors import ShError  # noqa: E402
from shpipe.log import get_logger  # noqa: E402
from shpipe.paths import GATES, Episode, create_episode, find_episode  # noqa: E402


def _episode(ref: str) -> Episode:
    return Episode(find_episode(ref))


def _report(result: dict, as_json: bool) -> int:
    if as_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"STATUS: {result['status'].upper()}")
        for e in result.get("errors", []):
            print(f"  ERROR   {e}")
        for w in result.get("warnings", []):
            print(f"  WARNING {w}")
    return 1 if result["status"] == "fail" else 0


def cmd_episode_new(a):
    ep = create_episode(a.episode_id, a.slug, a.title, a.pillar)
    print(f"Created {ep.root}")
    return 0


def cmd_approve(a):
    ep = _episode(a.episode)
    ep.approve(a.gate, by=a.by)
    get_logger("approve", ep.log_file).info("gate %s approved by %s", a.gate, a.by)
    print(f"{ep.episode_id}: {a.gate} approved by {a.by}")
    return 0


def cmd_research(a):
    return _report(research.coverage(_episode(a.episode)), a.json)


def cmd_ledger_md(a):
    ep = _episode(a.episode)
    out = ep.root / "research" / "CLAIM_LEDGER.md"
    out.write_text(research.ledger_markdown(ep) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


def cmd_script(a):
    r = script.check(_episode(a.episode))
    if not a.json and "sections" in r:
        for s in r["sections"]:
            print(f"  {s['heading']:<32} {s['words']:>5} words  markers: {', '.join(s['markers']) or '-'}")
        print(f"  Total {r['word_count']} words ≈ {r['estimated_seconds'] / 60:.1f} min at 145 wpm")
    return _report(r, a.json)


def cmd_storyboard(a):
    ep = _episode(a.episode)
    r = storyboard.check(ep)
    if not a.json and "timeline" in r:
        for row in r["timeline"]:
            print(f"  {row['scene_id']:<8} {row['start_timecode']}  {row['frames']:>5} frames")
        print(f"  Total {r['total_seconds']:.2f} s")
    if a.shot_list and "timeline" in r:
        print(f"Shot list: {storyboard.write_shot_list(ep, ep.root / 'storyboard' / 'shot_list.csv')}")
    return _report(r, a.json)


def cmd_assets(a):
    return _report(assets.check(), a.json)


def cmd_srt(a):
    print(f"Wrote {edit.write_srt(_episode(a.episode))}")
    return 0


def cmd_clip(a):
    ep = _episode(a.episode)
    log = get_logger("edit", ep.log_file)
    scenes = a.scenes or [s["scene_id"] for s in storyboard.load(ep)["scenes"]]
    for sid in scenes:
        out = edit.encode_scene_clip(ep, sid, a.mode, log)
        log.info("clip %s → %s", sid, out)
    return 0


def cmd_concat(a):
    ep = _episode(a.episode)
    log = get_logger("edit", ep.log_file)
    clips = [ep.clip(a.mode, s["scene_id"]) for s in storyboard.load(ep)["scenes"]]
    missing = [str(c) for c in clips if not c.is_file()]
    if missing:
        raise ShError("Missing clips (run `sh.py clip` first): " + ", ".join(missing))
    out = edit.concat(clips, ep.root / "edit" / f"{ep.episode_id}_{a.mode}_picture.mp4", log)
    log.info("concat → %s", out)
    return 0


def cmd_mux(a):
    ep = _episode(a.episode)
    log = get_logger("edit", ep.log_file)
    video = ep.root / "edit" / f"{ep.episode_id}_{a.mode}_picture.mp4"
    audio = Path(a.audio) if a.audio else ep.root / "audio" / "mix" / "final_mix.wav"
    suffix = "" if a.mode == "final" else f"_{a.mode}"
    out = edit.mux(video, audio, ep.root / "final" / f"{ep.episode_id}{suffix}.mp4", log)
    log.info("mux → %s", out)
    return 0


def cmd_qc(a):
    ep = _episode(a.episode)
    report = qc.run(ep, final=a.final)
    get_logger("qc", ep.log_file).info("QC %s: %s", report["mode"], report["status"])
    if a.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(qc.to_markdown(report))
        print(f"Report: {ep.qc_dir / 'qc_report.md'}")
    return 1 if report["status"] == "fail" else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sh.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True, metavar="command")

    def add(name, fn, help_, episode=True, json_flag=True):
        sp = sub.add_parser(name, help=help_)
        if episode:
            sp.add_argument("episode", help="episode folder or ID, e.g. EP002")
        if json_flag:
            sp.add_argument("--json", action="store_true", help="machine-readable output")
        sp.set_defaults(fn=fn)
        return sp

    sp = add("episode-new", cmd_episode_new, "create an episode folder from templates", episode=False, json_flag=False)
    sp.add_argument("episode_id")
    sp.add_argument("slug")
    sp.add_argument("title")
    sp.add_argument("--pillar", default="Deep Unknown",
                    choices=["Hidden Earth", "Deep Unknown", "Strange Signals", "Forbidden Theories", "Prototype"])
    sp = add("approve", cmd_approve, "record an approval gate in episode.json", json_flag=False)
    sp.add_argument("gate", choices=GATES)
    sp.add_argument("--by", required=True, help="who approved")
    add("research", cmd_research, "check source dossier and claim ledger coverage")
    add("ledger-md", cmd_ledger_md, "write research/CLAIM_LEDGER.md from claim_ledger.json")
    add("script", cmd_script, "check claim markers, story beats and timing")
    sp = add("storyboard", cmd_storyboard, "validate storyboard, show timeline and requirements")
    sp.add_argument("--shot-list", action="store_true", help="also write storyboard/shot_list.csv")
    add("assets", cmd_assets, "check the asset register against assets/", episode=False)
    add("srt", cmd_srt, "write subtitles from storyboard narration", json_flag=False)
    for name, fn, help_ in (("clip", cmd_clip, "encode rendered frames to one clip per scene"),
                            ("concat", cmd_concat, "join scene clips without re-encoding"),
                            ("mux", cmd_mux, "add the final audio mix to the joined picture")):
        sp = add(name, fn, help_, json_flag=False)
        sp.add_argument("--mode", choices=["preview", "final"], default="preview")
        if name == "clip":
            sp.add_argument("--scenes", nargs="*", help="scene IDs (default: all)")
        if name == "mux":
            sp.add_argument("--audio", help="audio file (default: audio/mix/final_mix.wav)")
    sp = add("qc", cmd_qc, "run every check and write qc/qc_report.{json,md}")
    sp.add_argument("--final", action="store_true", help="final-delivery QC: every approval gate required")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except (ShError, FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
