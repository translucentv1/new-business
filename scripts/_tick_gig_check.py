#!/usr/bin/env python3
"""Tick-Check: Preisstufen und Checkout-Links in gig.html gegen die
Paket-Tabelle in docs/fiverr_gig.md pruefen (MEASURED, HTTP-Code je Link)."""
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
html = (ROOT / "gig.html").read_text(encoding="utf-8")

for price in ("3,99", "7,99", "14,99"):
    print(f"{price} EUR in gig.html: {html.count(price)}x")

links = sorted(set(re.findall(r"https://buy\.stripe\.com/[A-Za-z0-9]+", html)))
print(f"Checkout-Links gefunden: {len(links)}")
for u in links:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (tick-check)"})
        with urllib.request.urlopen(req, timeout=25) as r:
            code = r.status
    except Exception as e:  # noqa: BLE001
        code = f"FEHLER {e}"
    print(f"  {code}  {u[:48]}...")
