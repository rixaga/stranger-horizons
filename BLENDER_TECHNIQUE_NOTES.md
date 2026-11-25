# Blender Technique Notes

**Purpose:** for each important visual technique seen in the reference (`REFERENCE_VIDEO_ANALYSIS.md`, `REFERENCE_SCENE_BREAKDOWN.md`), explain how to recreate it in Blender for Stranger Horizons, which features and assets it needs, and what should be procedural versus hand-made.

**Status:** planning notes only. Nothing has been built or rendered. Blender is not yet confirmed on the render machine (see `PROJECT_UNDERSTANDING.md` §5.3), so every feature below must be checked against the installed version before use. Python API names in particular changed between Blender 4.x and 5.x.

**Principle:** adapt the *technique*, not the shot. Each section ends with an **SH adaptation** describing how the technique serves our subjects, with the deep-ocean prototype (EP001) first.

---

## Overview table

| # | Technique (reference time) | Core Blender features | Procedural | Manual / sourced asset |
|---|---|---|---|---|
| T1 | Atmospheric depth fog (throughout) | Principled Volume (World or domain cube), EEVEE volumetrics / Cycles volume, Mist pass | Fog density, gradient by height/distance | — |
| T2 | Moonlight key + long soft shadows (13:05, 0:03) | Sun light (angle), World background, AgX view transform, exposure | Light rig values from config | — |
| T3 | Descending aerial through canopy (12:58–13:05) | Camera on a curve path (Follow Path) or keyframed with Bezier easing; Track To target | Path + easing generated from parameters | Hero tree/branch placement near the path |
| T4 | Foreground occlusion pass (13:03–13:04) | Near-camera geometry, camera clip start, motion blur | Placement relative to the camera path | Branch / kelp / rock meshes |
| T5 | Medium close-up of a character (13:06–13:09) | Rigged character, Camera depth of field, area-light key | DoF distance driver to the target | Character model + rig (sourced or generated) |
| T6 | Over-the-shoulder reveal with deep focus (13:10–13:15) | Second camera, slow dolly-in keyframes, small aperture | Push distance and duration | Foreground silhouette subject |
| T7 | Emissive accent in fog (bear eyes) | Emission shader, Bloom (EEVEE) / Glare node (compositor), light linking | Strength tied to config | Accent object |
| T8 | Forest / environment set dressing (whole scene) | Geometry Nodes scatter (Distribute Points on Faces → Instance on Points), Asset Browser | Scatter density, seed, scale and rotation randomness | Tree, rock and shrub assets (Poly Haven CC0) |
| T9 | Multi-camera single render (12:50 "Setting up 3 cameras") | Timeline markers bound to cameras (Bind Camera to Markers), one frame range | Marker and camera creation from storyboard JSON | — |
| T10 | Restricted cool palette + one warm accent | Colour management (AgX, Look), compositor colour balance, material tints | Grade values from config | — |
| T11 | Iterative art direction by prompt (9:05 "make it darker", "move the car to the left") | Re-runnable Python scripts with exposed parameters | Entire scene build | — |

---

## T1 — Atmospheric depth fog

**Seen:** layers of trees fade to a pale blue-grey with distance; haze glows around the moon (12:58).

**How:**
- **Global fog:** a large cube enclosing the set with a *Principled Volume* material (low density, about 0.005–0.05 per metre as a starting point, tuned by eye), or a World volume (cheaper to set up, but harder to localize).
- **Height falloff:** drive density with a Gradient or Noise texture through a Map Range on the Z coordinate so fog pools low.
- **EEVEE:** enable volumetrics and set the volume start/end distances to cover the set. Tile size trades quality for speed. Enable volumetric shadows for light shafts. Setting names differ by version, so verify them.
- **Cycles:** true scattering. Volumes are the most expensive part of the render, so keep step rate and bounces low for previews.
- **Cheaper alternative / supplement:** the *Mist* render pass mixed in the compositor gives distance fade with no volume cost. It works well for previews or very distant layers.

**Procedural:** all of it (density, colour, height falloff, noise scale). Expose these in the config.
**Assets:** none.

**SH adaptation:**
- **Deep ocean (EP001):** use *Volume Absorption* (blue-green tint, red absorbed first) plus *Volume Scatter* rather than grey fog. Visibility should drop to near-black within tens of metres. This is the "realistic water attenuation" required by `VISUAL_STYLE_GUIDE.md`.
- **Antarctica:** low ground blizzard volume with an animated noise offset.
- **Ancient sites:** warm dust haze.

## T2 — Moonlight key and long soft shadows

**Seen:** cool high key from behind/side; long soft diagonal tree shadows (13:05).

