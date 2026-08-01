#!/usr/bin/env python3
"""retitle.py — repariert Titel/H1/Description der Landingpages ($0-SEO).

Befund 2026-08-01: 13 der 21 blog/-Seiten trugen noch den Bug-Titel aus der
alten traffic_engine ("KI: Bewerbung Schreiben Lassen Ki – KI in 24h":
Title-Case, doppeltes "Ki"). 3 weitere hatten das Suffix doppelt
("... in 24h – KI in 24h"). Beides kostet Klickrate im Suchergebnis.

Dieses Skript schreibt die kuratierten Titel/Descriptions aus
traffic_engine.KEYWORDS in die bestehenden Seiten. Idempotent.

  python scripts/retitle.py           # reparieren
  python scripts/retitle.py --check   # nur pruefen (Exit 1 = noch kaputt)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import traffic_engine as te  # noqa: E402

SUFFIX = " – KI in 24h"


def full_title(title: str) -> str:
    """Suffix nur anhaengen, wenn der kuratierte Titel ihn nicht schon traegt."""
    return title if "24h" in title else title + SUFFIX


def main() -> int:
    check = "--check" in sys.argv
    fixed, stale = [], []
    for kw, title, desc in te.KEYWORDS:
        p = ROOT / "blog" / f"{te.slug(kw)}.html"
        if not p.exists():
            continue
        html = orig = p.read_text(encoding="utf-8")
        html = re.sub(r"<title>.*?</title>",
                      lambda _m: f"<title>{full_title(title)}</title>", html, count=1, flags=re.S)
        html = re.sub(r'<meta name="description" content=".*?">',
                      lambda _m: f'<meta name="description" content="{desc}">',
                      html, count=1, flags=re.S)
        html = re.sub(r"<h1>.*?</h1>", lambda _m: f"<h1>{title}</h1>",
                      html, count=1, flags=re.S)
        if html != orig:
            (stale if check else fixed).append(te.slug(kw))
            if not check:
                p.write_text(html, encoding="utf-8")
    print(f"retitle: {len(fixed)} repariert, {len(stale)} veraltet")
    for s in fixed + stale:
        print(f"  {s}")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
