"""Builds the प mark, wordmarks and lockups as outlined SVGs, plus PNG renders.

Needs fonttools and uharfbuzz (pip install fonttools uharfbuzz) and rsvg-convert on PATH.
Run from the repo root: python docs/brand/make_lockups.py
"""

import subprocess
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/brand/lockups"
NUNITO_BLACK = ROOT / "apps/web/public/fonts/Nunito-Black.ttf"

NAVY = "#1B3A6E"
ORANGE = "#E8720C"
PAPER = "#F9F7F5"
BORDER = "#E5E0D8"


class Wordmark:
    """Nunito Black shaped by HarfBuzz, so kerning matches what the browser draws."""

    def __init__(self, path):
        self.tt = TTFont(path)
        self.glyphs = self.tt.getGlyphSet()
        self.hb_font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
        self.cap = self.tt["OS/2"].sCapHeight

    def shape(self, text, tracking=0):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb_font, buf, {"kern": True})
        x, placed = 0, []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            placed.append((self.tt.getGlyphName(info.codepoint), x + pos.x_offset, info.cluster))
            x += pos.x_advance + tracking
        return placed, x - tracking

    def svg(self, text, x, baseline, cap_px, colours, tracking=0):
        """colours maps a character index to a fill; anything unmapped is colours[None]."""
        scale = cap_px / self.cap
        placed, advance = self.shape(text, tracking)
        parts = []
        for name, gx, cluster in placed:
            pen = SVGPathPen(self.glyphs)
            self.glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x + gx * scale, baseline)))
            d = pen.getCommands()
            if d:
                parts.append(f'<path d="{d}" fill="{colours.get(cluster, colours[None])}"/>')
        return "".join(parts), advance * scale


# The प is drawn on a grid where the stroke is 100 units: a U whose right arm runs on down
# to the baseline as the stem, hung from a headline. Proportions follow Kohinoor Devanagari
# Bold, with the bowl bottom at about 68% of the height, simplified to a true semicircle.
# Stroke to height is 0.21, close to Nunito Black's stem to cap height (184/705), so the
# mark and the wordmark read as one weight.
def pa(w=100, counter=150, height=470, bowl=0.68, lead=30, overhang=110, open_arm=False):
    """open_arm starts the left arm just under the headline with a round end instead of
    joining it, the way ChatGPT drew it in round 2. Friendlier, less correct."""
    r = (w + counter) / 2
    left = lead + w / 2
    stem = left + 2 * r
    top = w / 2
    bowl_centre = bowl * height - w / 2 - r
    arm_top = top + w * 1.3 if open_arm else top
    body = (
        f"M{left} {arm_top} V{bowl_centre} A{r} {r} 0 0 0 {stem} {bowl_centre} "
        f"M{stem} {top} V{height - w / 2}"
    )
    return {
        "w": w, "body": body, "bar": (w / 2, top, stem + overhang),
        "height": height, "body_left": lead, "body_right": stem + w / 2,
        "lead": lead, "overhang": overhang,
        "bowl": ((left + stem) / 2, bowl_centre, counter / 2),
    }


def glyph_svg(g, x, y, scale, ink, bar_ink, extra=""):
    left, top, end = g["bar"]
    stroke = f'stroke-width="{g["w"]}" stroke-linecap="round" stroke-linejoin="round" fill="none"'
    return (
        f'<g transform="translate({x:.2f} {y:.2f}) scale({scale:.5f})">'
        f'<path d="{g["body"]}" stroke="{ink}" {stroke}/>'
        f'<path d="M{left} {top} H{end}" stroke="{bar_ink}" {stroke}/>{extra}</g>'
    )


def bowl_dot(g, fill):
    """A shaded answer bubble, concentric with the bowl and clear of the headline."""
    cx, cy, half = g["bowl"]
    r = half - 0.32 * g["w"]
    return f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="{fill}"/>'


