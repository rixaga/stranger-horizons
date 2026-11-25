# Project Understanding — Stranger Horizons

**Stage:** 1 of 7 (Understand the repository), per START_HERE_CLAUDE_CODE.md
**Prepared:** 2026-11-26
**Repository state reviewed:** `rixaga/stranger-horizons`, single commit `33b249f` ("Add Stranger Horizons project foundation")
**Scope of this stage:** read and inspect only. No existing file was modified. This file is the only addition.

---

## 0. What was actually read and run

Every file in the repository was read in full (16 files, ~290 KB including `.git`):

| Area | Files |
|---|---|
| Root | `CLAUDE.md`, `README.md`, `START_HERE_CLAUDE_CODE.md` |
| Docs | `docs/CHANNEL_BIBLE.md`, `docs/PRODUCTION_PIPELINE.md`, `docs/REPOSITORY_MAP.md`, `docs/RESEARCH_STANDARDS.md`, `docs/VISUAL_STYLE_GUIDE.md` |
| Config | `config/channel.json`, `config/render_config.json`, `config/visual_style.json` |
| Schema | `schemas/storyboard.schema.json` |
| Pipeline | `pipeline/assemble_video.py`, `pipeline/validate_episode.py` |
| Episodes | `episodes/EP001_ocean_prototype/README.md` |

Checks actually run (in the cloud workspace, outside the repo where they produced files):

| Check | Result |
|---|---|
| All 4 JSON files parse | OK |
| `storyboard.schema.json` is a valid JSON Schema draft 2020-12 | OK |
| Minimal storyboard validates against schema | OK |
| Both Python scripts compile (Python 3.13.18) | OK |
| `validate_episode.py episodes/EP001_ocean_prototype` | **FAILED**: 9 missing folders (expected; see §6) |
| `assemble_video.py` on 30 synthetic 1280×720 PNG frames | OK: H.264, yuv420p, 30 fps, 30 frames. `color_space=unknown` |
| `assemble_video.py` with a missing frame pattern | Exits 254 (raw FFmpeg error, no friendly message) |
| `assemble_video.py --help` | **CRASH**: `TypeError` (bug, see §6) |

Not done: no YouTube reference was viewed (that is Stage 2), and the owner's Mac was not inspected (see §5.3).

---

## 1. Project overview

Stranger Horizons is a **faceless, English-language, cinematic mystery and science documentary YouTube channel**. The repository is the production foundation: editorial rules, a staged workflow for Claude, a draft visual direction, render settings, a storyboard schema and two small pipeline utilities.

The project is at **pre-production / foundation stage**. No research, script, Blender file, asset or render exists yet. The first technical goal is a **10-second deep-ocean Blender prototype** (EP001), which must be approved before any full episode is made.

Claude's role (CLAUDE.md): research partner, documentary writer, Blender technical director and pipeline engineer. Claude works one stage at a time and stops at each approval gate.

## 2. Channel identity

| Element | Definition (from repo) |
|---|---|
| Name | Stranger Horizons |
| Tagline | "Explore Beyond What We Know." |
| Format | Faceless cinematic mystery and science documentary entertainment, English |
| Audience | International general audience, teens and adults |
| Promise | Investigate unusual questions with curiosity, atmosphere and intellectual honesty |
| Positioning | **Not** a horror or conspiracy channel. Mystery is the entry point; evidence is the substance |

The core tension the channel has to manage: it wants the *pull* of mystery content (UAPs, hidden places, "forbidden" theories) and the *credibility* of science documentary. Nearly every rule in the repo exists to protect that credibility: evidence labels, counter-explanations, and CGI never passed off as real footage.

## 3. Content strategy

### 3.1 Pillars and target mix

| Pillar | Share | Scope |
|---|---|---|
| Hidden Earth | 30% | Antarctica, remote / underground / lost places, ancient sites |
| Deep Unknown | 30% | Deep ocean, unusual marine life, underwater sounds and anomalies |
| Strange Signals | 25% | UAP reports, unexplained signals, unusual observations and data |
| Forbidden Theories | 15% | Simulation hypothesis, Dark Forest, other speculation, clearly framed |

### 3.2 Storytelling approach

