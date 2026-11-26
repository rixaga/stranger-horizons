# EP001 Ocean Prototype — Stage 6 Evaluation

**Status:** evaluation complete; v3 rendered. **Awaiting owner approval.** Full episode production has *not* started.
**Evaluated:** `final/EP001_preview_v2.mp4` (the Stage 5 deliverable). The improved version is v3 (see `IMPROVEMENT_LOG.md`).
**Compared against:** `REFERENCE_VIDEO_ANALYSIS.md` (§6 "Adopt / Do not adopt"), `docs/VISUAL_STYLE_GUIDE.md`, `docs/CINEMATOGRAPHY_GUIDE.md`, `docs/LIGHTING_GUIDE.md`, `docs/ENVIRONMENT_GUIDE.md`.

## How this was evaluated (what was actually done)

- **Watched:** the v2 MP4 frames were decoded and inspected as stills (frames 1, 150, 300 and a contact sheet), plus an *autocontrast* copy that stretches the darkest 10% of the range to expose hidden detail. I did not "watch" the video as a person would; motion was judged from the numbers below plus per-frame stills.
- **Measured** on the delivery MP4 with FFmpeg/NumPy (`/tmp` scripts, same method for every version):
  luma average per frame (`signalstats` YAVG), frame-to-frame change, share of near-black pixels, number of distinct luma levels in the water (top 30% of frame, a banding proxy), subject-vs-water brightness ratio (pinnacle box vs open-water box), and seabed brightness (bottom 20%).
- **Not done:** no viewing on a phone or TV, no audience test, no colourimeter. "Phone readability" below is a judgement from the stills, not a test.

Scores are 1–5 (5 = meets the guide fully). They are judgements, backed by the measurements where a number exists.

## Scores (v2, with v3 for comparison)

