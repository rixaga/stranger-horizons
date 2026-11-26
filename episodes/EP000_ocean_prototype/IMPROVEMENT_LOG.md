# EP001 Ocean Prototype — Improvement Log

All renders: EEVEE, 1920×1080, 30 fps, 300 frames, 32 samples, AgX Medium High Contrast, on the owner's Mac (Apple M4, Blender 5.3.0, FFmpeg 9.1).
Weakness IDs (W1–W11) refer to `PROTOTYPE_EVALUATION.md`.

## Versions

| Version | Date | What changed | Render | MP4 |
|---|---|---|---|---|
| v1 | 2026-11-26 | Stage 5 first render | 725 s (2.42 s/frame) | 2.8 MB |
| v2 | 2026-11-26 | Less in-scatter, clip start 0.6 m (Stage 5 fixes) | 698 s (2.33 s/frame) | 2.6 MB |
| v3cal | 2026-11-26 | 3 EEVEE calibration stills (frames 1/150/300), three passes | ~10 s each | — |
| v3a | 2026-11-26 | All Stage 6 changes **except** the W11 material fix (bug not yet found) | 12.7 min | 9.8 MB |
| v3 | 2026-11-26 | All Stage 6 changes including the W11 fix | 842 s (2.81 s/frame), 14.0 min | 9.1 MB |
| v4cal | 2026-11-26 | ROV scale cue: 3 calibration passes (facing subject → in sun shaft → side-on) | ~10 s each | — |
| **v4** | 2026-11-26 | v3 + ROV scale cue + exposure +2.3 (owner request) | **767 s (2.56 s/frame)**, 12.8 min | **10.3 MB** |

v3 renders slower than v2 because the terrain is 2.4× denser (W3) and there are 2.4× more particles (W5); the Mac also throttles thermally over long runs (2.2 → 2.8 s/frame).
The MP4 is larger because of CRF 16 and the encode grain; that is intended (W4) and still small for a 10 s master preview.

## Changes (v2 → v3)

| W | File | Change |
|---|---|---|
| W1 | `storyboard/storyboard.json` | Exposure +0.6 → +1.8; world colour (0.002, 0.008, 0.012) |
| W1 | — (process) | Calibrate with EEVEE stills on the Mac, not cloud Cycles stills |
| W2 | `scripts/ep001_set.json` | Gobo `open_at` [[16,25,9],[10,42,8]]: a shaft behind the pinnacle |
| W2 | `storyboard/storyboard.json` | Water scatter density 0.008 → 0.0065 |
| W3 | `scripts/ep001_set.json` | Terrain layers CLOUDS 40/5, CLOUDS 10/2.2, DISTORTED_NOISE 7/1.1 (distortion 1.5), STUCCI 0.8/0.18 (turbulence 5); resolution 220 → 340 |
| W3 | `blender/scripts/sh_environment_kit.py` | `_displace(..., extra=)` for texture-specific settings; slope-aware material (`slope_weight`, `slope_from`); new sediment/basalt colours |
| W4 | `config/render_config.json` | `preview_hd` PNG colour depth 8 → 16 |
| W4 | `pipeline/shpipe/ffmpeg.py`, `scripts/run_ep001.py` | `encode_sequence(grain=2.0, dark_scene=True)`: temporal grain, x264 `aq-mode=3`, deblock −1; CRF 16 |
| W5 | `storyboard/storyboard.json` | Particles 22,000 in a 16×24×8 m box around the camera path, 4 mm, size_random 0.8 |
| W6 | `scripts/ep001_set.json` | Seamount roughness 5, strength 1.2, facet 10 m |
| W7 | `pipeline/shpipe/ffmpeg.py` | `retag_bt709()`: stream-copy remux with `h264_metadata` BSF + `write_colr` |
| W10 | `storyboard/storyboard.json` | Lamps size 0.5, blend 0.85; sun angle 2° → 5°, diffuse 0.3 → 0.2 |
| W11 | `blender/scripts/sh_environment_kit.py` | Default materials no longer overwrite materials defined in the config; gobo threshold safe at `open_fraction` 0 |

## Changes (v3 → v4, owner request: a visible scale cue, not too dark)

