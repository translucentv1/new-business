#!/usr/bin/env python3
"""Einmal-Reparatur Ticket 13: Datenschutz-Link in den Rechts-Footer JEDER Seite.

Ersetzt genau den bestehenden Footer-Block
    <div class="note"><a ...impressum.html>Impressum</a> &middot; <a ...agb.html>AGB</a></div>
durch dieselbe Zeile inkl. Datenschutz. Faellt eine Seite nicht auf dieses Muster,
wird sie NICHT angefasst, sondern gemeldet -- kein Blind-Insert in fremdes Markup.
"""
from __future__ import annotations

import glob
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DS = '<a href="/new-business/datenschutz.html">Datenschutz</a>'

# Footer-Zeile mit Impressum + AGB, aber ohne Datenschutz.
PAT = re.compile(
    r'(<div class="note">\s*<a href="/new-business/impressum\.html">Impressum</a>\s*&middot;\s*'
    r'<a href="/new-business/agb\.html">AGB</a>)(\s*</div>)'
)


def main() -> int:
    dry = "--apply" not in sys.argv
    files = sorted(glob.glob(os.path.join(ROOT, "*.html"))) + sorted(
        glob.glob(os.path.join(ROOT, "blog", "*.html"))
    )
    patched, skipped, already = [], [], []
    for f in files:
        rel = os.path.relpath(f, ROOT).replace("\\", "/")
        text = open(f, encoding="utf-8").read()
        if "datenschutz.html" in text:
            already.append(rel)
            continue
        new, n = PAT.subn(r'\1 &middot; ' + DS + r'\2', text, count=1)
        if n != 1:
            skipped.append(rel)
            continue
        if not dry:
            open(f, "w", encoding="utf-8", newline="").write(new)
        patched.append(rel)

    print("Modus            = %s" % ("APPLY" if not dry else "DRY-RUN"))
    print("hat Link bereits = %d" % len(already))
    print("gepatcht         = %d" % len(patched))
    print("NICHT gepatcht   = %d" % len(skipped))
    for s in skipped:
        print("   ! Muster nicht gefunden: %s" % s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
