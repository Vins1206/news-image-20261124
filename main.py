#!/usr/bin/env python3
"""news-image-20261124 -- The World in One Picture: Tuesday 24 November 2026.

A pure-stdlib Python program (no Pillow, no numpy, no network) that draws a
1024x1024 newspaper front page summarising the day's world news and writes it
to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

Stories (all reported 22-24 Nov 2026, verified against live news sources):
  1. LEAD: Ukraine sinks the Russian corvette Merkury off Benghazi, Libya,
     with seven sea drones (22 Nov, confirmed 23 Nov); a Ka-27 helicopter
     aboard was destroyed and the cargo ship Angara was hit.
  2. COP31 collapses in Antalya, Turkey (22 Nov): no climate deal, the final
     text never mentions fossil fuels, ~90 nations walk out.
  3. Nvidia reinstates Jensen Huang as CEO (23 Nov) after direct
     intervention by President Trump; shares jump 33%.

Every pixel is drawn by this program: gradients, shapes, the warship, the
cracked earth, the chip, and all text through a hand-built 5x7 bitmap font.
The output is fully deterministic: same bytes on every run.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- canvas

buf = bytearray(W * H * 3)


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def fill_rect(x0, y0, x1, y1, c):
    """Fill [x0,x1) x [y0,y1) with RGB tuple c. Fast slice assignment."""
    x0 = _clamp(x0, 0, W)
    x1 = _clamp(x1, 0, W)
    y0 = _clamp(y0, 0, H)
    y1 = _clamp(y1, 0, H)
    if x0 >= x1 or y0 >= y1:
        return
    row = bytes(c) * (x1 - x0)
    for y in range(y0, y1):
        o = (y * W + x0) * 3
        buf[o:o + len(row)] = row


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        o = (y * W + x) * 3
        buf[o] = c[0]
        buf[o + 1] = c[1]
        buf[o + 2] = c[2]


def _lerp(a, b, t):
    return int(a + (b - a) * t + 0.5)


def vgrad(x0, y0, x1, y1, c0, c1):
    """Vertical gradient fill."""
    n = max(1, y1 - y0)
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.0
        c = (_lerp(c0[0], c1[0], t), _lerp(c0[1], c1[1], t),
             _lerp(c0[2], c1[2], t))
        fill_rect(x0, y0 + i, x1, y0 + i + 1, c)


def hline(x0, x1, y, c, w=1):
    fill_rect(x0, y, x1, y + w, c)


def vline(x, y0, y1, c, w=1):
    fill_rect(x, y0, x + w, y1, c)


def line(x0, y0, x1, y1, c):
    """Bresenham line."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def thick_line(x0, y0, x1, y1, c, w=3):
    for k in range(-w // 2, w // 2 + 1):
        line(x0 + k, y0, x1 + k, y1, c)
        line(x0, y0 + k, x1, y1 + k, c)


def circle(cx, cy, r, c):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)


def ellipse(cx, cy, rx, ry, c):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy * dy) / float(ry * ry)
        dx = int(rx * (t ** 0.5)) if t > 0 else 0
        fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)


def poly(points, c):
    """Even-odd scanline polygon fill."""
    ys = [p[1] for p in points]
    y0, y1 = max(0, min(ys)), min(H, max(ys) + 1)
    n = len(points)
    for y in range(y0, y1):
        xs = []
        for i in range(n):
            x_a, y_a = points[i]
            x_b, y_b = points[(i + 1) % n]
            if (y_a <= y < y_b) or (y_b <= y < y_a):
                t = (y - y_a) / float(y_b - y_a)
                xs.append(x_a + t * (x_b - x_a))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            fill_rect(int(xs[k]), y, int(xs[k + 1]) + 1, y + 1, c)


# ---------------------------------------------------------------- 5x7 font

# Each glyph: 7 rows of 5 cells, '#' = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
}

_BLANK = ("00000",) * 7


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(text, x, y, scale, c, align="left", cx=None):
    """Draw uppercase text. align 'center' centres on cx."""
    text = text.upper()
    if align == "center" and cx is not None:
        x = cx - text_width(text, scale) // 2
    for ch in text:
        g = FONT.get(ch, _BLANK)
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == "1":
                    fill_rect(x + col * scale, y + row * scale,
                              x + (col + 1) * scale, y + (row + 1) * scale, c)
        x += 6 * scale


