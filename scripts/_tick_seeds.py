#!/usr/bin/env python3
"""Einmal-Helper: Seed-Liste durch kw_demand.suggest jagen (UTF-8 sicher,
unabhaengig vom Shell-Encoding). Sortiert nach Trefferzahl, markiert
'kostenlos'-Modifier (= kein Bezahlwille)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kw_demand import suggest

SEEDS = [
    "fragebogen erstellen lassen",
    "umfrage erstellen lassen",
    "projektplan erstellen lassen",
    "wochenplan erstellen lassen",
    "agenda erstellen lassen",
    "zeitplan erstellen lassen",
    "urkunde erstellen lassen",
    "quiz erstellen lassen",
    "rätsel erstellen lassen",
    "firmennamen finden lassen",
    "persona erstellen lassen",
    "interviewleitfaden erstellen lassen",
    "weihnachtskarte text schreiben lassen",
    "glückwunsch schreiben lassen",
    "youtube beschreibung schreiben lassen",
    "podcast beschreibung schreiben lassen",
    "hausordnung erstellen lassen",
    "pflichtenheft erstellen lassen",
    "lastenheft erstellen lassen",
    "ablaufplan erstellen lassen",
    "grabrede schreiben lassen",
    "kalkulation erstellen lassen",
    "visitenkarte text schreiben lassen",
    "moderationstext schreiben lassen",
]

rows = []
for s in SEEDS:
    try:
        hits = suggest(s)
    except Exception as e:  # noqa: BLE001
        print(f"=== {s} === FEHLER: {e}")
        continue
    free = sum(1 for h in hits if "kostenlos" in h.lower() or "gratis" in h.lower())
    ki = sum(1 for h in hits if any(t in h.lower() for t in ("ki", "chatgpt", "gpt", "copilot")))
    rows.append((len(hits), free, ki, s, hits))

rows.sort(key=lambda r: (-r[0], r[1]))
for n, free, ki, s, hits in rows:
    print(f"=== {s} === ({n} Treffer, {free}x kostenlos, {ki}x KI-Modifier)")
    for h in hits:
        print("   -", h)
