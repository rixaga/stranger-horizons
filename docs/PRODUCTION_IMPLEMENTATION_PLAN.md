# Production Implementation Plan

**Stage:** 4. Plan written first; implementation follows it.
**Inputs:** approved Stage 1–3 documents, measured render machine (`PROJECT_UNDERSTANDING.md`: Apple M4, 16 GB, Blender 5.3.0, Metal; FFmpeg not yet installed).
**Companions:** `SYSTEM_ARCHITECTURE.md` (how the modules fit), `ASSET_MANAGEMENT_GUIDE.md`, `TECHNICAL_REQUIREMENTS.md`.

---

## 1. Principles

1. **Files are the interface.** Every module reads and writes plain files in one episode folder (JSON, Markdown, PNG sequences, WAV, MP4). Any step can be redone, inspected or done by hand.
2. **Small tools, one job each.** No framework, no database, no task queue. A shared `shpipe` package holds the handful of things every tool needs: config, paths, logging, errors and FFmpeg calls.
3. **Humans decide; code checks.** Research judgement, script writing and creative approval stay with the owner (and Claude in conversation). Code enforces structure, links, timing, licences and technical quality.
4. **Approval gates are data.** `episode.json` records who approved research, script, storyboard, prototype and final cut, and when. QC refuses a final export when a gate is missing.
5. **Preview first.** Every render path has a `preview` and a `final` mode (`config/render_config.json`).
6. **No new dependencies** beyond `jsonschema` and `pytest` (already in `requirements.txt`), FFmpeg, and Blender.

## 2. What is automated and what is not

| Module | Automated by code | Done by people / Claude in conversation |
|---|---|---|
| 1. Research Manager | Dossier and claim-ledger validation; coverage report (claims without sources, claims backed only by weak sources, unused sources, label counts) | Finding sources, reading them, judging evidence, choosing labels |
| 2. Script Generator | Claim-marker check against the ledger; reconstruction markers; word count and duration estimate per section; structure check against the seven story beats | Writing the script (Claude drafts from the dossier, owner approves) |
| 3. Storyboard Generator | Schema validation; timeline (frames per scene, cumulative timecode); asset and preset requirements list; shot list | Choosing shots (Claude drafts JSON from script, owner approves) |
| 4. Blender Production Engine | Build a shot `.blend` from one storyboard scene (preset, camera move, frame range, output path, render profile); validate a `.blend`; render preview/final; render log | Hero assets, terrain sculpting, art direction |
| 5. Audio Production | Measure loudness; probe durations; check narration length against scene duration | Recording or generating narration, choosing music, mixing |
| 6. Video Editor | Encode each scene to a clip; concat clips without re-encoding; mux the final mix; generate SRT from storyboard narration; final encode | Creative edit decisions beyond the storyboard |
| 7. Quality Control | One `qc` command that runs every check for an episode and writes a report | Watching the final cut |

## 3. Phases

| Phase | Stage | Scope | Status |
|---|---|---|---|
| **A. Foundations** | 4 | `shpipe` core; research, script, storyboard, asset and QC checks; subtitle generation; clip concat and mux; Blender shot builder and scene validator; episode layout and `episode.json` | **Done**: see §7 |
| B. Prototype | 5 | EP001 10-second deep-ocean prototype built with the Phase A tools; preview render on the M4 | After approval |
| C. Iterate | 6 | Prototype evaluation; fix high-impact issues; second preview | After B |
| D. Episode tooling | 7 (before production) | Narration import with per-scene alignment, music/SFX cue sheet, mix stem export, thumbnail checklist, burnt-in captions for Shorts | Only when Episode 001 starts |
| E. Hardening | Ongoing | Speed-ups from real render timings; anything a real episode shows is missing | Driven by need |

Deliberately **not** planned: automatic web research, automatic script writing, auto-generated narration, automatic publishing, a GUI, a job server.

## 4. Phase A deliverables (this stage)

