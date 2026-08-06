#!/usr/bin/env python3
"""Ticket 20 — Mutationsprobe: ist die neue noindex-Pruefung rot-faehig?

Ein gruener Selftest beweist nur, dass ein INJIZIERTER Body erkannt wird.
Hier wird der PRODUKTIVCODE mutiert (auto_fulfill.py verliert die
meta-robots-Zeile), die ECHTE write_page() erzeugt daraus eine echte Datei,
und verify_publish_leg.main() bekommt genau diesen echten Inhalt zu sehen.

Damit ist die Kette geschlossen: Produktiv-Template -> erzeugte Datei -> Pruefer.

Kein Netz, kein git-Write, kein Push. Die Quelldatei wird sha256-genau
wiederhergestellt; die erzeugte Canary-Datei wird geloescht.

ACHTUNG (hier real zugeschlagen): Quelldateien MUESSEN binaer gelesen und
geschrieben werden. Text-Modus uebersetzt Zeilenenden (\n <-> \r\n) und
veraendert die Datei beim Zurueckschreiben - der erste Lauf dieser Probe hat
auto_fulfill.py genau so beschaedigt. Nur die sha256-Zusicherung hat es
bemerkt.

Aufruf: python scripts/request_delivery/_mutation_probe_t20.py
"""

import contextlib
import hashlib
import importlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import verify_publish_leg as vpl  # noqa: E402

AF_PATH = os.path.join(HERE, "auto_fulfill.py")
NOINDEX_LINE = '<meta name="robots" content="noindex,nofollow">'


def sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def write_bytes(path: str, data: bytes) -> None:
    with open(path, "wb") as fh:
        fh.write(data)


def run_main_against_real_file() -> tuple[int, str]:
    """Faehrt die ECHTE main() - echte write_page(), aber ohne Netz/git."""
    g = vpl.__dict__
    keep = {k: g[k] for k in ("git", "http", "poll_until")}
    gp, argv = vpl.af.git_publish, sys.argv
    produced: dict[str, str] = {}

    real_write_page = vpl.af.write_page

    def _write_page(sid, title, text):
        path, url = real_write_page(sid, title, text)
        produced["path"] = path
        return path, url

    calls = [0]

    def _http(_url, method):
        if method == "HEAD":
            return 200, ""
        calls[0] += 1
        if calls[0] == 1:              # Schritt 2: vor dem Push -> 404
            return 404, ""
        body = open(produced["path"], encoding="utf-8").read()
        return 200, body               # Schritt 4c: der ECHTE Dateiinhalt

    vpl.af.write_page = _write_page
    vpl.af.git_publish = lambda _m: True
    g["git"] = lambda *a: (0, {"rev-parse": "gh-pages", "log": "stub",
                               "rev-list": "0",
                               "ls-tree": "dl/rtd/x.html"}[a[0]])
    g["http"] = _http
    g["poll_until"] = lambda _u, _m, w, **_k: (True, w, 0)
    sys.argv = ["x", "--keep"]         # kein git-Cleanup

    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = vpl.main()
    finally:
        g.update(keep)
        vpl.af.write_page, vpl.af.git_publish, sys.argv = (
            real_write_page, gp, argv)
        path = produced.get("path")
        if path and os.path.exists(path):
            os.remove(path)
    return rc, buf.getvalue()


def main() -> int:
    before = sha256(AF_PATH)
    original = read_bytes(AF_PATH)
    needle = NOINDEX_LINE.encode()
    if needle not in original:
        print(f"ABBRUCH: '{NOINDEX_LINE}' steht nicht in auto_fulfill.py - "
              "die Probe wuerde nichts beweisen.")
        return 2

    results = []
    print("== Ticket 20: Mutationsprobe am PRODUKTIVCODE ==")
    print(f"auto_fulfill.py sha256 vorher = {before[:16]}")

    # --- Gegenprobe: unmutiert muss gruen sein ---
    rc, out = run_main_against_real_file()
    ok = rc == 0 and "PUBLISH_LEG_OK" in out
    results.append(("unmutiert -> gruen", ok, rc))
    print(f"  [{'OK ' if ok else 'FAIL'}] unmutiert -> gruen            rc={rc}")

    # --- Mutant M1: Produktiv-Template verliert das noindex ---
    mutants = [
        ("M1 noindex-Zeile entfernt",
         original.replace(needle + b"\r\n", b"").replace(needle + b"\n", b""),
         "hat KEIN meta robots"),
        ("M2 noindex -> index,follow",
         original.replace(needle,
                          b'<meta name="robots" content="index,follow">'),
         "ohne noindex (index,follow)"),
    ]
    for name, mutated, expect in mutants:
        if mutated == original:
            print(f"  [FAIL] {name:<30} Mutation griff nicht")
            results.append((name, False, -1))
            continue
        write_bytes(AF_PATH, mutated)
        try:
            importlib.reload(vpl.af)
            rc, out = run_main_against_real_file()
        finally:
            write_bytes(AF_PATH, original)
            importlib.reload(vpl.af)
        crashed = "Traceback" in out
        ok = rc == 1 and expect in out and not crashed
        why = ("TRACEBACK" if crashed
               else "" if ok else f"erwartet: {expect!r}")
        results.append((name, ok, rc))
        print(f"  [{'OK ' if ok else 'FAIL'}] {name:<30} rc={rc}"
              + (f" | {why}" if why else " | Diagnose exakt getroffen"))

    after = sha256(AF_PATH)
    restored = after == before
    print(f"auto_fulfill.py sha256 nachher = {after[:16]} "
          f"({'identisch' if restored else 'ABWEICHUNG!'})")

    bad = [n for n, ok, _ in results if not ok]
    if bad or not restored:
        print("\nMUTATION_PROBE_DEFEKT:")
        for n in bad:
            print("  -", n)
        if not restored:
            print("  - Quelldatei NICHT sha256-genau wiederhergestellt")
        return 1
    print(f"\nMUTATION_PROBE_OK — {len(results)}/{len(results)}, "
          "rc-Wechsel 0->1->0, Quelldatei sha256-genau wiederhergestellt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
