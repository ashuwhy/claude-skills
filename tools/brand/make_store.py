"""Builds the Play listing art: six phone screenshots (1080x1920) and the feature graphic (1024x500).

Frames are HTML rendered by headless Chrome, so the type is the same Nunito the site ships.
captures/ holds real screens from my Pixel 8a (1080x2400) on the Play build, light theme
except the two -dark ones. Never capture a certificate search result: it shows a student's
name, school and roll number.

Run from the repo root: python3 docs/brand/store/make_store.py
Upload: python3 tools/play-store/play.py art --feature docs/brand/store/png/feature.png docs/brand/store/png/phone-*.png
"""

import base64
import io
import subprocess
import tempfile
from functools import cache
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CAPTURES = HERE / "captures"
OUT = HERE / "png"
FONTS = ROOT / "apps/web/public/fonts"
LOGO = ROOT / "docs/brand/logo"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

NAVY = "#1B3A6E"
ORANGE = "#E8720C"
TEAL = "#1B8A7A"
CREAM = "#FFFBF7"
PEACH = "#F9CDA8"

# The body is drawn, not traced. My phone reports its own display corners (radius 128)
# and camera cutout through dumpsys. The real 8a's bezel (75 px at the sides, deeper at
# the chin) read as too heavy at listing size, so the bezel is one even 58 px all round.
# The body corners are concentric with the display's, which is what makes the 8a look
# round and not boxy.
BEZEL = 58
BODY = (1080 + 2 * BEZEL, 2400 + 2 * BEZEL)
DISPLAY_AT = (BEZEL, BEZEL)
DISPLAY_RADIUS = 128
BODY_RADIUS = DISPLAY_RADIUS + BEZEL
CAMERA = (539.5, 68.7, 29)
RAIL = 12
BUTTON_OUT = 7
# Obsidian: matte black aluminium around black glass. The lit outer edge is what keeps a
# dark phone visible on the navy frames.
RAIL_RGB = (43, 44, 47)
EDGE_RGB = (112, 115, 121)
GLASS_RGB = (6, 6, 7)

# captures/status-bar.png is the top of my Pixel 8a with the battery service told the
# cable was out, which got the signal reading full. The battery still drew green with a
# shield: that is Pixel's charging-optimised state, and the override cannot clear it. So
# every capture's bar is rebuilt from that strip: the clock, signal and wifi keep their
# glyphs, the battery keeps its outline, fill level and digits in the plain ink colour,
# and the USB notification and the shield are left out. Rows 0-117 of every capture are
# flat colour apart from those icons, so the whole band can be repainted.
STATUS_ROWS = 118
CLOCK = (82, 154)
ICONS = (799, 901)
BATTERY = (919, 983)
# The shield sits over the middle of the battery's right cap. Rows 50-72 of the cap are
# one straight edge, so row 50, which the shield misses, stands in for 51-71.
CAP_COLUMNS = (972, 983)
CAP_ROWS = (50, 72)
# The empty part of the battery is the ink at this strength over the bar: measured on my
# phone, white at 55% on a dark bar and black at 20% on a light one.
TRACK_INK = {"dark": 0.55, "light": 0.20}
# Without the shield the battery is the last icon, so it moves out to where the shield
# ended, 82px from the edge like the clock.
ICON_SHIFT = 999 - BATTERY[1]


def font_face(family, file, weights):
    data = base64.b64encode((FONTS / file).read_bytes()).decode()
    return (
        f"@font-face{{font-family:{family};font-weight:{weights};"
        f"src:url(data:font/ttf;base64,{data}) format('truetype')}}"
    )


CSS = (
    font_face("Nunito", "Nunito-VariableFont_wght.ttf", "200 1000")
    + font_face("Roboto", "Roboto-VariableFont_wdth,wght.ttf", "100 900")
    + """
*{margin:0;padding:0;box-sizing:border-box}
body{position:relative;overflow:hidden;font-family:Nunito}
.head{position:absolute}
.line{display:block;width:fit-content;font-weight:900;line-height:1;white-space:nowrap}
.sub{font-family:Roboto;font-weight:500}
.phone{position:absolute;
  filter:drop-shadow(0 40px 50px rgba(16,24,40,.30)) drop-shadow(0 12px 16px rgba(16,24,40,.18))}
.card{position:absolute;overflow:hidden;
  box-shadow:0 40px 80px rgba(16,24,40,.28),0 10px 24px rgba(16,24,40,.16)}
.card img{display:block;width:100%}
"""
)

