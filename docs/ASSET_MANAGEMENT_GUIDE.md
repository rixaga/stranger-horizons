# Asset Management Guide — Stranger Horizons

**Stage:** 4. **Checked by:** `python3 pipeline/sh.py assets` (also part of `sh.py qc`).

Every model, texture, HDRI, sound, music track, voice file, font and piece of third-party footage used in an episode must be **registered, licensed and findable**. This protects the channel from copyright claims and keeps the "no fabricated evidence" rule auditable.

---

## 1. Where things live

| Kind | Folder | In git? |
|---|---|---|
| Models (`.blend`, `.glb`, `.fbx`) | `assets/models/<category>/` | No (git-ignored); back up separately |
| Textures, PBR sets | `assets/materials/<name>/` | No |
| HDRIs, terrain data, environment kits | `assets/environments/` | No |
| Music, SFX, ambience, voice | `assets/audio/{music,sfx,ambience,voice}/` | No |
| Reusable hero sets built in Blender | `blender/templates/<name>.blend` | Yes if small and made from CC0/original material; otherwise git-ignored and registered |
| **The register** | `assets/asset_register.json` | **Yes**, always |
| Episode-specific narration and mix | `episodes/<EP>/audio/` | No |

Large binaries stay out of git (see `.gitignore`). The register in git is the record of what exists and under which licence. Keep a backup of `assets/` outside the repo (external drive or cloud).

## 2. The register

Schema: `schemas/asset_register.schema.json`. Example: `templates/asset_register.example.json`.

| Field | Rule |
|---|---|
| `id` | `AST-###`, never reused |
| `name`, `kind` | Human name; one of model, texture, hdri, material, footage, image, music, sfx, voice, font, other |
| `source`, `url` | Site or creator, and the page the asset was downloaded from |
| `license` | Exact licence (e.g. `CC0`, `CC-BY-4.0`, `Artlist subscription`, `original`) |
| `attribution_required`, `attribution_text` | If attribution is required, the exact credit text must be filled in |
| `ai_generated` | `true` for anything made with a generative AI tool. Drives the disclosure review |
| `acquired` | Download or creation date |
| `local_path` | Repo-relative path of the file |

**Rules enforced by `sh.py assets`:**
- No file under `assets/{audio,environments,materials,models}` without a register entry.
- No register entry whose `local_path` is missing on disk.
- No `attribution_required` entry without `attribution_text`.
- No duplicate IDs.
- AI-generated assets are listed as a warning for disclosure review.

Storyboard scenes reference assets by `asset_ids`. `sh.py storyboard` fails on an unknown ID.

## 3. Sourcing policy

| Priority | Source type | Notes |
|---|---|---|
| 1 | **Original** (built procedurally or modelled for the channel) | Best: no licence risk, consistent look |
| 2 | **CC0** libraries (e.g. Poly Haven for models, textures, HDRIs) | Still register; licence `CC0` |
| 3 | Royalty-free subscriptions (music/SFX libraries) | Keep the licence certificate or download receipt; note the account |
| 4 | CC-BY | Allowed with exact attribution text in the register and in the video description |
| 5 | Agency or public-institution media (NASA, NOAA, ESA…) | Check each item's own terms; many have restrictions on implied endorsement; credit as required |
| ✗ | Ripped footage, "free" sites without clear licences, NC (non-commercial) licences | **Not allowed.** The channel is monetised |

**AI-generated assets** (for example characters or textures from a generative service): allowed only for illustration, registered with `ai_generated: true`, never used to depict real people or as evidence. They count as "altered or synthetic" content for YouTube's disclosure setting when realistic.

## 4. Naming and organisation

- Folders and files in `lower_snake_case`; no spaces.
- Models: `assets/models/<category>/<name>_v<NN>.<ext>`, e.g. `assets/models/rocks/basalt_boulder_v01.blend`.
- Materials: one folder per material with its maps: `basecolor`, `roughness`, `normal`, `displacement`, `ao`.
- Real-world scale in metres. Apply transforms before saving. Origin at the base for set dressing.
- Textures: prefer 2K for set dressing and 4K only for hero close-ups. Large textures cost memory on the 16 GB M4.

## 5. Using assets in Blender

1. Download, save to the right folder, **register it**, and run `python3 pipeline/sh.py assets`.
2. Build hero sets in `blender/templates/<name>.blend` by **linking** (not appending) assets where possible, so updates propagate and file sizes stay small.
3. Reference the template from the storyboard scene: `"blender": {"template": "blender/templates/<name>.blend", "target_m": [x, y, z]}`.
4. `sh_validate_scene.py` fails a shot with missing image files or missing linked libraries.

## 6. Episode credits

Before publishing, build the description credits from the register: every asset used in the episode with `attribution_required`, plus music credits required by the library. Phase D adds a script for this; until then, do it from the register by hand.
