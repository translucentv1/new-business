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

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FULFILL = os.path.join(REPO, "scripts", "request_delivery", "auto_fulfill.py")
HEALTH = os.path.join(REPO, "scripts", "request_delivery",
                      "cron_health_audit.py")
# Ticket 25: Beleg, dass die LIEFER-Pipeline gelaufen ist - geschrieben NACH
# Etappe [1]+[2] und damit kausal VOR dem Urteil von Etappe [3]. Das Audit
# darf sich nicht am Exitstatus dieses Jobs orientieren, weil es ihn selbst
# bestimmt (Latch: 5 Laeufe rot, Alter 909 -> 1031 min, Pipeline gesund).
HEARTBEAT = os.path.join(REPO, "scripts", "request_delivery",
                         ".pipeline_heartbeat.json")
HEALTH_TIMEOUT = 120
SITE = "https://translucentv1.github.io/new-business"
LIVE_URLS = ("rtd.html", "thanks.html")
TIMEOUT = 900


def run_health():
    """Ticket 24: das stehende Tor unbeaufsichtigt mitlaufen lassen.

    -> (rc, ausgabe). rc 0 = gesund | 1 = Defekt | alles andere = unmessbar.
    Ein fehlendes/abgestuerztes Audit ist NIE ein Defekt-Claim gegen den
    Geldpfad (Merkregel Ticket 17: unmessbar != kaputt).
    """
    if not os.path.isfile(HEALTH):
        return 2, f"cron_health_audit.py fehlt: {HEALTH}"
    try:
        p = subprocess.run([sys.executable, HEALTH], cwd=REPO,
                           capture_output=True, text=True,
                           timeout=HEALTH_TIMEOUT)
    except subprocess.TimeoutExpired:
        return 2, f"cron_health_audit Timeout nach {HEALTH_TIMEOUT}s"
    except OSError as exc:
        return 2, f"cron_health_audit nicht startbar: {exc}"
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).rstrip()


