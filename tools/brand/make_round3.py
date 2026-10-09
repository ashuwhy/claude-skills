"""Round 3 marks, Latin first: Sandeep's p with the प inside it, the bubble p, the answer-sheet
P and the geometry-box P. Each comes as tiles, a launcher circle and a PARIKSHANAM. lockup.

Same dependencies as make_lockups.py. Run from the repo root: python docs/brand/make_round3.py
"""

import math
import subprocess

from make_lockups import BORDER, NAVY, ORANGE, PAPER, ROOT, WM, doc, horizontal, label, place, tile

OUT = ROOT / "docs/brand/lockups/round3"
GOLD = "#F5C842"

# Stroke 100 as in pa(). A 360 bowl leaves a 160 counter, big enough that a bubble inside it is
# still a separate dot on a 48px launcher icon. The descender is a third of the bowl, as in
# Nunito Black's p (178 under a 514 bowl).
W = 100
D = 360
P_HEIGHT = 480


def line(d, ink, w=W):
    return (f'<path d="{d}" stroke="{ink}" stroke-width="{w}" stroke-linecap="round" '
            f'stroke-linejoin="round" fill="none"/>')


def ring(cx, cy, r, ink, w=W):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{ink}" stroke-width="{w}" fill="none"/>'


def disc(cx, cy, r, fill):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"/>'


def ring_p(s, ink, dot=None, gap=0.25, knockout=None):
    """Geometric p with its stem centre line at s. The ring has the stem's weight, so its left
    side is the stem. The dot is a shaded answer bubble, gap * W clear of the ring; at gap 0 it
    fills the counter, as in Sandeep's sketch. knockout cuts a tile-coloured moat round the p
    so a single-colour version still shows where it meets whatever is behind it."""
    r = (D - W) / 2
    cx, cy = s + r, D / 2
    stem = f"M{s} {W / 2} V{P_HEIGHT - W / 2}"
    art = ""
    if knockout:
        art += line(stem, knockout, W * 1.36) + ring(cx, cy, r, knockout, W * 1.36)
    if dot:
        art += disc(cx, cy, D / 2 - W - gap * W + (2 if gap == 0 else 0), dot)
    return art + line(stem, ink) + ring(cx, cy, r, ink)


def sandeep(p_ink, pa_ink, dot, r_u=(D - W) / 2, drop=D, knockout=None, gap=0):
    """Sandeep's sketch redrawn. The orange half is a headline, a left arm and a bowl that
    curves into the shared stem, so with the stem it is a प, and the stem and ring are a Latin
    p. r_u and drop shrink the प half when the Latin letter should lead."""
    s = 2 * r_u + W / 2
    cy = drop - W / 2 - r_u
    half = line(f"M{s} {W / 2} H{s - 2 * r_u} V{cy} A{r_u} {r_u} 0 0 0 {s} {cy}", pa_ink)
    return half + ring_p(s, p_ink, dot, gap, knockout), 2 * r_u + D, P_HEIGHT


def bubble(ink, dot, gap=0.25):
    return ring_p(W / 2, ink, dot, gap), D, P_HEIGHT


# An OMR answer sheet, 3 bubbles wide and 5 deep. The filled ones draw a P with a round bowl,
# because the top and bottom right bubbles stay empty.
OMR_P = ["XX.", "X.X", "XX.", "X..", "X.."]


def answer_sheet(filled, empty=None, marked=None, d=100, pitch=132):
    """marked shades the tip of the bowl in another colour, the answer just filled in."""
    art = ""
    for row, cells in enumerate(OMR_P):
        for col, cell in enumerate(cells):
            cx, cy = d / 2 + col * pitch, d / 2 + row * pitch
            if cell == "X":
                art += disc(cx, cy, d / 2, marked if marked and (row, col) == (1, 2) else filled)
            elif empty:
                art += ring(cx, cy, d / 2 - 6, empty, 12)
    return art, 2 * pitch + d, 4 * pitch + d


