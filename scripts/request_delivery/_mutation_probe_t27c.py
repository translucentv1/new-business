#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mutationssonde fuer Ticket 27, Nebenfrage B (Nebenring != Geldpfad).

Befund, der den Fix ausgeloest hat (MEASURED 2026-08-09):
`check_waechter()` schrieb seine Befunde in DIESELBE `defects`-Liste wie
`check_traeger()`. Ein Defekt der UEBERWACHUNG erzeugte damit rc=1, und
Etappe [3] in cron_auto_fulfill machte daraus `RTD_FULFILL_DEFEKT` - einen
Defekt-Vorwurf gegen den GELDPFAD, den keine Messung deckte. Real passiert
am 2026-08-08 05:41: ein nie gefeuerter Waechter riss den sauber liefernden
Job mit ins Rot.

Zweiter Befund gleicher Wurzel: in 48 Selftest-Faellen hatte
`check_waechter()` NULL Abdeckung - die Kopplung konnte gar nicht auffallen.

Die Fehlerrichtungen sind beide teuer, deshalb ist der Fix eine eigene Zahl
(rc=4) und nicht eine Herabstufung:
  * rc=1 (Alt-Stand) -> Falsch-ROT auf die Lieferung. Nach genug Falsch-Rot
    liest niemand mehr hin - die Klasse, an der Ticket 22 starb.
  * rc=0             -> Falsch-GRUEN auf die Ueberwachung. Ein toter zweiter
    Ring verschwindet lautlos; genau dann faellt Ausfallmodus D (stille
    Abwesenheit) auf niemanden mehr auf.

Drei Beweisarten:
  TEIL 1  Baseline beider Produktivdateien gruen.
  TEIL 2  MUTANTEN im Produktivcode - jeder stellt einen der beiden Fehler
          wieder her und muss den Selftest rot machen, ohne Absturz, mit der
          EXAKTEN Diagnosezeile.
  TEIL 3  sha256-genaue Wiederherstellung beider Dateien + rc-Wechsel
          0 -> 1 -> 0.

ERGEBNIS: MUTATION_PROBE_OK (0) | MUTATION_PROBE_DEFEKT (1)
          | MUTATION_PROBE_UNGEPRUEFT (2)
"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.join(HERE, "cron_health_audit.py")
FULFILL = os.path.join(HERE, "cron_auto_fulfill.py")
TB = "Traceback (most recent call last)"

# Die beiden Selftests drucken ihre Fehlzeile unterschiedlich - die Sonde darf
# das nicht raten, sonst besteht sie auch bei Rot aus dem falschen Grund
# (Merkregel Ticket 17: gegen die EXAKTE Diagnosezeile assertieren).
MARKER = {AUDIT: "[FAIL] ", FULFILL: "FAIL "}

# (Ziel, Name, alt, neu, erwarteter Label-Anfang hinter dem Marker)
MUTANTS = [
    (
        AUDIT,
        "A1 ALT-STAND: der Waechter schreibt wieder in die Geldpfad-Liste",
        "        check_waechter(job, path, text, execs, now, ring_defects, "
        "unknown, out,",
        "        check_waechter(job, path, text, execs, now, defects, "
        "unknown, out,",
        "nur der 2. Ring defekt -> eigener rc=4, KEIN Geldpfad-Defekt",
    ),
    (
        AUDIT,
        "A2 Nebenring-Defekt wird gruen (Falsch-Gruen auf die Ueberwachung)",
        "        return 4",
        "        return 0",
        "nur der 2. Ring defekt -> eigener rc=4, KEIN Geldpfad-Defekt",
    ),
    (
        AUDIT,
        "A3 die neue Zahl fehlt in der Signal-Konvention",
        '    4: "Nebenring defekt, Geldpfad NICHT betroffen (exit 4)",',
        '    4: "DEFEKT (exit 1)",',
        "exit 4 ist in der Signal-Konvention hinterlegt, kein "
        "Konventionsbruch",
    ),
    (
        AUDIT,
        "A4 Nebenring-Befund wird als Geldpfad-Defekt ueberschrieben",
        '        print(f"DEFEKTE NEBENRING ({len(ring_defects)}) - '
        'Ueberwachung, "',
        '        print(f"DEFEKTE GELDPFAD ({len(ring_defects)}) - '
        'Ueberwachung, "',
        "der Defekt wird dem Nebenring zugeschrieben, nicht dem Geldpfad",
    ),
    (
        FULFILL,
        "B1 ALT-STAND: Nebenring-Defekt vergiftet wieder das Hauptsignal",
        "        nebenring = True",
        "        defekt = True",
        "Nebenring-Defekt -> eigener rc=4, kein Geldpfad-Vorwurf",
    ),
    (
        FULFILL,
        "B2 Nebenring-Defekt endet gruen (Traeger meldet completed)",
        "        return EXIT_NEBENRING",
        "        return 0",
        "Nebenring-Defekt -> eigener rc=4, kein Geldpfad-Vorwurf",
    ),
    (
        FULFILL,
        "B3 PRAEFIX-FALLE (Ticket 19) wiederhergestellt: '  !~ ' faellt raus",
        '              or ln.lstrip().startswith(("!", "?"))]',
        '              or ln.startswith("  ! ") or ln.startswith("  ? ")]',
        "die Nebenring-Diagnosezeile wird durchgereicht",
    ),
]

