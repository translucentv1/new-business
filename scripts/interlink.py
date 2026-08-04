#!/usr/bin/env python3
"""interlink.py — thematische Querverlinkung der Landingpages ($0-SEO-Hebel).

Warum: bis 2026-08-01 zeigte jede blog/-Seite nur auf gig.html und rtd.html.
Untereinander waren sie unverbunden -> Google sieht 21 Blaetter ohne Cluster.
Dieses Skript setzt in jede Seite einen Block mit den thematisch naechsten
Schwester-Seiten (id="related"). Idempotent: vorhandener Block wird ersetzt,
nicht dupliziert.

Nutzung:
  python scripts/interlink.py            # schreibt
  python scripts/interlink.py --check    # nur pruefen (Exit 1 wenn etwas fehlt)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
BASE = "/new-business/blog"

# Cluster = Suchintent-Nachbarschaft. Wer "Anschreiben" sucht, will oft auch
# "Lebenslauf" — genau diese Wege soll der Crawler (und der Besucher) finden.
CLUSTERS: dict[str, list[str]] = {
    "Bewerbung & Karriere": [
        "bewerbung-schreiben-lassen-ki",
        "anschreiben-erstellen-lassen-ki",
        "lebenslauf-erstellen-lassen-ki",
        "motivationsschreiben-schreiben-lassen-ki",
    ],
    "Buero & Business": [
        "powerpoint-erstellen-lassen-ki",
        "businessplan-erstellen-lassen-ki",
        "excel-tabelle-erstellen-lassen",
        "protokoll-schreiben-lassen-ki",
        "arbeitszeugnis-schreiben-lassen-ki",
        "pressemitteilung-schreiben-lassen",
        "kuendigung-schreiben-lassen-ki",
    ],
    "Marketing & Texte": [
        "text-schreiben-lassen-guenstig",
        "produktbeschreibung-schreiben-lassen",
        "newsletter-schreiben-lassen",
        "linkedin-post-schreiben-lassen",
        "instagram-caption-ki",
        "expose-schreiben-lassen-ki",
        "seo-blogartikel-schreiben-lassen",
        "website-texte-schreiben-lassen",
        "flyer-erstellen-lassen-ki",
    ],
    "Lernen & Studium": [
        "hausarbeit-schreiben-lassen-ki",
        "study-guide-erstellen-lassen",
        "quiz-fragen-erstellen-lassen",
        "korrekturlesen-lassen-ki",
        "zusammenfassung-schreiben-lassen-ki",
    ],
    "Digitale Deliverables": [
        "python-skript-erstellen-lassen",
        "notion-template-erstellen-lassen",
        "ebook-cover-erstellen-lassen",
        "rede-schreiben-lassen-ki",
    ],
}

BLOCK_RE = re.compile(r'<p id="related".*?</p>\n?', re.S)
ANCHOR = '<p id="rtd-crosslink"'


def label(slug: str) -> str:
    """Lesbarer Ankertext aus dem <title> der Zielseite (Fallback: Slug)."""
    p = BLOG / f"{slug}.html"
    if p.exists():
        m = re.search(r"<title>(.*?)</title>", p.read_text(encoding="utf-8"), re.S)
        if m:
            return m.group(1).split("–")[0].strip()
    return slug.replace("-", " ")


def block_for(slug: str) -> str | None:
    for cluster, members in CLUSTERS.items():
        if slug in members:
            others = [s for s in members if s != slug and (BLOG / f"{s}.html").exists()]
            if not others:
                return None
            links = " &middot; ".join(
                f'<a href="{BASE}/{s}.html">{label(s)}</a>' for s in others)
            return (f'<p id="related" style="margin-top:2em;font-size:.95rem">'
                    f'<strong>{cluster}:</strong> {links}</p>\n')
    return None


def main() -> int:
    check = "--check" in sys.argv
    changed, missing, skipped = [], [], []
    for p in sorted(BLOG.glob("*.html")):
        slug = p.stem
        block = block_for(slug)
        if block is None:
            skipped.append(slug)
            continue
        html = p.read_text(encoding="utf-8")
        target = BLOCK_RE.sub("", html)
        if ANCHOR not in target:
            missing.append(f"{slug} (kein rtd-crosslink-Anker)")
            continue
        target = target.replace(ANCHOR, block + ANCHOR, 1)
        if target != html:
            if check:
                missing.append(slug)
            else:
                p.write_text(target, encoding="utf-8")
                changed.append(slug)
    print(f"interlink: {len(changed)} geschrieben, {len(missing)} offen, "
          f"{len(skipped)} ohne Cluster")
    for s in missing:
        print(f"  OFFEN: {s}")
    for s in skipped:
        print(f"  KEIN CLUSTER: {s}")
    return 1 if (check and missing) else 0


if __name__ == "__main__":
    sys.exit(main())
