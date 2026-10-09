"""Builds a course thumbnail (1600x900 JPEG) for one class.

Every card shows it whole at 16:9 now, so the text block is centred on the frame.
CourseHero lays a light scrim over the bottom 80pt (about y=590 down at phone width) and
its badges stay inside the bottom 27pt, clear of the subtitle; the cards put badges in
the top corners, clear of the tag line.

Run from the repo root: python3 docs/brand/course/make_thumbnail.py 7 8 9
Upload to course-thumbnails/courses/<id>/thumbnail-<ms>.jpg, a new path every time: the
free plan cannot purge the CDN, so an overwritten file stays stale for a year.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "store"))
from make_store import CHROME, CSS, LOGO, NAVY, ORANGE, PEACH  # noqa: E402

HERE = Path(__file__).resolve().parent
W, H = 1600, 900
PAPER = "#F9F7F5"


def tag(cls):
    # Classes 9 to 12 are sold as JEE and NEET courses; 7 and 8 as foundation.
    return "JEE, NEET + OLYMPIAD" if int(cls) >= 9 else "FOUNDATION + OLYMPIAD"


def page(cls):
    p_mark = (LOGO / "p-on-dark.svg").as_uri()
    return f"""<!doctype html><html><head><style>{CSS}
body{{width:{W}px;height:{H}px;background:{NAVY}}}
.grid{{position:absolute;inset:0;
  background-image:linear-gradient(rgba(255,255,255,.05) 2px,transparent 2px),
    linear-gradient(90deg,rgba(255,255,255,.05) 2px,transparent 2px);
  background-size:64px 64px;background-position:-2px -2px}}
.ring{{position:absolute;border-radius:50%}}
.block{{position:absolute;inset:0;display:flex;flex-direction:column;
  align-items:center;justify-content:center}}
.tag{{display:flex;align-items:center;gap:18px;color:{PEACH};font-weight:900;
  font-size:34px;letter-spacing:.14em}}
.tag img{{height:64px}}
.cls{{color:{PAPER};font-weight:900;font-size:290px;line-height:.92;letter-spacing:-.02em;
  margin-top:18px}}
.cls b{{color:{ORANGE}}}
.sub{{color:rgba(249,247,245,.82);font-size:40px;margin-top:22px}}
</style></head><body>
<div class="grid"></div>
<div class="ring" style="width:1040px;height:1040px;right:-470px;bottom:-760px;
  border:34px solid {ORANGE}"></div>
<div class="ring" style="width:620px;height:620px;left:-330px;top:-360px;
  border:22px solid rgba(249,247,245,.12)"></div>
<div class="block">
  <div class="tag"><img src="{p_mark}">{tag(cls)}</div>
  <div class="cls">Class <b>{cls}</b></div>
  <div class="sub">Maths and science, past the syllabus</div>
</div>
</body></html>"""


def build(cls):
    out = HERE / f"class-{cls}.jpg"
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "thumb.html"
        shot = Path(tmp) / "thumb.png"
        src.write_text(page(cls))
        subprocess.run(
            [
                CHROME,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--allow-file-access-from-files",
                "--force-device-scale-factor=1",
                "--virtual-time-budget=3000",
                f"--window-size={W},{H}",
                f"--screenshot={shot}",
                src.as_uri(),
            ],
            capture_output=True,
        )
        # Chrome can write the screenshot and then exit 2 when its teardown watchdog
        # fires, so the file is the success signal, not the exit code.
        if not shot.exists():
            raise SystemExit("Chrome wrote no screenshot")
        image = Image.open(shot).convert("RGB")
        if image.size != (W, H):
            raise SystemExit(f"Chrome drew {image.size}, wanted {(W, H)}")
        image.save(out, quality=88, optimize=True, progressive=True)
    return out


if __name__ == "__main__":
    for cls in sys.argv[1:]:
        print(build(cls))
