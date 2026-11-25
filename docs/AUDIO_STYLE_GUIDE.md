# Audio Style Guide — Stranger Horizons

**Status:** v1.0 proposed (Stage 3). Loudness targets are data in `config/render_config.json` (`audio`) and are checked by `pipeline/measure_loudness.py`.

**Principle:** the viewer should **trust their ears the way they trust the facts**. Narration is the spine; music and effects support it and never manufacture fear.

Note: the Stage 2 reference video's audio could not be analyzed (`REFERENCE_VIDEO_ANALYSIS.md` §0), so nothing here is derived from it.

---

## 1. Narration

| Aspect | Standard |
|---|---|
| Voice | Calm, curious, measured. Authoritative without drama. English, neutral international accent |
| Pace | About 140–150 words per minute; slower (≈120) for key facts and the verdict |
| Wording | Evidence labels are spoken, not just shown: "reported", "claimed", "one hypothesis is", "this has not been verified" |
| Pauses | 0.5–1.5 s of air after a key fact or before a reveal. Silence is a tool |
| Voice source | Authorised human voice or a licensed/authorised synthetic voice. Record the source and licence in `assets/asset_register.json` (`kind: voice`, `ai_generated` if applicable). Never clone a real person's voice without written consent |
| Recording | 48 kHz / 24-bit WAV, quiet room, no music under the raw take. Pronunciation notes in the script for names and places |
| Processing | High-pass ~80 Hz, gentle compression, de-ess. Keep it natural; no radio-announcer saturation |

## 2. Music

| Aspect | Standard |
|---|---|
| Character | Atmospheric, sparse, cinematic: drones, low strings, soft piano, analog synth pads, restrained percussion |
| Per topic | Ocean: deep pads, slow pulses. Antarctica: airy, glassy textures. Underground: low drones, distant metallic resonance. Ancient: modal, organic textures, hand percussion (no faux "exotic" clichés). UAP/Signals: minimal synth, clean tones. Space: wide pads, very slow evolution |
| Structure | Music follows the seven story beats: low under Context, builds under Anomaly, recedes under Investigation, resolves at Verdict |
| Never | Horror stingers, jump-scare hits, screaming risers, comedic cues |
| Licensing | Only licensed or original music. Every track in the asset register with licence, source and any attribution text. Keep proof of licence for Content ID disputes |
| Ducking | Music sits **−12 to −18 dB under narration**, via a sidechain compressor or duck bus (ratio 4:1–8:1, release 300–500 ms) so it breathes without pumping |

## 3. Sound effects and ambience

| Aspect | Standard |
|---|---|
| Motivated | Effects match what is on screen and what the place would sound like |
| Ocean | Low water rumble, distant creaks, equipment hum. Sonar pings only if a vessel with sonar is in the scene. No "whale cries" unless the species is shown and cited |
| Antarctica | Wind (layered: gusts plus constant), snow hiss, ice creak, crunch of footsteps |
| Underground | Room tone, drips, distant rumble, echo matched to the space size |
| Ancient | Wind, insects or birds appropriate to region and climate, sand and stone movement |
| UAP / Signals | Clean UI tones for data graphics; source audio (if any) presented as-is and labelled. **No invented "alien" sounds presented as recordings** |
| Space | Vacuum is silent. Use music and soft design tones only. Data sonifications must be labelled as sonifications |
| Graphics | Soft, short UI ticks on card and label reveals, at least 20 dB under narration |
| Honesty | Never add sound to archival or source footage that wasn't in it without labelling it as added |

## 4. Mix structure

Buses (DAW or editor): `Narration` · `Music` (→ `MusicDuck`) · `Ambience` · `SFX` · `Graphics` → `Master`.

| Stem | Typical level relative to narration |
|---|---|
| Narration | Reference (0 dB) |
| Music | −12 to −18 dB under narration |
| Ambience | −18 to −24 dB, but up front in narration gaps |
| SFX | Varies; peaks never above narration |
| Graphics | −20 dB or lower |

Mix with headphones **and** small speakers (phone or laptop), because most viewers listen on those.

## 5. Delivery loudness

| Target | Value | Checked by |
|---|---|---|
| Integrated loudness | **−14 LUFS ±1** (YouTube long-form and Shorts) | `pipeline/measure_loudness.py` |
| True peak | **≤ −1 dBTP** | same |
| Sample rate | 48 kHz | `assemble_video.py` (`-ar 48000`) |
| Codec in MP4 | AAC, 192 kbps | `assemble_video.py` |

```bash
python3 pipeline/measure_loudness.py final/EP001_mix.wav          # exit 0 = within target
python3 pipeline/measure_loudness.py final/EP001.mp4 --json        # machine-readable report
```

Note: −14 LUFS is a streaming-platform delivery target, not a game or broadcast target. Broadcast versions, if ever needed, use their own spec (e.g. −23 LUFS EBU R128).

## 6. Subtitles

- English subtitles (SRT) for every long-form episode, proofread against the final narration.
- Maximum 2 lines, about 42 characters per line, at least 1 s on screen.
- Sound-only information that matters (for example, the content of a recording) is captioned in brackets.
- Shorts: burnt-in captions at the size specified in `VISUAL_STYLE_GUIDE.md` §10.

## 7. Audio QA checklist

- [ ] Narration intelligible over music at every moment (phone-speaker test)
- [ ] Loudness −14 ±1 LUFS, true peak ≤ −1 dBTP (`measure_loudness.py` exit 0)
- [ ] No clipping, clicks, or room-tone gaps at edits
- [ ] Every music, SFX and voice file is in the asset register with a licence
- [ ] No invented sounds presented as authentic recordings
- [ ] Subtitles match the final narration
