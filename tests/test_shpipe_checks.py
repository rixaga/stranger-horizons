from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from conftest import REPO
from test_shpipe_core import FIXTURE, ep  # noqa: F401  (fixture re-export)


def test_research_coverage_flags_problems(ep):
    from shpipe import research
    from shpipe.paths import Episode
    r = research.coverage(Episode(ep))
    assert r["counts"]["claims"] == 4 and r["counts"]["sources"] == 3
    assert r["labels"]["speculation"] == 1
    assert r["claims_without_sources"] == ["C04"]            # speculation C03 is allowed
    assert r["claims_only_weak_sources"] == ["C02"]
    assert r["unused_sources"] == ["SRC-003"]
    assert r["status"] == "fail"


def test_script_check_reports_markers_beats_and_timing(ep):
    from shpipe import script
    from shpipe.paths import Episode
    r = script.check(Episode(ep))
    assert r["unknown_claim_markers"] == ["C99"]
    assert "Closing question" in r["missing_beats"]
    assert r["reconstruction_markers"] == 1
    assert r["word_count"] > 10
    assert r["estimated_seconds"] == pytest.approx(r["word_count"] / 145 * 60, rel=1e-6)
    assert "Reviewer checklist" not in " ".join(s["heading"] for s in r["sections"])
    assert r["status"] == "fail"


def test_storyboard_timeline_and_requirements(ep):
    from shpipe import storyboard
    from shpipe.paths import Episode
    r = storyboard.check(Episode(ep))
    tl = r["timeline"]
    assert [s["frames"] for s in tl] == [120, 60]
    assert tl[1]["start_frame_edit"] == 121 and tl[1]["start_timecode"] == "00:00:04:00"
    assert r["total_seconds"] == 6
    assert r["presets"] == ["deep_ocean"]
    assert r["missing_on_screen_label"] == ["S02"]
    assert r["narration_too_long"] == ["S02"]
    assert r["status"] == "fail"


def test_storyboard_unknown_preset_is_an_error(ep):
    from shpipe import storyboard
    from shpipe.paths import Episode
    sb = json.loads((ep / "storyboard/storyboard.json").read_text())
    sb["scenes"][0]["environment_preset"] = "atlantis"
    (ep / "storyboard/storyboard.json").write_text(json.dumps(sb))
    r = storyboard.check(Episode(ep))
    assert any("atlantis" in e for e in r["errors"])


def test_shot_list_csv(ep, tmp_path):
    from shpipe import storyboard
    from shpipe.paths import Episode
    out = storyboard.write_shot_list(Episode(ep), tmp_path / "shots.csv")
    lines = out.read_text().splitlines()
    assert lines[0].startswith("scene_id,start_timecode")
    assert lines[1].startswith("S01,00:00:00:00")


def test_assets_register_checks(tmp_path):
    from shpipe import assets
    root = tmp_path / "assets"
    (root / "models").mkdir(parents=True)
    (root / "models" / "rock.glb").write_bytes(b"x")
    (root / "models" / "stray.glb").write_bytes(b"x")
    (root / "models" / ".gitkeep").write_bytes(b"")
    reg = {"assets": [
        {"id": "AST-001", "name": "Rock", "kind": "model", "source": "Poly Haven", "license": "CC0", "acquired": "2026-11-20", "local_path": "assets/models/rock.glb"},
        {"id": "AST-002", "name": "Gone", "kind": "model", "source": "x", "license": "CC-BY-4.0", "acquired": "2026-11-20", "local_path": "assets/models/gone.glb", "attribution_required": True},
        {"id": "AST-003", "name": "Voice", "kind": "voice", "source": "tts", "license": "commercial", "acquired": "2026-11-20", "ai_generated": True}]}
    (root / "asset_register.json").write_text(json.dumps(reg))
    r = assets.check(root / "asset_register.json", repo_root=tmp_path)
    assert r["missing_files"] == ["AST-002"]
    assert r["unregistered_files"] == ["assets/models/stray.glb"]
    assert r["attribution_missing"] == ["AST-002"]
    assert r["ai_generated"] == ["AST-003"]
    assert r["status"] == "fail"


def test_srt_from_storyboard(ep, tmp_path):
    from shpipe import edit
    from shpipe.paths import Episode
    out = edit.write_srt(Episode(ep), tmp_path / "subs.srt")
    text = out.read_text()
    assert text.startswith("1\n00:00:00,000 --> ")
    cue_text = " ".join(l for b in text.strip().split("\n\n") for l in b.splitlines()[2:])
    assert "Far below the surface, the light gives out." in cue_text
    for block in text.strip().split("\n\n"):
        lines = block.splitlines()
        assert len(lines[2:]) <= 2 and all(len(l) <= 42 for l in lines[2:])
    last_end = text.strip().split("\n\n")[-1].splitlines()[1].split(" --> ")[1]
    assert last_end == "00:00:06,000"


def test_qc_report_aggregates_and_gates(ep):
    from shpipe import qc
    from shpipe.paths import Episode
    report = qc.run(Episode(ep), final=True)
    names = {c["name"]: c["status"] for c in report["checks"]}
    assert names["research"] == "fail" and names["script"] == "fail" and names["storyboard"] == "fail"
    assert names["approvals"] == "fail"          # final mode needs every gate
    assert report["status"] == "fail"
    assert (ep / "qc" / "qc_report.json").is_file() and (ep / "qc" / "qc_report.md").is_file()
