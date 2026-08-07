#!/usr/bin/env python3
"""Runde 2 des Tick-Seed-Screenings (siehe _tick_seeds.py)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kw_demand import suggest

SEEDS = [
    "traurede schreiben lassen",
    "eheversprechen schreiben lassen",
    "tischrede schreiben lassen",
    "einladung schreiben lassen",
    "kurzgeschichte schreiben lassen",
    "märchen schreiben lassen",
    "spielanleitung schreiben lassen",
    "app beschreibung schreiben lassen",
    "marketingplan erstellen lassen",
    "marketingkonzept erstellen lassen",
    "redaktionsplan erstellen lassen",
    "keyword recherche machen lassen",
    "zwischenzeugnis erstellen lassen",
    "unterrichtsmaterial erstellen lassen",
    "lernzettel erstellen lassen",
    "karteikarten erstellen lassen",
    "prüfungsfragen erstellen lassen",
    "klausur erstellen lassen",
    "text kürzen lassen",
    "exposé schreiben lassen",
    "hörbuch text schreiben lassen",
    "seo texte schreiben lassen",
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
