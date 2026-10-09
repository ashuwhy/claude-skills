"""The versus sheet for two or three finalist icons.

Each goes through what a launcher icon meets on a phone: the circle and squircle masks, a glance,
themed (monochrome) icons in light and dark system tones, and real pixel sizes, with the share of
the icon its mark covers.

    python make_versus.py candidates.json versus.png [--font Inter.ttf]

candidates.json, paths relative to it:

    {"title": "Icon decision",
     "candidates": [
       {"name": "Geometry-box P", "icon": "box.svg", "mono": "box-mono.svg",
        "notes": ["Reads as P, then as ruler and protractor"]},
       {"name": "Bubble p", "icon": "bubble-fg.svg", "adaptive": true, "background": "#1B3A6E",
        "mono": "bubble-mono.svg", "notes": ["Survives 16 px untouched"]}]}

icon is the square icon, SVG or PNG. With "adaptive": true, icon and mono are Android adaptive
layers (108 units, of which the launcher shows the middle 72) and background fills behind the
icon. mono is the mark alone; a one-colour tile works too. Without it the themed row stays empty. The notes are the
one-line verdicts; write them after looking, not before.

Needs Pillow 10.1+ and, for SVG inputs, rsvg-convert.
"""

import argparse
import io
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

CELL, GAP, MARGIN = 300, 40, 80
COLUMN = 2 * CELL + GAP
INK, MUTED = "#1F2937", "#6B7280"
SIZES = [48, 32, 24, 16]
ZOOM = 4
# Material You draws the monochrome layer in one tone on a tint of the wallpaper colour. These
# are its tones for a blue wallpaper, light theme then dark.
THEMED = [("Themed, light", "#DCE5F4", "#2E456B"), ("Themed, dark", "#1E2B40", "#C3D3EF")]


def rasterise(path, px):
    if path.suffix.lower() == ".svg":
        png = subprocess.run(["rsvg-convert", "-w", str(px), "-h", str(px), str(path)],
                             capture_output=True, check=True).stdout
        return Image.open(io.BytesIO(png)).convert("RGBA")
    return Image.open(path).convert("RGBA").resize((px, px), Image.LANCZOS)


def face(candidate, layer, px):
    """The part of a layer the launcher shows, rendered at px rather than scaled down to it, so
    small sizes look the way the phone draws them."""
    if not candidate.get("adaptive"):
        return rasterise(candidate[layer], px)
    full = round(px * 108 / 72)
    inset = (full - px) // 2
    return rasterise(candidate[layer], full).crop((inset, inset, inset + px, inset + px))


def icon(candidate, px):
    front = face(candidate, "icon", px)
    back = Image.new("RGBA", front.size, candidate.get("background", (0, 0, 0, 0)))
    return Image.alpha_composite(back, front)


def supersampled(px, draw):
    big = Image.new("L", (px * 4, px * 4))
    draw(ImageDraw.Draw(big), px * 4)
    return big.resize((px, px), Image.LANCZOS)


def circle(px):
    return supersampled(px, lambda d, s: d.ellipse((0, 0, s - 1, s - 1), fill=255))


def squircle(px, n=5):
    """A superellipse, near the shape iOS and One UI cut. Near, not their exact curve."""
    def draw(d, s):
        r = s / 2
        points = []
        for i in range(360):
            t = math.radians(i)
            c, si = math.cos(t), math.sin(t)
            points.append((r + r * math.copysign(abs(c) ** (2 / n), c),
                           r + r * math.copysign(abs(si) ** (2 / n), si)))
        d.polygon(points, fill=255)
    return supersampled(px, draw)


def masked(img, mask):
    out = img.copy()
    out.putalpha(ImageChops.multiply(img.getchannel("A"), mask))
    return out


def glyph(layer):
    """Where the mark is. An Android monochrome layer is the mark on transparency, so that is
    its alpha. A one-colour tile covers most of its square, so there it is whatever differs from
    the tile colour."""
    alpha = layer.getchannel("A")
    opaque = alpha.point(lambda a: 255 if a > 250 else 0)
    if sum(opaque.histogram()[255:]) < layer.width * layer.height / 2:
        return alpha
    rgb = layer.convert("RGB")
    raw = rgb.tobytes()
    tile = Counter(raw[i:i + 3] for i in range(0, len(raw), 3)).most_common(1)[0][0]
    distance = ImageChops.difference(rgb, Image.new("RGB", rgb.size, tuple(tile))).convert("L")
    return ImageChops.multiply(alpha, distance.point(lambda d: min(255, d * 4)))


