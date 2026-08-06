#!/usr/bin/env python3
"""No-Agent-Cron: RTD Auto-Fulfillment (Stripe -> Deliverable -> Push).

Warum ohne LLM (Ticket 22): der frueher agentengetriebene Job
bfb63346d942 wurde 143x hintereinander uebersprungen
("Skipped to prevent unintended spend" nach Config-Drift, davor HTTP 404)
und hat in seiner ganzen Lebenszeit KEIN einziges Mal die Pipeline gestartet.
Die Auslieferung bezahlter Ware darf nicht an Modellverfuegbarkeit,
Config-Drift oder Rate-Limits (429) haengen -> reines Skript, kein Inferenz-Call.

Ergebniswoerter (erstes Token der ERGEBNIS-Zeile):
    RTD_FULFILL_OK          rc=0  Pipeline lief, Live-Check gruen
    RTD_FULFILL_SALE        rc=0  wie OK, aber es wurde mindestens 1 Sale bedient
    RTD_FULFILL_DEFEKT      rc=1  Pipeline oder Live-Check rot
    RTD_FULFILL_UNGEPRUEFT  rc=2  nicht messbar (Repo/Skript fehlt, Netz tot)

Echter Defekt schlaegt Unmessbarkeit (Konvention aus Ticket 16/17/19).
"""

import os
import subprocess
import sys
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FULFILL = os.path.join(REPO, "scripts", "request_delivery", "auto_fulfill.py")
SITE = "https://translucentv1.github.io/new-business"
LIVE_URLS = ("rtd.html", "thanks.html")
TIMEOUT = 900


