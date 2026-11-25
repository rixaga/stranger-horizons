# Environment Guide — Stranger Horizons

**Status:** v1.0 approved by owner 2026-11-26 (Stage 3).
**Presets:** `config/presets/` (schema `schemas/environment_preset.schema.json`). Each topic preset `extends` `base.json`, inheriting the shared identity: AgX, palette, editorial rules, camera and render defaults.

---

## 1. How to use the presets

```bash
# Inside Blender, on an open .blend: (re)build the environment look. Safe to rerun.
blender --background shot.blend --python blender/scripts/sh_presets.py -- --preset deep_ocean --save

# Compare all presets on a neutral test set
blender --background --factory-startup --python blender/scripts/sh_preset_preview.py -- --out renders/lookdev
```

A preset builds the following inside the `SH_Environment` collection:

| Part | What gets built |
|---|---|
| World | Colour and strength |
| Volume domain | A box with Principled Volume (+ Volume Absorption for water), with optional height falloff and noise |
| Lights | The light rig. Lamps can be parented to the camera |
| Particles | Marine snow, snow or dust, as a particle system with tiny instanced grains |
| Scene settings | Colour management (AgX, look, exposure), EEVEE/Cycles volume settings, and the active camera's lens, DoF and clip range |

It does **not** build terrain or hero assets. Those are per episode.

Storyboard scenes name their preset in `environment_preset`.

## 2. Universal environment standards

| # | Standard |
|---|---|
| E1 | **Three depth layers:** foreground occluder, mid-ground subject, background dissolving into atmosphere |
| E2 | **Scale cue** of known size in every establishing shot (diver ≈ 1.8 m, vehicle, door, known landmark) |
| E3 | **Real-world units** (metres); terrain and texture scales match reality |
| E4 | **Source-faithful.** Real locations follow maps, bathymetry, DEMs, site plans or photos listed in the source dossier. Unknown parts are kept simple or ghosted, never invented in detail |
| E5 | **Generic means generic.** Illustrative environments avoid identifiable real features unless sourced |
| E6 | **Procedural first** for terrain, scatter and atmosphere (seeded, reproducible). **Sourced or manual** for hero assets (see `BLENDER_TECHNIQUE_NOTES.md`) |
| E7 | **Licences recorded** for every downloaded asset in `assets/asset_register.json` |

## 3. Topic presets

### 3.1 Deep Ocean (`deep_ocean`): accent Signal Cyan
**Look:** blue-green water, red absorbed first, visibility falling to near-black within about 30 m. Submersible lamps carve beams through marine snow.

| Element | Standard |
|---|---|
| Terrain | Displaced seabed with sediment, boulders, ridges, seamount silhouettes for scale |
| Volume | Water: scatter teal (0.10, 0.42, 0.48), density 0.035; absorption density 0.06; anisotropy 0.75 |
| Particles | Marine snow: 12,000 grains of about 6 mm, sinking 2 cm/s, slight Brownian drift |
| Camera | 24 mm, lamps parented to camera |
| Life | Generic and depth-plausible, or a cited species. **No undocumented creature silhouettes** |

### 3.2 Antarctica (`antarctica`): accent Ember Amber
**Look:** vast cold space, low sun, long shadows, ground blizzard.

| Element | Standard |
|---|---|
| Terrain | Ice sheet, sastrugi (wind ridges), nunataks (rock peaks), crevasses. Large-scale noise plus fine wind ridges |
| Materials | Snow: high albedo, subsurface scattering for ice edges. Blue ice where wind-scoured |
| Volume | Haze with height falloff (dense at 0 m, clear by 25 m) |
| Particles | Wind-driven snow: 12,000 grains, 6 m/s lateral drift |
| Human elements | Stations, vehicles and tents must match cited records; otherwise generic and labelled |

### 3.3 Underground (`underground`): accent Ember Amber
**Look:** total darkness broken by one working light; dust in the beam; wet or mineral surfaces catching highlights.

| Element | Standard |
|---|---|
| Terrain | Caves (procedural rock with layered strata), tunnels, bunkers (modular kit) |
| Materials | Wet rock: lower roughness in crevices, mineral streaks. Concrete: stains, efflorescence |
| Volume | Dust: warm grey, density 0.008, forward scatter |
| Light | Work lamp or head-torch spot; cool bounce fill |
| Real sites | Follow survey maps; do not invent chambers or artefacts |

### 3.4 Ancient Civilizations (`ancient_civilizations`): accent Ember Amber
**Look:** golden raking light across stone, warm haze, architectural symmetry.

| Element | Standard |
|---|---|
| Terrain | Desert, jungle or plateau context per site, from elevation data where possible |
| Materials | Stone with erosion, chipped edges, dust in recesses; restored and ruined states clearly different |
| Reconstruction | Follows cited archaeological plans. **Uncertain parts shown ghosted or wireframe**, labelled "Reconstruction based on …" |
| Speculative theories | Visually separated (wireframe or desaturated) and labelled. Never presented as archaeology |

### 3.5 UFO / UAP Visualization (`uap_visualization`): accent Signal Cyan
**Look:** an observer's sky. Plausible night (day-for-night) or day atmosphere, long lens, the object as a **labelled marker**.

| Element | Standard |
|---|---|
| Default status | `data_visualization`. Sensor footage, flight paths, timelines, positions |
| Object depiction | An abstract marker (glowing point or outline) unless the source describes the shape. Witness-described shapes are `illustrative_reconstruction` with label "Artist's impression of the reported object" |
| Never | A detailed craft no source describes; implied alien occupants; fabricated sensor overlays |
| Balance | Ordinary explanations (aircraft, balloons, satellites, Venus, sensor artefacts) get the **same** visual treatment and screen time as the anomaly |
| Source material | Original sensor or witness material shown in a Bone frame with its credit, separate from CGI |

### 3.6 Space & Cosmic (`space_cosmic`): accent Signal Cyan
**Look:** vacuum. Hard light, true black, precise scale.

| Element | Standard |
|---|---|
| Volume | None. No fog, no shafts |
| Light | Single hard star/sun; planet-shine only if a planet is in the scene |
| Bodies | Sizes, colours and surface data from cited missions and catalogues; texture maps only with verified licence and credit |
| Scale | Compressed scale stated on screen ("Not to scale") |
| Stars | From a real catalogue or a neutral sparse field. No coloured nebula backdrops unless the subject is that nebula |

## 4. Consistent identity across topics (what does not change)

Inherited from `base.json` and enforced by `tests/test_presets.py`:
- AgX view transform + Medium High Contrast look; exposure within ±1 EV.
- The same palette tokens and the **single-accent** rule.
- The same editorial rules: CGI is illustration, label reconstructions, keep subjects readable.
- The same camera defaults (sensor, clip start, motion blur) and render profiles.

## 5. Adding a new topic preset

1. Copy the closest preset, set `"extends": "base"`, a new `name` and `label`.
2. Add topic `editorial_rules` (what must not be invented).
3. Run `python3 -m pytest tests/test_presets.py` (schema and identity checks).
4. Render look-dev with `sh_preset_preview.py`. Check readability (`LIGHTING_GUIDE.md` §4).
5. Get owner approval before using the preset in an episode.
