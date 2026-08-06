#!/usr/bin/env python3
"""Idempotent: neue blog/-Seiten in sitemap.xml + index.html eintragen.

Kein Rateschritt: Format wird 1:1 aus bestehenden Eintraegen kopiert.
Aufruf: python scripts/_tick_add_urls.py <slug> [<slug> ...]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "sitemap.xml"
INDEX = ROOT / "index.html"
BASE = "https://translucentv1.github.io/new-business"


def title_of(slug: str) -> str:
    p = ROOT / "blog" / f"{slug}.html"
    m = re.search(r"<title>(.*?)</title>", p.read_text(encoding="utf-8"), re.S)
    return m.group(1).split("–")[0].strip() if m else slug.replace("-", " ")


def main() -> int:
    slugs = sys.argv[1:]
    if not slugs:
        print("kein slug uebergeben")
        return 1

    sm = SITEMAP.read_text(encoding="utf-8")
    added_sm = []
    for s in slugs:
        loc = f"{BASE}/blog/{s}.html"
        if loc in sm:
            continue
        entry = (f'  <url><loc>{loc}</loc><changefreq>weekly</changefreq>'
                 f'<priority>0.8</priority></url>\n')
        sm = sm.replace("</urlset>", entry + "</urlset>")
        added_sm.append(s)
    if added_sm:
        SITEMAP.write_text(sm, encoding="utf-8")

    ix = INDEX.read_text(encoding="utf-8")
    added_ix = []
    for s in slugs:
        href = f"/new-business/blog/{s}.html"
        if href in ix:
            continue
        t = title_of(s).replace("&", "&amp;")
        li = f'      <li><a href="{href}">{t}</a></li>\n'
        # nach dem LETZTEN vorhandenen blog-<li> einfuegen
        matches = list(re.finditer(r'[ \t]*<li><a href="/new-business/blog/[^"]+\.html">.*?</li>\n', ix))
        if not matches:
            print(f"KEIN ANKER fuer {s} in index.html")
            continue
        last = matches[-1]
        ix = ix[:last.end()] + li + ix[last.end():]
        added_ix.append(s)
    if added_ix:
        INDEX.write_text(ix, encoding="utf-8")

    print(f"sitemap +{len(added_sm)} {added_sm}")
    print(f"index   +{len(added_ix)} {added_ix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
