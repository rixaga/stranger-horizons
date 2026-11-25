# Reference Scene Breakdown

**Reference:** https://youtu.be/GM1DIGlDVa0 — "Claude + Blender Is The Best Way To Make AI Videos (Full Tutorial)", Danny Why, 13:53
**Method and limits:** see `REFERENCE_VIDEO_ANALYSIS.md` §0. Frames were sampled, not watched continuously, and **audio was not available**.
**Labels:** **[OBS]** seen in a captured frame · **[INT]** inferred by comparing frames.

Timestamps are mm:ss of the main video (the pre-roll ad is excluded). A range "a–b" means both a and b were captured and showed the same shot or segment; the true cut may fall anywhere between the last matching and first differing sample.

---

## Part 1 — Final cinematic render (the core visual reference)

Rendered in Blender by the creator's Claude session. On-screen status shows "Rendering 960 frames" (12:50) and output `forest_night.mp4` (12:56). About 17 s is shown full-screen.

| # | Time | Shot | Angle / distance | Camera move | Content and composition | Light / atmosphere |
|---|---|---|---|---|---|---|
| R1a | 12:58–13:00 | Establishing aerial | High aerial, extreme wide | **[INT]** Descending / pushing forward | **[OBS]** Mountain range veiled in fog; full moon top-centre; sparse stars; treeline silhouettes along the bottom edge | **[OBS]** Blue-grey haze; glow around moon; very low contrast in distance |
| R1b | 13:01–13:02 | (same shot, continuing) | High, wide, closer to canopy | **[INT]** Continues descending | **[OBS]** Single tall pine silhouette centred, others flanking; mountains behind | **[OBS]** Trees darker than background; fog separates layers |
| R1c | 13:03–13:04 | (same shot, continuing) | Inside canopy | **[INT]** Passing through branches | **[OBS]** Pine branches fill the frame as near-black foreground; glimpses of the lit forest beyond | **[OBS]** Foreground almost black, background fog-lit |
| R1d | 13:05 | (same shot, end) | High angle looking down, wide | **[INT]** Settling | **[OBS]** Forest floor; dark car left-centre; man standing beside it; long diagonal tree shadows | **[OBS]** Moonlight casting long soft shadows; fog fills mid-ground |
| R2 | 13:06–13:09 | Character | Eye-level, **medium close-up** | **[INT]** Near-static | **[OBS]** Man (cap, long hair, knit sweater) left-of-centre, looking off-frame right; car roof as dark shape right foreground; background dark trunks | **[OBS]** Soft cool key from frame left; fast falloff; dark background |
| R3 | 13:10–13:15 | Reveal | Eye-level, **over-the-shoulder** | **[INT]** Slow push-in (man grows in frame 13:10.5 → 13:14) | **[OBS]** Man's back/head as dark silhouette lower-centre; car body left edge; **bear** standing in mid-right background between trunks, **glowing eyes** | **[OBS]** Fog-lit corridor between trees isolates the bear; tall vertical trunks |
| — | ~13:16 | Cut | — | — | **[OBS]** Back to talking head | — |

**Sequence logic [INT]:** establish place → introduce observer → reveal what the observer sees. Three hard cuts, no transitions captured. Lighting and geography stay continuous across all three shots.

---

## Part 2 — Other appearances of the example scene

