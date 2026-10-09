"""Variable fonts cut down to woff2 for self-hosting.

    python make_fonts.py Nunito-VariableFont_wght.ttf --out web/src/app/fonts/nunito.woff2
    python make_fonts.py "Roboto-VariableFont_wdth,wght.ttf" --sets latin,greek,maths \\
        --chars "₹ U+2190-2193" --pin wdth=100 \\
        --out web/src/app/fonts/roboto.woff2 --out admin/src/app/fonts/roboto.woff2

Self-host because a framework that downloads fonts at build time (next/font/google) puts a
network fetch in every build, and one bad response fails the deploy. Files in the repo can't.

The output matches what Google Fonts serves: variable axes kept, so every weight is one file,
and unhinted, as Google serves it outside Windows. It is one file per font rather than Google's
per-script split, because next/font/local takes no unicode-range (checked 2026-10), so the file
carries latin plus whatever else the pages actually draw. Anything left out falls back to the
system font, as it does with Google's split.

Needs fonttools and brotli (pip install fonttools brotli).
"""

import argparse
import io
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

# Google's unicode-ranges for its latin and latin-ext files (checked 2026-10).
LATIN = [*range(0x00, 0x100), 0x131, 0x152, 0x153, 0x2BB, 0x2BC, 0x2C6, 0x2DA, 0x2DC, 0x304,
         0x308, 0x329, *range(0x2000, 0x2070), 0x20AC, 0x2122, 0x2191, 0x2193, 0x2212, 0x2215,
         0xFEFF, 0xFFFD]
LATIN_EXT = [*range(0x100, 0x2BB), *range(0x2BD, 0x2C6), *range(0x2C7, 0x2CD), *range(0x2CE, 0x2D8),
             *range(0x2DD, 0x300), 0x304, 0x308, 0x329, *range(0x1D00, 0x1DC0), *range(0x1E00, 0x1EA0),
             *range(0x1EF2, 0x1F00), 0x2020, *range(0x20A0, 0x20AC), *range(0x20AD, 0x20C1), 0x2113,
             *range(0x2C60, 0x2C80), *range(0xA720, 0xA800)]
GREEK = [*range(0x391, 0x3AA), *range(0x3B1, 0x3CA)]
# Lesson and quiz text: superscript and subscript digits, eighths, and the common operators.
MATHS = [*range(0x2070, 0x20A0), *range(0x215B, 0x215F), 0x2206, 0x2211, 0x221A, 0x221E, 0x2248,
         0x2260, 0x2264, 0x2265]
SETS = {"latin": LATIN, "latin-ext": LATIN_EXT, "greek": GREEK, "maths": MATHS}


def codepoints(chars):
    """Literal characters plus U+XXXX and U+XXXX-YYYY, separated by spaces or not at all."""
    found = []
    for word in chars.split():
        if word.upper().startswith("U+"):
            first, _, last = word[2:].partition("-")
            found += range(int(first, 16), int(last or first, 16) + 1)
        else:
            found += map(ord, word)
    return found


def cut(source, unicodes, pin):
    font = TTFont(source)
    options = subset.Options()
    options.flavor = "woff2"
    options.hinting = False
    # Google keeps the figure styles; tabular figures keep scores and timers from jittering.
    options.layout_features += ["lnum", "pnum", "tnum"]
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=unicodes)
    subsetter.subset(font)
    if pin:
        # Only after subsetting: the instancer leaves gvar without the glyphs it zeroed, and the
        # subsetter expects every glyph there.
        font = instancer.instantiateVariableFont(font, pin)
    woff2 = io.BytesIO()
    subset.save_font(font, woff2, options)
    return woff2.getvalue(), len(font.getBestCmap())


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("source", type=Path, help="a .ttf or .otf, variable or not")
    parser.add_argument("--out", type=Path, action="append", required=True,
                        help="woff2 to write; repeat to write the same file into several apps")
    parser.add_argument("--sets", default="latin", help=f"comma-separated: {', '.join(SETS)}")
    parser.add_argument("--chars", default="", help='extra characters, e.g. "₹ U+2190-2193"')
    parser.add_argument("--pin", action="append", default=[], metavar="AXIS=VALUE",
                        help="fix an axis the pages never set, e.g. wdth=100; drops it from the file")
    args = parser.parse_args()

    unicodes = codepoints(args.chars)
    for name in args.sets.split(","):
        unicodes += SETS[name.strip()]
    pin = {axis: float(value) for axis, value in (p.split("=") for p in args.pin)}

    woff2, characters = cut(args.source, unicodes, pin)
    for out in args.out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(woff2)
    print(f"{args.source.name}: {characters} characters, {len(woff2)} bytes")


if __name__ == "__main__":
    main()
