from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

import pytest

from conftest import REPO

FIXTURE = REPO / "tests" / "fixtures" / "EP900_fixture"


@pytest.fixture
def ep(tmp_path: Path) -> Path:
    dst = tmp_path / "EP900_fixture"
    shutil.copytree(FIXTURE, dst)
    return dst


def test_config_loads_render_profiles_and_validates():
    from shpipe import config
    assert config.render_config()["fps"] == 30
    assert config.validate({"episode_id": "E", "title": "T", "fps": 30, "scenes": []}, "storyboard")
    assert config.validate(json.loads((FIXTURE / "storyboard/storyboard.json").read_text()), "storyboard") == []


def test_episode_paths_follow_layout(ep: Path):
    from shpipe.paths import Episode
    e = Episode(ep)
    assert e.storyboard == ep / "storyboard" / "storyboard.json"
    assert e.render_dir("preview", "S01") == ep / "renders" / "preview" / "S01"
    assert e.clip("final", "S02") == ep / "edit" / "clips" / "final" / "S02.mp4"
    assert e.meta["episode_id"] == "EP900"


def test_find_episode_by_id(tmp_path: Path):
    from shpipe.paths import find_episode
    (tmp_path / "EP123_some_topic").mkdir()
    assert find_episode("EP123", root=tmp_path).name == "EP123_some_topic"
    with pytest.raises(FileNotFoundError):
        find_episode("EP999", root=tmp_path)


def test_create_episode_makes_valid_layout(tmp_path: Path):
    from shpipe import config
    from shpipe.paths import create_episode
    e = create_episode("EP777", "deep_trench", "The Deep Trench", "Deep Unknown", root=tmp_path)
    assert e.root.name == "EP777_deep_trench"
    for sub in ("research", "script", "storyboard", "blender/shots", "renders", "audio", "edit", "thumbnail", "final", "logs", "qc"):
        assert (e.root / sub).is_dir(), sub
    assert config.validate(e.meta, "episode") == []
    with pytest.raises(FileExistsError):
        create_episode("EP777", "deep_trench", "x", "Deep Unknown", root=tmp_path)


def test_approve_records_gate(ep: Path):
    from shpipe.paths import Episode
    e = Episode(ep)
    e.approve("script", by="owner", date="2026-11-27")
    assert Episode(ep).meta["approvals"]["script"] == {"approved_by": "owner", "date": "2026-11-27"}
    with pytest.raises(ValueError):
        e.approve("lunch", by="owner")


def test_logger_writes_to_episode_log(ep: Path):
    from shpipe.log import get_logger
    log = get_logger("test", ep / "logs" / "pipeline.log")
    log.info("hello")
    for h in log.handlers:
        h.flush()
    assert "hello" in (ep / "logs" / "pipeline.log").read_text()
    # calling again does not duplicate handlers
    assert len(get_logger("test", ep / "logs" / "pipeline.log").handlers) == len(log.handlers)


def test_missing_ffmpeg_raises_clear_error(monkeypatch):
    from shpipe import ffmpeg
    from shpipe.errors import ToolMissing
    monkeypatch.setattr(shutil, "which", lambda name: None)
    monkeypatch.setattr(ffmpeg, "EXTRA_DIRS", ())
    with pytest.raises(ToolMissing, match="brew install ffmpeg"):
        ffmpeg.find("ffmpeg")


def test_dossier_prefers_sources_json_when_present(ep: Path):
    from shpipe.paths import Episode
    e = Episode(ep)
    assert e.dossier.name == "source_dossier.json"            # legacy name still works
    (ep / "research" / "sources.json").write_text((ep / "research" / "source_dossier.json").read_text())
    assert e.dossier.name == "sources.json"


def test_claim_ledger_markdown_lists_every_claim_with_sources(ep: Path):
    from shpipe import research
    from shpipe.paths import Episode
    md = research.ledger_markdown(Episode(ep))
    ledger = json.loads((ep / "research" / "claim_ledger.json").read_text())
    for c in ledger["claims"]:
        assert c["claim_id"] in md
        for sid in c["source_ids"]:
            assert sid in md
    assert md.startswith("# Claim Ledger")