Every long-form episode follows a seven-beat structure:

1. Hook: a compelling question
2. Context: what is known and why it matters
3. Anomaly: the unusual evidence or observation
4. Investigation: sources, experts, alternatives, uncertainty
5. Possibilities: hypotheses with confidence labels
6. Verdict: what can and cannot be concluded
7. Closing question

Length target is 12–16 minutes "without padding". Cadence is one long-form episode per week, **only once the pipeline is stable**. Verified moments get repurposed into Shorts.

### 3.3 Research standards

- **Six evidence labels:** established fact, strong evidence, hypothesis, disputed, unverified report, speculation.
- **Source priority:** primary sources → peer-reviewed / institutions → reputable specialist press → secondary summaries (orientation only) → social / forums (leads, not proof).
- **Source dossier fields:** ID, title, author/org, publication and access dates, URL, type, claim supported, passage/page/timestamp, limitations, reliability.
- **Claim audit:** every important factual statement maps to one or more dossier entries. Unverifiable claims get qualified or cut.
- **Titles** must intrigue without asserting unsupported claims.

### 3.4 Editorial integrity (non-negotiable)

- Never fabricate sources, quotes, dates, measurements, experts, documents or archival material.
- Never present CGI reconstruction as authentic footage, and never imply CGI depicts a real undocumented creature or object.
- Always include credible ordinary explanations.
- Use hedged language ("reported", "claimed", "proposed", "unverified") where it applies.

## 4. Visual direction

**Status:** *initial working direction*. Both `VISUAL_STYLE_GUIDE.md` and `visual_style.json` say it is pending verified analysis of the YouTube reference (Stage 2) and owner approval (Stage 3).

| Dimension | Direction |
|---|---|
| Overall | Cinematic, realistic, atmospheric, documentary. "Observed and immersive", not a game trailer or horror montage |
| Composition | Clear focal subject, scale cues, negative space, layered fore/mid/background |
| Camera | Slow, stable, motivated: push-in, tracking, controlled orbit, aerial reveal, descent. No unmotivated shake |
| Lighting | Physically plausible, motivated sources, controlled highlights, readable shadows |
| Atmosphere | Restrained volumetrics, haze, particulates, dust or snow where justified |
| Materials | Physically based (PBR), correct roughness, specular, texture scale, weathering |
| Colour | Deep navy / charcoal base; restrained cyan and amber accents; adapt per subject |
| Typography | Minimal, legible editorial graphics; no gratuitous HUD |
| Avoid | Cartoon style, generic horror tropes, jumpscares, unsupported visual claims |

Subject treatments are defined for deep ocean, Antarctica, ancient sites, UAP/signals and space.

**Quality gates per shot:** Is the focal idea clear? Is the subject readable? Is the scale believable? Is the camera motivated? Are lighting and atmosphere controlled? *Could this CGI be mistaken for authentic footage?* Does it match the guide?

## 5. Technical architecture

### 5.1 Intended pipeline

```
Research → claim audit → script → narration → storyboard (JSON) → Blender scenes
→ render (image sequence) → sound/edit → subtitles/thumbnail → QA → publish
```

**Approval gates:** research → script → storyboard → visual prototype → final cut.

**Technical rules (CLAUDE.md):** modular Blender scripts that are safe to rerun; no assumed add-ons; save editable `.blend` files and source scripts; image sequences as render masters, delivery encoded separately; preview and final profiles; record software versions and render settings.

### 5.2 Render configuration (`config/render_config.json`)

| Profile | Resolution | Engine | Samples | Output |
|---|---|---|---|---|
| Preview | 1280×720 | `BLENDER_EEVEE_NEXT` | 16 | PNG sequence |
| Delivery | 1920×1080 | `BLENDER_CYCLES` (preferred) | not set | PNG, AgX view transform |
| Master | 3840×2160 | not set | not set | not set |

All profiles run at 30 fps. The EP001 prototype is 10 s = **300 frames**.

### 5.3 Machine capabilities (actually inspected)

There are two different machines, and that matters for Stage 5.

**Cloud workspace (where Claude works right now):**

