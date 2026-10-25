#!/usr/bin/env python3
"""Renders the social preview images og/<lang>.png (1200×630) with headless Chrome.

Usage: scripts/og.py [codes...]   (all languages when none are given)
Each card shows the localized App Store name and subtitle from data/store.json next to the
localized Home screenshot, on the app's green hero gradient. Run it again when the listing
or the screenshots change; gen/build.py only links to the images.
"""
import html, json, os, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "gen"))
from build import LANGUAGES, RTL, STORE  # noqa: E402

CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
PAGE = """<!doctype html><html lang="{code}" dir="{dir}"><meta charset="utf-8"><style>
html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", "Noto Sans", sans-serif;
  background: radial-gradient(120% 90% at 30% 0%, #2A8A60 0%, #1D6B4B 45%, #123F2D 100%); color: #FFF6E3;
  display: grid; grid-template-columns: 1fr 360px; gap: 56px; padding: 0 80px; box-sizing: border-box; }}
.text {{ align-self: center; }}
.icon {{ width: 112px; height: 112px; border-radius: 25px; box-shadow: 0 10px 30px rgba(0,0,0,.25); display: block; }}
h1 {{ font-size: {size}px; line-height: 1.08; font-weight: 800; letter-spacing: -.02em; margin: 36px 0 18px; }}
p {{ font-size: 34px; line-height: 1.25; margin: 0; color: #9BEBBE; font-weight: 600; }}
.site {{ margin-top: 40px; font-size: 24px; opacity: .75; }}
.phone {{ align-self: start; margin-top: 64px; background: #0b0b0c; border-radius: 56px; padding: 13px;
  box-shadow: 0 30px 60px rgba(0,0,0,.35); }}
.phone img {{ width: 100%; display: block; border-radius: 44px; }}
</style><body>
<div class="text"><img class="icon" src="{root}/assets/icon-512.png" alt="">
<h1>{name}</h1><p>{subtitle}</p><div class="site">kroky.nakolini.com</div></div>
<div class="phone"><img src="{root}/assets/shots/{code}/home.webp" alt=""></div>
</body></html>"""


def render(code):
    store = STORE.get(code, STORE["en"])
    name = store["name"]
    size = 76 if len(name) <= 22 else 64 if len(name) <= 32 else 54
    page = PAGE.format(code=code, dir="rtl" if code in RTL else "ltr", size=size, root="file://" + ROOT,
                       name=html.escape(name), subtitle=html.escape(store["subtitle"]))
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(page)
    out = os.path.join(ROOT, "og", code + ".png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    "--force-device-scale-factor=1", "--window-size=1200,630", "--screenshot=" + out,
                    "file://" + f.name], check=True, capture_output=True)
    os.unlink(f.name)
    print(code)


def main():
    os.makedirs(os.path.join(ROOT, "og"), exist_ok=True)
    codes = sys.argv[1:] or [code for code, _, _ in LANGUAGES]
    for code in codes:
        render(code)


if __name__ == "__main__":
    main()