ok = 0
bad = 0


def t(cond, label, extra=""):
    global ok, bad
    if cond:
        ok += 1
        print(f"  OK   {label}" + (f" | {extra}" if extra else ""))
    else:
        bad += 1
        print(f"  FAIL {label}" + (f" | {extra}" if extra else ""))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run_selftest(path):
    p = subprocess.run([sys.executable, path, "--selftest"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=HERE, timeout=600)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    print("== Mutationssonde Ticket 27c (Nebenring-Defekt != Geldpfad) ==")
    original = {p: open(p, "rb").read() for p in (AUDIT, FULFILL)}
    sha_vorher = {p: sha(b) for p, b in original.items()}
    for p, s in sha_vorher.items():
        print(f"Ziel  : {os.path.basename(p)}  sha256={s[:12]}")

    print("\n-- TEIL 1: Baseline --")
    for p in (AUDIT, FULFILL):
        rc0, out0 = run_selftest(p)
        t(rc0 == 0, f"Baseline gruen: {os.path.basename(p)}", f"rc={rc0}")
        t(TB not in out0, f"Baseline ohne Absturz: {os.path.basename(p)}")
        if rc0 != 0:
            print("ERGEBNIS: MUTATION_PROBE_UNGEPRUEFT (Baseline nicht gruen)")
            return 2

    print("\n-- TEIL 2: Mutanten --")
    try:
        for ziel, name, alt, neu, label in MUTANTS:
            print(f"\n-- {name}")
            src = original[ziel].decode("utf-8")
            if src.count(alt) != 1:
                t(False, "Mutationsanker genau 1x gefunden",
                  f"{src.count(alt)}x: {alt[:60]}")
                continue
            t(True, f"Mutationsanker gefunden: {alt.strip()[:56]}")
            with open(ziel, "w", encoding="utf-8", newline="") as fh:
                fh.write(src.replace(alt, neu))
            rc, out = run_selftest(ziel)
            t(rc != 0, f"Mutant ist ROT (rc={rc})", f"rc={rc}")
            t(TB not in out, "Mutant faellt durch Assertion, nicht Absturz")
            erwartet = MARKER[ziel] + label
            t(erwartet in out,
              f"exakte Diagnosezeile: {label[:50]}",
              "" if erwartet in out else "Zeile fehlt")
            # sofort zuruecksetzen: nie zwei Mutanten gleichzeitig aktiv
            with open(ziel, "wb") as fh:
                fh.write(original[ziel])
    finally:
        for p, b in original.items():
            with open(p, "wb") as fh:
                fh.write(b)

    print("\n-- TEIL 3: Wiederherstellung --")
    for p in (AUDIT, FULFILL):
        nach = sha(open(p, "rb").read())
        t(nach == sha_vorher[p],
          f"sha256-genau wiederhergestellt: {os.path.basename(p)}",
          f"{sha_vorher[p][:12]} -> {nach[:12]}")
        rc2, _ = run_selftest(p)
        t(rc2 == 0,
          f"nach Wiederherstellung wieder gruen (0->1->0): "
          f"{os.path.basename(p)}", f"rc={rc2}")

    print(f"\nERGEBNIS: "
          f"{'MUTATION_PROBE_OK' if bad == 0 else 'MUTATION_PROBE_DEFEKT'} "
          f"{ok}/{ok + bad}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
