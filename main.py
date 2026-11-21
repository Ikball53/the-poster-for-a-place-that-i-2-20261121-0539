#!/usr/bin/env python3
"""SORVANE — a travel poster for a place that does not exist.

Draws one deterministic poster: a spiral beacon rising from a ringed
lagoon at golden hour. Only text in the picture is the invented name.
"""
import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

PLACE_NAME = "SORVANE"
CANVAS_W = 1024
CANVAS_H = 1024
SEED = 20261121

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def pick_font(size):
    for candidate in FONT_CANDIDATES:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def blend(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def vertical_gradient(size, stops):
    """stops: list of (y_fraction, rgb). Returns RGB image."""
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        f = y / max(1, h - 1)
        # find surrounding stops
        lo = stops[0]
        hi = stops[-1]
        for i in range(len(stops) - 1):
            if stops[i][0] <= f <= stops[i + 1][0]:
                lo, hi = stops[i], stops[i + 1]
                break
        span = max(1e-6, hi[0] - lo[0])
        t = min(1.0, max(0.0, (f - lo[0]) / span))
        px[0, y] = blend(lo[1], hi[1], t)
    return img.resize((w, h))


def draw_poster():
    rng = random.Random(SEED)
    horizon_y = int(CANVAS_H * 0.62)

    # --- sky + sea base ---
    sky = vertical_gradient(
        (CANVAS_W, horizon_y),
        [
            (0.0, (24, 32, 78)),
            (0.35, (72, 62, 128)),
            (0.68, (214, 110, 92)),
            (1.0, (250, 186, 110)),
        ],
    )
    sea_h = CANVAS_H - horizon_y
    sea = vertical_gradient(
        (CANVAS_W, sea_h),
        [
            (0.0, (250, 186, 110)),
            (0.12, (84, 120, 148)),
            (0.45, (28, 74, 110)),
            (1.0, (10, 34, 64)),
        ],
    )
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H))
    canvas.paste(sky, (0, 0))
    canvas.paste(sea, (0, horizon_y))

    # --- sun glow (soft radial disc behind the beacon) ---
    glow = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    sun_cx, sun_cy, sun_r = CANVAS_W // 2, horizon_y - 90, 210
    for r in range(sun_r, 0, -6):
        alpha = int(10 + 90 * (1 - r / sun_r))
        gdraw.ellipse(
            [sun_cx - r, sun_cy - r, sun_cx + r, sun_cy + r],
            fill=(255, 196, 120, alpha),
        )
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), glow)

    draw = ImageDraw.Draw(canvas, "RGBA")

    # solid sun disc
    draw.ellipse(
        [sun_cx - 92, sun_cy - 92, sun_cx + 92, sun_cy + 92],
        fill=(255, 226, 160, 255),
    )

    # --- fading stars in the upper sky ---
    for _ in range(90):
        x = rng.randint(10, CANVAS_W - 10)
        y = rng.randint(8, int(horizon_y * 0.42))
        fade = 1.0 - y / (horizon_y * 0.42)
        a = int(40 + 150 * fade * rng.random())
        r = rng.choice([1, 1, 2])
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 244, 214, a))

    # --- thin cloud bands ---
    for i, (cy, cw, ch, col, alpha) in enumerate([
        (horizon_y - 300, 620, 26, (255, 170, 140), 70),
        (horizon_y - 238, 760, 20, (255, 196, 150), 60),
        (horizon_y - 168, 540, 16, (255, 214, 170), 55),
        (horizon_y - 120, 820, 14, (255, 226, 186), 50),
    ]):
        x0 = (CANVAS_W - cw) // 2 + (30 if i % 2 else -30)
        draw.rounded_rectangle([x0, cy, x0 + cw, cy + ch], radius=ch // 2, fill=col + (alpha,))

    # --- distant headlands (silhouettes framing the lagoon) ---
    draw.polygon(
        [(0, horizon_y + 6), (0, horizon_y - 46), (150, horizon_y - 58),
         (300, horizon_y - 18), (340, horizon_y + 6)],
        fill=(38, 44, 86, 255),
    )
    draw.polygon(
        [(CANVAS_W, horizon_y + 6), (CANVAS_W, horizon_y - 52),
         (880, horizon_y - 66), (740, horizon_y - 22), (700, horizon_y + 6)],
        fill=(38, 44, 86, 255),
    )

    # --- sea sparkle + sun path ---
    for _ in range(260):
        y = rng.randint(horizon_y + 8, CANVAS_H - 90)
        spread = 40 + (y - horizon_y) * 0.55
        x = int(sun_cx + rng.gauss(0, spread * 0.45))
        if 6 < x < CANVAS_W - 6:
            ln = rng.randint(6, 26)
            a = rng.randint(50, 150)
            draw.line([x - ln // 2, y, x + ln // 2, y], fill=(255, 214, 150, a), width=2)
    for _ in range(140):
        x = rng.randint(8, CANVAS_W - 8)
        y = rng.randint(horizon_y + 10, CANVAS_H - 80)
        ln = rng.randint(8, 30)
        draw.line([x, y, x + ln, y], fill=(170, 210, 235, rng.randint(30, 90)), width=2)

    # --- lagoon island: concentric rings ---
    isl_cx, isl_cy = CANVAS_W // 2, horizon_y + 118
    for rx, ry, col in [
        (330, 74, (16, 52, 84, 255)),
        (282, 60, (22, 68, 100, 255)),
        (232, 48, (32, 88, 118, 255)),
        (186, 38, (46, 112, 136, 255)),
    ]:
        draw.ellipse([isl_cx - rx, isl_cy - ry, isl_cx + rx, isl_cy + ry], fill=col)
    # sandy rim where the tower stands
    draw.ellipse(
        [isl_cx - 150, isl_cy - 30, isl_cx + 150, isl_cy + 30],
        fill=(238, 198, 140, 255),
    )
    draw.ellipse(
        [isl_cx - 118, isl_cy - 22, isl_cx + 118, isl_cy + 22],
        fill=(246, 214, 160, 255),
    )

    # --- THE LANDMARK: the Spiral Beacon ---
    base_y = isl_cy - 8
    top_y = horizon_y - 330
    base_half = 62
    top_half = 26
    # tower body (tapered)
    draw.polygon(
        [(isl_cx - base_half, base_y), (isl_cx + base_half, base_y),
         (isl_cx + top_half, top_y), (isl_cx - top_half, top_y)],
        fill=(248, 240, 222, 255),
    )
    # spiral bands wrapping the tower (clipped look via taper math)
    steps = 26
    for s in range(steps):
        t0 = s / steps
        t1 = (s + 0.55) / steps
        y0 = base_y + (top_y - base_y) * t0
        y1 = base_y + (top_y - base_y) * t1
        hw0 = base_half + (top_half - base_half) * t0
        hw1 = base_half + (top_half - base_half) * t1
        # band sweeps diagonally to read as a spiral
        skew = 14 * math.sin(t0 * math.pi * 2.2)
        col = (196, 64, 58, 255) if s % 2 == 0 else (30, 58, 96, 255)
        draw.polygon(
            [(isl_cx - hw0, y0 + skew), (isl_cx + hw0, y0 - skew),
             (isl_cx + hw1, y1 - skew), (isl_cx - hw1, y1 + skew)],
            fill=col,
        )
    # gallery + lamp room
    draw.rectangle([isl_cx - 40, top_y - 16, isl_cx + 40, top_y + 6], fill=(24, 34, 64, 255))
    draw.rectangle([isl_cx - 24, top_y - 52, isl_cx + 24, top_y - 14], fill=(255, 214, 120, 255))
    draw.polygon(
        [(isl_cx - 34, top_y - 50), (isl_cx + 34, top_y - 50), (isl_cx, top_y - 88)],
        fill=(24, 34, 64, 255),
    )
    # light beams
    beam = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(beam)
    lamp_y = top_y - 32
    bdraw.polygon([(isl_cx, lamp_y), (60, lamp_y - 66), (60, lamp_y + 40)], fill=(255, 230, 160, 70))
    bdraw.polygon([(isl_cx, lamp_y), (CANVAS_W - 60, lamp_y - 66), (CANVAS_W - 60, lamp_y + 40)], fill=(255, 230, 160, 70))
    beam = beam.filter(ImageFilter.GaussianBlur(10))
    canvas = Image.alpha_composite(canvas, beam)
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.ellipse([isl_cx - 10, lamp_y - 10, isl_cx + 10, lamp_y + 10], fill=(255, 246, 200, 255))

    # small sailboats for scale (simple silhouettes)
    for bx, by, s in [(250, horizon_y + 150, 1.0), (790, horizon_y + 205, 0.75)]:
        draw.polygon([(bx, by), (bx, by - 44 * s), (bx + 30 * s, by)], fill=(255, 244, 220, 235))
        draw.polygon([(bx - 4 * s, by), (bx - 4 * s, by - 34 * s), (bx - 24 * s, by)], fill=(214, 110, 92, 235))
        draw.polygon([(bx - 26 * s, by + 2), (bx + 30 * s, by + 2), (bx + 20 * s, by + 12 * s), (bx - 16 * s, by + 12 * s)], fill=(24, 34, 64, 255))

    # shimmering reflection of the beacon in the lagoon water
    refl_top = isl_cy + 34
    for i in range(46):
        ry = refl_top + i * 5
        if ry > CANVAS_H - 70:
            break
        wob = int(10 * math.sin(i * 0.55))
        half = max(8, 46 - i)
        col = (196, 64, 58) if (i // 3) % 2 == 0 else (248, 240, 222)
        alpha = max(24, 130 - i * 2)
        draw.line(
            [isl_cx - half + wob, ry, isl_cx + half + wob, ry],
            fill=col + (alpha,),
            width=3,
        )
    # lamp glow reflected as a bright pool under the island
    draw.ellipse(
        [isl_cx - 70, isl_cy + 26, isl_cx + 70, isl_cy + 58],
        fill=(255, 214, 130, 70),
    )

    # birds
    for bx, by, s in [(180, 300, 1.0), (228, 322, 0.7), (820, 268, 0.9), (864, 292, 0.65)]:
        draw.arc([bx - 16 * s, by - 8 * s, bx, by + 8 * s], start=200, end=330, fill=(24, 30, 60, 220), width=3)
        draw.arc([bx, by - 8 * s, bx + 16 * s, by + 8 * s], start=210, end=340, fill=(24, 30, 60, 220), width=3)

    # --- foreground framing rocks (bottom corners lead the eye in) ---
    draw.polygon([(0, CANVAS_H), (0, CANVAS_H - 120), (120, CANVAS_H - 150), (240, CANVAS_H - 70), (300, CANVAS_H)], fill=(12, 22, 48, 255))
    draw.polygon([(CANVAS_W, CANVAS_H), (CANVAS_W, CANVAS_H - 132), (900, CANVAS_H - 158), (790, CANVAS_H - 76), (730, CANVAS_H)], fill=(12, 22, 48, 255))

    # --- the NAME, set into the sky as integral type ---
    font = pick_font(118)
    # letter-spaced rendering, centred
    spacing = 14
    widths = []
    for ch in PLACE_NAME:
        bbox = draw.textbbox((0, 0), ch, font=font)
        widths.append(bbox[2] - bbox[0])
    total_w = sum(widths) + spacing * (len(PLACE_NAME) - 1)
    x = (CANVAS_W - total_w) // 2
    y = 64
    for ch, wch in zip(PLACE_NAME, widths):
        draw.text((x + 4, y + 5), ch, font=font, fill=(18, 22, 52, 200))
        draw.text((x, y), ch, font=font, fill=(255, 240, 206, 255))
        x += wch + spacing
    # slim rule under the name (graphic element, not copy)
    rule_y = y + 150
    draw.line([(CANVAS_W // 2 - 210, rule_y), (CANVAS_W // 2 + 210, rule_y)], fill=(255, 240, 206, 190), width=3)
    draw.ellipse([CANVAS_W // 2 - 6, rule_y - 6, CANVAS_W // 2 + 6, rule_y + 6], fill=(255, 240, 206, 230))

    # --- poster border ---
    draw.rectangle([22, 22, CANVAS_W - 22, CANVAS_H - 22], outline=(255, 240, 206, 210), width=4)
    draw.rectangle([36, 36, CANVAS_W - 36, CANVAS_H - 36], outline=(255, 240, 206, 110), width=2)

    # --- gentle grain for a printed-poster feel ---
    grain = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    gpx = grain.load()
    for _ in range(9000):
        gx = rng.randint(0, CANVAS_W - 1)
        gy = rng.randint(0, CANVAS_H - 1)
        v = rng.randint(0, 255)
        gpx[gx, gy] = (v, v, v, rng.randint(6, 20))
    canvas = Image.alpha_composite(canvas, grain)

    return canvas.convert("RGB")


def main():
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    poster = draw_poster()
    poster.save(out_dir / "entry.png", format="PNG", optimize=True)


if __name__ == "__main__":
    main()