| Item | Found |
|---|---|
| OS / arch | Linux x86_64 |
| CPU / RAM / free disk | 2 cores / 7.8 GiB / ~30 GB free |
| GPU | None (no `nvidia-smi`) |
| Blender | **Not installed** |
| FFmpeg / ffprobe | 6.1.1 |
| Python | 3.13.18, `jsonschema` 4.26.0 available |
| Git | 2.43.0 (read-only clone; this session cannot push to the repo) |

**Owner's computer (linked through the Claude desktop app):** a MacBook Air on Apple Silicon (arm64, macOS). **Blender version, RAM, free disk, Metal GPU support and FFmpeg presence were not inspected.** The desktop link exposes files only once a folder is connected, and its shell is a Linux VM, not macOS. Before Stage 5 these have to be confirmed, for example by having the owner run `blender --version` and share *About This Mac*, or by Claude using computer use with permission.

Implications:
- The cloud workspace can run research, documentation, JSON/schema tooling, FFmpeg assembly and QA scripts. It can render Blender only on CPU, slowly. Blender could be installed here as a portable Linux build, but Cycles volumetrics on 2 CPU cores would be very slow, and EEVEE needs a GPU/OpenGL context it does not have.
- The **real render machine is most likely the MacBook Air.** Fanless Apple Silicon throttles under sustained load. Cycles plus volumetric water is the most expensive case, so preview-first and EEVEE-first are the right calls.

## 6. Existing assets and tools: what works and what is wrong

### 6.1 What exists and is sound

- **Clear governance.** CLAUDE.md, the staged workflow and the approval gates are explicit and mutually consistent.
- **Strong editorial framework.** Evidence labels, source hierarchy, dossier fields and visual-integrity rules are already at a professional level.
- **`storyboard.schema.json`.** Valid draft 2020-12. Captures `reconstruction_status`, which is how the "CGI is not evidence" rule gets enforced in data.
- **`assemble_video.py`.** Works: PNG sequence (+ optional audio) → H.264 MP4.
- **`validate_episode.py`.** Works as a folder-structure check.

### 6.2 Bugs and defects found

| # | File | Issue | Severity |
|---|---|---|---|
| B1 | `pipeline/assemble_video.py` | `--help` crashes with `TypeError`. The `--input` help string contains `frame_%05d.png`, and argparse treats `%` as a format specifier. Fix: escape as `%%05d`. | Medium (breaks help; normal runs work) |
| B2 | `pipeline/assemble_video.py` | MP4 has no colour tags (`color_space=unknown`). Players may guess the wrong matrix and shift colours slightly, which matters for a navy/cyan palette. Fix: tag BT.709 (`-colorspace bt709 -color_primaries bt709 -color_trc bt709`). | Medium for final delivery |
| B3 | `pipeline/assemble_video.py` | No check that input frames exist; fails with FFmpeg's raw exit code 254. | Low |
| B4 | `pipeline/validate_episode.py` | Checks only that storyboard JSON has a `scenes` list. It does **not** validate against `storyboard.schema.json`, even though `jsonschema` is available. | Medium |
| B5 | `pipeline/validate_episode.py` | Requires all 9 full-episode folders (`research/`, `script/`, `audio/`…). EP001 is a prototype that by design has no research or script, so it fails and will keep failing. There is no "prototype" profile. | Medium |
| B6 | `schemas/storyboard.schema.json` | Accepts an empty `scenes` array; `camera` has no required fields; no `additionalProperties` guard, so typos pass silently. | Low |
| B7 | `config/render_config.json` | Engine ID `BLENDER_EEVEE_NEXT` is version-specific. It is the Blender 4.2–4.x identifier, and the name changed again in later releases (to the best of my knowledge, Blender 5.0 reverted it to `BLENDER_EEVEE`). The file's own note says to confirm. Scripts should resolve the ID from the installed version, not hard-code it. | **High for Stage 5** (wrong ID means the script fails) |

### 6.3 Schema and design observations (not bugs, but worth deciding)

- `reconstruction_status` has `documentary_footage`, but a faceless channel will mostly use **third-party archival / agency footage** (NASA, NOAA, etc.) that carries licences and attribution. A split such as `licensed_archival_footage` / `original_footage` / `illustrative_reconstruction` would make provenance and licensing auditable per scene.
- The storyboard has `source_ids`, but there is **no schema for the source dossier or claim ledger** they point to, so the link cannot be validated.
- `config/visual_style.json` and `VISUAL_STYLE_GUIDE.md` duplicate each other. One of them should be the source of truth after Stage 3.