def geometry_box(ruler, protractor, cut, gap=0, h=560, rw=130, rp=200, notch=62, ticks=True):
    """A ruler for the stem and a protractor for the bowl. The protractor's centre notch is the
    counter. Ticks are cut from the ruler's outer edge, long and short, and disappear below
    about 64px, which is fine: what is left is still a P. The bowl is 400 of the 560, as in
    ChatGPT's render; at Nunito's 0.62 the half-disc was too small for its radial ticks, and
    without those it read as a D, not a protractor."""
    px = rw + gap
    # The ruler's top right corner is square so the two pieces meet flush; rounded, it left a
    # tile-coloured wedge at the top of the P. With no gap the protractor also runs under the
    # ruler, otherwise both edges anti-alias against the tile and leave a hairline down the seam.
    # The notch runs under the ruler too and is drawn before it: cut after, it left that hidden
    # strip of orange in the ruler's edge pixel, a brown line down the notch's straight side.
    r, under = 16, 0 if gap else 4
    art = (
        f'<path d="M{px - under} 0 H{px} A{rp} {rp} 0 0 1 {px} {2 * rp} H{px - under} Z" '
        f'fill="{protractor}"/>'
        f'<path d="M{px - under} {rp - notch} H{px} A{notch} {notch} 0 0 1 {px} {rp + notch} '
        f'H{px - under} Z" fill="{cut}"/>'
        f'<path d="M{r} 0 H{rw} V{h - r} A{r} {r} 0 0 1 {rw - r} {h} H{r} A{r} {r} 0 0 1 0 {h - r} '
        f'V{r} A{r} {r} 0 0 1 {r} 0 Z" fill="{ruler}"/>'
    )
    if not ticks:
        return art, px + rp, h
    for i, y in enumerate([150, 250, 350, 450]):
        tick = rw * (0.5 if i % 2 else 0.3)
        art += f'<rect y="{y - 9}" width="{tick:.0f}" height="18" fill="{cut}"/>'
    for degrees in [-60, -30, 0, 30, 60]:
        a = math.radians(degrees)
        inner, outer = rp * 0.62, rp * 0.84
        art += line(f"M{px + inner * math.cos(a):.1f} {rp + inner * math.sin(a):.1f} "
                    f"L{px + outer * math.cos(a):.1f} {rp + outer * math.sin(a):.1f}", cut, 18)
    return art, px + rp, h


def fit(size, x, y, glyph, radius=0.37):
    """Fits the glyph's box inside a circle, because launchers mask to one. Fitting width and
    height separately let a wide mark like Sandeep's draw a fifth bigger than the tall
    geometry-box P."""
    art, w, h = glyph
    scale = size * radius / math.hypot(w / 2, h / 2)
    gx = x + (size - w * scale) / 2
    gy = y + (size - h * scale) / 2
    return f'<g transform="translate({gx:.2f} {gy:.2f}) scale({scale:.5f})">{art}</g>'


# name: (tile fill, glyph, caption). Paper tiles get the site's border so they hold an edge on
# white; the Play listing and launchers never show a white icon without one.
MARKS = {
    "sandeep": (PAPER, sandeep(NAVY, ORANGE, GOLD), "Sandeep's p, redrawn"),
    "sandeep-navy": (NAVY, sandeep(PAPER, ORANGE, GOLD), "On navy"),
    "sandeep-p-leads": (PAPER, sandeep(NAVY, ORANGE, GOLD, r_u=90, drop=280), "Latin p leads"),
    "sandeep-mono": (NAVY, sandeep(PAPER, PAPER, NAVY, knockout=NAVY, gap=0.25), "Themed icon"),
    "bubble": (PAPER, bubble(NAVY, ORANGE), "Bubble p"),
    "bubble-navy": (NAVY, bubble(PAPER, GOLD), "On navy, gold"),
    "bubble-navy-orange": (NAVY, bubble(PAPER, ORANGE), "On navy, orange"),
    "bubble-mono": (NAVY, bubble(PAPER, PAPER), "Themed icon"),
    "sheet": (PAPER, answer_sheet(NAVY, "#D8D1C5"), "Answer-sheet P"),
    "sheet-navy": (NAVY, answer_sheet(PAPER, "#4A6390"), "On navy"),
    "sheet-marked": (PAPER, answer_sheet(NAVY, marked=ORANGE), "Last answer marked"),
    "sheet-navy-marked": (NAVY, answer_sheet(PAPER, marked=ORANGE), "On navy, marked"),
    "box": (PAPER, geometry_box(NAVY, ORANGE, PAPER), "Ruler + protractor"),
    "box-navy": (NAVY, geometry_box(PAPER, ORANGE, NAVY), "On navy"),
    "box-gold": (NAVY, geometry_box(ORANGE, GOLD, NAVY), "Orange and gold"),
    "box-mono": (NAVY, geometry_box(PAPER, PAPER, NAVY, gap=16), "Themed icon"),
}


def tiled(name, size, x, y):
    fill, glyph, _ = MARKS[name]
    return tile(size, x, y, fill, BORDER if fill == PAPER else None) + fit(size, x, y, glyph)


def launcher(name, size, x, y):
    """Pixel launchers mask adaptive icons to a circle. The glyph keeps its tile size, which
    sits inside the 66/108 safe zone."""
    fill, glyph, _ = MARKS[name]
    edge = f' stroke="{BORDER}" stroke-width="{size * 0.012:.2f}"' if fill == PAPER else ""
    return (f'<circle cx="{x + size / 2}" cy="{y + size / 2}" r="{size / 2}" fill="{fill}"{edge}/>'
            + fit(size, x, y, glyph))