def http_code(url: str) -> int:
    """Statuscode oder -1 bei Netzfehler (nicht messbar, kein Defekt-Claim)."""
    req = urllib.request.Request(url, method="GET",
                                 headers={"User-Agent": "rtd-cron/1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.getcode()
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:                      # DNS/Timeout/TLS
        print(f"  NETZFEHLER {url}: {e}")
        return -1


def main() -> int:
    if not os.path.isfile(FULFILL):
        print(f"ERGEBNIS: RTD_FULFILL_UNGEPRUEFT (Skript fehlt: {FULFILL})")
        return 2

    print(f"[1] Pipeline: {sys.executable} auto_fulfill.py  (cwd={REPO})")
    try:
        p = subprocess.run([sys.executable, FULFILL], cwd=REPO,
                           capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        print(f"ERGEBNIS: RTD_FULFILL_DEFEKT (Timeout nach {TIMEOUT}s)")
        return 1
    out = (p.stdout or "") + (p.stderr or "")
    print(out.rstrip())

    defekt = p.returncode != 0
    if defekt:
        print(f"  auto_fulfill rc={p.returncode}")

    # Sale-Erkennung aus der Produktivausgabe: "neu=N" ist die Zahl der in
    # diesem Lauf bedienten Sales; "FULFILLED " steht pro ausgeliefertem Stueck.
    sale = False
    for tok in out.split():
        if tok.startswith("neu="):
            try:
                sale = sale or int(tok[4:]) > 0
            except ValueError:
                pass
    sale = sale or "FULFILLED cs_live" in out

    print("[2] Live-Check Kaufpfad")
    codes = {}
    for u in LIVE_URLS:
        codes[u] = http_code(f"{SITE}/{u}")
        print(f"  {u:<14} HTTP {codes[u]}")
    if any(c not in (200, -1) for c in codes.values()):
        defekt = True
    unmessbar = any(c == -1 for c in codes.values())

    if defekt:
        print("ERGEBNIS: RTD_FULFILL_DEFEKT")
        return 1
    if sale:
        print("*** ERSTER SALE / SALE BEDIENT — sales.log pruefen! ***")
        print("ERGEBNIS: RTD_FULFILL_SALE")
        return 0
    if unmessbar:
        print("ERGEBNIS: RTD_FULFILL_UNGEPRUEFT (Live-Check nicht messbar)")
        return 2
    print("ERGEBNIS: RTD_FULFILL_OK (Pipeline gelaufen, Kaufpfad HTTP 200)")
    return 0


def _selftest() -> int:
    """Fault Injection durch die ECHTE main(): nur FULFILL/http_code/SITE
    werden ersetzt, der Entscheidungsbaum bleibt der Produktivcode."""
    import io
    import tempfile
    import contextlib

    g = globals()
    orig = (g["FULFILL"], g["http_code"], g["TIMEOUT"])
    tmpdir = tempfile.mkdtemp(prefix="rtd_selftest_")
    ok = [0]
    bad = [0]

    def t(cond, label):
        if cond:
            ok[0] += 1
            print(f"  OK   {label}")
        else:
            bad[0] += 1
            print(f"  FAIL {label}")

    def stub(body: str, rc: int = 0) -> str:
        p = os.path.join(tmpdir, f"stub_{abs(hash(body + str(rc)))}.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write("import sys\n")
            for line in body.splitlines():
                f.write(f"print({line!r})\n")
            f.write(f"sys.exit({rc})\n")
        return p

    def run(fulfill, codes, timeout=900):
        g["FULFILL"] = fulfill
        g["TIMEOUT"] = timeout
        g["http_code"] = lambda url: codes.get(url.rsplit("/", 1)[-1], 200)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main()
        text = buf.getvalue()
        word = ""
        for line in text.splitlines():
            if line.startswith("ERGEBNIS:"):
                word = line.split()[1]          # exaktes erstes Token
        return rc, word, text

    try:
        rc, w, _ = run(stub("sessions=2 (roh) paid=0 neu=0"), {})
        t(rc == 0, "gruener Lauf rc=0")
        t(w == "RTD_FULFILL_OK", f"gruener Lauf Wort={w}")

        rc, w, _ = run(stub("sessions=3 paid=1 neu=1"), {})
        t(rc == 0 and w == "RTD_FULFILL_SALE", f"neu=1 -> SALE (war {w})")

        rc, w, _ = run(stub("neu=0\nFULFILLED cs_live_abc -> dl/rtd/x.html"), {})
        t(w == "RTD_FULFILL_SALE", f"FULFILLED cs_live -> SALE (war {w})")

        rc, w, _ = run(stub("neu=0 paid=0"), {})
        t(w == "RTD_FULFILL_OK", f"neu=0 ist KEIN Sale (war {w})")

        rc, w, _ = run(stub("boom", rc=1), {})
        t(rc == 1 and w == "RTD_FULFILL_DEFEKT", f"Pipeline rc=1 -> DEFEKT ({w})")

        rc, w, _ = run(stub("neu=0"), {"rtd.html": 404})
        t(rc == 1 and w == "RTD_FULFILL_DEFEKT", f"rtd.html 404 -> DEFEKT ({w})")

        rc, w, _ = run(stub("neu=0"), {"thanks.html": 500})
        t(rc == 1 and w == "RTD_FULFILL_DEFEKT", f"thanks.html 500 -> DEFEKT ({w})")

        rc, w, _ = run(stub("neu=0"), {"rtd.html": -1})
        t(rc == 2 and w == "RTD_FULFILL_UNGEPRUEFT", f"Netzfehler -> UNGEPRUEFT ({w})")

        rc, w, _ = run(stub("neu=0", rc=1), {"rtd.html": -1})
        t(rc == 1 and w == "RTD_FULFILL_DEFEKT",
          f"Defekt schlaegt Unmessbarkeit ({w})")

        rc, w, _ = run(stub("neu=1"), {"rtd.html": 404})
        t(rc == 1 and w == "RTD_FULFILL_DEFEKT",
          f"Sale + kaputter Kaufpfad -> DEFEKT ({w})")

        rc, w, _ = run(os.path.join(tmpdir, "gibtsnicht.py"), {})
        t(rc == 2 and w == "RTD_FULFILL_UNGEPRUEFT",
          f"fehlendes Skript -> UNGEPRUEFT ({w})")

        rc, w, _ = run(stub("import time"), {}, timeout=0)
        t(rc == 1, f"Timeout -> DEFEKT rc={rc}")

        # Der Produktivlauf darf NIE ein Stripe-Skript ueberspringen, nur weil
        # der Live-Check gruen ist: Reihenfolge Pipeline -> Live-Check pruefen.
        _, _, text = run(stub("MARKER_PIPELINE"), {})
        t("MARKER_PIPELINE" in text, "Pipeline-Ausgabe wird durchgereicht")
    finally:
        g["FULFILL"], g["http_code"], g["TIMEOUT"] = orig

    print(f"\nSELFTEST {'OK' if not bad[0] else 'FEHLGESCHLAGEN'}: "
          f"{ok[0]}/{ok[0] + bad[0]}")
    return 1 if bad[0] else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main())