| File | Change |
|---|---|
| `blender/scripts/sh_environment_kit.py` | New `make_vehicle()`: a generic work-class ROV built at real size (frame, buoyancy block, thrusters, lamp heads, cyan nav light), two spot lamps with volumetric beams, linear travel over the shot; `vehicles` section in the set config |
| `scripts/ep001_set.json` | ROV 2.8 m, 5 m above seabed at (−5, −42), travelling 4 m in +X (side-on to camera), lamps 1,500 W, 50° cone, 12° down, volume factor 3; extra gobo opening (−5.6, −23.5, r 4.5) so a sun shaft lights the ROV along its path |
| `storyboard/storyboard.json` | Exposure +1.8 → +2.3; visual intent and lighting notes updated |
| `tests/test_environment_kit.py` | `test_vehicle_scale_cue_is_built_lit_aimed_and_moving` (scale, ground height, heading, lamps, travel, collection) and `test_vehicle_rebuild_is_rerun_safe` |

ROV on screen (camera projection in Blender): 94 px wide at frame 1 → 160 px at frame 300, left-centre, below and left of the pinnacle.

## Measurements (delivery MP4, same scripts for every version)

Luma from the decoded MP4 as full-range grey (0–255). Subject/water = mean of a box over the pinnacle ÷ a box of open water (a rough proxy; the box includes some water around the rock).

| Metric | v2 | v3a | v3 | **v4** | Target / note |
|---|---|---|---|---|---|
| YAVG (limited range), min–max | 24.2–26.5 | 33.4–36.8 | 33.2–36.5 | **39.8–44.6** | Brighter each step, still a dark scene |
| Pixels below 20, frame 1 / 150 / 300 | 88% / 81% / 85% | 45% / 38% / 47% | 46% / 39% / 47% | **22% / 14% / 20%** | Shadows no longer crushed (L7) |
| Seabed mean (bottom 20%), f1 / f150 / f300 | 4.6 / 8.8 / 6.5 | 16.6 / 17.2 / 14.0 | 15.7 / 16.4 / 13.3 | **21.8 / 27.1 / 29.7** | ~4× v2; texture visible |
| Distinct levels in water (top 30%), f1 / f150 / f300 | 57 / 42 / 42 | 150 / 65 / 50 | 148 / 62 / 49 | **147 / 75 / 61** | More tonal steps = less banding |
| Subject / water ratio, f1 / f150 / f300 | 1.36 / 0.82 / 1.35 | 1.07 / 0.85 / 1.09 | 1.06 / 0.84 / 1.08 | **1.06 / 0.85 / 1.07** | The box metric barely moves; visually the pinnacle is a clearly darker silhouette from v3 on. Needs a better metric |
| Frame-to-frame mean-luma step, avg / max | 0.029 / 0.325 | — | 0.038 / 0.429 | **0.050 / 0.495** | No flicker (grain and the moving ROV lamps add small changes) |
| Colour tags (space / primaries / transfer) on the Mac | bt709 / bt709 / **iec61966-2-1** | bt709 ×3 | bt709 ×3 | **bt709 ×3** | Fixed |

Calibration stills (16-bit PNG, before encode), share of pixels below luma 5: v2 ≈ 28–37% → v3cal 0–3%.

**Caveat on motion numbers:** v3's per-second pixel change ([0.57, 0.74, 0.61, 0.49, 0.46, 0.44, 0.39, 0.32, 0.23, 0.22]) is higher than v2's because the encode grain changes every frame. It still shows the same ease-in and calm hold; the camera move was not changed.

## Tests

- New: `test_retag_bt709_fixes_an_srgb_transfer_tag`, `test_encode_with_grain_and_dark_scene_tuning`, `test_gobo_open_at_forces_a_clear_opening`, `test_terrain_layers_pass_texture_specific_settings`, `test_sediment_material_is_slope_aware`.
- Before the fixes, three failed for real reasons: the retag left the H.264 VUI as sRGB, the gobo crashed at `open_fraction` 0, and the slope material was wiped (W11).
- Final: system Python **81 passed, 3 skipped**; Blender bpy **104 passed** (cloud workspace), including the two ROV tests.

## Lessons

1. Cloud Cycles stills do not predict EEVEE volumes. Calibrate on the Mac with 3 stills (~1 min) before every full render.
2. Write a test for each config feature that checks the built object, not only that the build runs. W11 hid for two versions because nothing checked the material.
3. `device_commit_files` once delivered a stale copy to the Mac. Verify checksums on the Mac before launching a render.
4. A scale cue only works if the audience can read it: the first ROV pass was in frame but invisible (back view, beams pointing away under forward-scattering water). Turning it side-on fixed that without more light.