# ---------------------------------------------------------------- palette

NAVY = (16, 38, 63)
NAVY_DARK = (13, 27, 42)
GOLD = (232, 199, 102)
GOLD_DARK = (201, 162, 39)
CREAM = (247, 242, 230)
INK = (24, 32, 40)
WHITE = (255, 255, 255)
SEA_TOP = (22, 72, 110)
SEA_BOT = (14, 47, 77)
SKY_TOP = (59, 90, 125)
SKY_BOT = (233, 165, 88)
HULL = (91, 102, 115)
HULL_DARK = (61, 69, 79)
FIRE_O = (245, 130, 31)
FIRE_Y = (255, 201, 60)
FIRE_R = (214, 60, 20)
SMOKE = (46, 46, 46)
SMOKE2 = (68, 68, 68)
GREEN = (118, 185, 0)
GREEN_LT = (139, 224, 74)
CHIP_BG = (10, 46, 28)

# ---------------------------------------------------------------- scenes


def draw_masthead():
    fill_rect(0, 0, W, 112, NAVY)
    draw_text("THE WORLD", 0, 14, 7, WHITE, align="center", cx=W // 2)
    draw_text("TUESDAY 24 NOVEMBER 2026", 0, 74, 3, GOLD,
              align="center", cx=W // 2)
    hline(0, W, 110, GOLD_DARK, 2)


def draw_hero():
    # Dusk sky over Benghazi harbour.
    vgrad(0, 112, W, 332, SKY_TOP, SKY_BOT)
    circle(838, 296, 46, (242, 192, 120))
    circle(838, 296, 32, (247, 220, 154))
    # Port silhouette on the horizon.
    fill_rect(40, 296, 120, 332, (28, 39, 51))
    fill_rect(140, 282, 210, 332, (28, 39, 51))
    fill_rect(230, 306, 300, 332, (28, 39, 51))
    # Crane silhouettes.
    vline(170, 238, 332, (28, 39, 51), 5)
    hline(150, 235, 244, (28, 39, 51), 5)
    vline(262, 258, 332, (28, 39, 51), 5)
    hline(240, 320, 264, (28, 39, 51), 5)
    # Sea.
    vgrad(0, 332, W, 556, SEA_TOP, SEA_BOT)
    for yy in range(344, 552, 16):
        for xx in range(0, W, 64):
            ph = (xx // 64 + yy // 16) % 2
            hline(xx + ph * 22, xx + ph * 22 + 30, yy, (43, 106, 150), 2)
    # Capsized corvette: bow up at right, stern sinking at left.
    hull = [(296, 482), (326, 442), (592, 396), (718, 384),
            (704, 424), (648, 468), (540, 494), (380, 502)]
    poly(hull, HULL)
    poly([(326, 442), (592, 396), (718, 384), (664, 424), (360, 470)],
         HULL_DARK)
    # Deck stripe and mast, tilted with the hull.
    thick_line(326, 450, 700, 398, (200, 208, 216), 3)
    line(540, 404, 496, 322, (200, 208, 216))
    line(496, 322, 524, 330, (200, 208, 216))
    poly([(496, 322), (522, 328), (496, 336)], FIRE_R)
    # Funnel, listing.
    poly([(566, 400), (604, 396), (596, 368), (562, 372)], (38, 44, 52))
    # Flame tongues, then the fireball mid-ship.
    poly([(430, 396), (448, 356), (462, 394)], FIRE_O)
    poly([(470, 392), (486, 350), (500, 392)], FIRE_Y)
    poly([(500, 394), (516, 362), (528, 396)], FIRE_O)
    ellipse(470, 408, 66, 40, FIRE_R)
    ellipse(470, 404, 50, 30, FIRE_O)
    ellipse(470, 400, 32, 20, FIRE_Y)
    ellipse(440, 392, 18, 26, FIRE_O)
    ellipse(500, 390, 16, 22, FIRE_O)
    # Smoke plume drifting up and to the left with the wind.
    circle(458, 352, 22, SMOKE)
    circle(436, 318, 30, SMOKE2)
    circle(404, 284, 26, SMOKE)
    circle(372, 248, 38, SMOKE2)
    circle(330, 214, 30, SMOKE)
    circle(292, 182, 42, (88, 88, 88))
    circle(246, 158, 34, SMOKE2)
    circle(420, 330, 16, SMOKE)
    circle(486, 344, 14, SMOKE2)
    # Foreground water below the hull, with foam.
    fill_rect(0, 508, W, 556, (18, 63, 99))
    for xx in range(0, W, 48):
        hline(xx, xx + 26, 508, (220, 235, 240), 2)
    # Sea drones closing in: small dark boats with white wakes.
    for (dx, dy, s) in ((238, 522, 1), (760, 516, 1), (856, 528, 1)):
        poly([(dx, dy), (dx + 34 * s, dy - 6), (dx + 40 * s, dy),
              (dx + 34 * s, dy + 6)], (26, 26, 26))
        line(dx - 46, dy + 8, dx - 4, dy + 2, WHITE)
        line(dx - 46, dy + 12, dx - 4, dy + 6, WHITE)
        fill_rect(dx + 8, dy - 12, dx + 12, dy - 6, (26, 26, 26))


def draw_headline_band():
    fill_rect(0, 556, W, 700, NAVY_DARK)
    hline(0, W, 556, GOLD_DARK, 3)
    draw_text("UKRAINE SINKS RUSSIAN", 0, 568, 5, WHITE,
              align="center", cx=W // 2)
    draw_text("WARSHIP OFF LIBYA", 0, 608, 5, WHITE,
              align="center", cx=W // 2)
    draw_text("SEA DRONES HIT CORVETTE MERKURY AT BENGHAZI", 0, 652, 2,
              GOLD, align="center", cx=W // 2)
    draw_text("7 DRONES - KA-27 HELICOPTER LOST - ANGARA HIT", 0, 674, 2,
              (200, 210, 218), align="center", cx=W // 2)


def draw_chair(x, y, c, tipped=False):
    if tipped:  # fallen on its side: back flat on the floor, seat upright
        fill_rect(x, y + 22, x + 30, y + 28, c)
        fill_rect(x + 22, y + 8, x + 28, y + 28, c)
        fill_rect(x + 2, y + 28, x + 30, y + 31, c)
        return
    fill_rect(x, y, x + 16, y + 20, c)          # back
    fill_rect(x - 2, y + 20, x + 18, y + 26, c)  # seat
    fill_rect(x, y + 26, x + 3, y + 34, c)      # legs
    fill_rect(x + 13, y + 26, x + 16, y + 34, c)


def draw_cop_panel():
    x0, x1 = 12, 506
    fill_rect(x0, 700, x1, 950, CREAM)
    for k in range(3):
        fill_rect(x0 + k, 700 + k, x1 - k, 701 + k, NAVY)
    # Dry sky and cracked earth.
    vgrad(x0 + 4, 704, x1 - 4, 792, (246, 217, 160), (232, 185, 106))
    circle(452, 742, 24, (224, 123, 42))
    circle(452, 742, 16, (240, 160, 60))
    fill_rect(x0 + 4, 792, x1 - 4, 830, (160, 106, 46))
    fill_rect(x0 + 4, 792, x1 - 4, 798, (140, 90, 38))
    # Cracks in the earth.
    for (ax, ay, bx, by) in ((120, 798, 150, 814), (150, 814, 138, 828),
                            (150, 814, 178, 826), (300, 798, 320, 816),
                            (320, 816, 306, 829), (420, 798, 440, 812)):
        thick_line(ax, ay, bx, by, (95, 61, 22), 2)
    # Row of empty chairs, one tipped over: the summit that ended empty.
    for cx in (70, 130, 190, 250, 310):
        draw_chair(cx, 758, (39, 74, 107))
    draw_chair(380, 758, (39, 74, 107), tipped=True)
    # Torn cover text on the table: the missing words.
    poly([(60, 806), (180, 800), (184, 824), (64, 830)], WHITE)
    draw_text("NO DEAL", 70, 808, 2, (180, 40, 30))
    draw_text("COP31 COLLAPSES", 0, 840, 3, NAVY, align="center",
              cx=(x0 + x1) // 2)
    draw_text("NO CLIMATE DEAL", 0, 866, 3, NAVY, align="center",
              cx=(x0 + x1) // 2)
    draw_text("FOSSIL FUELS LEFT OUT", 0, 898, 2, (138, 109, 31),
              align="center", cx=(x0 + x1) // 2)
    draw_text("90 NATIONS WALK OUT - ANTALYA", 0, 918, 2, INK,
              align="center", cx=(x0 + x1) // 2)


def draw_nvidia_panel():
    x0, x1 = 518, 1012
    fill_rect(x0, 700, x1, 950, CREAM)
    for k in range(3):
        fill_rect(x0 + k, 700 + k, x1 - k, 701 + k, NAVY)
    # Dark board with circuit traces.
    fill_rect(x0 + 4, 704, x1 - 4, 830, CHIP_BG)
    for yy in (716, 742, 800, 822):
        hline(x0 + 14, x1 - 14, yy, (31, 107, 58), 2)
    for xx in (548, 590, 950, 984):
        vline(xx, 712, 824, (31, 107, 58), 2)
    circle(590, 716, 4, GREEN_LT)
    circle(950, 800, 4, GREEN_LT)
    # The chip.
    cx0, cy0, cx1, cy1 = 700, 724, 830, 812
    fill_rect(cx0, cy0, cx1, cy1, GREEN)
    fill_rect(cx0 + 12, cy0 + 12, cx1 - 12, cy1 - 12, (90, 148, 0))
    fill_rect(cx0 + 34, cy0 + 30, cx1 - 34, cy1 - 30, (58, 96, 0))
    draw_text("GPU", 0, cy0 + 36, 2, WHITE, align="center",
              cx=(cx0 + cx1) // 2)
    for k in range(6):  # pins
        px_off = cx0 + 10 + k * 22
        fill_rect(px_off, cy0 - 8, px_off + 10, cy0, (201, 209, 201))
        fill_rect(px_off, cy1, px_off + 10, cy1 + 8, (201, 209, 201))
        py_off = cy0 + 8 + k * 12
        fill_rect(cx0 - 8, py_off, cx0, py_off + 8, (201, 209, 201))
        fill_rect(cx1, py_off, cx1 + 8, py_off + 8, (201, 209, 201))
    # Rising market arrow and the day's jump.
    draw_text("+33%", 534, 712, 4, GREEN_LT)
    thick_line(560, 822, 968, 724, GREEN_LT, 4)
    poly([(968, 724), (930, 716), (944, 748)], GREEN_LT)
    draw_text("HUANG BACK AS", 0, 840, 3, NAVY, align="center",
              cx=(x0 + x1) // 2)
    draw_text("NVIDIA CEO", 0, 866, 3, NAVY, align="center",
              cx=(x0 + x1) // 2)
    draw_text("TRUMP INTERVENED", 0, 898, 2, (138, 109, 31),
              align="center", cx=(x0 + x1) // 2)
    draw_text("BOARD REVERSES DECISION", 0, 918, 2, INK,
              align="center", cx=(x0 + x1) // 2)


def draw_footer():
    fill_rect(0, 950, W, H, NAVY)
    hline(0, W, 950, GOLD_DARK, 2)
    draw_text("BENGHAZI - ANTALYA - SANTA CLARA", 0, 964, 2, GOLD,
              align="center", cx=W // 2)
    draw_text("THE WORLD IN ONE PICTURE - 24 NOVEMBER 2026", 0, 988, 2,
              WHITE, align="center", cx=W // 2)


# ---------------------------------------------------------------- PNG


def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def encode_png():
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        o = y * W * 3
        raw += buf[o:o + W * 3]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", idat) + _chunk(b"IEND", b""))


def main():
    draw_masthead()
    draw_hero()
    draw_headline_band()
    draw_cop_panel()
    draw_nvidia_panel()
    draw_footer()
    png = encode_png()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    print("wrote %s (%d bytes, %dx%d)" % (path, len(png), W, H))


if __name__ == "__main__":
    main()