def end_bubble(g, fill):
    """The headline finishes in an OMR bubble half again as tall as the bar."""
    _, top, end = g["bar"]
    return f'<circle cx="{end}" cy="{top}" r="{g["w"] * 0.78:.1f}" fill="{fill}"/>'


def bar_dot_svg(g, x, y, scale, ink, bar_ink):
    """Headline stops at the stem and a full stop follows it, like the period in PARIKSHANAM."""
    left, top, _ = g["bar"]
    w = g["w"]
    stroke = f'stroke-width="{w}" stroke-linecap="round" fill="none"'
    stem_x = g["body_right"] - w / 2
    dot_x = g["body_right"] + 0.55 * w + w / 2
    return (
        f'<g transform="translate({x:.2f} {y:.2f}) scale({scale:.5f})">'
        f'<path d="{g["body"]}" stroke="{ink}" {stroke} stroke-linejoin="round"/>'
        f'<path d="M{left} {top} H{stem_x}" stroke="{bar_ink}" {stroke}/>'
        f'<circle cx="{dot_x}" cy="{top}" r="{w / 2}" fill="{bar_ink}"/></g>'
    )


def tile(size, x, y, fill, stroke=None):
    border = f' stroke="{stroke}" stroke-width="{size * 0.012:.2f}"' if stroke else ""
    return (
        f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{size * 0.225:.2f}" '
        f'fill="{fill}"{border}/>'
    )


def mark(size, x, y, style="navy", g=None):
    """A tiled app mark. The glyph is 56% of the tile high. The U and stem are centred and
    the whole glyph shifted back by a third of the headline's overhang, because the eye
    centres on the heavy part and not on the thin bar end."""
    g = g or pa()
    scale = size * (0.5 if style == "seal" else 0.56) / g["height"]
    body_mid = (g["body_left"] + g["body_right"]) / 2
    gx = x + size / 2 - body_mid * scale - (g["overhang"] - g["lead"]) * scale * 0.3
    gy = y + (size - g["height"] * scale) / 2
    if style == "navy":
        return tile(size, x, y, NAVY) + glyph_svg(g, gx, gy, scale, PAPER, ORANGE)
    if style == "paper":
        return tile(size, x, y, PAPER, BORDER) + glyph_svg(g, gx, gy, scale, NAVY, ORANGE)
    if style == "orange":
        return tile(size, x, y, ORANGE) + glyph_svg(g, gx, gy, scale, PAPER, NAVY)
    if style == "dot":
        return tile(size, x, y, NAVY) + bar_dot_svg(g, gx, gy, scale, PAPER, ORANGE)
    if style == "mono":
        return tile(size, x, y, NAVY) + glyph_svg(g, gx, gy, scale, PAPER, PAPER)
    if style == "bubble":
        return tile(size, x, y, NAVY) + glyph_svg(g, gx, gy, scale, PAPER, ORANGE,
                                                  end_bubble(g, ORANGE))
    if style == "bowl":
        return tile(size, x, y, NAVY) + glyph_svg(g, gx, gy, scale, PAPER, ORANGE,
                                                  bowl_dot(g, ORANGE))
    if style == "open":
        return tile(size, x, y, NAVY) + glyph_svg(g, gx, gy, scale, PAPER, ORANGE)
    if style == "seal":
        ring = size * 0.045
        return (
            f'<circle cx="{x + size / 2}" cy="{y + size / 2}" r="{size / 2 - ring / 2}" '
            f'fill="{PAPER}" stroke="{NAVY}" stroke-width="{ring:.2f}"/>'
            + glyph_svg(g, gx, gy, scale, NAVY, ORANGE)
        )
    raise ValueError(style)


def doc(width, height, body, background=None):
    bg = f'<rect width="{width}" height="{height}" fill="{background}"/>' if background else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}">{bg}{body}</svg>'
    )


WM = Wordmark(NUNITO_BLACK)


