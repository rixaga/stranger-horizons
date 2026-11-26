"""Build storyboard.json for EP001 The Bloop from the APPROVED script.

Every scene takes the next sentences of the approved narration (up to and including the
sentence that contains `until`), so the storyboard cannot drift from the script:
the build fails if any sentence is skipped, repeated or out of order.
Claim IDs per scene come from the [C##] markers on the script lines those sentences came from.
Durations: spoken words at 145 wpm + `pad` seconds of air + `extra` seconds of picture-only time.

    python3 episodes/EP001_the_bloop/storyboard/build_storyboard.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EP = Path(__file__).resolve().parents[1]
REPO = EP.parents[1]
sys.path.insert(0, str(REPO / "pipeline"))

WPM = 145
FPS = 30
ABBREV = ("U.S.", "H.", "P.")  # never end a sentence on these

IMAG = "Imagined — theory, not evidence"
RECON = "Illustrative reconstruction"
DATA = "Data visualisation"
NOAA_AUDIO = "NOAA hydrophone recording, 1997 — sped up 16×"


def sentences(md: str) -> list[dict]:
    body = re.split(r"^---\s*$", md, maxsplit=1, flags=re.M)[0]
    out, sec = [], None
    for raw in body.splitlines():
        if raw.startswith("## "):
            sec = raw[3:].strip()
            continue
        if sec is None or raw.startswith("#"):
            continue
        claims = re.findall(r"\[(C\d+)\]", raw)
        line = re.sub(r"\s+", " ", re.sub(r"\[C\d+\]|\{RECON\}|<[^>]*>", " ", raw)).strip()
        if not line:
            continue
        parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"“])', line)
        merged: list[str] = []
        for p in parts:
            if merged and merged[-1].endswith(ABBREV):
                merged[-1] += " " + p
            else:
                merged.append(p)
        out += [{"section": sec, "text": s, "claims": claims} for s in merged]
    return out


def cam(shot, angle, movement, position, lens=24, dof=True, fstop=4.0):
    return {"shot_size": shot, "angle": angle, "movement": movement, "position": position,
            "lens_mm": lens, "dof": dof, "fstop": fstop}


GRAPHIC_CAM = cam("full_frame_graphic", "flat", "slow push-in on graphic", "2D graphic plane", 50, False, 8.0)
OCEAN = "Deep open ocean, blue-black water, drifting marine snow"
SEABED = "Mid-water seabed (~150 m): sediment, basalt boulders (EP000 set kit)"
ANT = "Antarctic Peninsula / Southern Ocean: grey swell, tabular icebergs, overcast"

# (until, spec). `until` = a fragment of the LAST sentence spoken in this scene (None = picture-only scene).
SCENES: list[tuple[str | None, dict]] = [
    # ---------------- 1. Opening hook
    (None, dict(id="S001", extra=12.5, intent="Cold open: the real NOAA Bloop audio over black, then two seconds of silence.",
                status="abstract_visual", label=NOAA_AUDIO, camera=cam("black", "none", "none", "no camera", 24, False),
                env="Black screen", assets=["NOAA bloop.wav (16×)"], lighting="None",
                animation="Text label fades in at 0.5 s; a thin waveform line drawn from the real audio pulses with it.",
                sfx="NOAA bloop.wav unprocessed at −14 LUFS-I target, then 2 s silence.", transition="cut")),
    ("recorded in the Pacific Ocean in 1997", dict(id="S002", intent="First image: endless dark water, the scale of the ocean.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="slow_push_in",
                camera=cam("extreme_wide", "eye level", "slow push forward 6 m, eased", "mid-water 300 m depth, no seabed in view"),
                env=OCEAN, assets=["Volume water", "Marine snow particles"], lighting="Faint downwelling shafts from above, almost black below",
                animation="Particles drift upward past lens; shafts shimmer (gobo drift).", sfx="Low sub rumble pad, very quiet.", transition="dissolve 1 s")),
    ("officially unknown", dict(id="S003", intent="The network: a map of the Pacific with hydrophone points lighting up one after another.",
                status="data_visualization", label=DATA, camera=cam("map", "top-down", "slow pull-back over globe", "orbital globe view of the Pacific", 35, False, 8.0),
                env="Stylised globe, dark ocean, faint graticule", assets=["SH_Globe (Natural Earth coastlines, public domain)", "Hydrophone markers"],
                lighting="Flat graphic light, Signal Cyan accent on markers",
                animation="Markers ignite left to right; a ring pulse expands across thousands of km.", sfx="Soft UI ticks per marker (−20 dB).", transition="cut")),
    ("bigger than any whale", dict(id="S004", intent="Teaser: a vast shape moves at the edge of the light.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="static_hold",
                camera=cam("wide", "low angle", "locked, slight drift", "mid-water looking up toward faint surface"),
                env=OCEAN, assets=["CR_Giant (procedural squid-like creature)"], lighting="Backlit by surface glow; creature in silhouette",
                animation="A tentacle silhouette crosses the light shaft, 3 s, unhurried.", sfx="Deep pressure swell, no roars or creature voices.", transition="cut")),
    ("died out millions of years ago", dict(id="S005", intent="Teaser: a shark fin cuts a shaft of light.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="lateral_track",
                camera=cam("medium_wide", "eye level", "lateral track 4 m left", "beside the creature's path, 20 m away"),
                env=OCEAN, assets=["CR_Megalodon (procedural)"], lighting="Single sun shaft; creature passes through it",
                animation="Megalodon tail and fin pass through frame, marine snow swirls in its wake.", sfx="Water displacement whoosh, subtle.", transition="cut")),
    ("written seventy years earlier", dict(id="S006", intent="Teaser: ruins on a seafloor in darkness.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="descent_reveal",
                camera=cam("wide", "high angle", "slow descent 8 m", "above sunken ruins, looking down"),
                env="Abyssal floor with tilted monolithic ruins (original design)", assets=["SH_Ruins_Monolith (procedural)", "CR_Sleeper (hidden, only a shape)"],
                lighting="Cold rim light from an unseen source; ruins mostly silhouette", animation="Silt drifts off a monolith edge.", sfx="Distant low drone.", transition="cut")),
    ("knew more than it was saying", dict(id="S007", intent="Teaser: an unmarked submarine shape slides past a lone hydrophone.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="static_hold",
                camera=cam("wide", "eye level", "locked", "next to a hydrophone mooring cable"),
                env=OCEAN, assets=["SH_Submarine_Unmarked (no insignia)", "SH_Hydrophone_Mooring"], lighting="Near-black; submarine hull catches a faint blue sheen",
                animation="Hull passes left to right over 4 s.", sfx="Muffled machinery hum, no sonar pings.", transition="cut to black")),
    ("The Bloop.", dict(id="S008", intent="Title reveal: the word 'The Bloop' forms out of the real waveform.",
                status="abstract_visual", label=DATA, camera=GRAPHIC_CAM, env="Black with faint water caustics",
                assets=["Waveform of NOAA bloop.wav", "Title typeface (VISUAL_STYLE_GUIDE)"], lighting="Graphic",
                animation="Waveform line contracts into the title lettering.", sfx="A short excerpt of the real clip under the title.", transition="cut")),
    ("actually found", dict(id="S009", extra=4, intent="Promise to the viewer, then the channel card.",
                status="abstract_visual", label="Stranger Horizons", camera=GRAPHIC_CAM, env="Channel ident",
                assets=["Channel ident card"], lighting="Graphic", animation="Ident card: STRANGER HORIZONS — Explore Beyond What We Know.",
                sfx="Ident tone (owner-approved music from YouTube Audio Library).", transition="dissolve 1 s")),
    # ---------------- 2. The mysterious recording
    ("sound behaves differently", dict(id="S010", intent="Descent from the bright surface into darkness.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="descent_reveal",
                camera=cam("extreme_wide", "looking down", "continuous descent 40 m", "just below the surface, sinking"),
                env="Open ocean from surface to 300 m", assets=["Ocean surface", "Volume water"], lighting="Sun from above fading with depth",
                animation="Light shafts thin out as the camera sinks.", sfx="Surface wash fading to deep hum.", transition="cut")),
    ("cross an entire ocean basin", dict(id="S011", intent="Explain the deep sound channel.",
                status="data_visualization", label=DATA, camera=GRAPHIC_CAM, env="Cross-section diagram of the ocean",
                assets=["SH_SoundChannel diagram (original, from NOAA/DOSITS description)"], lighting="Graphic",
                animation="A pulse leaves a source, bends up and down along the channel axis and travels across the frame.", sfx="Soft low pulse sound design (labelled as illustration, not a recording).", transition="cut", sources=["SRC-016", "SRC-017"])),
    ("heard volcanoes erupting on the seafloor", dict(id="S012", intent="Cold War listening cables on the seafloor.",
                status="illustrative_reconstruction", label="Illustrative graphic", preset="deep_ocean", move="glide_reveal",
                camera=cam("wide", "low over seabed", "glide along a cable 15 m", "1 m above seabed following a cable"),
                env=SEABED, assets=["SH_Cable (procedural)", "SH_ListeningArray (generic, no insignia)", "EP000 set kit"], lighting="Cold, motivated by distant lamp; mostly dark",
                animation="Camera follows a cable to a listening node; a faint glow of a distant eruption on the horizon.", sfx="Low hum; distant rumble.", transition="cut")),
    ("earthquakes and eruptions on the seafloor", dict(id="S013", intent="NOAA's own moored hydrophone in the dark.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="rise_reveal",
                camera=cam("medium", "low angle", "rise along the mooring cable 10 m", "beside the hydrophone mooring"),
                env=OCEAN, assets=["SH_Hydrophone_Mooring (anchor, cable, float, hydrophone)"], lighting="Faint blue ambient; hydrophone catches rim light",
                animation="Cable sways slightly in current; marine snow drifts.", sfx="Hydrophone 'room tone' sound design.", transition="cut")),
    ("caught something else", dict(id="S014", intent="Something arrives: the hydrophone in close-up, a faint vibration.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="slow_push_in",
                camera=cam("close_up", "eye level", "slow push-in 1 m", "0.5 m from the hydrophone"),
                env=OCEAN, assets=["SH_Hydrophone_Mooring"], lighting="Low key; rim light",
                animation="Particles near the hydrophone tremble very slightly.", sfx="Low rumble begins.", transition="cut")),
    ("over about a minute", dict(id="S015A", intent="The real evidence: our spectrogram of NOAA's file draws itself while the real audio plays.",
                status="data_visualization", label="Spectrogram generated from the NOAA recording (sped up 16×)", camera=GRAPHIC_CAM,
                env="Dark graph field", assets=["Spectrogram from NOAA bloop.wav (research/audio_analysis.md)"], lighting="Graphic, Signal Cyan accent",
                animation="Spectrogram reveals left to right in sync with the audio; the rising sweep is highlighted.", sfx="NOAA bloop.wav under narration (ducked).", transition="cut", sources=["SRC-001", "SRC-002", "SRC-037"])),
    ("so that human ears can hear it at all", dict(id="S015", intent="Repeated detections and the speed-up: a summer-1997 timeline with repeated ticks, then a '16×' playback-speed badge on the waveform.",
                status="data_visualization", label="Spectrogram generated from the NOAA recording (sped up 16×)", camera=GRAPHIC_CAM,
                env="Dark graph field", assets=["Spectrogram from NOAA bloop.wav (research/audio_analysis.md)"], lighting="Graphic, Signal Cyan accent",
                animation="Timeline ticks appear across summer 1997 (illustrative spacing, labelled); waveform speeds up with a 16× badge.", sfx="Soft ticks.", transition="cut", sources=["SRC-001", "SRC-002"])),
    ("coast of southern South America", dict(id="S016", intent="Locate the early estimate: 50°S 100°W.",
                status="data_visualization", label=DATA, camera=cam("map", "top-down", "zoom from Pacific to South Pacific", "orbital globe view", 35, False, 8.0),
                env="Stylised globe", assets=["SH_Globe", "Location marker 50°S 100°W"], lighting="Graphic",
                animation="Globe rotates; marker drops at 50°S 100°W with coordinates text.", sfx="UI tick.", transition="cut", sources=["SRC-001"])),
    ("the way animal calls do", dict(id="S017A", intent="Comparison: an earthquake, a ship and the Bloop as three spectrogram shapes.",
                status="data_visualization", label=DATA, camera=GRAPHIC_CAM, env="Three-panel graph",
                assets=["Schematic spectrogram shapes (illustrative, labelled)", "Real Bloop spectrogram"], lighting="Graphic",
                animation="Panels appear one by one; the Bloop's rising line is highlighted.", sfx="Quiet.", transition="cut")),
    ("most resembled an animal", dict(id="S017", intent="Fox's 2002 remark: a recreated, empty acoustics lab (no people), monitors showing the real spectrogram; citation card 'New Scientist, 15 June 2002 (paraphrased)'.",
                status="illustrative_reconstruction", label=RECON, camera=cam("medium", "eye level", "slow push past monitors", "inside a generic acoustics lab"),
                env="Generic 1990s acoustics lab, night, no people, no real logos", assets=["SH_Lab (procedural)", "Real Bloop spectrogram on monitors", "Citation card"], lighting="Monitor glow, desk lamp (Ember Amber accent)",
                animation="Monitor shows the spectrogram scrolling; citation card fades in.", sfx="Computer fans, quiet.", transition="cut", sources=["SRC-007"])),
    ("enormously efficient at making sound", dict(id="S018", intent="Distance as a puzzle: a pulse ring spans five thousand kilometres.",
                status="data_visualization", label=DATA, camera=cam("map", "top-down", "slow pull-back", "globe", 35, False, 8.0),
                env="Stylised globe", assets=["SH_Globe", "Distance ring > 5,000 km"], lighting="Graphic",
                animation="Ring expands from the source to the hydrophones; a ruler reads '> 5,000 km'.", sfx="Low swell.", transition="cut")),
    ("an unknown creature", dict(id="S019A", intent="NOAA's list of guesses as an animated list card.",
                status="abstract_visual", label="Source: NOAA National Ocean Service", camera=GRAPHIC_CAM, env="List card",
                assets=["List card: military exercises, ship engines, fishing-boat winches, giant squid, whales, unknown creature"], lighting="Graphic",
                animation="Items appear one by one, the last one ('unknown creature') lingers.", sfx="Soft ticks.", transition="cut", sources=["SRC-004"])),
    ("The theories wrote themselves.", dict(id="S019", intent="Unknown ocean: camera hangs above an unexplored abyss.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="slow_push_in",
                camera=cam("extreme_wide", "high angle", "slow push toward a dark trench", "over the edge of a deep trench"),
                env="Abyssal plain falling into a trench", assets=["EP000 set kit (terrain variant: trench)"], lighting="Single faint shaft; trench is black",
                animation="Marine snow falls into the dark.", sfx="Music: low pulse builds (Anomaly beat).", transition="dissolve 1 s")),
    # ---------------- 3. The theories
    ("perhaps a giant squid", dict(id="S020", intent="THEORY ONE title card, then the Giant appears.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="rise_reveal",
                camera=cam("wide", "low angle", "rise 6 m as the creature rises", "beside a tiny ROV for scale"),
                env=OCEAN, assets=["CR_Giant (procedural: mantle, 8 arms, 2 long tentacles)", "SH_ROV (2.8 m, scale cue)"],
                lighting="ROV lamps catch the creature's skin; backlit by a shaft",
                animation="Creature rises past the ROV, arms uncoiling slowly; mantle pulses; never attacks.", sfx="Deep pressure, water movement; no creature voice.",
                transition="cut", card="THEORY ONE: THE GIANT")),
    ("bigger than anything alive", dict(id="S021A", intent="The Giant's scale: its eye slides through the ROV's lamp beam.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="lateral_track",
                camera=cam("medium", "eye level", "lateral track with the creature 5 m", "10 m from the ROV"),
                env=OCEAN, assets=["CR_Giant", "SH_ROV"], lighting="ROV lamps",
                animation="A huge eye slides through the ROV's beam; ROV is dwarfed.", sfx="Low swell.", transition="cut", sources=["SRC-031"])),
    ("Many readers heard", dict(id="S021", intent="How the press told it: invented headline cards (no real mastheads) over a dark Giant silhouette.",
                status="abstract_visual", label="Illustration", camera=GRAPHIC_CAM, env="Graphic collage over 3D inset",
                assets=["Invented headline cards (illegible body text, no real mastheads)", "CR_Giant (silhouette inset)"], lighting="Graphic",
                animation="Cards slide in; the word 'MONSTER' sharpens last.", sfx="Paper/UI.", transition="cut", sources=["SRC-008", "SRC-028"])),
    ("finally caught on tape", dict(id="S022", extra=2, intent="THEORY TWO: the Survivor, megalodon gliding out of the blue-black.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="slow_push_in",
                camera=cam("wide", "slightly low", "slow push-in, then hold as it banks away", "mid-water, 30 m ahead of the shark's path"),
                env=OCEAN, assets=["CR_Megalodon (procedural)", "SH_ROV (distant, scale)"], lighting="Shafts from above; shark crosses two shafts",
                animation="Shark emerges head-on, banks away, tail sweep; marine snow streams off its fins.", sfx="Water displacement; heartbeat-free, no stingers.",
                transition="cut", card="THEORY TWO: THE SURVIVOR")),
    ("Then there is Cthulhu.", dict(id="S023A", intent="THEORY THREE title: first glimpse of sunken ruins far below.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="descent_reveal",
                camera=cam("extreme_wide", "high angle", "slow descent", "high above the ruins"), env="Abyssal floor with ruins (original design)",
                assets=["SH_Ruins_Monolith"], lighting="Faint cyan glints", animation="Silt haze; ruins emerge.", sfx="Low drone.", transition="cut", card="THEORY THREE: THE SLEEPER")),
    ("one hundred and twenty-six degrees west", dict(id="S023", intent="THEORY THREE: Lovecraft's 1928 text, the coordinate line legible.",
                status="abstract_visual", label="From 'The Call of Cthulhu', H. P. Lovecraft, 1928 (public domain)", camera=cam("insert", "top-down", "slow push to the coordinate line", "over a book page", 60, True, 2.8),
                env="Aged paper on a dark table (original design, no imitation of a real edition)", assets=["SH_BookPage (text from public-domain story)"], lighting="Single warm practical (Ember Amber accent)",
                animation="Text blurred except the coordinate line, which sharpens.", sfx="Page rustle, quiet.", transition="cut", sources=["SRC-034"])),
    ("almost exactly there", dict(id="S024", intent="The Sleeper: camera descends to sunken ruins; an immense dormant figure.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="descent_reveal",
                camera=cam("extreme_wide", "high angle", "descent 15 m revealing the figure", "above sunken monolithic ruins"),
                env="Abyssal floor, tilted cyclopean monoliths (original design)", assets=["SH_Ruins_Monolith", "CR_Sleeper (original design from the 1928 text only)"],
                lighting="Cold blue rim; faint bioluminescent cyan in the ruins",
                animation="Silt drifts; the figure's folded wings and tentacled head emerge from the dark.", sfx="Low drone, no voices.", transition="cut")),
    ("We will come back to it.", dict(id="S025", extra=1.5, intent="The Sleeper's eye slowly opens; then a map pin 'R'lyeh (fiction)' appears.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="slow_push_in",
                camera=cam("close_up", "eye level", "slow push-in 2 m", "in front of the figure's closed eye"),
                env="Ruins", assets=["CR_Sleeper"], lighting="Eye catches a cyan glint",
                animation="Eyelid opens a few millimetres; hold; cut to globe pin.", sfx="Silence for 1 s before the cut.", transition="cut")),
    ("The Navy.", dict(id="S026A", intent="THEORY FOUR: recreated generic sonar room.",
                status="illustrative_reconstruction", label=IMAG, camera=cam("medium", "eye level", "slow lateral track along consoles", "inside a generic sonar room"),
                env="Generic Cold War-style sonar room (no real insignia or documents)", assets=["SH_SonarRoom (procedural)"], lighting="Dim green screen glow",
                animation="Screens show abstract scrolling waterfalls.", sfx="Room hum; no fabricated radio chatter.", transition="cut", card="THEORY FOUR: THE NAVY KNEW", sources=["SRC-035"])),
    ("Before anyone had heard of the Bloop.", dict(id="S026", intent="The 2001 NOAA release: paraphrase card with source line, over the sonar screens.",
                status="illustrative_reconstruction", label=IMAG, camera=cam("medium", "eye level", "slow lateral track along consoles", "inside a generic sonar room"),
                env="Generic Cold War-style sonar room (no real insignia or documents)", assets=["SH_SonarRoom (procedural)", "Quote card: paraphrase of NOAA release, 24 Aug 2001"],
                lighting="Dim green screen glow", animation="Screens show abstract scrolling waterfalls; quote card fades in with source line.",
                sfx="Room hum; no fabricated radio chatter.", transition="cut", sources=["SRC-006"])),
    ("a test you could not admit", dict(id="S027", intent="An unmarked submarine passes a lone hydrophone.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="static_hold",
                camera=cam("wide", "eye level", "locked", "beside the hydrophone mooring"),
                env=OCEAN, assets=["SH_Submarine_Unmarked", "SH_Hydrophone_Mooring"], lighting="Near-black, faint sheen",
                animation="Submarine slides past over 6 s; its wake disturbs the particles.", sfx="Muffled hum.", transition="cut", sources=["SRC-043", "SRC-044"])),
    ("the way we use the sky", dict(id="S028", extra=2, intent="THEORY FIVE: the Visitor rises from a trench.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="rise_reveal",
                camera=cam("wide", "low angle", "rise 8 m with the craft", "at the lip of a trench"),
                env="Trench edge (set kit)", assets=["CR_Visitor_Craft (smooth, unlit, original)"], lighting="Craft's cyan ring is the only light",
                animation="Craft rises silently, ring pulses once, scattering particles.", sfx="Pressure swell, no 'alien' sounds.", transition="cut", card="THEORY FIVE: SOMETHING NOT FROM HERE")),
    ("hidden species of sea people", dict(id="S029A", intent="THEORY SIX: stylised TV frame with the note 'Fiction (2012)'.",
                status="abstract_visual", label="Fiction (2012)", camera=GRAPHIC_CAM, env="Stylised TV frame graphic",
                assets=["TV frame graphic (no programme footage or branding)"], lighting="Graphic", animation="Static noise resolves into the 'Fiction (2012)' note.",
                sfx="TV static, soft.", transition="cut", card="THEORY SIX: THE MERMAIDS", sources=["SRC-023", "SRC-024"])),
    ("reached the U.S. government", dict(id="S029", intent="THEORY SIX: 'Fiction (2012)' TV frame, then distant swimmers at the edge of a lamp beam.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="static_hold",
                camera=cam("wide", "eye level", "locked, slow focus pull", "behind an ROV lamp beam"),
                env=OCEAN, assets=["Stylised TV frame with note 'Fiction (2012)' (no programme footage/branding)", "CR_Swimmers (distant humanoid silhouettes)", "SH_ROV"],
                lighting="ROV beam; figures in shadow", animation="Two figures cross the far edge of the beam and vanish; never close-up.", sfx="Water hush.", transition="cut",
                sources=["SRC-022"])),
    ("other sea monsters", dict(id="S030A", intent="The legend online: invented, illegible forum threads and fan-art style creature sketches.",
                status="abstract_visual", label="Illustration", camera=GRAPHIC_CAM, env="Phone/forum UI collage (invented)",
                assets=["Invented forum UI (illegible)", "Original sketch-style creature drawings"], lighting="Screen glow", animation="Threads scroll; sketches pile up.",
                sfx="Notification taps.", transition="cut", sources=["SRC-045", "SRC-046"])),
    ("It was never heard again.", dict(id="S030", intent="The 'Bloop Beast' of internet legend surfacing in a storm.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="aerial_reveal",
                camera=cam("extreme_wide", "high angle", "aerial pull-back over a storm sea", "50 m above the surface"),
                env="Storm surface, night", assets=["Invented, illegible forum/phone UI", "CR_BloopBeast (pale leviathan, original)"],
                lighting="Lightning flashes; creature lit only by flashes", animation="Phone screens flicker, then the leviathan's back breaks the surface.", sfx="Wind, rain, waves; no roar.", transition="cut",
                sources=["SRC-045", "SRC-046"])),
    ("still call it unsolved", dict(id="S031", intent="Headlines blur together on screen (invented, illegible).",
                status="abstract_visual", label="Illustration", camera=GRAPHIC_CAM, env="Graphic collage", assets=["Invented headline cards (no real mastheads)"],
                lighting="Graphic", animation="Cards stack and shuffle.", sfx="Paper/UI shuffle.", transition="cut", sources=["SRC-047"])),
    ("A sleeping god.", dict(id="S032", intent="Montage line-up: Giant, Survivor, Sleeper, one shot each.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="static_hold",
                camera=cam("wide", "eye level", "three locked shots, 1 s each", "creature hero angles"),
                env=OCEAN, assets=["CR_Giant", "CR_Megalodon", "CR_Sleeper"], lighting="Each creature's hero lighting",
                animation="One beat per creature.", sfx="Music hit per cut (no horror stinger).", transition="hard cuts")),
    ("Mermaids.", dict(id="S033", intent="Montage line-up continued: submarine, craft, swimmers.",
                status="illustrative_reconstruction", label=IMAG, preset="deep_ocean", move="static_hold",
                camera=cam("wide", "eye level", "three locked shots", "hero angles"),
                env=OCEAN, assets=["SH_Submarine_Unmarked", "CR_Visitor_Craft", "CR_Swimmers"], lighting="Hero lighting",
                animation="One beat per shot.", sfx="Music builds.", transition="hard cuts")),
    ("recorded the sound in the first place", dict(id="S034", extra=1.5, intent="Turn: all creatures fade; only the lone hydrophone remains in the dark.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="slow_push_in",
                camera=cam("wide", "eye level", "slow push to the hydrophone", "mid-water"),
                env=OCEAN, assets=["SH_Hydrophone_Mooring"], lighting="Single faint shaft",
                animation="Silence; particles settle.", sfx="Music drops out; 1 s of near silence.", transition="dip to black 1 s")),
    # ---------------- 4. The investigation
    ("suspected ice, off the coast of Antarctica", dict(id="S035", intent="Reveal begins: a research vessel on a grey swell at dusk.",
                status="illustrative_reconstruction", label=RECON, preset="antarctica", move="aerial_reveal",
                camera=cam("extreme_wide", "high angle", "aerial drift toward the vessel", "60 m above the sea"),
                env="Southern Ocean at dusk", assets=["SH_ResearchVessel (generic, no real name/livery)"], lighting="Low sun, overcast",
                animation="Ship pitches gently; spray.", sfx="Wind, swell; music shifts to the Investigation theme.", transition="cut", sources=["SRC-008"])),
    ("listen much closer to the ice", dict(id="S036", intent="Map turns south; a faint line from the hydrophones toward Antarctica.",
                status="data_visualization", label=DATA, camera=cam("map", "top-down", "globe rotates south", "globe", 35, False, 8.0),
                env="Stylised globe", assets=["SH_Globe", "Antarctic outline (Natural Earth)"], lighting="Graphic",
                animation="Dotted line grows south; '?' marker.", sfx="UI tick.", transition="cut", sources=["SRC-006"])),
    ("until 2009", dict(id="S037", intent="Antarctic Peninsula: icebergs, grey light; hydrophone lowered over the side.",
                status="illustrative_reconstruction", label=RECON, preset="antarctica", move="glide_reveal",
                camera=cam("wide", "eye level", "glide past icebergs toward the vessel", "10 m above water"),
                env=ANT, assets=["SH_Iceberg_Tabular", "SH_ResearchVessel", "SH_Hydrophone_Mooring (deploying)"], lighting="Flat overcast, cold",
                animation="Mooring lowered on a winch; splash.", sfx="Winch, water, wind.", transition="cut", sources=["SRC-012", "SRC-011"])),
    ("Thousands of times.", dict(id="S038", intent="Under the ice: dozens of crack-flashes along an iceberg keel.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="lateral_track",
                camera=cam("wide", "low angle", "lateral track under an iceberg keel", "15 m below the keel"),
                env="Under an iceberg, blue-green water", assets=["SH_Iceberg_Tabular (underwater keel)", "Crack VFX"], lighting="Glow through the ice from above",
                animation="Small crack flashes ripple along the keel, many of them.", sfx="Creaks and cracks (sound design, labelled in description).", transition="cut", sources=["SRC-030", "SRC-011"])),
    ("called icequakes", dict(id="S039", intent="Icequake close-up: a crack propagates; an iceberg scrapes the seafloor.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="slow_push_in",
                camera=cam("medium", "eye level", "slow push-in", "near the iceberg wall"),
                env="Under an iceberg / seafloor contact", assets=["SH_Iceberg_Tabular", "Fracture VFX (cell fracture)", "EP000 set kit"], lighting="Ice glow",
                animation="Crack races through the ice; fragments shear; keel grinds the seabed raising silt.", sfx="Deep crack, groan (sound design).", transition="cut",
                sources=["SRC-002", "SRC-018", "SRC-019"])),
    ("broke apart near the island of South Georgia", dict(id="S040", intent="A53a: a 60 km iceberg drifting and splitting near South Georgia (map + 3D).",
                status="illustrative_reconstruction", label=RECON, camera=cam("map", "top-down", "slow push on Scotia Sea", "satellite-style map", 35, False, 8.0),
                env="Scotia Sea map, South Georgia outline", assets=["SH_Globe", "SH_Iceberg_A53a (60 km long proxy)"], lighting="Graphic + soft sun",
                animation="Iceberg drifts east and splits into pieces.", sfx="Distant cracks.", transition="cut", sources=["SRC-010", "SRC-002"])),
    ("five thousand kilometres away", dict(id="S041", extra=2, intent="Side-by-side: the Bloop spectrogram and NOAA's iceberg calving recording.",
                status="data_visualization", label="Spectrograms generated from NOAA recordings: Bloop (1997, 16×) · Iceberg calving (2008, 3×)", camera=GRAPHIC_CAM,
                env="Split graph", assets=["Spectrogram: NOAA bloop.wav", "Spectrogram: NOAA A53JD33Calving_3x.wav"], lighting="Graphic",
                animation="Both draw in; shapes highlighted; note that playback speeds differ.", sfx="Short excerpts of both real NOAA files.", transition="cut",
                sources=["SRC-002", "SRC-037"])),
    ("reveal the direction it came from", dict(id="S042", intent="How a bearing works: one wavefront reaching three hydrophones at different times.",
                status="data_visualization", label=DATA, camera=GRAPHIC_CAM, env="Top-down diagram", assets=["Bearing diagram (original)"], lighting="Graphic",
                animation="Wavefront sweeps across three markers, timing ticks appear; arrow forms.", sfx="Three soft ticks.", transition="cut")),
    ("perhaps Cape Adare", dict(id="S043", extra=1.5, intent="The bearing line sweeps past 50°S 100°W to the Antarctic coast; arc of possible sources.",
                status="data_visualization", label=DATA, camera=cam("map", "top-down", "follow the line south", "globe", 35, False, 8.0),
                env="Stylised globe", assets=["SH_Globe", "Bearing line", "Arc Bransfield Strait – Ross Sea – Cape Adare"], lighting="Graphic",
                animation="Line extends; coastline arc highlights.", sfx="Low swell resolves.", transition="cut", sources=["SRC-002"])),
    # ---------------- 5. Scientific explanations
    ("releases energy into the water as sound", dict(id="S044", intent="Macro: ice under stress, cracks propagating.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="slow_push_in",
                camera=cam("macro", "eye level", "slow push-in", "centimetres from an ice face", 85, True, 2.8),
                env="Ice face underwater", assets=["SH_IceMacro (procedural)", "Fracture VFX"], lighting="Light through ice",
                animation="Micro-cracks branch and release bubbles.", sfx="Crackle (sound design).", transition="cut", sources=["SRC-002"])),
    ("carry across an ocean", dict(id="S045", intent="Sound channel again, now from an iceberg to a distant hydrophone.",
                status="data_visualization", label=DATA, camera=GRAPHIC_CAM, env="Cross-section diagram",
                assets=["SH_SoundChannel diagram", "Iceberg icon", "Hydrophone icon"], lighting="Graphic",
                animation="Pulse from iceberg travels along the channel to the hydrophone thousands of km away.", sfx="Pulse.", transition="cut", sources=["SRC-016"])),
    ("essentially identical", dict(id="S046", intent="Scale of icequakes: a counter of icequakes per year over Antarctic coastline.",
                status="data_visualization", label=DATA, camera=cam("map", "top-down", "slow orbit around Antarctica", "globe", 35, False, 8.0),
                env="Antarctica on globe", assets=["SH_Globe", "Flash points (illustrative density)"], lighting="Graphic",
                animation="Many small flashes around the coast; caption 'tens of thousands each year (Dziak, 2012)'.", sfx="Soft crackle bed.", transition="cut", sources=["SRC-009"])),
    ("as they crack and fracture.", dict(id="S047", extra=1.5, intent="NOAA's conclusion as an on-screen quote card.",
                status="abstract_visual", label="NOAA PMEL Acoustics Program", camera=GRAPHIC_CAM, env="Quote card",
                assets=["Quote card (NOAA PMEL wording, U.S. government work)"], lighting="Graphic",
                animation="Text types on; source line under it.", sfx="Quiet.", transition="cut", sources=["SRC-002"])),
    ("slowed back down to its real speed", dict(id="S047B", intent="Set-up for the listening moment: the 16× waveform on screen.",
                status="data_visualization", label="NOAA recording, sped up 16×", camera=GRAPHIC_CAM, env="Dark graph field",
                assets=["Waveform of NOAA bloop.wav"], lighting="Graphic", animation="Waveform pulses once.", sfx="Music out.", transition="cut", sources=["SRC-002"])),
    (None, dict(id="S048", extra=27, intent="The slowed-down truth: the real NOAA clip at 16×, then a 20–30 s excerpt slowed to approximate real time.",
                status="data_visualization", label="Approximate real-time playback — our reconstruction from the NOAA recording", camera=GRAPHIC_CAM,
                env="Dark graph field", assets=["NOAA bloop.wav", "Slowed excerpt (our processing)", "Live spectrogram"], lighting="Graphic",
                animation="Spectrogram stretches 16× horizontally as the slowed audio plays; frequency axis relabels to real Hz.", sfx="16× clip, then slowed excerpt; no music.", transition="cut", sources=["SRC-037"])),
    ("original recording", dict(id="S049A", intent="Pitch and time: a note climbs four octave rungs; a 165 s bar compresses into 10.3 s.",
                status="data_visualization", label=DATA, camera=GRAPHIC_CAM, env="Graph", assets=["Octave ladder graphic", "Timeline ruler 165 s vs 10.3 s"], lighting="Graphic",
                animation="Ladder and ruler animate.", sfx="Quiet tones.", transition="cut", sources=["SRC-037"])),
    ("barely audible to human ears", dict(id="S049", intent="Hearing threshold: the true-speed sweep (~9–28 Hz, our analysis) drawn against the ~20 Hz lower edge of typical human hearing.",
                status="data_visualization", label=DATA, camera=GRAPHIC_CAM, env="Graph", assets=["Octave ladder graphic", "Timeline ruler 165 s vs 10.3 s"], lighting="Graphic",
                animation="Note climbs four octave rungs; a 165 s bar compresses to 10.3 s.", sfx="Quiet tones.", transition="cut", sources=["SRC-037"])),
    ("so that we could hear it.", dict(id="S050", intent="The monster dissolves into sound: the Giant's silhouette turns into a waveform, then into ice.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="slow_push_in",
                camera=cam("wide", "eye level", "slow push-in", "mid-water"), env=OCEAN, assets=["CR_Giant (dissolve)", "Waveform VFX"], lighting="Single shaft",
                animation="Silhouette breaks into particles that align into the Bloop waveform.", sfx="The 16× clip, once, quiet.", transition="dissolve 1 s")),
    # ---------------- 6. What the evidence tells us
    ("go back through every theory", dict(id="S051", intent="The six theory cards return.",
                status="abstract_visual", label="Illustration", camera=GRAPHIC_CAM, env="Card wall", assets=["Theory cards ×6"], lighting="Graphic",
                animation="Cards slide in as a grid.", sfx="UI.", transition="cut")),
    ("not from measuring it", dict(id="S052A", intent="The Giant answered (1/3): the creature freezes mid-motion; 'louder than a blue whale' card marked 'no measurement found'.",
                status="illustrative_reconstruction", label="Answered: no evidence", preset="deep_ocean", move="static_hold",
                camera=cam("wide", "low angle", "locked", "same angle as S020"), env=OCEAN, assets=["CR_Giant (frozen)", "Claim card"], lighting="Shafts",
                animation="Creature motion freezes; frost spreads over its skin.", sfx="Cold crackle.", transition="cut", sources=["SRC-031"])),
    ("two hundred kilometres away", dict(id="S052B", intent="The Giant answered (2/3): a real-scale blue whale with its measured call range vs the Bloop's detection range.",
                status="data_visualization", label="Illustration + data (Širović et al. 2007)", camera=cam("map", "top-down", "pull back from 200 km ring to 5,000 km ring", "map", 35, False, 8.0),
                env="Map with distance rings", assets=["Blue whale model (procedural, labelled illustration)", "Rings: 200 km vs > 5,000 km"], lighting="Graphic",
                animation="Small ring for the whale, then the huge Bloop ring.", sfx="Quiet.", transition="cut", sources=["SRC-015"])),
    ("like breaking ice", dict(id="S052", intent="The Giant answered (3/3): the frozen creature cracks and breaks into drifting ice.",
                status="illustrative_reconstruction", label="Answered: no evidence", preset="deep_ocean", move="static_hold",
                camera=cam("wide", "low angle", "locked", "same angle as S020"), env=OCEAN, assets=["CR_Giant → ice (fracture VFX)", "Blue whale vs Bloop distance graphic"],
                lighting="Shafts", animation="Creature cracks and shatters into ice blocks that drift up.", sfx="Ice crack (sound design).", transition="cut",
                sources=["SRC-002"])),
    ("no evidence that it survives", dict(id="S053", intent="The Survivor answered: megalodon turns to ice; fossil-timeline graphic.",
                status="illustrative_reconstruction", label="Answered: no evidence", preset="deep_ocean", move="static_hold",
                camera=cam("wide", "eye level", "locked", "same angle as S022"), env=OCEAN, assets=["CR_Megalodon → ice", "Timeline graphic: ~23 to ~2.6 million years ago"],
                lighting="Shafts", animation="Shark freezes and fractures.", sfx="Crack.", transition="cut", sources=["SRC-039"])),
    ("toward Antarctica", dict(id="S054", intent="The Sleeper answered: map with 'R'lyeh (fiction)' and the Bloop's early estimate; measured line ≈ 1,980 km; bearing to Antarctica.",
                status="data_visualization", label=DATA, camera=cam("map", "top-down", "pull back to show both pins and Antarctica", "globe", 35, False, 8.0),
                env="Stylised globe", assets=["SH_Globe", "Pins", "Distance ruler ≈ 1,980 km (research.json computed_distances)"], lighting="Graphic",
                animation="Ruler draws between pins; then the bearing line sweeps to Antarctica; the Sleeper shot (inset) turns to ice.", sfx="UI ticks; crack.", transition="cut",
                sources=["SRC-034", "SRC-001", "SRC-002"])),
    ("asked and denied it", dict(id="S055A", intent="The Navy answered (1/2): the 2001 quote card gets an 'UNVERIFIED' stamp.",
                status="abstract_visual", label="Answered: unverified", camera=GRAPHIC_CAM, env="Quote card",
                assets=["Quote card with UNVERIFIED stamp"], lighting="Graphic", animation="Stamp lands.", sfx="Soft stamp thud.", transition="cut", sources=["SRC-006", "SRC-043", "SRC-044"])),
    ("no evidence that it was", dict(id="S055", intent="The Navy answered (2/2): the unmarked submarine dissolves into particles beside the hydrophone.",
                status="illustrative_reconstruction", label="Answered: unverified / no evidence", camera=GRAPHIC_CAM, env="Quote card + 3D inset",
                assets=["Quote card with UNVERIFIED stamp", "SH_Submarine_Unmarked → dissolve"], lighting="Graphic",
                animation="Stamp lands on the card; inset submarine fades to particles.", sfx="Stamp thud (soft).", transition="cut", sources=["SRC-006", "SRC-043"])),
    ("no evidence of any craft", dict(id="S056", intent="The Visitor answered: the craft cracks into ice.",
                status="illustrative_reconstruction", label="Answered: no evidence", preset="deep_ocean", move="static_hold",
                camera=cam("wide", "low angle", "locked", "same angle as S028"), env="Trench edge", assets=["CR_Visitor_Craft → ice"], lighting="Cyan ring fades out",
                animation="Ring light dies; hull frosts and fractures.", sfx="Crack.", transition="cut")),
    ("has ever been found", dict(id="S057", intent="The Mermaids answered: NOAA's statement as a quote card; swimmers fade.",
                status="abstract_visual", label="Answered: NOAA statement, 2012", camera=GRAPHIC_CAM, env="Quote card",
                assets=["Quote card: 'No evidence of aquatic humanoids has ever been found.' (NOAA)"], lighting="Graphic",
                animation="Card types on; inset swimmers fade.", sfx="Quiet.", transition="cut", sources=["SRC-022"])),
    ("recorded every year", dict(id="S058", intent="The Legend answered: myth vs record table; the Bloop Beast freezes and sinks as ice.",
                status="data_visualization", label="Answered: NOAA record", camera=GRAPHIC_CAM, env="Two-column table",
                assets=["Myth vs record table", "CR_BloopBeast → ice (inset)"], lighting="Graphic",
                animation="Myth lines strike through one by one; NOAA facts appear.", sfx="Soft ticks.", transition="cut", sources=["SRC-001", "SRC-032"])),
    ("The iceberg was never identified.", dict(id="S059A", intent="The honest part (1/3): an iceberg at dusk; 'No witness. Iceberg unknown.'",
                status="illustrative_reconstruction", label=RECON, preset="antarctica", move="slow_push_in",
                camera=cam("wide", "eye level", "slow push-in on an iceberg at dusk", "sea level, 200 m from the berg"), env=ANT, assets=["SH_Iceberg_Tabular", "Open-questions card"],
                lighting="Last light", animation="First two open questions fade in.", sfx="Wind; music recedes.", transition="cut", sources=["SRC-002"])),
    ("interviews", dict(id="S059B", intent="The honest part (2/3): stack of papers and web pages; none analyses the 1997 recording itself.",
                status="abstract_visual", label="Illustration", camera=GRAPHIC_CAM, env="Document stack graphic (titles of real cited papers, no fake documents)",
                assets=["Citation cards: Fox 2001, Dziak 2013, Dziak 2015, NOAA PMEL page"], lighting="Graphic", animation="Cards fan out; a missing slot 'paper on the 1997 Bloop — not found'.",
                sfx="Paper.", transition="cut", sources=["SRC-005", "SRC-010", "SRC-011", "SRC-002"])),
    ("not absent", dict(id="S059C", intent="The honest part (3/3, season): calendar of 1997 showing northern summer = austral winter, with icequake seasonality.",
                status="data_visualization", label=DATA, camera=GRAPHIC_CAM, env="Calendar/season graphic", assets=["Season ring: northern vs southern seasons", "Icequake activity curve (qualitative, Dziak 2015)"],
                lighting="Graphic", animation="Ring rotates to June–August; curve dips but stays above zero.", sfx="Quiet.", transition="cut", sources=["SRC-001", "SRC-011"])),
    ("2005, 2008, or 2012", dict(id="S059", intent="The honest part: three different 'solved' dates side by side.",
                status="illustrative_reconstruction", label=RECON, preset="antarctica", move="slow_push_in",
                camera=cam("wide", "eye level", "slow push-in on an iceberg at dusk", "sea level, 200 m from the berg"),
                env=ANT, assets=["SH_Iceberg_Tabular", "Open-questions card (no witness, iceberg unknown, no paper on 1997 signal, austral winter, dates differ)"],
                lighting="Last light", animation="Three date cards: 2005 (NOAA NOS), 2008 (PMEL data), 2012 (WIRED UK interview).", sfx="Wind.", transition="dissolve 1 s",
                sources=["SRC-004", "SRC-002", "SRC-009"])),
    # ---------------- 7. Final verdict
    ("deep sound channel", dict(id="S060", intent="Verdict: a vast tabular iceberg at dusk; camera descends below the waterline into the deep.",
                status="illustrative_reconstruction", label=RECON, preset="antarctica", move="descent_reveal",
                camera=cam("extreme_wide", "eye level → below waterline", "descent through the surface 12 m", "beside the iceberg"),
                env="Iceberg above and below water", assets=["SH_Iceberg_Tabular (above + keel)"], lighting="Dusk above; blue-black below",
                animation="Camera breaks the surface; the berg's dark mass disappears into the deep; one crack flash.", sfx="Surface to underwater transition; one deep crack.", transition="cut",
                sources=["SRC-002", "SRC-009"])),
    ("never will be", dict(id="S061", extra=3, intent="Verdict card.",
                status="abstract_visual", label="Stranger Horizons verdict", camera=GRAPHIC_CAM, env="Verdict card",
                assets=["VERDICT — Antarctic icequake: strongly supported, not directly observed"], lighting="Graphic",
                animation="Card holds 3 s after the line.", sfx="Music resolves.", transition="cut")),
    ("how little we had been listening", dict(id="S062", intent="Reflection: the lone hydrophone in the dark, the ROV passing far off.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="glide_reveal",
                camera=cam("wide", "eye level", "glide toward the hydrophone", "mid-water"), env=OCEAN, assets=["SH_Hydrophone_Mooring", "SH_ROV (distant)"],
                lighting="Prototype v4 look", animation="Particles drift; ROV lamps far away.", sfx="Low pad.", transition="cut")),
    ("remain a mystery", dict(id="S063A", intent="NOAA still listening: the hydrophone in the dark, cable rising.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="glide_reveal",
                camera=cam("wide", "eye level", "glide toward the hydrophone", "mid-water"), env=OCEAN, assets=["SH_Hydrophone_Mooring"],
                lighting="Prototype v4 look", animation="Particles drift.", sfx="Low pad.", transition="cut", sources=["SRC-006"])),
    ("haven't learned to hear", dict(id="S063", extra=3, intent="Closing: camera rises toward a faint surface; hydrophone silhouette in foreground.",
                status="illustrative_reconstruction", label=RECON, preset="deep_ocean", move="rise_reveal",
                camera=cam("extreme_wide", "low angle", "slow rise 20 m", "below the hydrophone looking up"), env=OCEAN, assets=["SH_Hydrophone_Mooring"],
                lighting="Surface glow growing", animation="Rise; hold on the surface glow.", sfx="Music swells gently; fade.", transition="dip to black")),
    (None, dict(id="S064", extra=10, intent="End card: sources and evidence labels in the description; subscribe card.",
                status="abstract_visual", label="Sources: see description", camera=GRAPHIC_CAM, env="End card",
                assets=["End card", "YouTube end-screen safe areas"], lighting="Graphic", animation="Static end card for end-screen elements.",
                sfx="Music tail.", transition="end")),
]


def build() -> dict:
    sents = sentences((EP / "script" / "script.md").read_text(encoding="utf-8"))
    i, scenes = 0, []
    for until, spec in SCENES:
        taken = []
        if until is not None:
            while True:
                if i >= len(sents):
                    raise SystemExit(f"{spec['id']}: ran out of narration looking for {until!r}")
                taken.append(sents[i]); i += 1
                if until in taken[-1]["text"]:
                    break
        text = " ".join(s["text"] for s in taken)
        words = len(text.split())
        dur = words / WPM * 60 + (0.8 if words else 0) + spec.get("extra", 0)
        dur = max(3.0, round(dur * 2) / 2)
        claims = []
        for s in taken:
            for c in s["claims"]:
                if c not in claims:
                    claims.append(c)
        scene = {
            "scene_id": spec["id"],
            "script_section": taken[0]["section"] if taken else (scenes[-1]["script_section"] if scenes else "1. Opening hook"),
            "duration_seconds": dur,
            "narration": text,
            "visual_intent": spec["intent"],
            "reconstruction_status": spec["status"],
            "on_screen_label": spec["label"],
            "claim_ids": claims,
            "source_ids": spec.get("sources", []),
            "camera": spec["camera"],
            "environment": spec["env"],
            "assets": spec["assets"],
            "lighting": spec["lighting"],
            "animation": spec["animation"],
            "sound_notes": spec["sfx"],
            "transition": spec["transition"],
        }
        if spec.get("card"):
            scene["title_card"] = spec["card"]
        if spec.get("preset"):
            scene["environment_preset"] = spec["preset"]
        if spec.get("move"):
            scene["camera_preset"] = spec["move"]
        hints_file = EP / "blender" / "templates" / f"{spec['id']}_shot.json"
        if hints_file.is_file():  # Blender build hints live next to the shot template
            scene["blender"] = json.loads(hints_file.read_text(encoding="utf-8"))
        scenes.append(scene)
    if i != len(sents):
        raise SystemExit(f"{len(sents) - i} narration sentences not assigned to any scene; next: {sents[i]['text']!r}")
    return {"episode_id": "EP001", "title": "The Bloop: The Ocean Sound Nobody Could Explain", "fps": FPS,
            "source_script": "script/script.md (v2, approved 2026-11-26)", "scenes": scenes}


def markdown(sb: dict) -> str:
    """Human-readable overview for owner review (storyboard.json stays the source of truth)."""
    rows, t = [], 0.0
    for s in sb["scenes"]:
        m, sec = divmod(int(t), 60)
        cam_ = s["camera"]
        rows.append(f"| {s['scene_id']} | {m}:{sec:02d} | {s['duration_seconds']:g}s | {s['visual_intent']} | "
                    f"{cam_.get('movement', '')} ({cam_.get('position', '')}) | {s['animation']} | {s['reconstruction_status']} · *{s['on_screen_label']}* | "
                    f"{', '.join(s['claim_ids']) or '—'} | {s['narration'][:70] + ('…' if len(s['narration']) > 70 else '') or '(no narration)'} |")
        t += s["duration_seconds"]
    assets = sorted({a.split(' (')[0].split(' →')[0] for s in sb["scenes"] for a in s["assets"] if a.startswith(("CR_", "SH_"))})
    creatures = [a for a in assets if a.startswith("CR_")]
    out = [f"# Storyboard — {sb['episode_id']} {sb['title']}", "",
           f"Generated by `storyboard/build_storyboard.py` from {sb['source_script']}. Edit the builder, not this file.", "",
           f"**{len(sb['scenes'])} scenes · {t / 60:.1f} min · {sb['fps']} fps**", "",
           "| Scene | Start | Dur | Visual objective | Camera (position) | Animation | Status · on-screen label | Claims | Narration |",
           "|---|---|---|---|---|---|---|---|---|", *rows, "",
           "## 3D assets to build (Phase 4)", "", "Creatures (procedural, original designs): " + ", ".join(creatures), "",
           "Sets and props: " + ", ".join(a for a in assets if a.startswith("SH_")), ""]
    return "\n".join(out)


if __name__ == "__main__":
    sb = build()
    (EP / "storyboard" / "STORYBOARD.md").write_text(markdown(sb), encoding="utf-8")
    out = EP / "storyboard" / "storyboard.json"
    out.write_text(json.dumps(sb, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total = sum(s["duration_seconds"] for s in sb["scenes"])
    print(f"wrote {out}: {len(sb['scenes'])} scenes, {total / 60:.1f} min")
