# System Architecture — Stranger Horizons

**Stage:** 4. Describes what exists after Phase A (`PRODUCTION_IMPLEMENTATION_PLAN.md`).

---

## 1. Shape of the system

```
                         ┌──────────────── people + Claude in conversation ────────────────┐
                         │ research · script writing · storyboard drafting · art direction │
                         └───────────────────────────────┬─────────────────────────────────┘
                                                         │ writes files
                                                         ▼
 episodes/EPxxx_slug/   episode.json ─ research/ ─ script/ ─ storyboard/ ─ blender/ ─ renders/ ─ audio/ ─ edit/ ─ final/ ─ qc/ ─ logs/
        ▲      ▲                │            │            │             │           │          │         │
        │      │                ▼            ▼            ▼             ▼           ▼          ▼         ▼
        │      │          shpipe.research shpipe.script shpipe.storyboard  Blender engine   shpipe.edit  shpipe.qc
        │      │                                                     (blender/scripts/*)
        │      └── pipeline/sh.py (CLI, system Python)          blender --python … (Blender's Python)
        └───────── config/ (render profiles, presets, camera moves, style) · schemas/ · templates/ · assets/
```

- **Two Python runtimes, one codebase.** `pipeline/` runs in the system Python (3.9+). `blender/scripts/` runs inside Blender's bundled Python (3.13 in Blender 5.3). Blender scripts import the pure-Python parts of `shpipe` (paths, storyboard timing); `shpipe` never imports Blender.
- **The episode folder is the only shared state.** There is no database or server. A step's input is a file another step wrote.
- **Config is data.** Render profiles, environment presets, camera moves and the visual identity are JSON in `config/`, validated by JSON Schemas in `schemas/`.

## 2. Modules

| # | Module | Code | Inputs → outputs | Status |
|---|---|---|---|---|
| 1 | Research Manager | `shpipe/research.py` · `sh.py research` | `source_dossier.json`, `claim_ledger.json` → coverage report | Phase A ✅ |
| 2 | Script Generator | `shpipe/script.py` · `sh.py script` · `templates/script_template.md` | `script.md` + ledger → markers, beats, timing | Phase A ✅ (writing is human/Claude) |
| 3 | Storyboard Generator | `shpipe/storyboard.py` · `sh.py storyboard [--shot-list]` | `storyboard.json` → timeline, requirements, `shot_list.csv` | Phase A ✅ (drafting is human/Claude) |
| 4 | Blender Production Engine | `blender/scripts/` | storyboard scene → `blender/shots/<scene>.blend` → `renders/<mode>/<scene>/frame_####.png` | Phase A ✅ foundations |
| 5 | Audio Production | `pipeline/measure_loudness.py` · `shpipe/qc.check_audio` | `audio/mix/final_mix.wav` → loudness report | Partial; narration/music import is Phase D |
| 6 | Video Editor | `shpipe/edit.py` · `sh.py srt/clip/concat/mux` | frames → scene clips → picture → final MP4 + SRT | Phase A ✅ |
| 7 | Quality Control | `shpipe/qc.py` · `sh.py qc [--final]` · `sh_validate_scene.py` | whole episode → `qc/qc_report.{json,md}` | Phase A ✅ |

### 2.1 Blender Production Engine (sub-systems)

| Sub-system | Script | Notes |
|---|---|---|
| Shot builder | `sh_build_shot.py` | One storyboard scene → one `.blend`. Sets fps, frame range, render profile, camera move, environment preset, output path and metadata. Optional `blender.template` opens a hero-set `.blend` first |
| Environment, lighting, atmosphere, particles | `sh_presets.py` | Builds world, volume, light rig and particle system from `config/presets/<topic>.json` into the `SH_Environment` collection; rerun-safe |
| Camera system | `sh_camera.py` | Eight eased moves from `config/camera_presets.json`; lens override from storyboard |
| Render manager | `sh_render.py` | Profiles (preview/delivery/master/shorts), engine-name resolution per Blender version, Metal/OptiX/CUDA GPU selection, `render_log.json` |
| Scene validation | `sh_validate_scene.py` | Checks a `.blend` against the storyboard and profile before rendering |
| Environment checks | `sh_env_check.py`, `sh_run_checks.py` | Blender version, engines, GPU backends; runnable from the Blender GUI |
| Look-dev | `sh_preset_preview.py` | One still per preset on a neutral set |
| Asset and material manager | `assets/asset_register.json` + `shpipe/assets.py` | Registration and licence checks now; Blender-side asset linking is Phase B (see `ASSET_MANAGEMENT_GUIDE.md`) |
| Animation system | camera moves + particle drift | Object animation beyond this is per-shot work in the template `.blend` |

