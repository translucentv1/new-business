#!/usr/bin/env python3
"""Rot-Probe fuer verify_ticket13_live --selftest (Ticket 17).

Zwei Teile:

A) ALT-STAND-PROBE (Gegenbeweis statt Argument): die Fassung VOR Ticket 17 wird
   aus git geholt und gegen zwei Auslieferungen gefahren, die nachweislich kaputt
   sind. Sagt sie dabei "LIVE_OK", war sie blind -- kein theoretisches Risiko.
     A1 Defekt auf einer Seite AUSSERHALB der 7er-Stichprobe
     A2 Defekt (fehlender Impressum-Link) INNERHALB der Stichprobe
   Zur Kontrolle laeuft die NEUE Fassung gegen dieselbe Auslieferung.

B) MUTATIONSPROBE: mutiert den PRODUKTIVCODE der neuen Fassung, laesst den
   echten --selftest laufen und verlangt:
     - rc wechselt 0 -> 1 (der Pruefer wird ROT)
     - der Grund ist eine ERKANNTE Abweichung, KEIN Absturz ('Traceback')
     - genau der erwartete Fall faellt um
   Danach wird die Datei bitgenau wiederhergestellt (sha256-Vergleich).
"""
import contextlib
import hashlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "verify_ticket13_live.py")
BACKUP = TARGET + ".mutbak"
ALT_REV = "68946f0"   # letzter Commit VOR Ticket 17
REL = "scripts/request_delivery/verify_ticket13_live.py"

GESUND = ("<html><body>ok " + "x" * 900
          + " <a href='impressum.html'>Impressum</a>"
          + " <a href='datenschutz.html'>Datenschutz</a>"
          + " <a href='agb.html'>AGB</a></body></html>")
OHNE_IMPRESSUM = GESUND.replace("impressum.html", "x.html")
# Eine echte Seite aus dem Baum, die in der alten 7er-Stichprobe NICHT vorkam:
AUSSERHALB = "blog/arbeitszeugnis-schreiben-lassen-ki.html"

MUTATIONEN = [
    ("Leere Zielmenge wieder durchwinken (Leere-Schleife-Falle)",
     'print("  ! leere Zielmenge -- Ableitung aus dem Baum lieferte 0 Seiten")\n        return 2',
     'print("  ! leere Zielmenge -- Ableitung aus dem Baum lieferte 0 Seiten")\n        pages = []',
     "Leere Zielmenge ist NICHT gruen (rc=2 LIVE_UNGEPRUEFT)"),
    ("Soft-404-Erkennung entfernen (HTTP 200 mit Fehlerseiten-Text)",
     '    if any(m in body for m in SOFT404_MARKER):',
     '    if False and any(m in body for m in SOFT404_MARKER):',
     "Soft-404 (HTTP 200 + Fehlerseiten-Text) wird rot"),
    ("Statuscode ignorieren (nur noch auf Links schauen)",
     '    if code != 200:\n        return "DEFEKT", "HTTP %s" % code',
     '    if code != 200 and False:\n        return "DEFEKT", "HTTP %s" % code',
     "404 auf einer Zielseite wird rot"),
    ("Zielmenge wieder hartkodieren (die 7er-Stichprobe)",
     '    for pat in ("*.html", "blog/*.html"):\n        files.extend(sorted(glob.glob(os.path.join(root, pat))))',
     '    for pat in ("rtd.html",):\n        files.extend(sorted(glob.glob(os.path.join(root, pat))))',
     "target_pages leitet Zielmenge aus dem Baum ab (>7 Seiten)"),
]


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run_selftest():
    p = subprocess.run([sys.executable, TARGET, "--selftest"],
                       capture_output=True, text=True, timeout=300, check=False)
    return p.returncode, p.stdout + p.stderr


def _load(source_text, name):
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, name + ".py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(source_text)
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m, tmpdir


def _responder(mapping, default=(200, GESUND)):
    def r(url, timeout=25):
        for frag, resp in mapping.items():
            if frag in url:
                return resp
        return default
    return r


def _fahre(modul, responder, pages=None):
    orig_get = modul.get
    orig_sleep = modul.time.sleep
    modul.get = responder
    modul.time.sleep = lambda s: None
    orig_pages = getattr(modul, "target_pages", None)
    if pages is not None and orig_pages is not None:
        modul.target_pages = lambda root: list(pages)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = modul.main()
    finally:
        modul.get = orig_get
        modul.time.sleep = orig_sleep
        if orig_pages is not None:
            modul.target_pages = orig_pages
    return rc, buf.getvalue()


