"""Every shipped copy of the geometry-box P, rendered from the one drawing in make_round3.py:
the app's launcher, adaptive, themed, notification and splash images, the three web favicons,
the in-page icons, the website lockups, the bare P and the Play listing icon.

Run from the repo root: python docs/brand/make_icons.py
"""

import io
import subprocess

from make_lockups import BORDER, NAVY, ORANGE, PAPER, ROOT, WM, doc, tile
from make_round3 import fit, geometry_box
from PIL import Image

MOBILE = ROOT / "apps/mobile/assets/images"
PLAY = ROOT / "docs/brand/lockups/play-icon.png"

# Android draws the launcher at 72dp out of a 108dp canvas, so the foreground glyph is scaled
# to sit where fit()'s 0.37 puts it on a full-size icon.
ADAPTIVE = 0.37 * 72 / 108

# The paper tile: navy ruler, orange protractor, cuts in paper. Chosen over the navy tile.
FULL = geometry_box(NAVY, ORANGE, PAPER)
# Below about 64px the ticks are noise, and in one colour they are holes that close up.
PLAIN = geometry_box(NAVY, ORANGE, PAPER, ticks=False)


def raster(svg, px):
    png = subprocess.run(["rsvg-convert", "-w", str(px), "-h", str(px)], input=svg.encode(),
                         capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGBA")


def silhouette(svg, px):
    """One-colour layers (themed icon, status bar) are alpha masks, so the cuts have to be
    holes rather than navy. Drawn white on black, the brightness becomes the alpha."""
    img = raster(svg, px)
    alpha = Image.new("L", img.size, 0)
    alpha.paste(img.convert("L"), mask=img.getchannel("A"))
    white = Image.new("RGBA", img.size, "white")
    white.putalpha(alpha)
    return white


def square(glyph, px, radius=0.37):
    return raster(doc(1024, 1024, fit(1024, 0, 0, glyph, radius), PAPER), px)


def paper_tile(size, x, y):
    """The tile with its hairline drawn inside the edge, so nothing is clipped at the canvas."""
    inset = size * 0.006
    return tile(size - 2 * inset, x + inset, y + inset, PAPER, BORDER)


def rounded(glyph, px):
    return raster(doc(1024, 1024, paper_tile(1024, 0, 0) + fit(1024, 0, 0, glyph)), px)


def splash(width):
    """The glyph alone, cropped to its own box. app.json sets the same width in dp and the JS
    overlay in components/ui/SplashOverlay.tsx draws the same width, so the handover from the
    native splash lines up exactly."""
    art, w, h = FULL
    scale = width / w
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{width}" '
           f'height="{round(h * scale)}">{art}</svg>')
    png = subprocess.run(["rsvg-convert"], input=svg.encode(), capture_output=True,
                         check=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGBA")


def bare(ruler, height):
    """The P with no tile, for pages we draw ourselves; the tile belongs to the app icon. The
    cuts are holes through a mask instead of paper paint, so one file works on white, cream and
    navy. Each piece is a flat fill under its own mask, so a cut edge anti-aliases into the page
    and never into the other piece. One mask over both blended the orange under the ruler into
    its edge first, then cut it, which left a brown line beside the notch."""
    protractor, w, h = geometry_box("none", "white", "black")
    ruler_cuts, _, _ = geometry_box("white", "none", "black")
    box = f'x="0" y="0" width="{w}" height="{h}"'
    scale = height / h
    return (f'<g transform="scale({scale:.5f})">'
            f'<mask id="protractor" maskUnits="userSpaceOnUse" {box}>{protractor}</mask>'
            f'<mask id="ruler" maskUnits="userSpaceOnUse" {box}>{ruler_cuts}</mask>'
            f'<rect {box} fill="{ORANGE}" mask="url(#protractor)"/>'
            f'<rect {box} fill="{ruler}" mask="url(#ruler)"/></g>'), w * scale


def lockup(ruler, ink, cap=100):
    """The one logo on pages: the bare P 1.8 times the cap height, centred on PARIKSHANAM. At
    twice the cap it outweighed the word. The canvas stays two caps tall, as it was then, so the
    pages' heights still give the same word and only the P shrank. The gap is one and a half
    ruler widths; at one width the P read as the word's first letter. The words are Nunito Black
    outlines, so the lockup needs no font loaded. On dark grounds the ruler turns paper, because
    a navy ruler disappears into navy."""
    height, p = 2 * cap, 1.8 * cap
    mark, width = bare(ruler, p)
    gap = 1.5 * 130 / 560 * p
    words, advance = WM.svg("PARIKSHANAM.", width + gap, height / 2 + cap / 2, cap,
                            {None: ink, 11: ORANGE}, tracking=20)
    mark = f'<g transform="translate(0 {(height - p) / 2:.2f})">{mark}</g>'
    return doc(width + gap + advance, height, mark + words)


def stacked(ruler, ink, cap=100):
    """The P over the word, for the sign-in pages, where the logo stands alone above a form.
    The P is centred on the letters without the dot, which would pull it right of centre."""
    p = 2.8 * cap
    mark, width = bare(ruler, p)
    baseline = p + 0.75 * cap + cap
    words, advance = WM.svg("PARIKSHANAM.", 0, baseline, cap, {None: ink, 11: ORANGE},
                            tracking=20)
    _, letters = WM.svg("PARIKSHANAM", 0, baseline, cap, {None: ink}, tracking=20)
    mark = f'<g transform="translate({(letters - width) / 2:.2f} 0)">{mark}</g>'
    # Nunito Black's round letters dip 1.6% of a cap under the baseline.
    return doc(advance, baseline + 0.02 * cap, mark + words)


def main():
    square(FULL, 1024).convert("RGB").save(MOBILE / "icon.png")
    raster(doc(1024, 1024, fit(1024, 0, 0, FULL, ADAPTIVE)), 1024).save(
        MOBILE / "android-icon-foreground.png")
    Image.new("RGB", (1024, 1024), PAPER).save(MOBILE / "android-icon-background.png")

    mono = geometry_box("white", "white", "black", gap=16)
    silhouette(doc(1024, 1024, fit(1024, 0, 0, mono, ADAPTIVE)), 1024).save(
        MOBILE / "android-icon-monochrome.png")

    # 24dp with a 20dp live area: the P is drawn 20 of the 24 tall.
    art, w, h = geometry_box("white", "white", "black", ticks=False)
    scale = 80 / h
    status = (f'<g transform="translate({(96 - w * scale) / 2:.2f} 8) scale({scale:.5f})">'
              f'{art}</g>')
    silhouette(doc(96, 96, status), 96).save(MOBILE / "notification-icon.png")

    splash(576).save(MOBILE / "splash-icon.png")
    rounded(PLAIN, 196).save(MOBILE / "favicon.png")

    for app in ["web", "admin", "teacher"]:
        rounded(PLAIN, 512).save(ROOT / f"apps/{app}/src/app/icon.png")
    # Pages round these with CSS, so they stay full-bleed squares.
    square(FULL, 512).convert("RGB").save(ROOT / "apps/web/public/icon.png")
    square(FULL, 512).convert("RGB").save(ROOT / "apps/admin/public/app-icon.png")

    for app in ["web", "admin", "teacher"]:
        brand = ROOT / f"apps/{app}/public/brand"
        brand.mkdir(parents=True, exist_ok=True)
        (brand / "lockup.svg").write_text(lockup(NAVY, NAVY))
        (brand / "lockup-on-dark.svg").write_text(lockup(PAPER, PAPER))
        (brand / "lockup-stacked.svg").write_text(stacked(NAVY, NAVY))
    mark, width = bare(NAVY, 560)
    (ROOT / "apps/web/public/brand/p.svg").write_text(doc(width, 560, mark))

    # The finished logo for everything outside the code: decks, posters, social, print.
    # PNGs are transparent, so the on-dark ones look empty in a white preview.
    kit = ROOT / "docs/brand/logo"
    kit.mkdir(exist_ok=True)
    dark_mark, _ = bare(PAPER, 560)
    for name, svg, px in [("lockup", lockup(NAVY, NAVY), 2400),
                          ("lockup-on-dark", lockup(PAPER, PAPER), 2400),
                          ("lockup-stacked", stacked(NAVY, NAVY), 1600),
                          ("lockup-stacked-on-dark", stacked(PAPER, PAPER), 1600),
                          ("p", doc(width, 560, mark), 600),
                          ("p-on-dark", doc(width, 560, dark_mark), 600)]:
        (kit / f"{name}.svg").write_text(svg)
        subprocess.run(["rsvg-convert", "-w", str(px), "-o", str(kit / f"{name}.png")],
                       input=svg.encode(), check=True)
    square(FULL, 1024).convert("RGB").save(kit / "app-icon.png")
    # Rounder than the launcher's 0.225, for slides and posts that do not mask it themselves.
    rounder = f'<rect width="1024" height="1024" rx="{1024 * 0.3:.0f}" fill="{PAPER}"/>'
    raster(doc(1024, 1024, rounder + fit(1024, 0, 0, FULL)), 1024).save(
        kit / "app-icon-rounded.png")

    # Play masks the listing icon itself and rejects transparency.
    square(FULL, 512).convert("RGB").save(PLAY)


if __name__ == "__main__":
    main()