@cache
def status_layers():
    """Ink coverage of the clock and icons, and battery fill and track, from the real strip."""
    strip = np.asarray(Image.open(CAPTURES / "status-bar.png").convert("RGB"), dtype=float)
    top, bottom = CAP_ROWS
    strip[top + 1 : bottom, slice(*CAP_COLUMNS)] = strip[top, slice(*CAP_COLUMNS)]
    bar = strip[5, 540, 0]
    glyphs = np.clip((strip.mean(2) - bar) / (255 - bar), 0, 1)
    # The fill is the only strongly green part, so green over red measures it: 180 for the
    # fill, 0 for the bar and the grey track. The digits are a dark green (45), and since
    # they are cut out of the fill they should read as zero too; they only ever sit inside
    # the capsule, so that is where 45 counts as nothing. The grey track is what is left of
    # the red channel once the fill is accounted for.
    battery = strip[:, slice(*BATTERY)]
    red, green = battery[..., 0], battery[..., 1]
    chroma = green - red
    fill = np.clip(chroma / 180, 0, 1)
    fill[47:76, 4:] = np.clip((chroma[47:76, 4:] - 45) / 135, 0, 1)
    track = np.clip((red - bar - 7 * fill) / (148 - bar), 0, 1)
    return glyphs, fill, track


def repaint_status_bar(screen):
    pixels = np.asarray(screen, dtype=float).copy()
    bar = pixels[10, 540]
    dark = bar.mean() < 128
    ink = np.full(3, 255.0 if dark else 0.0)
    glyphs, fill, track = status_layers()
    band = np.broadcast_to(bar, (STATUS_ROWS, 1080, 3)).copy()
    for (x0, x1), shift in ((CLOCK, 0), (ICONS, ICON_SHIFT)):
        cover = glyphs[:, x0:x1, None]
        band[:, x0 + shift : x1 + shift] = cover * ink + (1 - cover) * bar
    track_rgb = bar + TRACK_INK["dark" if dark else "light"] * (ink - bar)
    fill, track = fill[..., None], track[..., None]
    x0, x1 = BATTERY
    band[:, x0 + ICON_SHIFT : x1 + ICON_SHIFT] = (
        fill * ink + track * track_rgb + (1 - fill - track) * bar
    )
    pixels[:STATUS_ROWS] = band
    return pixels


def rounded_rect(shape, box, radius):
    """Antialiased coverage of a rounded rectangle, from its exact distance field."""
    x0, y0, x1, y1 = box
    ys, xs = np.mgrid[: shape[0], : shape[1]].astype(np.float32) + 0.5
    half_w, half_h = (x1 - x0) / 2, (y1 - y0) / 2
    qx = np.abs(xs - (x0 + half_w)) - (half_w - radius)
    qy = np.abs(ys - (y0 + half_h)) - (half_h - radius)
    outside = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0))
    distance = outside + np.minimum(np.maximum(qx, qy), 0) - radius
    return np.clip(0.5 - distance, 0, 1)[..., None]


def lay(canvas, cover, rgb):
    canvas[..., :3] = canvas[..., :3] * (1 - cover) + np.asarray(rgb, dtype=np.float32) * cover
    canvas[..., 3:] = canvas[..., 3:] + (1 - canvas[..., 3:]) * cover


