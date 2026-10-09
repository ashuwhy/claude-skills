"""Nunito and Roboto for the website, admin and teacher apps, cut down to what our pages draw and
loaded with next/font/local. They used to come from next/font/google, which fetches from Google
during the build; on 2026-10-05 one of those fetches came back with a URL Turbopack could not
resolve and the website deploy failed. Files in the repo cannot do that.

Both stay variable, so every weight is one file, and unhinted, as Google serves them outside
Windows. Each is one file rather than Google's per-script split, because next/font/local has no
unicode-range: latin, which is what was preloaded before, plus the few characters our pages
actually use. Anything else falls back to the system font, as it already did outside latin.

Run from the repo root: python docs/brand/make_fonts.py (needs fonttools and brotli)
"""

import io

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from make_lockups import ROOT

SOURCES = ROOT / "apps/web/public/fonts"

# Google's unicode-range for its latin subset, the file next/font/google preloaded.
LATIN = [*range(0x00, 0x100), 0x131, 0x152, 0x153, 0x2BB, 0x2BC, 0x2C6, 0x2DA, 0x2DC, 0x304,
         0x308, 0x329, *range(0x2000, 0x2070), 0x20AC, 0x2122, 0x2191, 0x2193, 0x2212, 0x2215,
         0xFEFF, 0xFFFD]
RUPEE = [0x20B9]
# Quiz questions and lesson text are Roboto: Greek letters for angles and constants,
# superscript and subscript digits, eighths, and the operators in the answer keys. Roboto has no
# arrows, thirds or set symbols, and Nunito no Greek; those fell back before and still do.
MATHS = [*range(0x391, 0x3AA), *range(0x3B1, 0x3CA), *range(0x2070, 0x20A0),
         *range(0x215B, 0x215F), 0x2206, 0x2211, 0x221A, 0x221E, 0x2248, 0x2260, 0x2264, 0x2265]


def cut(font, unicodes, name, pin=None):
    options = subset.Options()
    options.flavor = "woff2"
    options.hinting = False
    # Google keeps the figure styles too; tabular figures line up the scores and timers.
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
    for app in ["web", "admin", "teacher"]:
        out = ROOT / f"apps/{app}/src/app/fonts/{name}.woff2"
        out.parent.mkdir(exist_ok=True)
        out.write_bytes(woff2.getvalue())
    print(f"{name}: {len(font.getBestCmap())} characters, {len(woff2.getvalue())} bytes")


def main():
    cut(TTFont(SOURCES / "Nunito-VariableFont_wght.ttf"), LATIN + RUPEE, "nunito")
    # The pages never set font-stretch, so width is pinned at normal, as Google serves it.
    cut(TTFont(SOURCES / "Roboto-VariableFont_wdth,wght.ttf"), LATIN + RUPEE + MATHS, "roboto",
        pin={"wdth": 100})


if __name__ == "__main__":
    main()