def write_heartbeat(pipeline_rc, codes):
    """Beleg der Liefer-Etappe schreiben. -> (ok, meldung).

    Nur wenn die Pipeline sauber lief UND der Kaufpfad erreichbar war. Ein
    fehlgeschlagener Lauf darf den Heartbeat NICHT auffrischen, sonst
    verschweigt er genau den Fall, fuer den er da ist.
    """
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "pipeline_rc": pipeline_rc,
        "live": codes,
        "quelle": "cron_auto_fulfill.py Etappe [1]+[2]",
    }
    try:
        with open(HEARTBEAT, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1)
    except OSError as exc:
        return False, f"Heartbeat nicht schreibbar: {exc}"
    return True, payload["ts"]


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

    # [2b] Ticket 25: Liefer-Beleg schreiben, BEVOR Etappe [3] urteilt.
    # Nur bei sauberer Pipeline + erreichbarem Kaufpfad - sonst wuerde der
    # Heartbeat genau den Ausfall zudecken, den er melden soll.
    if not defekt and not unmessbar:
        hb_ok, hb_msg = write_heartbeat(p.returncode, codes)
        print(f"[2b] Pipeline-Heartbeat {'geschrieben' if hb_ok else 'FEHLER'}"
              f": {hb_msg}")
        if not hb_ok:
            unmessbar = True
    else:
        print("[2b] Pipeline-Heartbeat NICHT aufgefrischt "
              "(Pipeline/Kaufpfad nicht sauber)")

    # [3] Ticket 24: das stehende Cron-Tor laeuft hier UNBEAUFSICHTIGT mit.
    # Damit haengt es nicht mehr daran, dass ein Agenten-Tick es aufruft -
    # genau die Bauform, die in Ticket 22 143x ausgefallen ist.
    print("[3] Cron-Gesundheit (Ticket 24)")
    hrc, hout = run_health()
    zeilen = [ln for ln in hout.splitlines()
              if ln.startswith("ERGEBNIS:") or ln.startswith("  ! ")
              or ln.startswith("  ? ")]
    for ln in (zeilen or hout.splitlines()[-2:]):
        print(f"  {ln.strip()}")
    if hrc == 1:
        defekt = True
    elif hrc != 0:
        unmessbar = True

    # Der Sale ist das lauteste Signal des ganzen Systems - er wird IMMER
    # gedruckt, auch wenn parallel ein Defekt das Ergebniswort bestimmt.
    # (Sonst haette ausgerechnet ein Cron-Health-Defekt die ERSTER-SALE-
    # Meldung verschluckt.)
    if sale:
        print("*** ERSTER SALE / SALE BEDIENT — sales.log pruefen! ***")

    if defekt:
        print("ERGEBNIS: RTD_FULFILL_DEFEKT")
        return 1
    if sale:
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
    import hashlib

    g = globals()
    orig = (g["FULFILL"], g["http_code"], g["TIMEOUT"], g["run_health"],
            g["HEARTBEAT"])
    tmpdir = tempfile.mkdtemp(prefix="rtd_selftest_")
    # >>> Der Selftest darf die PRODUKTIV-Evidenz nicht anfassen. <<<
    # MEASURED 2026-08-07: er tat es - ein --selftest-Lauf schrieb die echte
    # .pipeline_heartbeat.json neu (ts 15:16:12 -> 15:19:49, sha256 geaendert).
    # Damit faelschte der Test genau den Beleg, auf den Kriterium [B] des
    # Audits sich stuetzt: jeder Tick haette [B] dauerhaft gruen gehalten,
    # auch bei toter Pipeline. Attrappen-Falle (Ticket 19), diesmal in der
    # Gegenrichtung: nicht die Attrappe war zu grosszuegig, sondern der Test
    # hat Produktivzustand erzeugt.
    prod_hb = orig[4]
    prod_hb_before = None
    if os.path.isfile(prod_hb):
        with open(prod_hb, "rb") as fh:
            prod_hb_before = hashlib.sha256(fh.read()).hexdigest()
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

    def run(fulfill, codes, timeout=900, health=(0, "ERGEBNIS: CRON_HEALTH_OK"),
            hb_path=None):
        g["FULFILL"] = fulfill
        g["TIMEOUT"] = timeout
        g["http_code"] = lambda url: codes.get(url.rsplit("/", 1)[-1], 200)
        g["run_health"] = lambda: health
        # Immer in den Temp-Ordner schreiben, nie in den Produktivpfad.
        g["HEARTBEAT"] = hb_path or os.path.join(tmpdir, "hb.json")
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

        # -- [3] Cron-Gesundheit (Ticket 24) ------------------------------
        rc, w, text = run(stub("neu=0"), {},
                          health=(1, "ERGEBNIS: CRON_HEALTH_DEFEKT\n"
                                     "  ! bfb63346d942: 0 completed"))
        t(rc == 1 and w == "RTD_FULFILL_DEFEKT",
          f"Cron-Health DEFEKT -> Job wird rot ({w})")
        t("0 completed" in text,
          "Cron-Health-Diagnosezeile wird durchgereicht")

        rc, w, _ = run(stub("neu=0"), {},
                       health=(2, "ERGEBNIS: CRON_HEALTH_UNGEPRUEFT"))
        t(rc == 2 and w == "RTD_FULFILL_UNGEPRUEFT",
          f"Cron-Health unmessbar -> UNGEPRUEFT, kein Defekt-Claim ({w})")

        rc, w, _ = run(stub("boom", rc=1), {},
                       health=(2, "ERGEBNIS: CRON_HEALTH_UNGEPRUEFT"))
        t(rc == 1 and w == "RTD_FULFILL_DEFEKT",
          f"echter Defekt schlaegt Health-Unmessbarkeit ({w})")

        # Regression, die dieser Umbau beinahe eingebaut haette: ein
        # Cron-Health-Defekt darf die SALE-Meldung nicht verschlucken.
        rc, w, text = run(stub("neu=1"), {},
                          health=(1, "ERGEBNIS: CRON_HEALTH_DEFEKT"))
        t(rc == 1 and w == "RTD_FULFILL_DEFEKT" and "ERSTER SALE" in text,
          f"Sale-Banner ueberlebt Cron-Health-Defekt ({w})")

        rc, w, _ = run(stub("neu=0"), {}, health=(0, "ERGEBNIS: CRON_HEALTH_OK"))
        t(rc == 0 and w == "RTD_FULFILL_OK",
          f"gesunde Cron-Health aendert nichts ({w})")

        # -- [2b] Pipeline-Heartbeat (Ticket 25) ---------------------------
        # Der Heartbeat ist der einzige Beleg, mit dem das Audit "die
        # Lieferung laeuft" von "der Job-Exit ist rot" trennt. Er muss
        # GENAU DANN frisch werden, wenn Pipeline UND Kaufpfad sauber waren.
        hb1 = os.path.join(tmpdir, "hb_gruen.json")
        rc, w, text = run(stub("neu=0"), {}, hb_path=hb1)
        hb_data = None
        if os.path.isfile(hb1):
            with open(hb1, encoding="utf-8") as fh:
                hb_data = json.load(fh)
        t(rc == 0 and hb_data is not None and hb_data.get("pipeline_rc") == 0
          and datetime.fromisoformat(hb_data["ts"]).tzinfo is not None,
          "gesunder Lauf schreibt Heartbeat mit tz-bewusstem Zeitstempel")
        t("[2b] Pipeline-Heartbeat geschrieben" in text,
          "Heartbeat-Schreibvorgang wird protokolliert")

        # Gegenprobe: ein FEHLGESCHLAGENER Lauf darf den Heartbeat nicht
        # auffrischen - sonst verschweigt er genau den Ausfall, fuer den er
        # da ist (dann meldete das Audit ewig "Pipeline liefert").
        hb2 = os.path.join(tmpdir, "hb_defekt.json")
        with open(hb2, "w", encoding="utf-8") as fh:
            fh.write('{"ts": "2000-01-01T00:00:00+00:00"}')
        rc, w, text = run(stub("boom", rc=1), {}, hb_path=hb2)
        with open(hb2, encoding="utf-8") as fh:
            alt = json.load(fh)
        t(rc == 1 and alt.get("ts") == "2000-01-01T00:00:00+00:00"
          and "NICHT aufgefrischt" in text,
          "defekte Pipeline frischt den Heartbeat NICHT auf")

        hb3 = os.path.join(tmpdir, "hb_unmessbar.json")
        with open(hb3, "w", encoding="utf-8") as fh:
            fh.write('{"ts": "2000-01-01T00:00:00+00:00"}')
        rc, w, _ = run(stub("neu=0"), {"rtd.html": -1}, hb_path=hb3)
        with open(hb3, encoding="utf-8") as fh:
            alt3 = json.load(fh)
        t(rc == 2 and alt3.get("ts") == "2000-01-01T00:00:00+00:00",
          "unmessbarer Kaufpfad frischt den Heartbeat NICHT auf")

        # Nicht schreibbarer Heartbeat darf nicht als gruen durchgehen:
        # ohne Beleg kann das Audit die Lieferung nicht bestaetigen.
        rc, w, text = run(stub("neu=0"), {},
                          hb_path=os.path.join(tmpdir, "fehlt", "hb.json"))
        t(rc == 2 and w == "RTD_FULFILL_UNGEPRUEFT"
          and "Heartbeat nicht schreibbar" in text,
          f"nicht schreibbarer Heartbeat -> UNGEPRUEFT ({w})")

        # Ergebniswort exakt, nicht per Praefix (Merkregel Ticket 19).
        _, w, _ = run(stub("neu=0"), {},
                      health=(0, "ERGEBNIS: CRON_HEALTH_OK_TEILMENGE"))
        t(w == "RTD_FULFILL_OK",
          "Health-Wort wird ueber rc gelesen, nicht per Substring")
    finally:
        (g["FULFILL"], g["http_code"], g["TIMEOUT"],
         g["run_health"], g["HEARTBEAT"]) = orig

    # >>> Der wichtigste Test kommt NACH dem finally: hat dieser Selftest
    # die echte Heartbeat-Datei angefasst? (MEASURED-Defekt vom 2026-08-07)
    prod_hb_after = None
    if os.path.isfile(prod_hb):
        with open(prod_hb, "rb") as fh:
            prod_hb_after = hashlib.sha256(fh.read()).hexdigest()
    t(prod_hb_after == prod_hb_before,
      "PRODUKTIV-Heartbeat vom Selftest UNANGETASTET "
      f"({str(prod_hb_before)[:12]} -> {str(prod_hb_after)[:12]})")

    print(f"\nSELFTEST {'OK' if not bad[0] else 'FEHLGESCHLAGEN'}: "
          f"{ok[0]}/{ok[0] + bad[0]}")
    return 1 if bad[0] else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main())