| # | Criterion | v2 | v3 | Main reason (v2) |
|---|---|---|---|---|
| 1 | Visual realism | 2.5 | 3 | Water and shafts are convincing; seabed reads as faceted slabs, materials read flat |
| 2 | Composition | 3.5 | 3.5 | Three layers (foreground rocks, mid pinnacle, far seamount) per Cinematography §1; pinnacle on the right third. Weakened by low subject separation |
| 3 | Camera movement | 4.5 | 4.5 | One eased move, calm 1.5 s hold, no shake (Cinematography movement rules 1–3 met) |
| 4 | Lighting | 2 | 3.5 | Motivated single key (sun through gobo, L1) and volumetric shafts (L5) are right, but exposure fails L6/L7: shadows crushed |
| 5 | Volumetrics | 3.5 | 4 | Shafts and haze sell depth; no flicker. Haze also flattens the subject |
| 6 | Environmental depth | 3 | 3.5 | Atmospheric perspective works (Reference §6 Adopt #1); near field is too dark to carry depth |
| 7 | Particles | 2.5 | 3.5 | 9,000 grains spread over a large volume: too sparse to read as marine snow (Environment Guide asks for ~12,000 near the lens) |
| 8 | Animation smoothness | 4.5 | 4.5 | Motion energy eases in and out; no frame jumps (max change 0.33 levels) |
| 9 | Continuity | 4.5 | 4.5 | No flicker, popping or exposure drift (YAVG range 24.2–26.5 across 300 frames) |
| 10 | Rendering quality | 2.5 | 3.5 | Clean render, but 8-bit banding in the water gradient and H.264 contouring in the dark |
| 11 | Overall documentary quality | 3 | 3.5 | Right tone and restraint, labelled as reconstruction; too dark to pass Quality Gate Q2 (readable on a phone) |

## Strengths to keep

- **Camera (W8):** `glide_reveal` follows every movement rule. Motion energy per second was 0.13 → 0.28 → 0.28 … 0.12 → 0.04 → 0.03: an eased start, steady glide and a still hold. Nothing changed here.
- **Restraint:** no creature, no horror cues, one cyan accent, the "Illustrative reconstruction" label in the storyboard. This matches the Reference "Do not adopt" list.
- **Stability:** no volumetric flicker or fireflies, which the Style Guide §12 QA asks for.

## Weaknesses: problem → why it matters → solution

### W1. Underexposure and crushed blacks — **High**
- **Problem:** v2 averaged YAVG 25 (limited range); 80–88% of each frame sat below luma 20 and the seabed averaged 4–9 out of 255. Autocontrast showed the shafts, pinnacle, ridge and seamount were all there, packed into the darkest ~10% of the range.
- **Why it matters:** fails Lighting L6 (readable exposure) and L7/Style Guide §1.3 (shadows never crushed to black). On a phone at normal brightness most of the frame is a black field, so Quality Gate Q2 fails. YouTube's encoder also spends few bits in near-black, so detail there is lost a second time.
- **Solution (done):** exposure +0.6 → +1.8 EV in the storyboard, world colour lifted slightly toward Abyss Navy (0.002, 0.008, 0.012), and calibration with EEVEE stills on the Mac before the full render (cloud Cycles stills had misled v1).
- **Result (v3):** YAVG 33–37; pixels below luma 20 down from 81–88% to 39–47%; seabed mean 13–16 (was 4.6–8.8). Still a dark, moody scene, but readable.

### W2. Weak subject silhouette — **High**
- **Problem:** pinnacle-to-water brightness ratio was 0.82–1.36 depending on the frame: the subject is about the same tone as the water around it.
- **Why it matters:** Quality Gate Q1 ("focal idea clear in under 2 seconds"). Lighting L3 calls for separating dark subjects from dark backgrounds with a motivated rim/backlight.
- **Solution (done):** forced openings in the light gobo behind the pinnacle (`open_at`, two openings) so a shaft stands behind it as a backlight; water scatter density 0.008 → 0.0065 so less haze sits in front of it; config basalt colour actually applied (see W11), which makes the rock darker than the lit water.
- **Result (v3):** visually the pinnacle is now a clear dark silhouette against the shafts. My box metric (0.84–1.08) barely moved because the box includes water around the rock, so this gain is a visual judgement, not a measurement.

### W3. Seabed "slab" terracing and flat material — **High**
- **Problem:** the 4 m Voronoi displacement layer produced flat-topped plates with sharp steps; at 1.2 m mesh spacing the 5 m noise looked faceted near the lens. Material was a single noise blend with no slope logic.
- **Why it matters:** Style Guide §5 (real-world scale and texture) and §4 (environment realism). Terracing is a recognisable CG artefact and pulls viewers out of a "documentary" image.
- **Solution (done):** displacement stack changed to CLOUDS 40 m / CLOUDS 10 m / DISTORTED_NOISE 7 m / STUCCI 0.8 m; terrain resolution 220 → 340 (0.76 m spacing); slope-aware material (sediment on upward faces, darker rock on steep faces) in `sh_environment_kit.make_material`.

### W4. Banding and compression contouring — **Medium-high**
- **Problem:** only 42–57 distinct luma levels in the water at the top of frame; contour lines visible; at frame 165 an H.264 keyframe visibly redraws the contours.
- **Why it matters:** Style Guide §12 rendering standard; banding is the most visible artefact in dark gradients and YouTube's re-encode makes it worse.
- **Solution (done):** 16-bit PNG masters (`preview_hd` colour depth 16), light temporal grain (`noise=c0s=2:c0f=t`) applied at encode to dither the gradient, CRF 18 → 16, and x264 `aq-mode=3` (dark-scene adaptive quantisation) with gentler deblocking (`encode_sequence(grain=…, dark_scene=True)`).
- **Result (v3):** distinct water levels 148 / 62 / 49 (was 57 / 42 / 42). Banding is reduced, not gone, at frames 150–300.

### W5. Sparse particles — **Medium**
- **Problem:** 9,000 grains spread over the whole set; only a few dozen are near the camera at any time.
- **Why it matters:** marine snow is the main near-field depth and motion cue (Environment Guide §3.1; Reference "Adopt" #3, foreground particulate).
- **Solution (done):** 22,000 grains concentrated in a 16 × 24 × 8 m box around the camera path, smaller (4 mm) with more size variation and a cooler grey.

### W6. Jagged seamount silhouette — **Low-medium**
- **Problem:** the far seamount's outline was saw-toothed.
- **Why it matters:** far shapes should dissolve softly into the water (atmospheric perspective). A jagged edge reads as low-poly CG.
- **Solution (done):** seamount roughness 5, displacement strength 1.2, facet size 10 m.

### W7. MP4 transfer tag — **Low**
- **Problem:** FFmpeg 9.1 on the Mac tagged `color_transfer` as `iec61966-2-1` (sRGB) instead of BT.709.
- **Why it matters:** players and YouTube may apply a slightly different gamma; QC flagged it.
- **Solution (done, verified on the Mac):** `retag_bt709()` remuxes with `-c copy`, the `h264_metadata` bitstream filter (rewrites the H.264 VUI) and `-movflags write_colr` (rewrites the MP4 box). The v3a and v3 renders encoded on the Mac report `bt709` for all three fields.

### W10. Hard-edged lamp pools — **Low-medium**
- **Problem:** the vehicle lamps made sharp-edged ellipses on the seabed.
- **Why it matters:** real submersible lamps through particulate water have soft, scattering falloff; hard pools look like stage spotlights.
- **Solution (done):** spot size 0.5 rad with blend 0.85; sun disc widened to 5° and its diffuse contribution cut to 0.2 so shafts read in the water rather than as hard dapples on the floor.

### W11. Material spec ignored (found during Stage 6 testing) — **High (bug)**
- **Problem:** `build_set` called `materials.setdefault(name, make_material(name, {}))`. Python evaluates the default argument first, so the defaults rebuilt (and wiped) the `sediment` and `basalt` materials defined in `ep001_set.json`. v1, v2 and the first v3 render (`v3a`) therefore used generic grey materials, not the configured colours or the slope logic.
- **Why it matters:** every set built with the kit silently ignored its material settings.
- **Solution (done):** only build a default when the config does not define it. A new test (`test_sediment_material_is_slope_aware`) failed before the fix and passes after.

### W9. Launch friction (workflow) — not a visual issue
Typing into Blender's console via remote control drops characters, and the screen can be taken back by the owner mid-command. Recalling the launch command with the Up arrow worked reliably. **Recommendation for the next stage:** a one-click Blender add-on button or a `.command` file the owner can double-click.

## Against the reference analysis

| Reference "Adopt" item | v2 | v3 |
|---|---|---|
| 1. Atmospheric-perspective depth | Yes, but near field lost in black | Yes, near/mid/far all read |
| 2. Descending establishing move | Not used (glide forward with rise). Fine for a 10 s test; consider for the episode opener | Same |
| 3. Foreground occlusion / particulate near lens | Weak | Denser marine snow near the lens |
| 4. Deep-focus reveal, subject isolated by fog | Partly (subject not separated) | Backlight shaft behind the pinnacle |
| 5. Restricted palette, one accent | Yes (cyan) | Yes |
| "Do not adopt" 4: darkness for its own sake | **Violated** | Fixed |

## Remaining limits (honest list)

- Subject separation is better but still moderate; a stronger fix is an actual rim/backlight object or a scale cue (a small ROV with lamps) in the frame, which also answers Cinematography §1 "scale cue in every establishing shot". Not added: it is a content decision for the owner.
- Sun shafts at this depth (~150 m) are at the edge of plausible (Lighting Guide: shafts only above ~200 m). Below that the scene should be lamp-only.
- Rendering stays at EEVEE preview quality (32 samples). Final-quality settings are untested.
- Phone/TV viewing was not tested.

## Decision needed from the owner

1. Approve v3 as the visual baseline for EP001, or ask for another iteration.
2. Whether to add a scale cue (ROV/diver) to establishing shots.
3. Approval to move to the next stage. **I will not start full episode production without explicit approval.**