def alt_stand_probe():
    root = os.path.abspath(os.path.join(HERE, "..", ".."))
    p = subprocess.run(["git", "show", "%s:%s" % (ALT_REV, REL)],
                       cwd=root, capture_output=True, text=True, check=False)
    if p.returncode != 0:
        print("[FEHLER] Alt-Stand %s nicht lesbar: %s" % (ALT_REV, p.stderr.strip()[:200]))
        return False
    alt, tmp_alt = _load(p.stdout, "alt_verify13")
    with open(TARGET, encoding="utf-8") as fh:
        neu, tmp_neu = _load(fh.read(), "neu_verify13")

    print("  Alt-Stand prueft live: %d Seiten (STICHPROBE) | Neu: aus dem Baum abgeleitet"
          % len(getattr(alt, "STICHPROBE", [])))

    ok = True

    # --- A1: Defekt AUSSERHALB der alten Stichprobe -----------------------
    resp = _responder({AUSSERHALB: (404, "")})
    rc_alt, out_alt = _fahre(alt, resp)
    blind1 = rc_alt == 0 and "LIVE_OK" in out_alt
    print("[%s] A1 Defekt ausserhalb der Stichprobe (%s = 404):" % ("OK " if blind1 else "ROT", AUSSERHALB))
    print("        Alt-Stand: rc=%s -> %s" % (rc_alt, "LIVE_OK -> war BLIND" if blind1 else "hat es bemerkt"))
    seiten = [AUSSERHALB, "index.html", "rtd.html"]
    rc_neu, out_neu = _fahre(neu, resp, pages=seiten)
    sieht1 = rc_neu == 1 and "LIVE_DEFEKT" in out_neu and AUSSERHALB in out_neu
    print("        Neu:       rc=%s -> %s" % (rc_neu, "LIVE_DEFEKT, Seite benannt" if sieht1 else "NICHT erkannt"))
    ok &= blind1 and sieht1

    # --- A2: Defekt INNERHALB der Stichprobe, aber anderer Pflichtlink ----
    resp2 = _responder({"index.html": (200, OHNE_IMPRESSUM)})
    rc_alt2, out_alt2 = _fahre(alt, resp2)
    blind2 = rc_alt2 == 0 and "LIVE_OK" in out_alt2
    print("[%s] A2 index.html live OHNE Impressum-Link (Stichprobe deckt die Seite ab):"
          % ("OK " if blind2 else "ROT"))
    print("        Alt-Stand: rc=%s -> %s" % (rc_alt2, "LIVE_OK -> prueft nur datenschutz.html" if blind2 else "hat es bemerkt"))
    rc_neu2, out_neu2 = _fahre(neu, resp2, pages=["index.html", "rtd.html"])
    sieht2 = rc_neu2 == 1 and "impressum.html" in out_neu2
    print("        Neu:       rc=%s -> %s" % (rc_neu2, "LIVE_DEFEKT, Impressum benannt" if sieht2 else "NICHT erkannt"))
    ok &= blind2 and sieht2

    shutil.rmtree(tmp_alt, ignore_errors=True)
    shutil.rmtree(tmp_neu, ignore_errors=True)
    return ok


def main():
    print("== A) Alt-Stand-Probe: war die 7er-Stichprobe wirklich blind? ==")
    alt_blind = alt_stand_probe()

    print("\n== B) Mutationsprobe gegen den neuen Produktivcode ==")
    original = sha(TARGET)
    shutil.copy2(TARGET, BACKUP)

    rc0, _ = run_selftest()
    print("[BASIS ] unmutiert: rc=%s -> %s" % (rc0, "GRUEN" if rc0 == 0 else "ROT"))
    if rc0 != 0:
        print("ABBRUCH: Basis ist nicht gruen.")
        shutil.copy2(BACKUP, TARGET)
        os.remove(BACKUP)
        return 1

    alle_ok = True
    try:
        with open(BACKUP, encoding="utf-8") as fh:
            quelle = fh.read()

        for name, alt, neu, erwarteter_fall in MUTATIONEN:
            if alt not in quelle:
                print("[FEHLER] Mutation '%s': Muster nicht gefunden" % name)
                alle_ok = False
                continue
            with open(TARGET, "w", encoding="utf-8") as fh:
                fh.write(quelle.replace(alt, neu, 1))

            rc, out = run_selftest()
            wurde_rot = rc == 1
            kein_absturz = "Traceback" not in out
            fall_gefallen = ("  ! " + erwarteter_fall) in out
            ok = wurde_rot and kein_absturz and fall_gefallen
            alle_ok &= ok
            print("[%s] %s: rc=%s rot=%s kein_absturz=%s erwarteter_fall_faellt=%s"
                  % ("OK " if ok else "ROT", name, rc, wurde_rot, kein_absturz, fall_gefallen))
            if not fall_gefallen:
                rote = [ln.strip() for ln in out.splitlines() if ln.startswith("  ! ")]
                print("        tatsaechlich rot: %s" % rote)
    finally:
        shutil.copy2(BACKUP, TARGET)
        os.remove(BACKUP)

    wiederhergestellt = sha(TARGET) == original
    print("[%s] Datei bitgenau wiederhergestellt (sha256 %s...)"
          % ("OK " if wiederhergestellt else "ROT", original[:12]))

    rc_final, _ = run_selftest()
    print("[%s] rc-Wechsel belegt: 1 (mutiert) -> %s (repariert)"
          % ("OK " if rc_final == 0 else "ROT", rc_final))

    gesamt = alt_blind and alle_ok and wiederhergestellt and rc_final == 0
    print("\nERGEBNIS: " + ("MUTATION_PROBE_OK" if gesamt else "MUTATION_PROBE_ROT"))
    return 0 if gesamt else 1


if __name__ == "__main__":
    raise SystemExit(main())