**How:** a *Sun* lamp at a low elevation for long shadows. Its *angle* (angular diameter) controls shadow softness: larger means softer. Use cool colour temperature or a blue-grey tint, a dark world background with a faint sky gradient, the *AgX* view transform (already in `render_config.json` delivery profile), and negative exposure for night.

**Procedural:** light direction, intensity, colour, angle, exposure, all from a lighting preset.
**Assets:** optional HDRI for night sky or ambient (Poly Haven has CC0 HDRIs).

**SH adaptation:**
- **Deep ocean:** there is no sun at depth. The motivated sources are a faint downwelling surface light (shallow scenes only), a submersible's lamps (spot lights with soft falloff) and bioluminescence (emissive points). "Motivated volumetric light" in the EP001 README means **light shafts from a plausible source through the water volume**.
- **Antarctica:** low polar sun, long shadows. Directly reusable.

## T3 — Descending aerial move through the canopy

**Seen:** extreme-wide above mountains → descend → pass through branches → settle on the subject (12:58–13:05, ~7 s).

**How:**
- **Option A (simple, re-runnable):** keyframe camera location and rotation at 3–4 key poses with *Bezier* interpolation and ease-in/ease-out, so there are no linear starts or stops.
- **Option B (smooth path):** a *Bezier curve* + *Follow Path* constraint on the camera (animate offset/eval time) + *Track To* / *Damped Track* to an empty that also moves. This is easier to adjust by editing the curve.
- Avoid camera shake. If any "presence" is wanted, add a very low-amplitude *Noise* F-curve modifier, well below what reads as handheld (the style guide says "no unmotivated shake").
- **Lens:** a moderate-long focal length (e.g. 50–85 mm) for the aerial to compress the mountains. Optionally animate the focal length down as the camera enters the canopy for more depth.

**Procedural:** path generation from start/end points, height, duration (frames from `render_config.json` fps).
**Manual:** placement of a "hero" tree that the camera passes close to, which is an art-directed choice.

**SH adaptation (EP001):** descend from just below the dark surface through a layer of drifting particulate toward a barely-readable seabed silhouette. This matches the EP001 plan: slow, stable, forward movement ending on a readable hold.

## T4 — Foreground occlusion pass

**Seen:** near-black pine branches sweep across the frame (13:03–13:04).

**How:** place geometry very close to the camera path. Lower the camera *clip start* so it doesn't clip. Optional motion blur (Cycles/EEVEE motion blur, short shutter) to keep the pass soft. Keep these objects dark so they read as silhouettes against the fog.

**Procedural:** auto-place one or two occluders at a set distance along the camera path.
**Manual:** choose the occluder asset.

**SH adaptation:** underwater, use kelp fronds, a rock overhang or dense particulate close to the lens. In caves or ruins, use an arch or doorway edge.

## T5 — Character medium close-up

**Seen:** MCU of the man, soft key from frame left, fast falloff, near-static (13:06–13:09).

**How:** a rigged character (armature + mesh). Idle motion from a short action or a few hand-set keys on spine/neck. Camera DoF on, focus object set to the head bone or an empty parented to it, f-stop about 2–4 for soft background. Key with a large *Area* light (soft) at 45° and a faint rim.

**Procedural:** camera framing from a target and distance; DoF focus driver.
**Manual:** the character itself.

**SH note:** Stranger Horizons is faceless documentary. Human characters appear only as **illustrative reconstructions** (for example, a historical expedition member) and must be labelled. Prefer silhouettes and back views over realistic faces of real people. **Never depict an identifiable real person** with a generated face.

## T6 — Over-the-shoulder reveal with deep focus

**Seen:** observer silhouette in the foreground, bear in a fog-lit corridor far back, slow push-in (13:10–13:15).

**How:** a second camera behind and slightly above the foreground subject's shoulder. DoF either **off** or at a small aperture (f/8+) so the background subject stays readable. Slow dolly keyframes (a few percent of the subject distance over 4–6 s). Clear a corridor through the trees and brighten the fog behind the subject slightly with a hidden light inside the volume for separation.

**Procedural:** push distance/duration; "separation light" placed automatically behind the target.
**Manual:** composition (thirds placement), which needs art review.

**SH adaptation:** use an observer such as a submersible, a diver silhouette or a researcher, looking at a **documented** subject such as a seamount, a wreck, an ice formation or a ruin. **Do not** use this framing to reveal an undocumented creature or object as if real. That is exactly the case `RESEARCH_STANDARDS.md` forbids.

## T7 — Emissive accent in fog

**Seen:** small glowing eyes on the distant bear.

**How:** an *Emission* shader on small geometry. In EEVEE, bloom-like glow (in recent versions done via the compositor *Glare* node rather than a render toggle; verify for the installed version). In Cycles, the compositor *Glare* (Fog Glow / Bloom). *Light linking* (Cycles) can keep the emitter from lighting unwanted objects.

