from __future__ import annotations

import json

import pytest

from conftest import REPO


def test_resolve_eevee_prefers_available_identifier():
    from sh_render import resolve_engine
    assert resolve_engine("EEVEE", ["BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH", "CYCLES"]) == "BLENDER_EEVEE_NEXT"
    assert resolve_engine("EEVEE", ["BLENDER_EEVEE", "BLENDER_WORKBENCH", "CYCLES"]) == "BLENDER_EEVEE"


def test_resolve_cycles_and_unknown():
    from sh_render import resolve_engine
    assert resolve_engine("CYCLES", ["BLENDER_EEVEE", "CYCLES"]) == "CYCLES"
    with pytest.raises(ValueError):
        resolve_engine("EEVEE", ["CYCLES"])


def test_legacy_identifiers_in_config_are_accepted():
    from sh_render import resolve_engine
    assert resolve_engine("BLENDER_EEVEE_NEXT", ["BLENDER_EEVEE", "CYCLES"]) == "BLENDER_EEVEE"
    assert resolve_engine("BLENDER_CYCLES", ["BLENDER_EEVEE", "CYCLES"]) == "CYCLES"


def test_profile_loader_merges_fps_and_frames():
    from sh_render import load_profile
    cfg = json.loads((REPO / "config" / "render_config.json").read_text())
    prof = load_profile("preview", cfg)
    assert prof["fps"] == cfg["fps"]
    assert prof["resolution_x"] == 1280
    assert prof["engine"] in ("EEVEE", "BLENDER_EEVEE_NEXT")
    with pytest.raises(KeyError):
        load_profile("nope", cfg)


def test_bpy_free_import():
    """sh_render must import without Blender so it stays unit-testable."""
    import importlib
    import sh_render
    importlib.reload(sh_render)
