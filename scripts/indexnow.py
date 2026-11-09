#!/usr/bin/env python3
"""Tells IndexNow (Bing, Yandex, Seznam, Naver) which pages changed, so they're recrawled within hours.

Usage: scripts/indexnow.py [YYYY-MM-DD]   (default: today) after the deploy is live.
Submits every URL whose lastmod in data/lastmod.json is that date. Standard library only.
"""
import datetime, json, os, sys, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "gen"))
from build import BASE_URL, INDEXNOW_KEY  # noqa: E402


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    with open(os.path.join(ROOT, "data", "lastmod.json"), encoding="utf-8") as f:
        urls = [u for u, v in json.load(f).items() if v["date"] == day]
    if not urls:
        print("nothing changed on", day)
        return
    body = json.dumps({"host": BASE_URL.split("//")[1], "key": INDEXNOW_KEY,
                       "keyLocation": "%s/%s.txt" % (BASE_URL, INDEXNOW_KEY), "urlList": urls[:10000]}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(resp.status, "submitted", len(urls), "URLs for", day)


if __name__ == "__main__":
    main()
