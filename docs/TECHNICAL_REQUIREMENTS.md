# Technical Requirements — Stranger Horizons

**Stage:** 4. Measured values come from `PROJECT_UNDERSTANDING.md` (render machine, 2026-11-26).

---

## 1. Software

| Component | Required | Measured on owner's Mac | Notes |
|---|---|---|---|
| Blender | **5.x** (tested 5.3.0) | 5.3.0 ✅ | Scripts tolerate 4.2+ API differences, but only 5.3 is tested |
| Python (system) | 3.9+ | `/usr/bin/python3` ✅ | Runs `pipeline/` |
| Python (Blender) | bundled | 3.13.13 ✅ | Runs `blender/scripts/` |
| FFmpeg + ffprobe | 6.x or newer, with libx264 and AAC | 9.1 (Homebrew) ✅ | `brew install ffmpeg` |
| jsonschema | ≥ 4.20 | Not checked in system Python | `pip3 install -r requirements.txt` |
| pytest | ≥ 8.0 | — | Tests only |
| Git | any recent | — | For pulling the repo |

**No other packages.** Nothing in the pipeline needs NumPy, PIL, OpenCV, a web framework or a database. Blender add-ons are not assumed (`CLAUDE.md`).

### Setup on the Mac

```bash
# once
brew install ffmpeg                     # needs Homebrew (https://brew.sh)
cd "<repo folder>"
pip3 install -r requirements.txt

# check everything
python3 pipeline/check_environment.py
python3 -m pytest
```

Inside Blender (Scripting → Python console), to record versions and GPU:
```python
import runpy; runpy.run_path('<repo folder>/blender/scripts/sh_run_checks.py')
```

## 2. Hardware

| Item | Minimum | Owner's machine |
|---|---|---|
| CPU/GPU | Apple Silicon M1+ or a CUDA/OptiX GPU | Apple M4, 10-core GPU (Metal) ✅ |
| RAM | 16 GB | 16 GB ✅ (keep textures ≤ 4K, scenes lean) |
| Free disk | 50 GB per episode in production | 255 GB ✅ |

**Disk budget (estimates):** a 1080p 16-bit PNG frame is roughly 4–8 MB. Twelve minutes at 30 fps is 21,600 frames, roughly 90–170 GB for one full final render set. Plan: render and encode per scene, archive or delete masters after the final cut is approved, and back up `final/` and `blender/`.

**Thermals:** the M4 MacBook Air has no fan. Long Cycles renders throttle. Use EEVEE for previews, render Cycles finals scene by scene, and record times in `render_log.json` to plan.

## 3. Render and encode specifications

From `config/render_config.json` (single source of truth):

| Profile | Use | Output |
|---|---|---|
| `preview` | Approvals, timing | 1280×720, EEVEE, 16 samples, 8-bit PNG |
| `delivery` | Final long-form | 1920×1080, Cycles (Metal), 256 samples + denoise, 16-bit PNG |
| `master` | When time allows | 3840×2160, Cycles |
| `shorts` | Vertical | 1080×1920, EEVEE |

| Encode | Setting |
|---|---|
| Video | H.264 (libx264), yuv420p, CRF 18 final / 23 preview, BT.709 tags, `+faststart` |
| Audio | AAC 192 kbps, 48 kHz; mix at −14 LUFS ±1, true peak ≤ −1 dBTP |
| Subtitles | SRT, ≤ 2 lines × 42 characters |
| Frame rate | 30 fps |

## 4. Code requirements

| Requirement | How it is met |
|---|---|
| Python | All tools in Python; standard library + jsonschema |
| Blender Python API | `blender/scripts/*`, version-tolerant, rerun-safe |
| FFmpeg | `shpipe.ffmpeg` (find, run, probe, encode); one clear error if missing |
| JSON configuration | `config/*.json` validated by `schemas/*.schema.json` |
| Modular scripts | One module per pipeline step, each usable alone; module size kept small (largest ≈ 180 lines) |
| Reusable assets | Presets, camera moves, templates, asset register |
| Clear folder structure | `shpipe.paths.LAYOUT`; `sh.py episode-new` creates it |
| Error handling | Typed errors, exit codes 0/1/2, atomic writes |
| Logging | `<episode>/logs/pipeline.log` + console |
| Preview and final modes | `--mode preview|final` throughout; separate render folders |
| Tests | `pytest`: 78 pass with system Python (2 skipped); 93 pass with Blender's `bpy` |

## 5. Command reference

```bash
python3 pipeline/sh.py episode-new EP002 deep_trench "The Deep Trench" --pillar "Deep Unknown"
python3 pipeline/sh.py research EP002
python3 pipeline/sh.py script EP002
python3 pipeline/sh.py storyboard EP002 --shot-list
python3 pipeline/sh.py approve EP002 storyboard --by "<name>"
blender -b --factory-startup --python blender/scripts/sh_build_shot.py -- --episode episodes/EP002_deep_trench --scene S01 S02 --mode preview
blender -b episodes/EP002_deep_trench/blender/shots/S01.blend --python blender/scripts/sh_validate_scene.py -- --episode episodes/EP002_deep_trench
blender -b episodes/EP002_deep_trench/blender/shots/S01.blend --python blender/scripts/sh_render.py -- --profile preview --render
python3 pipeline/sh.py clip EP002 --mode preview
python3 pipeline/sh.py concat EP002 --mode preview
python3 pipeline/sh.py srt EP002
python3 pipeline/sh.py mux EP002 --mode preview
python3 pipeline/sh.py qc EP002            # add --final for delivery
```

On macOS the Blender binary is `/Applications/Blender.app/Contents/MacOS/Blender`; add an alias `blender` to it in `~/.zshrc`.
