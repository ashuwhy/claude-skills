"""Head to head for the icon decision: Sandeep's p, the geometry-box P, and the bubble p I picked
after round 3. Each goes through what a launcher icon meets on a phone: the Pixel's circle mask,
a glance, the Android 13 themed icon, and real pixel sizes.

Run from the repo root after make_round3.py: python docs/brand/make_versus.py
"""

import base64
import io
import subprocess

from make_lockups import NAVY, PAPER, WM, doc, label
from make_round3 import OUT, launcher, tiled
from PIL import Image, ImageFilter

# Material You draws the monochrome layer in one tone on a tint of the wallpaper colour. These
# are its tones for a blue wallpaper, light theme then dark.
THEMED = [("Themed, light", "#DCE5F4", "#2E456B"), ("Themed, dark", "#1E2B40", "#C3D3EF")]

CANDIDATES = [
    ("Sandeep's p", "sandeep", ["Reads as up or cp before it reads as p",
                                "The Hindi pa shows once it is pointed out",
                                "3 colours, 5 parts"]),
    ("Geometry-box P", "box", ["Reads as P, then as ruler and protractor",
                               "Ticks go below 64 px; it stays a P",
                               "2 colours on the tile, 3 parts plus ticks"]),
    ("Bubble p, my round 3 pick", "bubble", ["Reads as p with a dot",
                                             "Survives 16 px untouched",
                                             "The answer bubble has to be explained"]),
]


def raster(svg, px):
    png = subprocess.run(["rsvg-convert", "-w", str(px), "-h", str(px)], input=svg.encode(),
                         capture_output=True, check=True).stdout
    rgba = Image.open(io.BytesIO(png)).convert("RGBA")
    white = Image.new("RGBA", rgba.size, "white")
    return Image.alpha_composite(white, rgba).convert("RGB")


def embed(img, x, y):
    buf = io.BytesIO()
    img.save(buf, "PNG")
    href = base64.b64encode(buf.getvalue()).decode()
    return (f'<image x="{x}" y="{y}" width="{img.width}" height="{img.height}" '
            f'href="data:image/png;base64,{href}"/>')


def ink_share(name):
    """Share of the navy tile covered by the mark. Tall letters lose here: the launcher circle
    clips the corners, so a P can't grow to fill the tile the way a wide mark does."""
    img = raster(doc(1024, 1024, tiled(name, 1024, 0, 0)), 512)
    navy = tuple(int(NAVY[i:i + 2], 16) for i in (1, 3, 5))
    tile = ink = 0
    for px in img.get_flattened_data():
        if px == (255, 255, 255):
            continue
        tile += 1
        ink += sum(abs(a - b) for a, b in zip(px, navy)) > 60
    return round(100 * ink / tile)


def note(text, x, y, cap=17):
    words, _ = WM.svg(text, x, y, cap, {None: NAVY}, 0)
    return words


def column(title, key, notes, x, y):
    cell, gap = 300, 40
    right = x + cell + gap
    body = [note(title, x, y, 30)]
    y += 60

    body.append(label("On paper", x, y) + label("On navy", right, y))
    body.append(tiled(key, cell, x, y + 20) + tiled(f"{key}-navy", cell, right, y + 20))
    y += cell + 80

    body.append(label("Pixel launcher", x, y) + label("At a glance", right, y))
    body.append(launcher(f"{key}-navy", cell, x, y + 20))
    glance = raster(doc(cell, cell, launcher(f"{key}-navy", cell, 0, 0)), cell)
    body.append(embed(glance.filter(ImageFilter.GaussianBlur(9)), right, y + 20))
    y += cell + 80

    for i, (caption, back, glyph) in enumerate(THEMED):
        cx = x + i * (cell + gap)
        themed = launcher(f"{key}-mono", cell, cx, y + 20)
        body.append(label(caption, cx, y))
        body.append(themed.replace(NAVY, back).replace(PAPER, glyph))
    y += cell + 80

    body.append(label("48 32 24 16 px, shown 4x", x, y))
    px_x = x
    for px in [48, 32, 24, 16]:
        img = raster(doc(1024, 1024, tiled(f"{key}-navy", 1024, 0, 0)), px)
        img = img.resize((px * 4, px * 4), Image.NEAREST)
        body.append(embed(img, px_x, y + 20 + (192 - px * 4) / 2))
        px_x += px * 4 + 20
    y += 192 + 80

    for line in notes + [f"Fills {ink_share(f'{key}-navy')}% of the tile"]:
        body.append(note(line, x, y))
        y += 34
    return "".join(body), y


def main():
    margin, width, gutter = 80, 640, 80
    title, _ = WM.svg("PARIKSHANAM.", margin, margin + 44, 44, {None: NAVY, 11: "#E8720C"}, 20)
    body = [title + label("Icon decision: Sandeep's p against the geometry-box P", margin,
                          margin + 84)]
    bottom = 0
    for i, (name, key, notes) in enumerate(CANDIDATES):
        art, y = column(name, key, notes, margin + i * (width + gutter), margin + 160)
        body.append(art)
        bottom = max(bottom, y)
    total = margin * 2 + 3 * width + 2 * gutter
    svg = doc(total, bottom + margin - 20, "".join(body), "#FFFFFF")
    (OUT / "versus.svg").write_text(svg)
    subprocess.run(["rsvg-convert", str(OUT / "versus.svg"), "-o", str(OUT / "png/versus.png")],
                   check=True)


if __name__ == "__main__":
    main()