def dotted_wordmark(cap=100, tracking=0, pad=60):
    """No icon at all: the wordmark in lower case with the bubble shaded inside its own p, so
    the period and the bubble are the same orange dot."""
    text = "parikshanam."
    scale = cap / WM.cap
    baseline = pad + 503 * scale
    words, advance = WM.svg(text, pad, baseline, cap, {None: NAVY, len(text) - 1: ORANGE}, tracking)
    dot = disc(pad + 320 * scale, baseline - 246 * scale, 62 * scale, ORANGE)
    return doc(advance + 2 * pad, baseline + 189 * scale + pad, words + dot)


def render(name, svg, png_width=None):
    path = OUT / f"{name}.svg"
    path.write_text(svg)
    cmd = ["rsvg-convert", str(path), "-o", str(OUT / "png" / f"{name}.png")]
    if png_width:
        cmd[1:1] = ["-w", str(png_width)]
    subprocess.run(cmd, check=True)


ROWS = [
    ("S. Sandeep's p: the Hindi pa hides inside a Latin p",
     ["sandeep", "sandeep-navy", "sandeep-p-leads", "sandeep-mono"]),
    ("B. Bubble p: the period of the wordmark, shaded in", ["bubble", "bubble-navy",
                                                            "bubble-navy-orange", "bubble-mono"]),
    ("O. Answer-sheet P", ["sheet", "sheet-navy", "sheet-marked", "sheet-navy-marked"]),
    ("G. Geometry-box P", ["box", "box-navy", "box-gold", "box-mono"]),
]

LOCKUPS = [("lockup-sandeep", "sandeep"), ("lockup-bubble", "bubble-navy"),
           ("lockup-sheet", "sheet-marked"), ("lockup-box", "box")]


def contact_sheet(files):
    width, margin, gutter, cell = 2400, 80, 40, 300
    body, y = [], margin
    title, _ = WM.svg("PARIKSHANAM.", margin, y + 44, 44, {None: NAVY, 11: ORANGE}, 20)
    body.append(title + label("Round 3: Latin first. S is Sandeep's sketch, redrawn", margin,
                              y + 84))
    y += 150

    sizes_x = margin + 4 * (cell + gutter) + 60
    for heading, names in ROWS:
        body.append(label(heading, margin, y))
        y += 26
        for i, name in enumerate(names):
            x = margin + i * (cell + gutter)
            body.append(tiled(name, cell, x, y) + label(MARKS[name][2], x, y + cell + 34))
        # The same primary mark as a Pixel launcher would show it, then at real pixel sizes.
        body.append(launcher(names[0], 200, sizes_x, y + 50))
        body.append(label("Launcher, then 48 32 24 16 px", sizes_x, y + 30))
        x = sizes_x + 240
        for px in [48, 32, 24, 16]:
            body.append(tiled(names[0], px, x, y + 150 - px / 2))
            body.append(tiled(names[1], px, x, y + 230 - px / 2))
            x += px + 36
        y += cell + 110

    half = (width - 2 * margin - gutter) / 2
    pairs = [LOCKUPS[:2], LOCKUPS[2:], [("lockup-dotted", None)]]
    captions = {"lockup-sandeep": "Sandeep's p", "lockup-bubble": "Bubble p",
                "lockup-sheet": "Answer-sheet P, marked", "lockup-box": "Geometry-box P",
                "lockup-dotted": "No icon: the dot lives in the wordmark's own p"}
    for row in pairs:
        tallest = 0
        for i, (name, _) in enumerate(row):
            svg, h = place(files[name], margin + i * (half + gutter), y, scale=0.62)
            body.append(svg + label(captions[name], margin + i * (half + gutter), y + h + 34))
            tallest = max(tallest, h)
        y += tallest + 90
    return doc(width, y + margin - 30, "".join(body), "#FFFFFF")


def main():
    (OUT / "png").mkdir(parents=True, exist_ok=True)
    for name in MARKS:
        render(f"mark-{name}", doc(1024, 1024, tiled(name, 1024, 0, 0)), 1024)
    for _, names in ROWS:
        render(f"launcher-{names[0]}", doc(1024, 1024, launcher(names[0], 1024, 0, 0)), 1024)

    files = {}
    for name, mark_name in LOCKUPS:
        files[name] = horizontal("PARIKSHANAM.", lambda s, x, y, m=mark_name: tiled(m, s, x, y))
        render(name, files[name], 1600)
    files["lockup-dotted"] = dotted_wordmark()
    render("lockup-dotted", files["lockup-dotted"], 1600)

    render("contact-sheet", contact_sheet(files))


if __name__ == "__main__":
    main()
