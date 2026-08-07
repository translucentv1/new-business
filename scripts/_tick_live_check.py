#!/usr/bin/env python3
"""Tick-Check: enthaelt die LIVE ausgelieferte sitemap.xml / index.html die
neuen Slugs? (MEASURED gegen das Netz, nicht gegen den lokalen Baum.)"""
import sys
import urllib.request

BASE = "https://translucentv1.github.io/new-business"
SLUGS = sys.argv[1:] or ["karteikarten-erstellen-lassen-ki", "text-kuerzen-lassen"]


def get(path: str) -> str:
    req = urllib.request.Request(f"{BASE}/{path}", headers={"User-Agent": "tick-check/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"{path}: HTTP {r.status}")
        return r.read().decode("utf-8", "replace")


sm = get("sitemap.xml")
ix = get("index.html")
for s in SLUGS:
    print(f"  {s}: live-sitemap={s in sm}  live-index={s in ix}")
print(f"live-sitemap <loc>-Eintraege: {sm.count('<loc>')}")
