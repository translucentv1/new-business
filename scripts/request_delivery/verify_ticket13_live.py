#!/usr/bin/env python3
"""Live-Beweis Ticket 13: gegen die AUSGELIEFERTEN Bodies, nicht gegen den Baum.

Prueft nach dem Push:
  1. die zwei zuvor 404er Traffic-Seiten liefern 200,
  2. eine Stichprobe gepatchter Seiten enthaelt den Datenschutz-Link WIRKLICH
     im ausgelieferten HTML (Baum != Auslieferung -> Branch-Falle),
  3. der Kaufpfad ist unveraendert erreichbar.
Wartet auf den Pages-Rebuild (MEASURED ~31 s) statt blind zu schlafen.
"""
from __future__ import annotations

import sys
import time
import urllib.request

BASE = "https://translucentv1.github.io/new-business/"

NEU = ["blog/hochzeitsrede-schreiben-lassen.html", "blog/pitch-deck-erstellen-lassen.html"]
STICHPROBE = [
    "index.html",
    "rtd.html",
    "blog/vortrag-erstellen-lassen-ki.html",
    "blog/bewerbung-schreiben-lassen-ki.html",
    "blog/study-guide-erstellen-lassen.html",
    "blog/hochzeitsrede-schreiben-lassen.html",
    "blog/pitch-deck-erstellen-lassen.html",
]
KAUFPFAD = ["rtd.html", "thanks.html", "agb.html", "datenschutz.html", "impressum.html"]
NEEDLE = "datenschutz.html"


def get(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={"User-Agent": "rtd-verify/1.0", "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # Netz/Timeout
        return -1, str(e)


def wait_live(path: str, tries: int = 18, delay: int = 10) -> tuple[int, str, int]:
    for i in range(tries):
        code, body = get(BASE + path)
        if code == 200:
            return code, body, i * delay
        time.sleep(delay)
    code, body = get(BASE + path)
    return code, body, tries * delay


def main() -> int:
    fails = []

    print("[1] Zuvor 404: erreichen die Seiten jetzt die Auslieferung?")
    for p in NEU:
        code, body, waited = wait_live(p)
        ok = code == 200 and len(body) > 800
        print("    %-46s HTTP %s  %6d B  nach %2ds  %s"
              % (p, code, len(body), waited, "OK" if ok else "FAIL"))
        if not ok:
            fails.append("%s HTTP %s" % (p, code))

    print("[2] Datenschutz-Link im AUSGELIEFERTEN Body:")
    for p in STICHPROBE:
        code, body = get(BASE + p)
        ok = code == 200 and NEEDLE in body
        print("    %-46s HTTP %s  link=%-5s %s"
              % (p, code, str(NEEDLE in body), "OK" if ok else "FAIL"))
        if not ok:
            fails.append("%s ohne Datenschutz-Link (HTTP %s)" % (p, code))

    print("[3] Kaufpfad unveraendert erreichbar:")
    for p in KAUFPFAD:
        code, body = get(BASE + p)
        ok = code == 200
        print("    %-46s HTTP %s  %6d B  %s" % (p, code, len(body), "OK" if ok else "FAIL"))
        if not ok:
            fails.append("%s HTTP %s" % (p, code))

    print()
    if fails:
        print("ERGEBNIS: LIVE_DEFEKT")
        for f in fails:
            print("  ! " + f)
        return 1
    print("ERGEBNIS: LIVE_OK (alle Pruefungen bestanden)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
