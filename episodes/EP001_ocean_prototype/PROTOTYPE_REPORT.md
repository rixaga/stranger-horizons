# EP001 Ocean Prototype — Stage 5 Report

**Status:** v2 rendered and encoded on the owner's Mac on 2026-11-26. **Awaiting owner approval** (Stage 6 evaluation follows).
**What it is:** a 10-second illustrative deep-ocean establishing shot testing the channel's visual direction and the Blender pipeline. It is not a published episode and depicts no real location.

---

## 1. Pre-render checks (measured on the Mac by `run_ep001.py`)

| Check | Result |
|---|---|
| Blender | 5.3.0 (`/Applications/Blender.app`), bundled Python 3.13.13 |
| System Python | 3.9.6 (`/usr/bin/python3`) |
| FFmpeg | 9.1 at `/opt/homebrew/bin/ffmpeg` |
| GPU | Metal: Apple M4, 10-core GPU |
| Memory | 16 GB |
| Free disk | 253.6 GB |
| Engines offered | `BLENDER_EEVEE`, `CYCLES` |

**Render settings decision:** a 3-frame EEVEE timing test at 1920×1080 measured 2.1 s/frame (first frame 7.4 s with shader compilation), estimating 10.8 min for 300 frames, well within the 60-minute budget. So the preview was rendered at **1920×1080** (new `preview_hd` profile) rather than falling back to 1280×720.

## 2. Scene design

| Element | Implementation |
|---|---|
| Environment | Procedural seabed 260 × 280 m, 4 displacement layers (40 m swells, 10 m undulation, 4 m Voronoi rock texture, 1.5 m fine), sediment material; 143 basalt boulders (6 procedural variants, seeded scatter, 3 placed "hero" rocks near the camera path) |
| Subject | **Basalt pinnacle**, a geological formation 38 m tall and about 70–88 m from camera, leaning, with faceted surface. Supported by a low ridge and a distant seamount silhouette for scale. Labelled *Illustrative reconstruction*; no creature is implied |
| Water | `deep_ocean` preset + per-shot overrides: scatter 0.008/m, absorption 0.020/m (blue-green), anisotropy 0.78, slow drifting density noise |
| Light | Faint downwelling daylight (sun, blue-green) broken into **volumetric shafts** by a drifting perforated gobo high in the water; surface lighting reduced (diffuse 0.3) so shafts read in the water and not as pools on the floor. Two vehicle lamps (500 W spots) on the camera rig for the near field |
| Particles | 9,000 marine-snow grains slowly sinking and drifting around the camera path |
| Camera | `glide_reveal`: 24 mm, forward glide of about 18 m with a 3.4 m rise, eased, 1.5 s final hold; DoF f/4 focused on the subject; clip start 0.6 m |
| Environmental motion | Particle drift, gobo drift (shimmering shafts), drifting water-density noise. No other motion |
| Depth context | Lower twilight zone (~150 m). Shafts are only plausible above ~200 m (Lighting Guide) |

**Reusable by design:** the terrain, formations, boulders and gobo come from `blender/scripts/sh_environment_kit.py` driven by `scripts/ep001_set.json`. The look comes from the `deep_ocean` preset plus storyboard overrides, the camera from `config/camera_presets.json`, and the build and validation from `sh_build_shot.py` / `sh_validate_scene.py`. A new location is a new JSON file, not new code.

## 3. Render results

| | v1 | v2 (current) |
|---|---|---|
| Engine / resolution | EEVEE, 1920×1080, 32 samples, AgX Medium High Contrast, exposure +0.6 | same |
| Frames | 300/300 | 300/300 |
| Render time | 725 s (12.1 min), 2.42 s/frame | **698 s (11.6 min), 2.33 s/frame** |
| Whole pipeline (build → MP4) | ~13 min | 11 min 50 s (10:06:13 → 10:18:03) |
| MP4 | `final/EP001_preview_v1.mp4` (2.8 MB) | **`final/EP001_preview_v2.mp4` (2.6 MB)**: H.264, 1920×1080, 30 fps, 10.00 s, yuv420p |
| Verdict | Shafts strong, but the subject was washed out by in-scattering and barely visible | Subject emerges gradually and reads as a silhouette by mid-shot; near-lens artefact gone |