def themed(candidate, px, back, tone):
    tile = Image.new("RGBA", (px, px), back)
    tile.paste(Image.new("RGBA", (px, px), tone), mask=glyph(face(candidate, "mono", px)))
    tile.putalpha(circle(px))
    return tile


def ink_share(candidate):
    """Share of the circle the mark covers, taking the commonest colour as the background. Tall
    letters lose here: the circle clips the corners, so they can't grow the way a wide mark can."""
    img = masked(icon(candidate, 512), circle(512)).tobytes()
    inside = [img[i:i + 3] for i in range(0, len(img), 4) if img[i + 3] > 250]
    back = Counter(inside).most_common(1)[0][0]
    ink = sum(sum(abs(a - b) for a, b in zip(px, back)) > 60 for px in inside)
    return round(100 * ink / len(inside))


class Sheet:
    def __init__(self, font, columns):
        self.font = font
        self.canvas = Image.new("RGB", (2 * MARGIN + columns * COLUMN + (columns - 1) * MARGIN,
                                        4000), "white")
        self.pen = ImageDraw.Draw(self.canvas)
        self.bottom = 0

    def text(self, words, x, y, size, fill=INK):
        typeface = ImageFont.truetype(self.font, size) if self.font else ImageFont.load_default(size)
        self.pen.text((x, y), words, font=typeface, fill=fill)

    def image(self, img, x, y):
        self.canvas.paste(img, (round(x), round(y)), img)

    def column(self, candidate, x, y):
        right = x + CELL + GAP
        self.text(candidate["name"], x, y, 30)
        y += 60

        square = icon(candidate, CELL)
        launcher = masked(square, circle(CELL))
        self.text("Circle (Pixel)", x, y, 18, MUTED)
        self.text("Squircle", right, y, 18, MUTED)
        self.image(launcher, x, y + 28)
        self.image(masked(square, squircle(CELL)), right, y + 28)
        y += CELL + 80

        glance = Image.alpha_composite(Image.new("RGBA", launcher.size, "white"), launcher)
        self.text("At a glance", x, y, 18, MUTED)
        self.image(glance.filter(ImageFilter.GaussianBlur(CELL * 0.03)), x, y + 28)
        y += CELL + 80

        # The row stays when there is no mono layer, so every column's rows line up.
        for i, (caption, back, tone) in enumerate(THEMED):
            cx = x + i * (CELL + GAP)
            self.text(caption, cx, y, 18, MUTED)
            if candidate.get("mono"):
                self.image(themed(candidate, CELL, back, tone), cx, y + 28)
            elif i == 0:
                self.text("No monochrome layer given", cx, y + 40, 18)
        y += CELL + 80

        self.text(f"{' '.join(map(str, SIZES))} px, shown {ZOOM}x", x, y, 18, MUTED)
        px_x, tallest = x, SIZES[0] * ZOOM
        for px in SIZES:
            small = icon(candidate, px).resize((px * ZOOM, px * ZOOM), Image.NEAREST)
            self.image(small, px_x, y + 28 + (tallest - px * ZOOM) / 2)
            px_x += px * ZOOM + 20
        y += tallest + 80

        for line in candidate.get("notes", []) + [f"Fills {ink_share(candidate)}% of the circle"]:
            self.text(line, x, y, 20)
            y += 34
        self.bottom = max(self.bottom, y)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("spec", type=Path, help="candidates.json")
    parser.add_argument("out", type=Path, help="the sheet, as PNG")
    parser.add_argument("--font", help="a .ttf for the labels; Pillow's own font otherwise")
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text())
    candidates = spec["candidates"]
    for candidate in candidates:
        for layer in ("icon", "mono"):
            if layer in candidate:
                candidate[layer] = args.spec.parent / candidate[layer]

    sheet = Sheet(args.font, len(candidates))
    sheet.text(spec.get("title", "Icon decision"), MARGIN, MARGIN, 44)
    for i, candidate in enumerate(candidates):
        sheet.column(candidate, MARGIN + i * (COLUMN + MARGIN), MARGIN + 100)
    sheet.canvas.crop((0, 0, sheet.canvas.width, sheet.bottom + MARGIN)).save(args.out)
    print(f"{args.out}: {len(candidates)} candidates")


if __name__ == "__main__":
    main()