## 7. Missing components

### 7.1 Listed in `REPOSITORY_MAP.md` but absent

`blender/scripts/`, `blender/templates/`, `assets/audio/`, `assets/environments/`, `assets/materials/`, `assets/models/`. The map says "create as needed", so this is expected, not an error.

### 7.2 Needed before or during Stage 5 (Blender prototype)

| Component | Why |
|---|---|
| Environment capability check script (Blender version, engine IDs, render devices, disk, FFmpeg) | CLAUDE.md requires validation before rendering; resolves B7 |
| Blender scene-builder module(s) under `blender/scripts/` (water volume, light shafts, particulates, seabed, camera rig) | Core of EP001; must be modular and safe to rerun |
| Render-profile loader that applies `render_config.json` inside Blender | Keeps preview and final settings consistent |
| Render metadata log (versions, settings, timings) written per render | CLAUDE.md "record software versions and render settings" |
| `.gitignore` (renders, caches, `__pycache__`, `.blend1`) | No ignore file exists; renders and caches would be committed |
| Prototype validation profile | Fixes B5 |

### 7.3 Needed before Stage 7 (Episode 001)

| Component | Notes |
|---|---|
| Source-dossier and claim-ledger templates / schemas | Research standards define the fields but there is no file format |
| Script template with source markers and evidence labels | Pipeline §2 output |
| Narration plan: voice source (human or authorised TTS), pronunciation notes, timing | No voice decision recorded |
| Music and SFX sourcing and licence register | Pipeline says "licensed music" but no library or register exists |
| Subtitle workflow (SRT/VTT) | Not started |
| Thumbnail and title guidelines | Must follow the "no unsupported claims in titles" rule; no brand assets (logo, fonts, colours) yet |
| QA checklist script (black frames, dropped frames, duration, loudness, encoding) | Pipeline §8 lists checks, no tooling yet |
| On-screen disclosure convention for CGI (e.g. "Illustrative reconstruction") | Rules forbid misleading CGI but don't define how it is labelled on screen |
| Shorts spec (9:16, length, captions) | Mentioned in the bible, undefined |
| Loudness target for delivery (e.g. around -14 LUFS integrated for YouTube) | Not defined |

### 7.4 Project hygiene

No `LICENSE`, no `requirements.txt` / dependency list, no automated tests, no CI. All are low priority right now, but tests for the two pipeline scripts would be cheap and useful.

## 8. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **Stage 2 depends on watching a YouTube video.** Claude cannot play video from a URL; a page fetch gives only metadata. | Stage 2 is blocked unless media is supplied | Owner supplies a local video file (frames can then be extracted with FFmpeg and examined) or timestamped screenshots. Per the rules, nothing is inferred from the URL |
| Render hardware unknown; likely a fanless MacBook Air | Slow or thermally throttled volumetric renders | Confirm specs first; EEVEE preview; short frame ranges; keep Cycles for final only |
| Blender version unknown; engine IDs and APIs differ across 4.x / 5.x | Scripts break | Version-detection step before any scene code (B7) |
| Prototype validator always fails (B5) | Gate becomes meaningless or ignored | Add prototype vs. episode profile |
| Mystery topics (UAPs, "forbidden theories") pull toward sensationalism | Credibility and audience-trust damage | Already strongly covered by the research standards; enforce via claim ledger and `reconstruction_status` |
| Teen audience | Content must stay teen-appropriate; no gore or shock imagery | Fits the existing "no horror tropes" rule |
| Third-party footage and music licensing not yet tracked | Copyright claims | Licence register per asset, linked from the storyboard |
| This session can read but not push the repo | Changes must be delivered as files or the GitHub app must be given push access | Decide delivery route before Stage 3 edits |

## 9. Recommended development sequence

Follows START_HERE_CLAUDE_CODE.md without skipping gates. Small fixes are slotted where they unblock the next stage.