**Procedural:** strength and colour from config.

**SH adaptation:** the deep ocean's natural emissive accent is **bioluminescence** (documented in real organisms), so it is well suited to the "restrained cyan accent". Equipment lights (amber) are another option. **Avoid "eyes in the dark"** imagery: it is a horror trope.

## T8 — Environment set dressing (scatter)

**Seen:** dense conifer forest, rocks, shrubs, debris, sourced from Poly Haven (7:05–8:05).

**How:** *Geometry Nodes* on the ground mesh: *Distribute Points on Faces* (Poisson disk for natural spacing) → *Instance on Points* with a *Collection Info* of assets, random rotation (Z) and scale, density from a weight map or noise for clearings. Keep the **seed** in config so layouts are reproducible. Use *Realize Instances* only if needed.

**Procedural:** placement, density, variation, seed.
**Manual / sourced:** the individual assets. Poly Haven assets are **CC0** (licence to be recorded in the asset licence register for each download). Download into `assets/` with a record of source URL and date.

**SH adaptation (EP001):** scatter rocks, sediment mounds and sparse sponge or coral forms on a displaced seabed (a large plane + noise displacement). Keep any organisms generic and plausible for the stated depth, and labelled as illustrative.

## T9 — Multi-camera, single-render sequence

**Seen:** "Setting up 3 cameras", one 960-frame render, three shots (12:50–13:15).

**How:** create cameras per shot, add timeline markers at shot starts, and use *Bind Camera to Markers* so the active camera switches at each marker within one frame range. Alternative: one scene per shot and assembly in the Video Sequencer or with FFmpeg.

**Procedural:** generate cameras and markers straight from `storyboard.schema.json` scene entries (duration_seconds × fps → frame ranges). This connects the storyboard to Blender.

**Recommendation for SH:** render **each shot to its own image sequence** (per `CLAUDE.md`: image sequences as masters). That makes re-rendering one shot cheap and fits `pipeline/assemble_video.py`.

## T10 — Restricted palette and grade

**Seen:** near-monochrome blue-grey with one warm accent.

**How:** AgX view transform plus a *Look* (contrast) setting. Compositor *Color Balance* (lift/gamma/gain, or offset/power/slope) for a cool shadow tint. Keep material base colours fairly neutral and let the light and volume colour do the tinting. This keeps assets reusable across subjects.

**Procedural:** grade values in config, so each subject gets its own preset (ocean, ice, desert, space).

## T11 — Iterative art direction

**Seen:** short follow-up prompts adjust the scene ("make it darker", "move the car to the left", 9:05).

**How for SH:** every scene is built by a **re-runnable script with named parameters** (exposure, fog density, object positions, camera keys) read from a JSON preset. An art-direction note becomes a parameter change plus a re-run, not hand edits to the .blend. This is already required by `CLAUDE.md` ("modular and safe to rerun").

---

## Procedural vs. manual: summary

| Should be procedural (scripted, parameterized) | Should be manual or sourced |
|---|---|
| Fog / water volumes and their gradients | Hero assets (rocks, wrecks, vehicles, terrain features) |
| Lighting rigs and presets | Characters (only if used, and labelled) |
| Camera paths, easing, framing, DoF focus | Final composition sign-off (thirds, silhouettes) |
| Scatter of environment assets (seeded) | Choice of which assets to download |
| Particles (marine snow, dust, snow) | Thumbnail key art |
| Shot cameras and markers from storyboard JSON | |
| Render profiles and grade presets | |

## Assets needed for EP001 (deep-ocean prototype), first pass

| Asset | Source | Notes |
|---|---|---|
| Seabed terrain | Procedural (plane + noise displacement) | No download needed |
| Rocks / boulders | Poly Haven (CC0) or procedural | Record licence |
| Sediment / rock PBR textures | Poly Haven (CC0) | Record licence |
| Particulate "marine snow" | Procedural (Geometry Nodes points, tiny instances, slow noise drift) | — |
| Light source | Procedural (spot lights for a submersible lamp or faint downwelling) | Motivated |
| Distant silhouette scale cue | Procedural ridge / seamount, or a sourced rock | Must **not** imply an undocumented creature (EP001 README) |

## Things to verify on the render machine before Stage 5

1. Blender version, and whether the EEVEE engine identifier is `BLENDER_EEVEE` or `BLENDER_EEVEE_NEXT` (affects `render_config.json`).
2. GPU backend (Metal on Apple Silicon) available to Cycles.
3. EEVEE volumetric and bloom/glare settings for that version.
4. Free disk for image sequences: 300 frames of PNG at 1280×720 is a few hundred MB.
5. Whether the owner wants the Claude ↔ Blender connector (as in the reference, 2:53–4:41) or script-file execution (`blender --background --python …`). The scripted route is more reproducible and works without a live connection.
