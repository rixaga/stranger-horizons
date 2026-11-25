# Repository Map

```text
.
├── CLAUDE.md, README.md, START_HERE_CLAUDE_CODE.md   Rules and staged workflow
├── PROJECT_UNDERSTANDING.md                          Stage 1 report
├── REFERENCE_VIDEO_ANALYSIS.md                       Stage 2 (observations vs. interpretation)
├── REFERENCE_SCENE_BREAKDOWN.md                      Stage 2 timestamped shots
├── BLENDER_TECHNIQUE_NOTES.md                        Stage 2 Blender recreation notes
├── config/
│   ├── channel.json                 Channel identity and pillars
│   ├── visual_style.json            Visual identity (palette, type, rules)
│   ├── render_config.json           Render profiles, encode and audio loudness targets
│   ├── camera_presets.json          Camera moves
│   └── presets/                     Environment look presets (base + 6 topics)
├── docs/
│   ├── CHANNEL_BIBLE.md, PRODUCTION_PIPELINE.md, RESEARCH_STANDARDS.md
│   ├── VISUAL_STYLE_GUIDE.md        Umbrella visual system
│   ├── CINEMATOGRAPHY_GUIDE.md, LIGHTING_GUIDE.md, ENVIRONMENT_GUIDE.md, AUDIO_STYLE_GUIDE.md
│   └── images/                      Look-dev references
├── schemas/                         JSON Schemas: storyboard, source dossier, claim ledger,
│                                    asset register, environment preset
├── templates/                       Example files and script template for new episodes
├── pipeline/                        System-Python tools
│   ├── check_environment.py         Tools, Blender, disk check before rendering
│   ├── validate_episode.py          Folder + schema + source-ID checks (--profile prototype|episode)
│   ├── assemble_video.py            Image sequence (+audio) → H.264 MP4, BT.709, atomic write
│   └── measure_loudness.py          −14 LUFS / −1 dBTP check
├── blender/
│   ├── scripts/                     Run inside Blender (bpy)
│   │   ├── sh_env_check.py          Blender version, engines, GPU backends
│   │   ├── sh_render.py             Render profiles, engine resolution, render log
│   │   ├── sh_presets.py            Apply environment presets (rerun-safe)
│   │   ├── sh_camera.py             Build camera moves
│   │   └── sh_preset_preview.py     Look-dev stills for all presets
│   └── templates/                   Reusable .blend templates
├── assets/
│   ├── asset_register.json          Licence record for every asset (schema: asset_register)
│   └── audio/ environments/ materials/ models/   (contents git-ignored)
├── episodes/EP001_ocean_prototype/  blender/ scripts/ renders/ (renders git-ignored)
├── tests/                           pytest suite; test_blender_integration.py needs bpy
└── requirements.txt
```

## Commands

```bash
pip install -r requirements.txt
python3 -m pytest                                  # pipeline + preset + camera tests
python3 pipeline/check_environment.py              # before rendering
python3 pipeline/validate_episode.py episodes/EP001_ocean_prototype --profile prototype
```

Large render caches and licensed third-party assets stay out of git (see `.gitignore`); record them in `assets/asset_register.json`.