@cache
def framed(capture):
    """One finished PNG per phone, so a rotated frame has no seam between screen and body."""
    width, height = BODY
    shape = (height, width + BUTTON_OUT)
    canvas = np.zeros((*shape, 4), dtype=np.float32)
    # Power key, then the volume rocker, on the right edge.
    for top, length in ((0.255, 0.075), (0.37, 0.13)):
        box = (width - 12, height * top, width + BUTTON_OUT, height * (top + length))
        lay(canvas, rounded_rect(shape, box, 6), RAIL_RGB)
    lay(canvas, rounded_rect(shape, (0, 0, width, height), BODY_RADIUS), EDGE_RGB)
    lay(canvas, rounded_rect(shape, (2, 2, width - 2, height - 2), BODY_RADIUS - 2), RAIL_RGB)
    inner = (RAIL, RAIL, width - RAIL, height - RAIL)
    lay(canvas, rounded_rect(shape, inner, BODY_RADIUS - RAIL), GLASS_RGB)

    x, y = DISPLAY_AT
    screen = repaint_status_bar(Image.open(CAPTURES / capture).convert("RGB"))
    cover = rounded_rect(shape, (x, y, x + 1080, y + 2400), DISPLAY_RADIUS)
    under = np.zeros((*shape, 3), dtype=np.float32)
    under[y : y + 2400, x : x + 1080] = screen
    canvas[..., :3] = canvas[..., :3] * (1 - cover) + under * cover

    cx, cy, r = CAMERA
    lens = (x + cx - r, y + cy - r, x + cx + r, y + cy + r)
    lay(canvas, rounded_rect(shape, lens, r), (4, 4, 5))
    glass = (x + cx - 13, y + cy - 13, x + cx + 13, y + cy + 13)
    lay(canvas, rounded_rect(shape, glass, 13), (22, 25, 34))

    canvas[..., 3] *= 255
    pixels = Image.fromarray(canvas.round().clip(0, 255).astype(np.uint8), "RGBA")
    png = io.BytesIO()
    pixels.save(png, "PNG")
    return "data:image/png;base64," + base64.b64encode(png.getvalue()).decode()


def phone(capture, width, left, top, rotate=0, z=1):
    """A capture in the Pixel 8a body. Width is the outside of the body, in px."""
    return (
        f'<img class="phone" src="{framed(capture)}" style="width:{width}px;left:{left}px;'
        f'top:{top}px;transform:rotate({rotate}deg);z-index:{z}">'
    )


def card(capture, box, width, left, top, rotate=0, radius=36, z=3):
    """A piece of a capture lifted off the screen, the way the FT listing floats one story."""
    x0, y0, x1, y1 = box
    scale = width / (x1 - x0)
    return f"""
<div class="card" style="width:{width}px;height:{round((y1 - y0) * scale)}px;left:{left}px;top:{top}px;
  border-radius:{radius}px;transform:rotate({rotate}deg);z-index:{z}">
  <img src="{(CAPTURES / capture).as_uri()}" style="width:{round(1080 * scale)}px;
    margin:{-round(y0 * scale)}px 0 0 {-round(x0 * scale)}px">
</div>"""


def headline(lines, size, left, top, block, ink, indent):
    """Highlighter blocks, one per line, each line stepped in from the one above."""
    spans = "".join(
        f'<span class="line" style="background:{block};color:{ink};font-size:{size}px;'
        f'padding:{size * 0.16:.0f}px {size * 0.32:.0f}px {size * 0.22:.0f}px;margin-left:{i * indent}px">'
        f"{text}</span>"
        for i, text in enumerate(lines)
    )
    return f'<div class="head" style="left:{left}px;top:{top}px;z-index:5">{spans}</div>'


def sub(text, size, left, top, width, color):
    return (
        f'<p class="sub" style="position:absolute;left:{left}px;top:{top}px;width:{width}px;'
        f'font-size:{size}px;line-height:1.35;color:{color};z-index:5">{text}</p>'
    )


def page(width, height, background, body):
    return (
        f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}"
        f"body{{width:{width}px;height:{height}px;background:{background}}}</style></head>"
        f"<body>{body}</body></html>"
    )


def logo(file, width, left, top):
    return f'<img src="{(LOGO / file).as_uri()}" style="position:absolute;width:{width}px;left:{left}px;top:{top}px">'