| # | Deliverable | Test |
|---|---|---|
| A1 | `pipeline/shpipe/` core: `config`, `paths` (episode layout), `log`, `errors`, `ffmpeg` | Unit tests |
| A2 | `schemas/episode.schema.json` + `templates/episode.example.json` (status, approvals) | Schema tests |
| A3 | `shpipe.research`: dossier + ledger coverage report | Fixture episode tests |
| A4 | `shpipe.script`: marker parser, beat-structure check, timing estimate | Fixture tests |
| A5 | `shpipe.storyboard`: timeline, requirements, shot list | Fixture tests |
| A6 | `shpipe.assets`: asset-register validation, missing files, unregistered files, AI-generated list | Tmp-dir tests |
| A7 | `shpipe.edit`: SRT from storyboard; encode a scene clip; concat clips; mux audio | FFmpeg tests (skipped without FFmpeg) |
| A8 | `shpipe.qc`: run all checks, write `qc/qc_report.json` and `.md`, gate check | Fixture tests |
| A9 | `pipeline/sh.py`: one CLI with subcommands for all of the above | CLI smoke tests |
| A10 | `blender/scripts/sh_build_shot.py`: storyboard scene → shot `.blend`; `sh_validate_scene.py` | bpy integration tests |
| A11 | `sh episode-new`: create a correctly laid-out episode folder from templates | Tmp-dir test |

Existing tools stay and are reused: `validate_episode.py`, `assemble_video.py`, `measure_loudness.py`, `check_environment.py`, and `blender/scripts/sh_render.py`, `sh_presets.py` and `sh_camera.py`.

## 5. Episode workflow with gates

```
sh episode-new EP002 "title"           → episode folder + episode.json
research (Claude + owner)             → research/source_dossier.json, claim_ledger.json
sh research EP002                     → coverage report             ◆ GATE: research approved
script (Claude drafts, owner edits)   → script/script.md
sh script EP002                       → markers, beats, timing      ◆ GATE: script approved
storyboard (Claude drafts JSON)       → storyboard/storyboard.json
sh storyboard EP002                   → timeline, requirements      ◆ GATE: storyboard approved
blender: sh_build_shot.py per scene   → blender/shots/<scene>.blend
sh_validate_scene.py, render preview  → renders/preview/<scene>/    ◆ GATE: prototype/look approved
render final                          → renders/final/<scene>/
audio (narration, music, mix)         → audio/mix/final_mix.wav
sh edit clips / concat / mux / srt    → final/<EP>.mp4, final/<EP>.srt
sh qc EP002                           → qc/qc_report.md             ◆ GATE: final cut approved
```

Approvals are recorded with `sh approve EP002 script --by "<name>"`, which writes the date into `episode.json`.

## 6. Risks and mitigations

| Risk | Mitigation |
|---|---|
| FFmpeg not on the Mac | `shpipe.ffmpeg` gives one clear error; install `brew install ffmpeg` (see `TECHNICAL_REQUIREMENTS.md`). FFmpeg tests skip, never fail, without it |
| Blender API changes (4.x → 5.x) | Version-tolerant helpers already exist (engine resolution, layered actions, `use_nodes`); integration tests run against real bpy |
| Long Cycles volume renders on a fanless laptop | EEVEE preview default; per-scene renders so one shot can be redone; render log timings drive later decisions |
| Framework creep | Each module has a size budget (≈ 150 lines) and must be usable on its own from the CLI |
| Approval skipped under time pressure | QC gate check fails the final export without recorded approvals |

## 7. Phase A results (2026-11-26)

All deliverables A1–A11 are implemented. Validation:

| Check | Result |
|---|---|
| `python3 -m pytest` (system Python, no Blender) | 78 passed, 2 skipped (Blender-only) |
| Same suite with Blender 5.3.0 as `bpy` (cloud, CPU) | 93 passed |
| Python 3.9 syntax compatibility of `pipeline/` (macOS `/usr/bin/python3`) | OK |
| End-to-end on a fixture episode: storyboard → 2 shot `.blend`s → validate → render 12 frames (Cycles CPU) → clips → concat → SRT → mux → QC | Worked. Final MP4 1280×720, BT.709, video + audio, 0.40 s as planned. QC caught every planted defect (unsourced claim, weak-only claim, unused source, unknown script marker, missing beat, missing on-screen label, long narration, off-target loudness) |
| `validate_episode.py EP001 --profile prototype` | PASSED |

**Gaps found and carried into Stage 5:**
- Shots built without a `blender.template` contain only environment (water volume, lights, marine snow); the EP001 prototype needs a seabed/silhouette template.
- EEVEE could not be tested in the headless cloud workspace (no GPU context); it must be tested on the Mac.
- FFmpeg must be installed on the Mac before the edit steps can run there.
