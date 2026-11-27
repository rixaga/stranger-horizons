"""Draw the Shorts HUD / question card / callouts over the toon 3D render (vertical 1080x1920).

    python3 make_overlay.py IN.png OUT.png [--font-dir DIR]

Every factual string carries the claim it rests on (see research/claim_ledger.json).
Fonts: Poppins (SIL Open Font License); pass --font-dir if it is not in the default location.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AMBER = (255, 176, 32)
INK = (8, 16, 34)
PANEL = (10, 24, 48, 225)
WHITE = (240, 246, 252)
TEAL = (110, 220, 235)
RED = (255, 92, 72)

# text -> claim ids it depends on (empty = design / label, not a factual claim)
TEXT = {
    "speed": ("16x FASTER", ["C47"]),          # NOAA's public Bloop file is sped up 16x
    "pitch": ("9–28 Hz", ["C47"]),             # main sweep at true speed (our analysis of NOAA's file)
    "where": ("1997 · PACIFIC", ["C01"]),
    "q": ("WHAT MADE THIS SOUND?", []),
    "theory": ("THEORY: A GIANT SHARK?", ["C48"]),
    "shark": ("MEGALODON", ["C48"]),
    "shark_sub": ("gone from the fossil record ~2.6 million yrs ago", ["C49"]),
    "rov": ("ROV · 2.8 m", []),               # our own model's size, used as a scale cue
    "tag": ("IMAGINED — NOT EVIDENCE", []),
    "brand": ("STRANGER HORIZONS", []),
}


def font(d: Path, weight: str, size: int):
    return ImageFont.truetype(str(d / f"Poppins-{weight}.ttf"), size)


def pill(dr, xy, text, f, fill, fg, pad=(22, 10), r=None):
    x, y = xy
    b = dr.textbbox((0, 0), text, font=f)
    w, h = b[2] - b[0] + 2 * pad[0], b[3] - b[1] + 2 * pad[1]
    dr.rounded_rectangle([x, y, x + w, y + h], radius=r or h // 2, fill=fill)
    dr.text((x + pad[0] - b[0], y + pad[1] - b[1]), text, font=f, fill=fg)
    return x + w, y + h


def callout(dr, anchor, box_xy, title, sub, f1, f2):
    bx, by = box_xy
    tb = dr.textbbox((0, 0), title, font=f1)
    w = max(tb[2] - tb[0], dr.textbbox((0, 0), sub, font=f2)[2] if sub else 0) + 36
    h = (tb[3] - tb[1]) + (44 if sub else 0) + 30
    ax, ay = anchor
    elbow = (ax, by + h // 2) if abs(ax - bx) > abs(ay - by) else (bx + w // 2, ay)
    for seg in ((anchor, elbow), (elbow, (bx + (w if elbow[0] > bx + w else 0), by + h // 2))):
        dr.line([seg[0], seg[1]], fill=AMBER, width=4)
    dr.ellipse([ax - 9, ay - 9, ax + 9, ay + 9], outline=AMBER, width=4)
    dr.rectangle([bx, by, bx + w, by + h], fill=PANEL, outline=AMBER, width=3)
    dr.text((bx + 18, by + 14 - tb[1]), title, font=f1, fill=WHITE)
    if sub:
        dr.text((bx + 18, by + 14 + (tb[3] - tb[1]) + 12), sub, font=f2, fill=TEAL)


def render(inp: Path, out: Path, fonts: Path):
    img = Image.open(inp).convert("RGBA").resize((1080, 1920))
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(lay)
    fb = lambda s: font(fonts, "Bold", s)  # noqa: E731
    fm = lambda s: font(fonts, "Medium", s)  # noqa: E731

    # HUD strip: playback speed badge, a level meter, and the real pitch readout
    dr.rectangle([0, 0, 1080, 150], fill=(4, 10, 24, 170))
    pill(dr, (36, 48), TEXT["speed"][0], fb(34), AMBER, INK)
    for i in range(14):  # meter: rising bars, like a sweep climbing in pitch
        x = 330 + i * 22
        hgt = 14 + i * 3
        dr.rectangle([x, 100 - hgt, x + 12, 100], fill=AMBER if i < 10 else (70, 90, 120))
    dr.rectangle([680, 42, 1044, 108], fill=PANEL, outline=TEAL, width=3)
    dr.text((700, 50), "REAL PITCH", font=fm(22), fill=TEAL)
    dr.text((700, 70), TEXT["pitch"][0], font=fb(30), fill=WHITE)
    dr.text((36, 112), TEXT["where"][0], font=fm(24), fill=(170, 190, 215))

    # numbered question card + answer pill
    dr.rectangle([60, 200, 1020, 300], fill=PANEL, outline=AMBER, width=4)
    dr.ellipse([30, 212, 106, 288], fill=AMBER)
    dr.text((68, 250), "1", font=fb(44), fill=INK, anchor="mm")
    dr.text((560, 250), TEXT["q"][0], font=fb(46), fill=WHITE, anchor="mm")
    t = TEXT["theory"][0]
    tw = dr.textbbox((0, 0), t, font=fb(30))[2]
    pill(dr, ((1080 - tw - 44) // 2, 318), t, fb(30), RED, WHITE, r=8)

    # callouts
    callout(dr, (430, 830), (60, 1010), TEXT["shark"][0], TEXT["shark_sub"][0], fb(40), fm(24))
    callout(dr, (930, 1280), (520, 1440), TEXT["rov"][0], None, fb(36), fm(24))

    # editorial tag + brand
    pill(dr, (60, 1640), TEXT["tag"][0], fb(30), (255, 255, 255, 235), RED, r=8)
    dr.text((540, 1840), TEXT["brand"][0], font=fb(28), fill=(200, 215, 235), anchor="mm")

    Image.alpha_composite(img, lay).convert("RGB").save(out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("inp", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--font-dir", type=Path, default=Path("/usr/share/fonts/truetype/google-fonts"))
    a = ap.parse_args()
    print(render(a.inp, a.out, a.font_dir))