def horizontal(text, mark_svg_fn, cap=100, ink=NAVY, period=ORANGE, tracking=20, background=None,
               pad=60):
    """Mark on the left, wordmark centred on it. The tile is 2.3 cap heights, the same ratio as
    the navbar's 32px tile against 1.2rem uppercase Nunito."""
    size = cap * 2.3
    gap = size * 0.34
    colours = {None: ink}
    if text.endswith("."):
        colours[len(text) - 1] = period
    baseline = pad + size / 2 + cap / 2
    words, advance = WM.svg(text, pad + size + gap, baseline, cap, colours, tracking)
    width = pad + size + gap + advance + pad
    return doc(width, size + 2 * pad, mark_svg_fn(size, pad, pad) + words, background)


def stacked(text, style="navy", cap=100, ink=NAVY, period=ORANGE, tracking=20, background=None,
            tagline=None, pad=70):
    size = cap * 3.4
    colours = {None: ink}
    if text.endswith("."):
        colours[len(text) - 1] = period
    _, advance = WM.shape(text, tracking)
    advance *= cap / WM.cap
    tag_cap = cap * 0.34
    tag_adv = 0
    if tagline:
        _, tag_adv = WM.shape(tagline, 160)
        tag_adv *= tag_cap / WM.cap
    width = max(advance, size, tag_adv) + 2 * pad
    body = mark(size, (width - size) / 2, pad, style)
    baseline = pad + size + cap * 0.75 + cap
    words, _ = WM.svg(text, (width - advance) / 2, baseline, cap, colours, tracking)
    body += words
    height = baseline + pad
    if tagline:
        tag_base = baseline + tag_cap * 2.6
        tag, _ = WM.svg(tagline, (width - tag_adv) / 2, tag_base, tag_cap, {None: ORANGE}, 160)
        body += tag
        height = tag_base + pad
    return doc(width, height, body, background)


def horizontal_glyph(text, cap=100, ink=NAVY, bar_ink=ORANGE, period=ORANGE, tracking=20,
                     background=None, pad=60):
    """Untiled प beside the wordmark, at the Nunito Black stem weight. The headline sits on the
    cap height and the stem drops below the baseline like a descender, which is how Devanagari
    and Latin share a line in bilingual Indian signage."""
    g = pa()
    scale = 184 * cap / WM.cap / g["w"]
    colours = {None: ink}
    if text.endswith("."):
        colours[len(text) - 1] = period
    cap_top = pad
    baseline = cap_top + cap
    words_x = pad + g["bar"][2] * scale + g["w"] / 2 * scale + cap * 0.32
    words, advance = WM.svg(text, words_x, baseline, cap, colours, tracking)
    body = glyph_svg(g, pad, cap_top, scale, ink, bar_ink)
    return doc(words_x + advance + pad, cap_top + g["height"] * scale + pad, body + words, background)


def headline_lockup(cap=100, tracking=20, ink=NAVY, background=None, pad=60):
    """The प's headline carries on over the whole Latin word, the way a shirorekha joins the
    letters of a Devanagari word. The प is drawn at the Nunito Black stem weight (184 of 705
    cap units) and a little wider than Nunito's P, so it sits in the word as a letter."""
    unit = cap / WM.cap
    stem = 184 * unit
    bar = stem * 0.72
    lead = stem * 0.3
    cap_top = pad + bar + cap * 0.12
    baseline = cap_top + cap
    left = pad + lead + stem / 2
    right = left + stem + stem * 1.2
    r = (right - left) / 2
    bowl_centre = pad + 0.68 * (baseline - pad) - stem / 2 - r
    stem_end = baseline + 9 * unit - stem / 2
    body = (
        f'<path d="M{left:.2f} {pad + bar / 2:.2f} V{bowl_centre:.2f} '
        f'A{r:.2f} {r:.2f} 0 0 0 {right:.2f} {bowl_centre:.2f} '
        f'M{right:.2f} {pad + bar / 2:.2f} V{stem_end:.2f}" '
        f'stroke="{ink}" stroke-width="{stem:.2f}" stroke-linejoin="round" fill="none"/>'
        f'<circle cx="{right:.2f}" cy="{stem_end:.2f}" r="{stem / 2:.2f}" fill="{ink}"/>'
    )
    words_x = right + stem / 2 + (40 + tracking) * unit
    words, advance = WM.svg("ARIKSHANAM", words_x, baseline, cap, {None: ink}, tracking)
    end = words_x + advance - 64 * unit
    body += (
        f'<rect x="{pad}" y="{pad}" width="{end - pad:.2f}" height="{bar:.2f}" '
        f'rx="{bar / 2:.2f}" fill="{ORANGE}"/>'
    )
    return doc(end + pad, baseline + pad, body + words, background)


