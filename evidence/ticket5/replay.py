#!/usr/bin/env python3
"""Ticket 5 - Replay der konservierten DDG-Antworten vom 2026-08-07.

Warum es das gibt: die Aussage "BING_NICHT_INDEXIERT" stuetzt sich auf zwei
Netzantworten, die sich nicht beliebig wiederholen lassen (DDG ratelimitet nach
wenigen Abfragen mit HTTP 202). Die Rohbodies liegen deshalb hier, und dieses
Skript faehrt sie durch die ECHTE main() von bing_index_check.py - nur die
Netzschicht wird ersetzt, kein Parser nachgebaut.

WICHTIG (Attrappen-Falle): dekodiert wird mit errors="replace", exakt wie
real_fetch() es tut. Ein strenges utf-8-Decode waere GROSSZUEGIGER/anders als
die Produktivfunktion und wuerde einen anderen Text auswerten.

Aufruf:  python evidence/ticket5/replay.py
Erwartet: ERGEBNIS: BING_NICHT_INDEXIERT  (rc=1)
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts", "request_delivery"))

import bing_index_check as b  # noqa: E402

FILES = {
    "control": os.path.join(HERE, "ddg_control_2026-08-07.txt"),
    "target": os.path.join(HERE, "ddg_target_2026-08-07.txt"),
}

bodies = {}
for role, path in FILES.items():
    raw = open(path, "rb").read()
    # identisch zum Vertrag von real_fetch()
    bodies[role] = raw.decode("utf-8", "replace")
    print("konserviert %-8s %6d B  sha256=%s  (%d Zeichen nach Decode)"
          % (role, len(raw), hashlib.sha256(raw).hexdigest()[:16], len(bodies[role])))
print()


def replay_fetch(url):
    """Vertrag von real_fetch: (status:int, body:str), wirft nie."""
    if "wikipedia.org" in url:
        return 200, bodies["control"]
    if "translucentv1" in url:
        return 200, bodies["target"]
    raise AssertionError("unerwartete URL im Replay: %s" % url)


rc, out = b.main(["--quiet"], fetch=replay_fetch,
                 sources=[("ddg_html_replay", b.ddg_url, b.ddg_parse)],
                 sleep=lambda _s: None)
print(out)
print("\nrc=%d" % rc)
sys.exit(0 if rc == 1 else 1)