def phone_frames():
    return {
        "phone-1-practice": page(
            1080,
            1920,
            "linear-gradient(170deg,#FDE6D2 0%,#FAD2B0 100%)",
            logo("lockup.svg", 380, 84, 118)
            + headline(["Practise for", "your olympiad"], 104, 64, 250, CREAM, NAVY, 96)
            + sub("Maths and science sample papers for classes&nbsp;7&nbsp;to&nbsp;12", 38, 90, 545, 820, NAVY)
            + phone("practice.png", 780, 196, 720, rotate=-6),
        ),
        "phone-2-quiz": page(
            1080,
            1920,
            f"linear-gradient(180deg,{CREAM} 0%,#FBE4D0 100%)",
            headline(["29 questions.", "One at a time."], 104, 64, 150, PEACH, NAVY, 96)
            + sub("A YMRC maths paper and a YSRC science paper for your class", 38, 90, 445, 820, NAVY)
            + phone("quiz.png", 800, 140, 640),
        ),
        "phone-3-lesson": page(
            1080,
            1920,
            f"linear-gradient(180deg,{NAVY} 0%,#11284D 100%)",
            headline(["Lessons that go", "past the syllabus"], 90, 64, 150, ORANGE, "#fff", 80)
            + sub("Recorded video lessons, with a list of what each one covers", 38, 90, 420, 820,
                  "rgba(255,255,255,.82)")
            + phone("lesson.png", 800, 140, 640),
        ),
        "phone-4-my-learning": page(
            1080,
            1920,
            "linear-gradient(170deg,#FDE6D2 0%,#FAD2B0 100%)",
            headline(["Keep track of", "every lesson"], 104, 64, 150, CREAM, NAVY, 96)
            + sub("The app remembers which lessons you have finished", 38, 90, 445, 820, NAVY)
            + phone("my-learning.png", 800, 140, 640),
        ),
        "phone-5-certificate": page(
            1080,
            1920,
            f"linear-gradient(180deg,{TEAL} 0%,#136558 100%)",
            headline(["Certificates,", "on your phone"], 104, 64, 150, CREAM, NAVY, 96)
            + sub("Took part in the Young Scientist Challenge? Find yours and download it", 38, 90,
                  445, 860, "rgba(255,255,255,.88)")
            + phone("certificate.png", 800, 140, 700)
            + card("practice.png", (53, 391, 1027, 564), 900, 90, 1752, rotate=-3),
        ),
        "phone-6-budget": page(
            1080,
            1920,
            "linear-gradient(180deg,#14223D 0%,#0B1426 100%)",
            headline(["Smooth on", "budget phones"], 104, 64, 150, ORANGE, "#fff", 96)
            + sub("Light or dark theme, and lighter visuals on <span style='white-space:nowrap'>low-memory</span> phones", 38, 90, 445, 860,
                  "rgba(255,255,255,.82)")
            + phone("quiz.png", 620, 40, 700, rotate=-5, z=1)
            + phone("practice-dark.png", 620, 420, 760, rotate=5, z=2),
        ),
    }


def feature():
    return page(
        1024,
        500,
        f"linear-gradient(160deg,{NAVY} 0%,#11284D 100%)",
        logo("lockup-on-dark.svg", 330, 60, 62)
        + headline(["Practise for", "your olympiad"], 58, 46, 150, ORANGE, "#fff", 54)
        + sub("Maths and science sample papers for classes&nbsp;7&nbsp;to&nbsp;12", 21, 62, 330, 420,
              "rgba(255,255,255,.82)")
        + phone("quiz.png", 300, 560, 70, rotate=-8, z=1)
        + phone("practice.png", 300, 760, 40, rotate=6, z=2),
    )


def render(name, html, width, height):
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"{name}.html"
        shot = Path(tmp) / f"{name}.png"
        src.write_text(html)
        subprocess.run(
            [
                CHROME,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--allow-file-access-from-files",
                "--force-device-scale-factor=1",
                "--virtual-time-budget=3000",
                f"--window-size={width},{height}",
                f"--screenshot={shot}",
                src.as_uri(),
            ],
            capture_output=True,
        )
        # Chrome can write the screenshot and then exit 2 when its teardown watchdog
        # fires, so the file is the success signal, not the exit code.
        if not shot.exists():
            raise SystemExit(f"{name}: Chrome wrote no screenshot")
        # Play takes 24-bit PNG for the feature graphic; dropping alpha everywhere keeps
        # the set uniform.
        image = Image.open(shot).convert("RGB")
        if image.size != (width, height):
            raise SystemExit(f"{name}: Chrome drew {image.size}, wanted {(width, height)}")
        image.save(OUT / f"{name}.png", optimize=True)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, html in phone_frames().items():
        render(name, html, 1080, 1920)
    render("feature", feature(), 1024, 500)
    print("\n".join(sorted(p.name for p in OUT.glob("*.png"))))
