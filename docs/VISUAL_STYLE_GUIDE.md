# Visual Style Guide — Stranger Horizons

**Status:** Initial working direction. The supplied YouTube reference has not yet been independently analyzed. Update after verified review and owner approval.

## Creative target
Cinematic, realistic, atmospheric documentary imagery. It should feel observed and immersive, not like a game trailer or generic horror montage.

## Visual language
- Composition: clear focal subject, scale cues, deliberate negative space, layered foreground/midground/background.
- Camera: motivated, slow, stable movement; push-ins, tracking, controlled orbits, aerial reveals, and descents where story-appropriate.
- Lighting: physically plausible, motivated sources, controlled highlights, readable shadows.
- Atmosphere: restrained volumetrics, haze, particles, water particulates, dust, or snow where justified.
- Materials: physically based response, appropriate roughness, specular, texture scale, and weathering.
- Color: deep navy/charcoal where appropriate, restrained cyan and amber accents; adapt to subject.
- Motion: subtle and purposeful.
- Typography: minimal, legible editorial graphics; no cluttered HUD without story reason.

## Subject treatment
- Deep ocean: layered darkness, scale cues, particulate matter, realistic water attenuation, motivated light shafts.
- Antarctica: vast scale, natural cold light, wind-driven snow, credible ice and weather.
- Ancient sites: historical context first; do not present invented structures as archaeology.
- UAP/signals: separate source material from illustrative visualization.
- Space: accurate scale cues and restrained scientific graphics.

## Blender implementation
Use physically plausible materials and lighting. Save reusable camera rigs and lighting presets. Organize collections by environment, hero assets, cameras, lights, and effects. Expose key controls in configuration. Make scripts safe to rerun.

## Quality gates
Is the focal idea clear? Is the subject readable? Does scale feel believable? Is camera movement motivated? Are lighting and atmosphere controlled? Could CGI be mistaken for authentic footage? Does the shot match the approved guide?

## Render profiles
Preview: 1280×720 or 1920×1080, 30 FPS, low samples, denoising where suitable.
Delivery: 1920×1080 minimum; 3840×2160 master when practical; 30 FPS unless story requires otherwise.
Keep image sequences as render masters and encode delivery separately.