## 3. Data contracts

| File | Schema | Written by | Read by |
|---|---|---|---|
| `episode.json` | `episode.schema.json` | `sh.py episode-new`, `sh.py approve` | QC (gates, profile) |
| `research/source_dossier.json` | `source_dossier.schema.json` | People/Claude | research, storyboard source IDs, QC |
| `research/claim_ledger.json` | `claim_ledger.schema.json` | People/Claude | research, script, QC |
| `script/script.md` | Markdown with `[C##]` and `{RECON}` markers | People/Claude | script check |
| `storyboard/storyboard.json` | `storyboard.schema.json` | People/Claude | storyboard check, shot builder, SRT, edit, QC |
| `blender/shots/<scene>.blend` | Scene custom properties `sh_*` | Shot builder | Validator, render |
| `renders/<mode>/<scene>/frame_####.png` + `render_log.json` | Profile in `render_config.json` | Blender | Clip encoder, QC |
| `assets/asset_register.json` | `asset_register.schema.json` | People | assets check, storyboard check |
| `qc/qc_report.json` | — | QC | People |

Timing rule: a scene of `duration_seconds` at the storyboard's `fps` is `round(duration × fps)` frames, rendered as shot frames `1…N`. Edit timecode is cumulative across scenes (`shpipe.storyboard.timeline`).

## 4. Cross-cutting concerns

| Concern | Implementation |
|---|---|
| **Errors** | `shpipe.errors`: `ShError` (expected, user-facing), `ToolMissing` (with install hint), `CommandFailed` (last stderr lines). CLI exit codes: 0 pass/warn, 1 check failed, 2 tool or usage error |
| **Logging** | `shpipe.log.get_logger(name, <episode>/logs/pipeline.log)`: console plus a timestamped file per episode; no duplicate handlers |
| **Atomic writes** | Media goes to `name.partial.mp4` and is renamed only on success; JSON via a temp file plus rename |
| **Preview vs final** | `--mode preview|final` in Blender and edit tools maps to `render_config.json` profiles (`preview` / `delivery`); paths are kept apart (`renders/preview` vs `renders/final`) |
| **Version tolerance** | Engine IDs resolved at runtime; layered-action F-curves; `use_nodes` only before Blender 5 |
| **Validation** | JSON Schema for every data file; if `jsonschema` is missing, checks degrade to structural ones and say so |
| **Editorial integrity in code** | Non-footage scenes must have `on_screen_label`; every claim except speculation needs a source; unknown script markers fail; final QC needs every approval gate |

## 5. Extension points

- **New topic look:** add `config/presets/<name>.json` (see `ENVIRONMENT_GUIDE.md` §5).
- **New camera move:** add an entry to `config/camera_presets.json`; tests build every move automatically.
- **Hero sets:** save `blender/templates/<name>.blend` and reference it from a scene's `blender.template`.
- **New QC check:** add a function returning `{"status", "errors", "warnings"}` to `shpipe/qc.py` and list it in `run()`.

## 6. Known limits (Phase A)

- Shots without a template are environment-only (water/fog, lights, particles; no terrain or subject).
- EEVEE needs a GPU context, so it renders on the Mac but not in the headless cloud workspace. Cloud tests render with CPU Cycles instead.
- `pipeline/assemble_video.py` predates `shpipe.ffmpeg.encode_sequence` and duplicates its settings. It is kept as a stand-alone tool.
- Narration import, music cues and stem export are Phase D.
