# Lighting Guide — Stranger Horizons

**Status:** v1.0 proposed (Stage 3). Light rigs are data in `config/presets/<topic>.json` (`lights` array) and are built by `blender/scripts/sh_presets.py`. Values were checked in a Cycles look-dev render (`docs/images/lookdev_presets_v1.jpg`).

**Principle:** light tells the viewer **where they are and what is real**. Every light must have a source the viewer could name.

---

## 1. Standards that apply to every shot

| # | Standard |
|---|---|
| L1 | **One key light**, motivated: sun, moon, lamp, opening, bioluminescence, screen |
| L2 | **Fill from the environment** (sky, bounce, water scatter), at least 2 stops below the key. Never a frontal "flash" fill |
| L3 | **Rim / separation** only if a source could exist (sky glow behind, a second lamp). Used to separate dark subjects from dark backgrounds |
| L4 | **Accent emitter** in the frame's accent colour (Signal Cyan or Ember Amber), small in area |
| L5 | **Volumetric shafts** only where a medium exists (water, haze, dust). Never in vacuum |
| L6 | **Readable exposure.** The focal subject's mid-tones land roughly in the middle third of the histogram after AgX. Measure it: look-dev mean luminance below about 15/255 is too dark (see §4) |
| L7 | **Shadow tint** toward Abyss Navy, never pure black, except in space |
| L8 | Physically plausible units: Sun in W/m² (irradiance), spot/area/point in W. Record the final values per shot in the render log |

## 2. Lighting by topic (preset values)

| Preset | Key | Fill / other | Volume interaction | Accent |
|---|---|---|---|---|
| `deep_ocean` | Two submersible spot lamps parented to camera (2,500 W, 40°, cool white) | Faint downwelling area light from above (300 W, blue-green, 60 m) | Strong: forward scatter (anisotropy 0.75) makes beams visible; red absorbed | Signal Cyan (bioluminescence, instruments) |
| `antarctica` | Low polar sun, 8° elevation, warm-neutral, 4 W/m², angle 0.55° | Sky (world colour) | Light ground haze with height falloff | Ember Amber (expedition gear, tents, beacons) |
| `underground` | Work lamp / head-torch spot (2,500 W, 60°, 2,700 K-like amber) | Cool bounce area (60 W) | Dust catches the beam | Ember Amber |
| `ancient_civilizations` | Low golden sun, raking across stone, 3.5 W/m² | Large sky-blue area from above (150 W) | Warm haze, height falloff | Ember Amber |
| `uap_visualization` | Moon (0.6 W/m², cool) | Night sky world, documentary day-for-night exposure (+1 EV) | Very thin high haze | Signal Cyan (marker for the reported object, sensor overlays) |
| `space_cosmic` | Single star / sun, hard (angle 0.53°, which is the Sun seen from Earth; adjust for distance) | None. Vacuum has no fill except planet-shine if a planet is present | None | Signal Cyan (graphics only) |

**Topic notes**
- **Deep ocean:** sunlight shafts are allowed only for scenes shallower than about 200 m. Below that, all light is artificial or bioluminescent. Lamps falling off into blackness are the look.
- **Antarctica:** in polar summer the sun can stay low for hours, so long shadows are accurate. Snow is very bright; keep exposure negative (−0.4 EV) so texture holds.
- **Underground:** darkness is the default. If the source isn't in frame, the narration or a previous shot must have established it.
- **UAP:** night scenes use **day-for-night** (a documentary convention): a slightly lifted moonlit exposure so the horizon, sky and the object's position stay readable. The look-dev v1 render at true moon level (0.08 W/m²) averaged under 9/255 and was unreadable, so it was raised.
- **Space:** hard terminator, true black sky. No volumetric "god rays" around planets unless an atmosphere is being shown edge-on.

## 3. Light rig recipes (manual additions per shot)

| Recipe | Setup |
|---|---|
| **Separation rim** | Small area light behind subject, 1–2 stops under key, colour from the background's source |
| **Practical glow** | Emissive material on the visible source (lamp lens, screen) plus a matching light. The visible emitter and the light it casts must agree in colour |
| **Shaft through an opening** | Spot or sun through a gap (window, hole in ice, cave mouth) into a haze/dust volume; raise volume density locally rather than globally |
| **Bioluminescent point** | Tiny emissive mesh, Signal Cyan, strength 5–20. Optional point light at 0.1–1 W for local spill |
| **Instrument light** | Small amber or cyan emitters on equipment for human scale and presence |

## 4. Exposure check (measured, not guessed)

Run `blender/scripts/sh_preset_preview.py` after any lighting change and check the mean luminance of the stills:

| Look-dev v1 (after fixes) | Mean luminance (0–255) |
|---|---|
| Antarctica | 106 |
| Ancient Civilizations | 89 |
| Space & Cosmic | 84 |
| UAP Visualization | 43 |
| Underground | 27 |
| Deep Ocean | 23 |

Dark topics (ocean, underground) are meant to sit low, but the **subject** must still read. In look-dev v1 the test block is clearly visible in both. Under about 15 overall, with no bright focal area, means a shot fails L6.

## 5. Lighting checklist (per shot)

- [ ] I can name the source of every light
- [ ] Key/fill ratio at least 2 stops
- [ ] Accent colour present once, and it is the topic's accent
- [ ] No shafts in vacuum; shafts have a medium elsewhere
- [ ] Subject readable on a phone at 50% brightness
- [ ] Final light values recorded (render log / storyboard `lighting` field)