def place(svg, x, y, width=None, scale=None):
    """Nests a finished SVG document inside another, at a width or at a scale."""
    view = svg.split('viewBox="')[1].split('"')[0]
    vw, vh = (float(n) for n in view.split()[2:])
    width = width or vw * scale
    height = width * vh / vw
    inner = svg.split(">", 1)[1].rsplit("</svg>", 1)[0]
    return (f'<svg x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
            f'viewBox="{view}">{inner}</svg>'), height


def label(text, x, y, colour="#8A8478"):
    words, _ = WM.svg(text.upper(), x, y, 15, {None: colour}, 90)
    return words


def contact_sheet():
    width, margin, gutter = 2400, 80, 40
    files = {p.stem: p.read_text() for p in OUT.glob("*.svg") if p.stem != "contact-sheet"}
    body, y = [], margin

    title, _ = WM.svg("PARIKSHANAM.", margin, y + 44, 44, {None: NAVY, 11: ORANGE}, 20)
    body.append(title + label("Mark and lockups, round 2", margin, y + 84))
    y += 140

    marks = [("navy", "Primary"), ("paper", "Light"), ("orange", "Orange"), ("mono", "Themed icon"),
             ("dot", "Headline + stop"), ("bubble", "OMR bubble"), ("bowl", "Answer in bowl"),
             ("open", "Open arm"), ("seal", "Certificate seal")]
    cell = (width - 2 * margin - gutter * (len(marks) - 1)) / len(marks)
    for i, (style, name) in enumerate(marks):
        svg, h = place(files[f"mark-{style}"], margin + i * (cell + gutter), y, cell)
        body.append(svg + label(name, margin + i * (cell + gutter), y + h + 34))
    y += cell + 90

    body.append(label("Real pixel sizes: 96, 48, 32, 24, 16", margin, y))
    x = margin
    for px in [96, 48, 32, 24, 16]:
        for style, dx in [("navy", 0), ("paper", px + 16)]:
            svg, _ = place(files[f"mark-{style}"], x + dx, y + 24, px)
            body.append(svg)
        x += 2 * px + 64
    y += 96 + 80

    rows = [
        [("lockup-horizontal", "Horizontal, recommended"),
         ("lockup-horizontal-glyph", "Untiled, bilingual baseline")],
        [("lockup-horizontal-site", "Exactly as the website header"),
         ("lockup-horizontal-mono", "Single colour mark")],
        [("lockup-horizontal-title", "Title case"), ("lockup-horizontal-lower", "Lower case")],
        [("lockup-horizontal-dark", "On navy"), ("lockup-horizontal-dark-glyph", "On navy, untiled")],
        [("lockup-headline", "Wild card: the headline runs over the word"),
         ("lockup-headline-dark", "Wild card on navy")],
    ]
    # One scale for every lockup, so the cap heights match across the sheet.
    half = (width - 2 * margin - gutter) / 2
    for row in rows:
        tallest = 0
        for i, (name, caption) in enumerate(row):
            svg, h = place(files[name], margin + i * (half + gutter), y, scale=0.62)
            body.append(svg + label(caption, margin + i * (half + gutter), y + h + 34))
            tallest = max(tallest, h)
        y += tallest + 90

    third = (width - 2 * margin - 2 * gutter) / 3
    tallest = 0
    for i, (name, caption) in enumerate([("lockup-stacked", "Stacked"),
                                         ("lockup-stacked-tagline", "Stacked with line"),
                                         ("lockup-stacked-dark", "Stacked on navy")]):
        svg, h = place(files[name], margin + i * (third + gutter), y, scale=0.5)
        body.append(svg + label(caption, margin + i * (third + gutter), y + h + 34))
        tallest = max(tallest, h)
    y += tallest + 60 + margin

    return doc(width, y, "".join(body), "#FFFFFF")


