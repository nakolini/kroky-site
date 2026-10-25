Public website for Kroky: Walk Breaks, an iPhone app by [nakolini](https://nakolini.com/), served at https://kroky.nakolini.com
from the `main` branch by GitHub Pages.

This repo is the source of truth for the site. The HTML in the root and in the language folders is generated, so
edit the sources and rebuild instead of editing pages. Don't copy the app repo's old `site/` folder over it.

## Sources

- `i18n/<code>.json`: all copy, one file per language (49). `en.json` is the master; every other file has the same
  keys, placeholders and HTML tags. Covers the home page, FAQ, three guides, support, the Privacy Policy and the
  Terms of Use.
- `data/store.json`: App Store name, subtitle and keywords per language, copied from the app repo's
  `docs/app-store/listing/`. `data/captions.json`: screenshot captions.
- `gen/build.py`: the generator (Python 3, standard library only). App ID, URLs, dates and the language list are
  constants at the top.
- `assets/`: CSS, icons, the official localized App Store badges (`badges/`, unmodified from Apple's marketing
  tools) and localized screenshots (`shots/<code>/`).
- `og/<code>.png`: social preview images.

## Commands

```sh
python3 gen/check_i18n.py        # every translation matches en.json (keys, placeholders, tags, links)
python3 gen/build.py             # regenerate all pages, sitemap.xml, robots.txt, llms.txt
python3 -m http.server 8765      # preview at http://localhost:8765/
```

When the app's screenshots or listing change:

```sh
python3 scripts/screenshots.py ../kroky   # raw Simulator shots → assets/shots/<code>/*.webp (needs Pillow)
python3 scripts/og.py                     # og/<code>.png via headless Chrome
```

## URLs

- English at `/`, other languages at `/<code>/` (lowercase, e.g. `/de/`, `/pt-br/`, `/zh-hant/`), each with hreflang
  alternates and an `x-default`.
- Privacy Policy: `/privacy-policy.html` (the URL in App Store Connect) and `/<code>/privacy-policy.html`.
- Terms of Use: `/terms.html` and `/<code>/terms.html`. They incorporate Apple's standard EULA.
- Support: `/support.html`. Guides: `/guides/`.

After a release, submit `https://kroky.nakolini.com/sitemap.xml` in Google Search Console and Bing Webmaster Tools.
If the App Store Connect provider token becomes known, set `PROVIDER_TOKEN` in `gen/build.py` so badge clicks
are attributed to campaigns.