1. **Stage 1 approval (now).** Owner reviews this document and approves or corrects it.
2. **Unblock Stage 2.** Owner supplies the reference as a local video file or timestamped screenshots. In parallel, owner confirms the render machine: Blender version, RAM, free disk.
3. **Stage 2: reference analysis.** `REFERENCE_VIDEO_ANALYSIS.md` and `REFERENCE_SCENE_BREAKDOWN.md`, observations kept separate from interpretation. Stop.
4. **Stage 3: refine the visual style guide.** Define reusable camera, lighting, atmosphere, material and environment presets. Pick one source of truth between the `.md` and `.json`. Stop.
5. **Stage 4: production implementation plan.** Include the pipeline fixes from §6.2 (B1–B7), the environment check script, `.gitignore`, and the prototype validation profile as the first bounded tasks. Stop.
6. **Stage 5: EP001 10-second prototype.** Capability check → modular scene scripts → preview render (EEVEE, 1280×720, 300 frames) → MP4 via `assemble_video.py` → report versions, settings, timings. Stop.
7. **Stage 6: evaluate and iterate.** `PROTOTYPE_EVALUATION.md`, fixes, second preview. Stop.
8. **Before Stage 7:** build the research templates, licence register, narration, subtitle and QA tooling from §7.3. Then **Stage 7: Episode 001**, only after explicit prototype approval.

---

## Decisions needed from the owner

1. Approve or correct this understanding.
2. How the Stage 2 reference will be supplied (local file or screenshots).
3. Which machine will render, and its Blender version.
4. Whether the pipeline fixes (B1–B7) should wait for Stage 4 as planned, or be done earlier as a small separate task.
5. How changes should reach the repository (this session currently has read-only access).

---

## Status update — 2026-11-26

What changed since this report (all on branch `claude/foundation-stages-1-3`):

- **Stage 1 gaps fixed (B1–B7)**, each with a test that failed first. `assemble_video.py` (help crash, BT.709 tags, missing-frame error, atomic write), `validate_episode.py` (prototype profile, schema validation, source-ID cross-check), and `render_config.json` (logical engine names). **B7 confirmed:** Blender 5.3 offers `BLENDER_EEVEE`, not `BLENDER_EEVEE_NEXT`.
- **Added:** `.gitignore`, `requirements.txt`, `templates/`, source dossier, claim ledger and asset register schemas, `check_environment.py`, `measure_loudness.py`, Blender scripts under `blender/scripts/`, and tests (`python3 -m pytest`).
- **Testing:** Blender 5.3.0 was installed in the cloud workspace as a Python module (`bpy`, CPU only), and the Blender integration tests and look-dev renders ran there. The owner's Mac still needs `pipeline/check_environment.py` and `sh_env_check.py` before Stage 5.
- **Stage 2 completed** (frame-sampled; audio not accessible). **Stage 3 approved by the owner on 2026-11-26** (as a working baseline, open to revision): see `docs/VISUAL_STYLE_GUIDE.md` and the four companion guides.

## Render machine — measured 2026-11-26

Measured on the owner's Mac by running `blender/scripts/sh_run_checks.py` inside Blender's Python console. Raw reports are in `reports/environment/`, which is git-ignored.

| Item | Result |
|---|---|
| Machine | Mac16,12, Apple M4, 10 CPU cores, 16 GB RAM |
| OS | macOS 27.2.1 |
| Blender | **5.3.0** (`/Applications/Blender.app`), bundled Python 3.13.13 |
| Render engines | `BLENDER_EEVEE`, `CYCLES` |
| Cycles GPU | **Metal: Apple M4 GPU, 10 cores** |
| Free disk | 254.9 GB |
| Xcode command-line tools | Installed; `/usr/bin/python3` available |
| **FFmpeg** | **Not found** (not on PATH, `/opt/homebrew/bin` or `/usr/local/bin`). Needed by `assemble_video.py` and `measure_loudness.py` |
| jsonschema | Not in Blender's Python; not checked for the system Python |

Implications for Stage 5: EEVEE preview at 1280×720 is the right default. Cycles with volumes runs on Metal but will be slow and warm on a fanless machine, so keep it for final shots with modest samples. FFmpeg must be installed before any video can be encoded.