def render(name, svg, png_width=None):
    path = OUT / f"{name}.svg"
    path.write_text(svg)
    cmd = ["rsvg-convert", str(path), "-o", str(OUT / "png" / f"{name}.png")]
    if png_width:
        cmd[1:1] = ["-w", str(png_width)]
    subprocess.run(cmd, check=True)


def main():
    (OUT / "png").mkdir(parents=True, exist_ok=True)

    for style in ["navy", "paper", "orange", "dot", "mono", "seal"]:
        render(f"mark-{style}", doc(1024, 1024, mark(1024, 0, 0, style)), 1024)
    render("mark-bubble", doc(1024, 1024, mark(1024, 0, 0, "bubble", pa(overhang=210))), 1024)
    render("mark-bowl", doc(1024, 1024, mark(1024, 0, 0, "bowl", pa(counter=190, height=520,
                                                                     bowl=0.75))), 1024)
    render("mark-open", doc(1024, 1024, mark(1024, 0, 0, "open", pa(height=560, bowl=0.73,
                                                                     open_arm=True))), 1024)

    navy_tile = lambda s, x, y: mark(s, x, y, "navy")  # noqa: E731
    render("lockup-horizontal", horizontal("PARIKSHANAM.", navy_tile), 1600)
    render("lockup-horizontal-site", horizontal("PARIKSHANAM.", navy_tile, period=NAVY, tracking=0),
           1600)
    render("lockup-horizontal-title", horizontal("Parikshanam", navy_tile, tracking=0), 1600)
    render("lockup-horizontal-lower", horizontal("parikshanam.", navy_tile, tracking=0), 1600)
    render("lockup-horizontal-glyph", horizontal_glyph("PARIKSHANAM."), 1600)
    render("lockup-horizontal-dark",
           horizontal("PARIKSHANAM.", lambda s, x, y: mark(s, x, y, "orange"), ink=PAPER,
                      background=NAVY), 1600)
    render("lockup-horizontal-dark-glyph",
           horizontal_glyph("PARIKSHANAM.", ink=PAPER, background=NAVY), 1600)
    render("lockup-horizontal-mono",
           horizontal("PARIKSHANAM.", lambda s, x, y: mark(s, x, y, "mono"), period=NAVY), 1600)
    render("lockup-stacked", stacked("PARIKSHANAM."), 1000)
    render("lockup-stacked-tagline",
           stacked("PARIKSHANAM.", tagline="OLYMPIAD PREP  CLASS 6-10"), 1000)
    render("lockup-stacked-dark", stacked("PARIKSHANAM.", "orange", ink=PAPER, background=NAVY),
           1000)
    render("lockup-headline", headline_lockup(), 1600)
    render("lockup-headline-dark", headline_lockup(ink=PAPER, background=NAVY), 1600)

    render("contact-sheet", contact_sheet())

    for px in [192, 96, 48, 32, 24, 16]:
        subprocess.run(["rsvg-convert", "-w", str(px), str(OUT / "mark-navy.svg"), "-o",
                        str(OUT / "png" / f"mark-navy-{px}.png")], check=True)


if __name__ == "__main__":
    main()
