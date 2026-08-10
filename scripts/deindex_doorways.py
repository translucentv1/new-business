#!/usr/bin/env python3
"""Nimmt die Stadt-Doorway-Seiten unter t/ aus der Index-Flaeche.

WARUM (MEASURED 2026-08-10, Tick):
-----------------------------------
Die Live-Sitemap enthielt 1232 URLs. Zusammensetzung gemessen:
    t/    468 Seiten   Median 65 Woerter
    seo/  693 Seiten   Median 191 Woerter
    blog/  51 Seiten   <- die einzigen Seiten, die das AKTUELLE Geschaeft tragen
Die 51 Geldseiten waren damit 4,1 % der eingereichten URL-Menge.

Duplikat-Messung (Eigennamen -> X, Zahlen -> N, dann Hash des Rumpftextes):
    t/    406 von 468 Dateien = 86,8 % liegen in Duplikatgruppen,
          groesste Gruppen 51/51/51/50/50 identische Ruempfe
          ("ADHS Wochenplaner Hagen" vs "... Luebeck" vs "... Bremen").
    seo/  2 von 693 = 0,3 % -> KEINE Duplikatstruktur.

Daraus folgt eine SAUBERE TRENNUNG statt eines Rundumschlags:
  * t/   ist eine Stadtnamen-Tauschvorlage = Doorway-Muster. Wird deindexiert.
  * seo/ ist trotz Duennheit eigenstaendiger Text. KEIN Beleg fuer einen Verstoss
         -> bleibt unangetastet. Vermutung ist kein Grund zum Loeschen.

WAS DAS SKRIPT NICHT BEHAUPTET:
Es ist NICHT gemessen, dass Bing/DDG die Domain wegen dieser Seiten abgewertet
hat. Gemessen ist nur: 0 Index-Treffer bei nachweislich zaehlfaehigem Instrument
(bing_index_check.py, Positivkontrolle 10 Treffer) und 86,8 % Duplikatquote unter
t/. Die Deindexierung entfernt ein bekanntes Risiko, sie ist keine bewiesene
Ursachenbehebung.

RISIKO ~ 0: die Seiten hatten in Wochen 0 gemessene Index-Treffer und 0 Sales.
Traffic, den es messbar nicht gibt, kann nicht verloren gehen. Die Dateien
bleiben online und kaufbar (kein 404, kein Rueckbau), nur die Index-Freigabe
faellt weg. noindex,FOLLOW -> interne Links bleiben verwertbar.

Nutzung:
    python scripts/deindex_doorways.py --check   # nur zaehlen, nichts schreiben
    python scripts/deindex_doorways.py           # anwenden (idempotent)

Ergebniswoerter:
    DOORWAY_OK        rc=0  Zielzustand erreicht (oder hergestellt)
    DOORWAY_OFFEN     rc=1  --check: Zielzustand NICHT erreicht
"""
from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOORWAY_DIR = "t"
SITEMAP = ROOT / "sitemap.xml"
NOINDEX_TAG = '<meta name="robots" content="noindex,follow">'
LOC_MARKER = "/new-business/t/"


def doorway_files() -> list[Path]:
    return sorted(Path(p) for p in glob.glob(str(ROOT / DOORWAY_DIR / "**" / "*.html"), recursive=True))


def page_state(text: str) -> str:
    """noindex | index | fehlt — was sagt das robots-Meta der Seite?"""
    m = re.search(r'<meta\s+name="robots"\s+content="([^"]*)"\s*/?>', text, re.I)
    if not m:
        return "fehlt"
    return "noindex" if "noindex" in m.group(1).lower() else "index"


def fix_page(text: str) -> str:
    state = page_state(text)
    if state == "noindex":
        return text
    if state == "index":
        return re.sub(
            r'<meta\s+name="robots"\s+content="[^"]*"\s*/?>',
            NOINDEX_TAG,
            text,
            count=1,
            flags=re.I,
        )
    # kein robots-Meta -> vor </head> einsetzen
    if "</head>" in text:
        return text.replace("</head>", NOINDEX_TAG + "\n</head>", 1)
    return text


def sitemap_counts(text: str) -> tuple[int, int]:
    """(gesamt <loc>, davon Doorway-URLs)"""
    locs = re.findall(r"<loc>(.*?)</loc>", text)
    return len(locs), sum(1 for u in locs if LOC_MARKER in u)


def strip_sitemap(text: str) -> str:
    """Entfernt genau die <url>-Bloecke, deren <loc> auf /t/ zeigt."""
    return re.sub(
        r"[ \t]*<url>(?:(?!</url>).)*?<loc>[^<]*" + re.escape(LOC_MARKER) + r"[^<]*</loc>.*?</url>\s*\r?\n?",
        "",
        text,
        flags=re.S,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="nur messen, nichts schreiben")
    args = ap.parse_args()

    files = doorway_files()
    if not files:
        print("KEINE Doorway-Dateien gefunden -> nichts zu tun")
        return 0

    before = {"noindex": 0, "index": 0, "fehlt": 0}
    for f in files:
        before[page_state(f.read_text(encoding="utf-8", errors="replace"))] += 1

    sm_text = SITEMAP.read_text(encoding="utf-8", errors="replace")
    sm_total, sm_doorway = sitemap_counts(sm_text)

    print(f"Doorway-Dateien unter {DOORWAY_DIR}/: {len(files)}")
    print(f"  robots-Meta vorher: noindex={before['noindex']} index={before['index']} fehlt={before['fehlt']}")
    print(f"Sitemap: {sm_total} <loc>, davon Doorway-URLs: {sm_doorway}")

    offen = before["index"] + before["fehlt"] + sm_doorway
    if args.check:
        if offen:
            print(f"ERGEBNIS: DOORWAY_OFFEN ({offen} offene Posten)")
            return 1
        print("ERGEBNIS: DOORWAY_OK (Zielzustand bereits erreicht)")
        return 0

    changed = 0
    for f in files:
        t = f.read_text(encoding="utf-8", errors="replace")
        n = fix_page(t)
        if n != t:
            f.write_text(n, encoding="utf-8", newline="")
            changed += 1

    if sm_doorway:
        new_sm = strip_sitemap(sm_text)
        SITEMAP.write_text(new_sm, encoding="utf-8", newline="")
    else:
        new_sm = sm_text

    # Gegenmessung am geschriebenen Zustand, nicht am Vorhaben
    after = {"noindex": 0, "index": 0, "fehlt": 0}
    for f in doorway_files():
        after[page_state(f.read_text(encoding="utf-8", errors="replace"))] += 1
    sm_total2, sm_doorway2 = sitemap_counts(SITEMAP.read_text(encoding="utf-8", errors="replace"))

    print(f"  Dateien geaendert: {changed}")
    print(f"  robots-Meta nachher: noindex={after['noindex']} index={after['index']} fehlt={after['fehlt']}")
    print(f"  Sitemap nachher: {sm_total2} <loc> (vorher {sm_total}), Doorway-URLs: {sm_doorway2}")

    rest = after["index"] + after["fehlt"] + sm_doorway2
    if rest:
        print(f"ERGEBNIS: DOORWAY_OFFEN ({rest} offen nach Lauf)")
        return 1
    print("ERGEBNIS: DOORWAY_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
