#!/usr/bin/env python3
"""Rot-Probe fuer verify_rtd_chain --selftest (Ticket 16).

Zwei Teile:

A) ALT-STAND-PROBE (Gegenbeweis, dass Rot-Fall 9 einen ECHTEN Defekt trifft):
   Die Fassung VOR Ticket 16 wird aus git geholt und mit einer rtd.html
   ohne einen einzigen Payment Link gefahren. Wenn sie dabei "KETTE_OK"
   sagt, war der Torwaechter nachweislich blind — kein theoretisches Risiko.

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
TARGET = os.path.join(HERE, "verify_rtd_chain.py")
BACKUP = TARGET + ".mutbak"
ALT_REV = "ad891dc"   # letzter Commit VOR Ticket 16

MUTATIONEN = [
    # (Name, alter Text, neuer Text, Fall der umkippen MUSS)
    ("Leere Linkliste durchwinken (der Alt-Defekt)",
     "    if not urls:\n        print(\"    KEIN EINZIGER LIVE-LINK auf der Kaufseite -> kein Geldpfad.\")\n        ok = False",
     "    if not urls:\n        print(\"    KEIN EINZIGER LIVE-LINK auf der Kaufseite -> kein Geldpfad.\")\n        pass",
     "0 Links auf rtd.html wird rot"),
    ("Preis-Pruefung entschaerfen (0 EUR waere ok)",
     "and isinstance(amt, int) and not isinstance(amt, bool) and amt > 0)",
     "and True)",
     "Preis 0 wird rot"),
    ("Hash-Paritaet nur behaupten statt messen (Alt-Verhalten von [3])",
     'return ("OK" if out == f"dl/rtd/{sid_hash(sid)}.html" else "ROT"), out, ""',
     'return "OK", out, ""',
     "Hash-Paritaet (slice 15) wird rot"),
    ("livemode/active ignorieren",
     'good = (pl.get("livemode") is True and pl.get("active") is True',
     'good = (True or pl.get("livemode") is True and pl.get("active") is True',
     "active=False wird rot"),
]


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run_selftest():
    p = subprocess.run([sys.executable, TARGET, "--selftest"],
                       capture_output=True, text=True, timeout=300, check=False)
    return p.returncode, p.stdout + p.stderr


def alt_stand_probe():
    """Faehrt die ALTE main() gegen eine rtd.html ohne Links."""
    root = os.path.abspath(os.path.join(HERE, "..", ".."))
    p = subprocess.run(["git", "show", f"{ALT_REV}:scripts/request_delivery/verify_rtd_chain.py"],
                       cwd=root, capture_output=True, text=True, check=False)
    if p.returncode != 0:
        print(f"[FEHLER] Alt-Stand {ALT_REV} nicht lesbar: {p.stderr.strip()[:200]}")
        return False

    tmpdir = tempfile.mkdtemp()
    altpy = os.path.join(tmpdir, "alt_verify.py")
    with open(altpy, "w", encoding="utf-8") as fh:
        fh.write(p.stdout)
    leer_rtd = os.path.join(tmpdir, "rtd_ohne_links.html")
    with open(leer_rtd, "w", encoding="utf-8") as fh:
        fh.write('<select><option value="3.99">Basis</option></select>\n'
                 '<!-- kein einziger https://buy.stripe.com Link -->\n')

    spec = importlib.util.spec_from_file_location("alt_verify", altpy)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    # Aussenwelt der ALTEN Fassung ersetzen (dieselben Namen wie damals)
    m.RTD = leer_rtd
    m.DL_DIR = tmpdir
    m.app.get_stripe_key = lambda: "sk_live_" + "x" * 20
    m.stripe_get = lambda path, key: {"data": []}

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = m.main()
    out = buf.getvalue()
    shutil.rmtree(tmpdir, ignore_errors=True)

    blind = (rc == 0 and "KETTE_OK" in out)
    print(f"[{'OK ' if blind else 'ROT'}] Alt-Stand ({ALT_REV}) mit 0 Links: "
          f"rc={rc}, sagt {'KETTE_OK -> war BLIND' if blind else 'nicht KETTE_OK'}")
    for line in out.strip().splitlines():
        print("        | " + line)
    if not blind:
        print("        (Erwartet war KETTE_OK — dann waere der Defekt-Claim falsch.)")
    return blind


def main():
    print("== A) Alt-Stand-Probe: war der Torwaechter wirklich blind? ==")
    alt_blind = alt_stand_probe()

    print("\n== B) Mutationsprobe gegen den neuen Produktivcode ==")
    original = sha(TARGET)
    shutil.copy2(TARGET, BACKUP)

    rc0, _ = run_selftest()
    print(f"[BASIS ] unmutiert: rc={rc0} -> {'GRUEN' if rc0 == 0 else 'ROT'}")
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
                print(f"[FEHLER] Mutation '{name}': Muster nicht gefunden")
                alle_ok = False
                continue
            with open(TARGET, "w", encoding="utf-8") as fh:
                fh.write(quelle.replace(alt, neu, 1))

            rc, out = run_selftest()
            wurde_rot = rc == 1
            kein_absturz = "Traceback" not in out
            fall_gefallen = any(
                line.startswith("  [ROT]") and erwarteter_fall in line
                for line in out.splitlines())
            ok = wurde_rot and kein_absturz and fall_gefallen
            alle_ok &= ok
            print(f"[{'OK ' if ok else 'ROT'}] {name}: rc={rc} "
                  f"rot={wurde_rot} kein_absturz={kein_absturz} "
                  f"erwarteter_fall_faellt={fall_gefallen}")
            if not fall_gefallen:
                rote = [l.strip() for l in out.splitlines() if l.startswith("  [ROT]")]
                print(f"        tatsaechlich rot: {rote}")
    finally:
        shutil.copy2(BACKUP, TARGET)
        os.remove(BACKUP)

    wiederhergestellt = sha(TARGET) == original
    print(f"[{'OK ' if wiederhergestellt else 'ROT'}] Datei bitgenau "
          f"wiederhergestellt (sha256 {original[:12]}...)")

    rc_final, _ = run_selftest()
    print(f"[{'OK ' if rc_final == 0 else 'ROT'}] rc-Wechsel belegt: "
          f"1 (mutiert) -> {rc_final} (repariert)")

    gesamt = alt_blind and alle_ok and wiederhergestellt and rc_final == 0
    print("\nERGEBNIS: " + ("MUTATION_PROBE_OK" if gesamt else "MUTATION_PROBE_ROT"))
    return 0 if gesamt else 1


if __name__ == "__main__":
    raise SystemExit(main())
