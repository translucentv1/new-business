#!/usr/bin/env python3
"""
kw_demand.py — MEASURED DE-Suchintent-Signal via Google Autocomplete ($0, kein API-Key).

Ersetzt geratene ("ASSUMED") Keywords durch echte Autocomplete-Treffer.
Wenn Google eine Phrase vorschlaegt, tippen sie echte Menschen -> Nachfrage-Beleg.

Nutzung:
  python scripts/kw_demand.py "powerpoint erstellen lassen" "businessplan erstellen"
"""
import json
import sys
import urllib.parse
import urllib.request

URL = "https://suggestqueries.google.com/complete/search"


def suggest(q, hl="de", gl="de"):
    params = urllib.parse.urlencode(
        {"client": "firefox", "hl": hl, "gl": gl, "q": q})
    req = urllib.request.Request(
        f"{URL}?{params}",
        headers={"User-Agent": "Mozilla/5.0 (compatible; kw-demand/1.0)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    # Google liefert je nach Query latin-1/utf-8 gemischt -> robust dekodieren
    for enc in ("utf-8", "latin-1"):
        try:
            data = json.loads(raw.decode(enc))
            break
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    else:
        return []
    return data[1] if len(data) > 1 else []


def main():
    seeds = sys.argv[1:] or ["schreiben lassen", "erstellen lassen"]
    for s in seeds:
        try:
            hits = suggest(s)
        except Exception as e:  # noqa: BLE001
            print(f"=== {s} === FEHLER: {e}")
            continue
        print(f"=== {s} === ({len(hits)} Treffer)")
        for h in hits:
            print("  -", h)


if __name__ == "__main__":
    main()
