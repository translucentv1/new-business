#!/usr/bin/env python3
"""Rot-Probe fuer funnel_check --selftest (Ticket 15).

Mutiert den PRODUKTIVCODE, laesst den echten --selftest laufen und verlangt:
  - rc wechselt 0 -> 1 (der Pruefer wird ROT)
  - der Grund ist eine ERKANNTE Abweichung, KEIN Absturz (kein 'Traceback')
  - genau der erwartete Fall faellt um
Danach wird die Datei bitgenau wiederhergestellt (sha256-Vergleich).
"""
import hashlib
import shutil
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "funnel_check.py")
BACKUP = TARGET + ".mutbak"

MUTATIONEN = [
    # (Name, alter Text, neuer Text, Fall der umkippen MUSS)
    ("Pagination ignorieren (der Defekt von heute)",
     'if not payload.get("has_more") or not page:',
     'if True:',
     "Pagination -> 101 statt 100"),
    ("Besucher als API-Probe verbuchen",
     '    if not s.get("payment_link"):\n        return "API-PROBE"\n    return "BESUCHER"',
     '    return "API-PROBE"',
     "echter Browser -> BESUCHER=1"),
    ("Truncation-Guard entschaerfen",
     "        return 3\n",
     "        pass\n",
     "Dauer-has_more -> vollzaehlig NEIN + rc=3"),
]


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run_selftest():
    p = subprocess.run([sys.executable, TARGET, "--selftest"],
                       capture_output=True, text=True, timeout=180)
    return p.returncode, p.stdout + p.stderr


def main():
    original = sha(TARGET)
    shutil.copy2(TARGET, BACKUP)

    rc0, out0 = run_selftest()
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

    gesamt = alle_ok and wiederhergestellt and rc_final == 0
    print("\nERGEBNIS: " + ("MUTATION_PROBE_OK" if gesamt else "MUTATION_PROBE_ROT"))
    return 0 if gesamt else 1


if __name__ == "__main__":
    raise SystemExit(main())
