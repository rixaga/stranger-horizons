# Cinematography Guide — Stranger Horizons

**Status:** v1.0 approved by owner 2026-11-26 (Stage 3). Camera moves are data in `config/camera_presets.json` and are built in Blender by `blender/scripts/sh_camera.py`.

The camera behaves like a **patient observer on an expedition**: it arrives, looks, and waits. It never performs.

---

## 1. Shot vocabulary

| Shot | Use in the story structure | Typical lens (full-frame equiv.) |
|---|---|---|
| Extreme wide / establishing | Hook, Context: where we are and how big it is | 24–35 mm (environment), 50–85 mm (compressed landscapes) |
| Wide | Anomaly: subject in its surroundings | 28–35 mm |
| Medium | Investigation: detail of subject or equipment | 35–50 mm |
| Close / insert | Evidence detail: texture, instrument, inscription | 50–100 mm, shallow DoF allowed |
| Observation (long lens) | Strange Signals / UAP: distant object as seen by an observer | 85–200 mm, deep focus, no DoF tricks |
| Over-the-shoulder | Possibilities: observer looking at subject | 35–50 mm, deep focus |
| Graphic / data plate | Facts, maps, timelines | Orthographic or 50 mm |

**Composition rules**
- **Three layers:** foreground occluder (dark, soft) + mid-ground subject + background in atmosphere.
- Subject on a third line or centred with symmetry (monuments, structures). Leave negative space in the direction the subject faces or moves.
- **Horizon:** level unless the camera is moving through an attitude change (descent).
- **Scale cue** in every establishing shot: a diver, a vehicle, a person-height object or a known feature.
- Keep the bottom 15% free of critical detail (YouTube controls, subtitles).

## 2. Movement presets

All moves are eased (Bezier, auto-clamped), aimed at a target empty via *Track To*, and end on a hold. Durations below are defaults; the storyboard's `duration_seconds` overrides them.

| Preset | Duration | Lens | Path (offset from target, metres) | Story use |
|---|---|---|---|---|
| `static_hold` | 6 s | 35 | Fixed at (0, −12, 2) with sub-2 cm drift | Contemplation, title plates, evidence |
| `slow_push_in` | 8 s (hold 1.5) | 35 | (0, −14, 2.5) → (0, −10, 2) | **Default.** Draws attention to the subject |
| `descent_reveal` | 10 s (hold 2) | 24 | (0, −6, 18) → (0, −9, 7) → (0, −12, 3) | **Signature opener.** Above → through an occluding layer → subject |
| `aerial_reveal` | 10 s (hold 2) | 35 | (−30, −60, 25) → (0, −45, 18) | Landscape scale (Antarctica, ancient sites) |
| `rise_reveal` | 8 s (hold 1.5) | 28 | (0, −8, 0.6) → (0, −10, 6) | Rising from the ground to reveal a structure |
| `lateral_track` | 8 s | 50 | (−6, −14, 2) → (6, −14, 2) | Parallax past foreground, revealing length |
| `controlled_orbit` | 12 s | 50 | Radius 15 m, height 4 m, −110° → −70° | Shows the form of an object; max 40–60° of arc |
| `over_shoulder_reveal` | 6 s (hold 1.5) | 40 | (0.8, −16, 1.7) → (0.7, −14.5, 1.7) | Observer → subject. Requires a foreground observer |

**Using a preset in Blender:**
```python
from sh_camera import build_camera_move
cam, keys = build_camera_move(bpy.context.scene, "descent_reveal", target=(0, 6, 2.5), frame_start=1)
```

### Movement rules
1. **One move per shot.** No push-in that then turns into an orbit.
2. **Speed:** the subject's apparent size changes by no more than about 30% over a push.
3. **No shake.** Drift is capped at 2 cm amplitude (`drift_cm`).
4. **Motivation:** the camera moves *toward* what the narration is about, and *away* only to reveal context.
5. **Occlusion passes** (branches, kelp, rock arches crossing the lens) are welcome in the first or last second of a move, never mid-sentence over key information.
6. **Focus pulls** only on close/insert shots, at most one per shot, eased over at least 1 s.

## 3. Lens and camera settings

| Setting | Standard |
|---|---|
| Sensor | 36 mm (full-frame equivalent) so lens numbers mean what they say |
| Depth of field | Off for wide shots and observation shots. On (f/2.8–5.6) for close-ups and underground |
| Motion blur | Shutter 0.5 (180°) for anything moving, set in base preset |
| Clip range | Start 5 cm; end per preset (200 m underwater, 5 km Antarctica, 10,000 km space) |
| Aspect | 16:9 full frame for long-form; Shorts re-framed to 9:16, never letterboxed |
| Frame rate | 30 fps |

## 4. Topic camera notes

| Topic | Camera character |
|---|---|
| Deep Ocean | Submersible point of view: wide (24 mm), slow forward motion, lamps attached to camera, slight vertical drift allowed (≤ 2 cm) |
| Antarctica | Wide and patient: aerial reveals, long lens across ice to compress distance, low angles into blowing snow |
| Underground | Close and enclosed: 28 mm, shallow DoF, the camera follows the light source |
| Ancient Civilizations | Architectural: level horizons, symmetry, rise reveals, slow laterals along walls |
| UFO / UAP | Observer's view: long lens, locked or very slow pans, matching the witness or sensor position stated in sources. No "chase cam" |
| Space & Cosmic | Stately and precise: slow orbits and push-ins, no shake, no lens flares unless a real lens is implied |

## 5. Shot-list format (storyboard)

Each storyboard scene sets `camera.shot_size`, `camera.angle`, `camera.movement`, `camera.lens_mm` and, where a preset applies, `camera_preset`. Validation: `python3 pipeline/validate_episode.py <episode> --profile prototype|episode`.

## 6. What we took from the reference, adapted

- The reference's three-shot logic (establish → observer → reveal, `REFERENCE_SCENE_BREAKDOWN.md` 12:58–13:15) becomes the **descent_reveal → static_hold / slow_push_in → over_shoulder_reveal** sequence pattern.
- Its pass through the canopy becomes our **occlusion pass** rule.
- Its "creature with glowing eyes" reveal is **not** adopted; reveals show documented subjects, or labelled illustrations of reported ones.
