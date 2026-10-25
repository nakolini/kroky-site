#!/usr/bin/env python3
"""Copies the app's localized raw Simulator screenshots into assets/shots/<lang>/ as WebP.

Usage: scripts/screenshots.py [path to the kroky app repo, default ../kroky]
Needs Pillow (pip install pillow). The raw screens come from the app repo's
build/app-store-shots/iphone/<lang>/raw/, made by its scripts/app-store-shots.sh; the site
frames them in CSS and writes the captions as text, so they stay readable to search engines.
"""
import os, sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SHOTS = ["route", "home", "guide", "nudge", "walk", "settings"]
WIDTH = 600  # shown at up to 300 CSS px, so sharp on 2x screens


def main():
    app = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "..", "kroky"))
    src_root = os.path.join(app, "build", "app-store-shots", "iphone")
    for lang in sorted(os.listdir(src_root)):
        raw = os.path.join(src_root, lang, "raw")
        if not os.path.isdir(raw):
            continue
        out = os.path.join(ROOT, "assets", "shots", lang)
        os.makedirs(out, exist_ok=True)
        for name in SHOTS:
            im = Image.open(os.path.join(raw, name + ".png")).convert("RGB")
            im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
            im.save(os.path.join(out, name + ".webp"), "WEBP", quality=78, method=6)
        print(lang)


if __name__ == "__main__":
    main()
