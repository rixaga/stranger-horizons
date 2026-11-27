"""Draw Shorts overlay elements (HUD, cards, pills, callouts, waveform...) over a plate frame.

Element types (see episodes/*/shorts/*/short.json): hud, big, card, pill, callout, meter, stamp,
tag, brand, credit, wave. Timing/opacity comes from shorts.element_alpha; elements also rise
24 px while they fade in.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .shorts import element_alpha, wave_envelope

REPO = Path(__file__).resolve().parents[2]
FONT_DIR = REPO / "assets" / "fonts" / "poppins"

AMBER = (255, 176, 32)
INK = (8, 16, 34)
PANEL = (10, 24, 48, 225)
WHITE = (240, 246, 252)
TEAL = (110, 220, 235)
RED = (255, 92, 72)
COLORS = {"amber": AMBER, "teal": TEAL, "red": RED, "white": WHITE}


@lru_cache(maxsize=64)
def _font(weight: str, size: int, folder: str):
    return ImageFont.truetype(str(Path(folder) / f"Poppins-{weight}.ttf"), size)


def _pill(dr, xy, text, f, fill, fg, pad=(22, 10), r=None):
    x, y = xy
    b = dr.textbbox((0, 0), text, font=f)
    w, h = b[2] - b[0] + 2 * pad[0], b[3] - b[1] + 2 * pad[1]
    dr.rounded_rectangle([x, y, x + w, y + h], radius=r if r is not None else h // 2, fill=fill)
    dr.text((x + pad[0] - b[0], y + pad[1] - b[1]), text, font=f, fill=fg)
    return w, h


def _draw(el, dr, size, t, frame, tracks, F, ctx):
    W, H = size
    kind = el["type"]
    if kind == "hud":
        dr.rectangle([0, 0, W, 150], fill=(4, 10, 24, 170))
        _pill(dr, (36, 48), el["speed"], F("Bold", 34), AMBER, INK)
        for i in range(14):  # level meter that breathes with time
            lvl = 0.55 + 0.45 * math.sin(t * 5.0 + i * 0.5)
            x, hgt = 330 + i * 22, int((14 + i * 3) * (0.6 + 0.4 * lvl))
            dr.rectangle([x, 100 - hgt, x + 12, 100], fill=AMBER if i < 10 else (70, 90, 120))
        dr.rectangle([680, 42, 1044, 108], fill=PANEL, outline=TEAL, width=3)
        dr.text((700, 50), "REAL PITCH", font=F("Medium", 22), fill=TEAL)
        dr.text((700, 70), el["pitch"], font=F("Bold", 30), fill=WHITE)
    elif kind == "big":
        dr.text((W // 2, el.get("y", H // 2)), el["text"], font=F("Bold", el.get("size", 64)),
                fill=COLORS.get(el.get("color", "white"), WHITE), anchor="mm",
                stroke_width=3, stroke_fill=(4, 10, 24))
    elif kind == "card":
        dr.rectangle([60, 200, 1020, 300], fill=PANEL, outline=AMBER, width=4)
        dr.ellipse([30, 212, 106, 288], fill=AMBER)
        dr.text((68, 250), str(el["num"]), font=F("Bold", 44), fill=INK, anchor="mm")
        dr.text((560, 250), el["text"], font=F("Bold", 46), fill=WHITE, anchor="mm")
    elif kind == "pill":
        f = F("Bold", el.get("size", 30))
        tw = dr.textbbox((0, 0), el["text"], font=f)[2]
        color = COLORS.get(el.get("color", "red"), RED)
        _pill(dr, ((W - tw - 44) // 2, el.get("y", 318)), el["text"], f, color,
              INK if color in (TEAL, AMBER) else WHITE, r=8)
    elif kind == "callout":
        pts = tracks.get(el["track"], {})
        anchor = pts.get(str(frame + 1))
        if not anchor or not (0 <= anchor[0] <= W and 0 <= anchor[1] <= H):
            return
        bx, by = el["box"]
        f1, f2 = F("Bold", 40), F("Medium", 24)
        tb = dr.textbbox((0, 0), el["title"], font=f1)
        sub = el.get("sub")
        w = max(tb[2] - tb[0], dr.textbbox((0, 0), sub, font=f2)[2] if sub else 0) + 36
        h = (tb[3] - tb[1]) + (44 if sub else 0) + 30
        ax, ay = anchor
        mid_y = by + h // 2
        edge_x = bx + w if ax > bx + w else (bx if ax < bx else bx + w // 2)
        dr.line([(ax, ay), (ax, mid_y), (edge_x, mid_y)], fill=AMBER, width=4)
        dr.ellipse([ax - 9, ay - 9, ax + 9, ay + 9], outline=AMBER, width=4)
        dr.rectangle([bx, by, bx + w, by + h], fill=PANEL, outline=AMBER, width=3)
        dr.text((bx + 18, by + 14 - tb[1]), el["title"], font=f1, fill=WHITE)
        if sub:
            dr.text((bx + 18, by + 14 + (tb[3] - tb[1]) + 12), sub, font=f2, fill=TEAL)
    elif kind == "meter":
        y = el.get("y", 1560)
        dr.rectangle([60, y, 1020, y + 120], fill=PANEL, outline=TEAL, width=3)
        dr.text((84, y + 14), el["label"], font=F("Medium", 26), fill=TEAL)
        dr.text((84, y + 50), el["value"], font=F("Bold", 46), fill=WHITE)
        fill = min(1.0, max(0.0, (t - el.get("in_s", 0)) / 1.2))
        dr.rectangle([760, y + 70, 760 + int(230 * fill), y + 92], fill=AMBER)
        dr.rectangle([760, y + 70, 990, y + 92], outline=(120, 140, 170), width=2)
    elif kind == "stamp":
        f = F("Bold", 84)
        tw, th = dr.textbbox((0, 0), el["text"], font=f)[2:]
        stamp = Image.new("RGBA", (tw + 80, th + 60), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stamp)
        sd.rectangle([6, 6, tw + 74, th + 54], outline=RED, width=10)
        sd.text((40, 22), el["text"], font=f, fill=RED)
        stamp = stamp.rotate(-12, expand=True, resample=Image.BICUBIC)
        ctx["paste"] = (stamp, ((W - stamp.width) // 2, el.get("y", 760)))
    elif kind == "tag":
        _pill(dr, (60, 1640), el["text"], F("Bold", 30), (255, 255, 255, 235), RED, r=8)
    elif kind == "brand":
        dr.text((W // 2, el.get("y", 1840)), el["text"], font=F("Bold", 34), fill=(200, 215, 235), anchor="mm")
    elif kind == "credit":
        dr.text((W // 2, el.get("y", 1880)), el["text"], font=F("Medium", 24), fill=(170, 190, 215), anchor="mm")
    elif kind == "wave":
        env = ctx["env"](el)
        x0, x1, yc, amp = 70, 1010, el.get("y", 960), el.get("amp", 300)
        shown = min(1.0, max(0.0, (t - el.get("in_s", 0)) / el["dur_s"]))
        n = len(env)
        bw = (x1 - x0) / n
        for i, v in enumerate(env):
            x = x0 + i * bw
            played = i / n <= shown
            col = AMBER if played else (60, 80, 110)
            hh = max(2, v * amp)
            dr.rectangle([x, yc - hh, x + max(1, bw - 1), yc + hh], fill=col)
        px = x0 + shown * (x1 - x0)
        dr.line([(px, yc - amp - 30), (px, yc + amp + 30)], fill=WHITE, width=4)
        dr.text((x0, yc + amp + 50), "REAL RECORDING · NOAA", font=F("Bold", 30), fill=TEAL)
        dr.text((x1, yc + amp + 50), el.get("speed_label", "PLAYED 16x FASTER"), font=F("Medium", 26),
                fill=(170, 190, 215), anchor="ra")


def render_frame(plate: Image.Image, shot: dict, t: float, tracks: dict, frame: int,
                 fonts: Path | None = None, base_dir: Path | None = None) -> Image.Image:
    """Composite every visible element of `shot` at time t (s) over the plate."""
    folder = str(fonts or FONT_DIR)
    F = lambda w, s: _font(w, s, folder)  # noqa: E731
    out = plate.convert("RGBA")
    envs = {}

    def env(el):
        key = (el["file"], el["from_s"], el["dur_s"])
        if key not in envs:
            envs[key] = wave_envelope((base_dir or Path(".")) / el["file"], el["from_s"], el["dur_s"], bins=180)
        return envs[key]

    for el in shot.get("elements", []):
        a = element_alpha(el, t, shot["duration_s"])
        if a <= 0:
            continue
        layer = Image.new("RGBA", out.size, (0, 0, 0, 0))
        ctx = {"env": env}
        _draw(el, ImageDraw.Draw(layer), out.size, t, frame, tracks, F, ctx)
        if "paste" in ctx:
            img, pos = ctx["paste"]
            scale = 1.0 + 0.6 * (1 - a)  # stamp slams down
            if scale != 1.0:
                img = img.resize((int(img.width * scale), int(img.height * scale)))
                pos = (pos[0] - (img.width - ctx["paste"][0].width) // 2, pos[1] - (img.height - ctx["paste"][0].height) // 2)
            layer.alpha_composite(img, (max(0, pos[0]), max(0, pos[1])))
        if a < 1:
            alpha = layer.getchannel("A").point(lambda v: int(v * a))
            layer.putalpha(alpha)
            dy = int((1 - a) * 24)
            if dy and el["type"] not in ("callout", "stamp", "hud"):
                shifted = Image.new("RGBA", layer.size, (0, 0, 0, 0))
                shifted.paste(layer, (0, dy))
                layer = shifted
        out = Image.alpha_composite(out, layer)
    return out.convert("RGB")
