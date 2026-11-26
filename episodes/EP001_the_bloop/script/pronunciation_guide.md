# Pronunciation Guide — EP001 The Bloop

For the ElevenLabs narration (Phase 5) and any human re-recording. Accent: neutral international English (Audio Style Guide §1).

**How to use in ElevenLabs:** add the "Alias" column as a pronunciation dictionary (alias rules work with every model; IPA phoneme rules only work with some). Always generate a test line for each entry marked ⚠ and listen before generating the full narration.

## Names and places

| Word in script | Say it like | Alias for TTS | Notes |
|---|---|---|---|
| NOAA | "NO-uh" (like the name Noah) | Noah | The agency itself says it as one word. Never spell out N-O-A-A. |
| NOAA's | "NO-uhz" | Noah's | |
| Bloop | "bloop" (rhymes with *loop*) | — | |
| Christopher Fox | as written | — | |
| Robert Dziak ⚠ | Undecided: "JAY-ak" (common anglicised reading) or "JAHK" (Polish spelling *dzia-* = "ja") | Jay-ack / Jahk | **Unverified.** We have not found a recording of how Dr. Dziak says his own name. Check a talk or interview by him (e.g. the AGU *Third Pod from the Sun* episode PMEL links to) before recording. Until then, the script can say "NOAA geophysicist Robert Dziak" once and "Dziak" at most once more. |
| Lovecraft | "LUV-kraft" | — | |
| Cthulhu ⚠ | "kuh-THOO-loo" | kuh-thoo-loo | A common modern reading. There is no single agreed pronunciation, so keep this one consistent throughout. |
| R'lyeh ⚠ | "RIL-yeh" | Rill-yeh | Variants exist (e.g. "ruh-LYE-eh"). Pick one and keep it. |
| Mermaids: The Body Found | as written | — | Title of a 2012 TV film; say it with a slight pause before "The Body Found". |
| Bransfield Strait | "BRANS-feeld strayt" | — | |
| Scotia Sea | "SKOH-shuh see" | Skosha Sea | |
| South Georgia | as written | — | The island in the South Atlantic, not the U.S. state. |
| Cape Adare ⚠ | "kayp uh-DAIR" | Cape uh-dare | |
| Ross Sea | as written | — | |
| French Polynesia | "French pol-ih-NEE-zhuh" | — | |
| Antarctica / Antarctic | "ant-ARK-tik-uh" (pronounce the first *c*) | — | Avoid "ant-AR-tik-uh". |
| Peninsula | "puh-NIN-syuh-luh" | — | |
| Pacific Marine Environmental Laboratory | "luh-BOR-uh-tor-ee" (British) or "LAB-ruh-tor-ee" (American) | — | Choose to match the voice's accent. |
| Slow Down / Julia | as written | — | Nicknames of two NOAA sounds; slight emphasis, as names. |
| megalodon | "MEG-uh-luh-don" | Meg-a-lo-don | |
| Loren Coleman | "LOR-en KOLE-man" | — | |
| cryptozoologist | "krip-toh-zoh-OL-uh-jist" | — | |
| humanoids | "HYOO-muh-noydz" | — | |
| Theory one … six | as written | — | Short beat after each "Theory one: …" title, like a chapter card. |

## Technical terms

| Word | Say it like | Notes |
|---|---|---|
| hydrophone(s) | "HY-druh-fone" | |
| icequake(s) | "ICE-quake" | One word, stress on *ice*. |
| spectrogram(s) | "SPEK-truh-gram" | |
| A53a ⚠ | "A fifty-three A" | Alias: `A fifty-three A`. Never "A five three A". |
| octaves | "OCK-tivs" | |
| decibels | "DESS-ih-bels" | |

## Numbers (write the alias exactly as below if the voice reads them wrongly)

| In the narration | Read as |
|---|---|
| 1944 | nineteen forty-four |
| 1996 / 1997 | nineteen ninety-six / nineteen ninety-seven |
| 2001, 2002, 2005, 2008, 2009, 2012 | two thousand one … two thousand twelve |
| 1928 | nineteen twenty-eight |
| 189 underwater decibels | one hundred and eighty-nine underwater decibels |
| "fifty degrees south and one hundred degrees west" | as written (already in words in the script) |
| "forty-seven degrees south, one hundred and twenty-six degrees west" | as written |

## Delivery notes

- Pace about 145 words per minute; slow to about 120 for the verdict (section 7) and for the slowed-down audio moment in section 2.
- Leave the `[pause]` (~0.8 s) and `[long pause]` (~1.5 s) marks from `narration.md` as real silence. In ElevenLabs, break the text at those marks or use break tags if the chosen model supports them.
- Evidence words carry the meaning, so do not swallow them: *suspected, consistent with, most likely, no evidence, never witnessed*.
- No dramatic "trailer voice". Curious, calm and precise.
