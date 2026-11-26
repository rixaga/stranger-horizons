from __future__ import annotations

import json
from pathlib import Path

from conftest import PIPELINE, REPO, run

SCRIPT = str(PIPELINE / "validate_episode.py")

GOOD_STORYBOARD = {
    "episode_id": "EP900",
    "title": "Test",
    "fps": 30,
    "scenes": [{
        "scene_id": "S01",
        "duration_seconds": 10,
        "visual_intent": "Slow descent",
        "reconstruction_status": "illustrative_reconstruction",
        "camera": {"movement": "push_in"},
    }],
}


def make_episode(root: Path, folders: tuple[str, ...]) -> Path:
    for f in folders:
        (root / f).mkdir(parents=True, exist_ok=True)
    return root


def test_prototype_profile_needs_only_blender_and_renders(tmp_path: Path):
    ep = make_episode(tmp_path / "EP900", ("blender", "renders"))
    result = run(SCRIPT, str(ep), "--profile", "prototype")
    assert result.returncode == 0, result.stdout


def test_episode_profile_still_requires_full_structure(tmp_path: Path):
    ep = make_episode(tmp_path / "EP900", ("blender", "renders"))
    result = run(SCRIPT, str(ep))
    assert result.returncode == 1
    assert "Missing folder: research" in result.stdout


def test_storyboard_is_checked_against_schema(tmp_path: Path):
    ep = make_episode(tmp_path / "EP900", ("blender", "renders", "storyboard"))
    bad = json.loads(json.dumps(GOOD_STORYBOARD))
    del bad["scenes"][0]["scene_id"]
    (ep / "storyboard" / "storyboard.json").write_text(json.dumps(bad))
    result = run(SCRIPT, str(ep), "--profile", "prototype")
    assert result.returncode == 1
    assert "scene_id" in result.stdout


def test_valid_storyboard_passes(tmp_path: Path):
    ep = make_episode(tmp_path / "EP900", ("blender", "renders", "storyboard"))
    (ep / "storyboard" / "storyboard.json").write_text(json.dumps(GOOD_STORYBOARD))
    result = run(SCRIPT, str(ep), "--profile", "prototype")
    assert result.returncode == 0, result.stdout


def test_storyboard_source_ids_must_exist_in_dossier(tmp_path: Path):
    ep = make_episode(tmp_path / "EP900", ("blender", "renders", "storyboard", "research"))
    sb = json.loads(json.dumps(GOOD_STORYBOARD))
    sb["scenes"][0]["source_ids"] = ["SRC-999"]
    (ep / "storyboard" / "storyboard.json").write_text(json.dumps(sb))
    (ep / "research" / "source_dossier.json").write_text(json.dumps({"episode_id": "EP900", "sources": []}))
    result = run(SCRIPT, str(ep), "--profile", "prototype")
    assert result.returncode == 1
    assert "SRC-999" in result.stdout


def test_ep001_prototype_folder_passes():
    result = run(SCRIPT, str(REPO / "episodes" / "EP000_ocean_prototype"), "--profile", "prototype")
    assert result.returncode == 0, result.stdout