Render speed drifted from 2.1 to about 2.4 s/frame during long runs, consistent with thermal throttling on the fanless MacBook Air.

## 4. Problems encountered

| # | Problem | Status |
|---|---|---|
| P1 | Cloud look-check stills (Cycles CPU) did not predict EEVEE: EEVEE in-scattering was much stronger, so v1's subject was lost in haze | **Fixed in v2** (scatter density halved, sun volume factor 2.5 → 1.6). Lesson: judge looks with EEVEE on the Mac |
| P2 | A marine-snow grain passing within centimetres of the lens rendered as a sharp white square | **Fixed in v2** (camera clip start 0.6 m, dimmer particles) |
| P3 | In the MP4 made by FFmpeg 9.1, `color_transfer` is tagged `iec61966-2-1` (sRGB) instead of `bt709`. Primaries and matrix are BT.709. The `setparams` fix works with FFmpeg 6.1 in the cloud but not with 9.1 | **Open.** Small practical effect (the curves are close and YouTube re-encodes), but QC now reports it. Needs a diagnosis run on the Mac |
| P4 | Typing into Blender's Python console through computer use dropped characters twice | Worked around by retyping in short pieces. Future: a one-click launcher (Blender menu button or startup script) |
| P5 | EEVEE cannot render in the headless cloud workspace | By design, rendering happens on the Mac |
| P6 | The seabed's finer geological detail is lost in the darkest areas; subject contrast is moderate | **For Stage 6** evaluation |
| P7 | Generated `.blend` files and renders are git-ignored (large, reproducible). They exist on the Mac only | Regenerate with `run_ep001.py`; back up `blender/` and `final/` |

## 5. Files

**Created or changed in the repository**

- `blender/scripts/sh_environment_kit.py` (new): reusable terrain, formations, boulders, gobo
- `episodes/EP001_ocean_prototype/scripts/ep001_set.json`, `run_ep001.py`, `launch_ep001.py`
- `episodes/EP001_ocean_prototype/storyboard/storyboard.json`, `assets/README.md`, this report
- `config/camera_presets.json` (+ `glide_reveal`), `config/render_config.json` (+ `preview_hd`)
- `blender/scripts/sh_build_shot.py` (preset overrides, profile override, storyboard DoF), `sh_presets.py` (custom volume range for Blender 5, density drift, light diffuse/specular factors), `sh_validate_scene.py` (profile override)
- `pipeline/shpipe/ffmpeg.py`, `pipeline/assemble_video.py` (frame colour relabel), `pipeline/shpipe/qc.py` (per-scene expected size, all three colour tags)
- `schemas/storyboard.schema.json`, `schemas/environment_preset.schema.json`, `tests/test_environment_kit.py`, `.gitignore`

**Generated on the Mac** (in `episodes/EP001_ocean_prototype/`, not in git)

- `blender/EP001_set.blend`, `blender/shots/S01.blend`: editable scenes
- `renders/preview/S01/frame_0001–0300.png` + `render_log.json`, `renders/preview/_timing/`
- `final/EP001_preview_v2.mp4`, `final/EP001_contact_sheet_v2.jpg`, `final/EP001_render_report_v2.json` (+ `_v1` versions)
- `logs/run_ep001.log`, `logs/blender_background.log`

## 6. How to re-run

From Blender's Python console (Scripting workspace):
```python
import runpy; runpy.run_path('<repo>/episodes/EP001_ocean_prototype/scripts/launch_ep001.py')
```
Optional `scripts/launch_args.json`, e.g. `["--tag", "v3", "--resolution", "auto"]`. Or from Terminal:
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
  --python episodes/EP001_ocean_prototype/scripts/run_ep001.py -- --tag v3
```