| Time | What is visible |
|---|---|
| 0:03–0:05 | **[OBS]** Teaser of the scene: high-angle, man walking near car, bear figure with glowing eyes in background fog. Facecam PiP top-right, Claude "Reply to Claude" input bar overlaid bottom-centre |
| 0:10 | **[OBS]** Blender UI: viewport split, left half solid/material view, right half rendered fog look. Forest, car and figure visible; timeline at bottom |
| 0:15 | **[OBS]** Blender viewport, camera-height view of car and figure in fog |
| 0:20 | **[OBS]** Blender viewport with brighter, lighter fog; moon visible; figure selected (selection circle) |
| 0:30 | **[OBS]** Motion graphic: render shown in a floating panel on blue stage, mascot to the right |
| 0:40–0:45 | **[OBS]** Motion graphic: mascot at desk with laptop; large screen shows the OTS shot (man's back, bear in fog); audience silhouettes in front of the screen |
| 1:30 | **[OBS]** OTS shot displayed inside a mock YouTube player with progress bar |
| 9:05 | **[OBS]** Work-in-progress render in Claude app: car in foggy forest; chat bubbles "make it darker", "move the car to the left" (iterative art direction by prompt) |
| 10:00 | **[OBS]** Same WIP render shown larger in the Claude app |
| 12:10 | **[OBS]** Motion graphic: stylized low-poly forest disc with car and figures, a camera icon circling it, mascot pointing |
| 12:30 | **[OBS]** Prompt text on screen: mini video where "the camera comes from the top and slowly zooms through the forest", followed by numbered shot cards 1–3 |
| 12:50 | **[OBS]** Expanded prompt describing three shots (top-down zoom through forest → man next to car looking at something → camera behind man, bear far away). Status "Setting up 3 cameras", "Rendering in Blender 28 min", progress 461/960 |
| 12:54 | **[OBS]** "59 min", 948/960; frame thumbnails labelled frame 1, 88, 175, 263, 350, 437, 524, 611, 698, 786, 873, 960 |
| 12:56 | **[OBS]** Output video tile `forest_night.mp4` |

---

## Part 3 — Full-video segment map

| Time | Segment type | Observed content |
|---|---|---|
| 0:00 | Talking head | **[OBS]** Presenter, medium shot, home studio: bookshelves left, warm table lamp and tripod floor lamp, neutral grey wall |
| 0:03–0:20 | Teaser + Blender | See Part 2 |
| 0:25 | Talking head | Same setup |
| 0:30–0:45 | Motion graphics | Blue gradient stage, white rounded mascot with headset; panels; "AI-generated video" panel crossed out (0:35); 3D character on turntable panel (0:35) |
| 0:50–0:55 | Motion graphics | Channel cards: New Mind, Mustard, Yarnhub, fern; Mustard highlighted |
| 1:00 | Screen/graphic | Grid of Mustard thumbnails (3D-rendered vehicles/places, bold uppercase titles) |
| 1:06–1:12 | Motion graphics | Revenue panel; "1,000 views → $5–$8" calculator, ×10 key |
| 1:18–1:30 | Motion graphics | Mascot with camera on tripod + monitor; mock channel "Night Forest" creation; OTS render in mock player |
| 1:36 | Motion graphics | Red cards with crude icons, text "AI SLOP" struck through |
| 1:42–2:00 | Motion graphics | Step podiums 1–6: Step 1 Claude icon ↔ Step 2 Blender icon; Step 3 chat bubble; Step 4 tree/rock/car thumbnails; Step 5 3D man; Step 6 render thumbnail |
| 2:06 | Talking head | — |
| 2:20 | Screen recording | Claude website "Get started with Claude Code" plan cards; facecam PiP |
| 2:55 | Motion graphics + PiP | Claude icon on blue stage |
| 3:30 | Screen recording + PiP | Claude app Settings → Claude Code options |
| 4:05 | Screen + callout | Creator community page; banner "LINK IN THE DESCRIPTION" with down arrow |
| 4:40 | Motion graphics + PiP | Mascot; Claude icon → "MCP" cable → Blender window with forest viewport |
| 5:20 | Motion graphics + PiP | "free" bracket over tree / rock / car; Higgsfield icon linked to person / animal |
| 6:00 | Screen recording | Claude "Connectors" popover enlarged: Blender — Connected, Higgsfield — Connected |
| 6:35 | Motion graphics + screen | Poly Haven homepage in a floating browser frame |
| 7:05 | Screen recording + PiP | Poly Haven "Fir Tree 01" page, Similar Assets; download tray at bottom |
| 7:35–8:05 | Screen recording + overlay | Poly Haven model categories; "Characters" category highlighted with dashed red box; download tray filling |
| 8:35 | Screen + illustration | Long prompt in Claude: create a nighttime forest scene with moonlight, "mysterious spooky", using downloaded Poly Haven objects; flat illustration of moon over pine trees |
| 9:05–10:00 | Screen | WIP renders with follow-up prompts (see Part 2) |
| 9:35 | Talking head | — |
| 10:30 | Screen + overlay | Higgsfield prompt (man with described clothing, plus skeleton for animation); glowing skeleton-on-turntable graphic |
| 11:00 | Screen | Higgsfield turnaround images: man front/side/back; bear front/side/back |
| 11:30 | Screen + PiP | New Claude session |
| 11:50 | Screen + diagram | Prompt to place man by the car and bear far away with shiny eyes in darkness; top-down blocking diagram (car, man, bear, trees) |
| 12:10–12:56 | Motion graphics / screen | See Part 2 |
| 12:58–13:15 | **Final render** | See Part 1 |
| 13:16–13:20 | Talking head | — |
| 13:35–13:50 | Split layout | Presenter left in rounded frame, community/comment screenshots right on blue stage |

---

## Part 4 — Not covered

- Any audio: narration content, music, sound effects, mix.
- Events shorter than the sampling interval in the tutorial body (2:10–12:50 sampled every 20–35 s).
- Exact cut frames within the final render (±1 s).
- Render engine, samples, resolution and fps of the creator's Blender output (not shown on screen).
