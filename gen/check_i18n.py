#!/usr/bin/env python3
"""Checks that i18n/<lang>.json matches i18n/en.json: the same keys, {placeholders}, HTML tags and link targets.

Usage: python3 gen/check_i18n.py [lang ...]   (no arguments: every language file)
"""
import json, os, re, sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Keys that must stay exactly as in English.
FIXED = {"g1.slug", "g2.slug", "g3.slug"}


def load(code):
    with open(os.path.join(ROOT, "i18n", code + ".json"), encoding="utf-8") as f:
        return json.load(f)


def shape(text):
    return (Counter(re.findall(r"\{\w+\}", text)), Counter(re.findall(r"</?([a-z]+)", text)),
            Counter(re.findall(r'href="([^"]*)"', text)))


def check(code, en):
    errors = []
    try:
        tr = load(code)
    except ValueError as err:
        return ["invalid JSON: %s" % err]
    for key in sorted(set(en) - set(tr)):
        errors.append("missing key %s" % key)
    for key in sorted(set(tr) - set(en)):
        errors.append("extra key %s" % key)
    for key in sorted(set(en) & set(tr)):
        if not isinstance(tr[key], str) or not tr[key].strip():
            errors.append("%s: empty" % key)
            continue
        if key in FIXED and tr[key] != en[key]:
            errors.append("%s: must stay %r" % (key, en[key]))
        (p1, t1, h1), (p2, t2, h2) = shape(en[key]), shape(tr[key])
        if p1 != p2:
            errors.append("%s: placeholders %s, English has %s" % (key, dict(p2), dict(p1)))
        if t1 != t2:
            errors.append("%s: tags %s, English has %s" % (key, dict(t2), dict(t1)))
        if h1 != h2:
            errors.append("%s: links %s, English has %s" % (key, dict(h2), dict(h1)))
        if re.search(r"[<>]", re.sub(r"</?(a|strong|em|br)\b[^>]*>", "", tr[key])):
            errors.append("%s: stray < or >" % key)
    return errors


def main():
    en = load("en")
    codes = sys.argv[1:] or sorted(f[:-5] for f in os.listdir(os.path.join(ROOT, "i18n")) if f != "en.json")
    bad = 0
    for code in codes:
        errors = check(code, en)
        bad += bool(errors)
        print("%s: %s" % (code, "ok" if not errors else "%d problems" % len(errors)))
        for err in errors:
            print("  " + err)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
