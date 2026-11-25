"""Runs only where Blender's Python module (bpy) is importable, e.g. `pip install bpy`
in a matching Python, or `blender --background --python-expr` with pytest available."""
from __future__ import annotations

import pytest

bpy = pytest.importorskip("bpy")


def test_cycles_is_listed_as_available_engine():
    from sh_render import available_engines
    engines = available_engines()
    assert "CYCLES" in engines
    assert any(e.startswith("BLENDER_EEVEE") for e in engines)


@pytest.mark.parametrize("profile", ["preview", "delivery", "master", "shorts"])
def test_every_profile_applies(profile):
    from sh_render import apply_profile, load_profile
    applied = apply_profile(bpy.context.scene, load_profile(profile), "//renders/frame_")
    assert applied["resolution"] == [load_profile(profile)["resolution_x"], load_profile(profile)["resolution_y"]]
    assert applied["view_transform"] == "AgX"
