#!/usr/bin/env python3
"""Generate the application icon into icons/ at several sizes.

Design: rounded-square badge with a deep blue-teal gradient, a white "log"
sheet with lines (one line highlighted red = an audit event), and a
magnifying glass suggesting inspection/search. Requires Pillow (build-time
only; the app itself does not depend on it).
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "icons")
S = 256  # master render size
SIZES = [32, 64, 128, 256]


def _rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def _gradient(size, top, bottom):
    grad = Image.new("RGB", (size, size), top)
    d = ImageDraw.Draw(grad)
    for y in range(size):
        t = y / (size - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        d.line([(0, y), (size, y)], fill=(r, g, b))
    return grad


def build_master():
    # Background: gradient clipped to a rounded square.
    bg = _gradient(S, (34, 76, 128), (18, 132, 132))
    icon = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    icon.paste(bg, (0, 0), _rounded_mask(S, radius=52))
    d = ImageDraw.Draw(icon)

    # Log sheet (white rounded rectangle).
    sx0, sy0, sx1, sy1 = 62, 54, 174, 196
    d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=12,
                        fill=(248, 250, 252), outline=(210, 220, 230), width=2)

    # Text lines; one highlighted red (an audit hit).
    line_x0, line_x1 = sx0 + 16, sx1 - 16
    ys = [sy0 + 26, sy0 + 52, sy0 + 78, sy0 + 104]
    colors = [(120, 132, 148), (198, 60, 52), (120, 132, 148), (120, 132, 148)]
    widths = [1.0, 1.0, 0.7, 0.85]
    for y, c, w in zip(ys, colors, widths):
        d.line([(line_x0, y), (int(line_x0 + (line_x1 - line_x0) * w), y)],
               fill=c, width=7)

    # Magnifying glass (audit/inspection), bottom-right, teal ring + handle.
    cx, cy, r = 176, 176, 34
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(15, 42, 68), width=12)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(120, 220, 210), width=6)
    d.line([(cx + r - 6, cy + r - 6), (cx + r + 22, cy + r + 22)],
           fill=(15, 42, 68), width=14)
    d.line([(cx + r - 6, cy + r - 6), (cx + r + 22, cy + r + 22)],
           fill=(120, 220, 210), width=6)
    return icon


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    master = build_master()
    for sz in SIZES:
        img = master.resize((sz, sz), Image.LANCZOS)
        path = os.path.join(OUT_DIR, "log-samba-audit-%d.png" % sz)
        img.save(path)
        print("wrote", path)
    # Multi-size .ico for completeness (desktop / Windows-style use).
    master.save(os.path.join(OUT_DIR, "log-samba-audit.ico"),
                sizes=[(s, s) for s in SIZES])
    print("wrote", os.path.join(OUT_DIR, "log-samba-audit.ico"))


if __name__ == "__main__":
    main()
