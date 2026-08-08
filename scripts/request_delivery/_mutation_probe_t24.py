#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mutationssonde fuer Ticket 24 (cron_health_audit.py).

Ein gruener --selftest beweist NICHT, dass er rot werden KANN
(Ungeprueft-Pruefer-Falle, Ticket 15). Diese Sonde mutiert den
PRODUKTIVCODE je Defektklasse und verlangt:

  * rc != 0                       (Selftest wird rot)
  * KEIN echter Traceback         (Exit-Code-Falle, Ticket 14)
  * die ERWARTETE Diagnosezeile   ([FAIL] <exaktes Label>, Ticket 17)

ACHTUNG (in dieser Sonde selbst gefunden): auf das blosse Wort 'Traceback'
zu filtern ist FALSCH - der Selftest hat ein Pruef-LABEL namens
"kein Traceback im Gruen-Fall". Ein Substring-Test darauf meldet auch den
kerngesunden Lauf als abgestuerzt (gemessen: Baseline rc=0 -> faelschlich
rot). Geprueft wird deshalb die echte Python-Kopfzeile
"Traceback (most recent call last)". Gleiche Klasse wie die
Praefix-Falle aus Ticket 19: nie per losem `in` gegen ein Stichwort.

Danach wird die Datei sha256-genau wiederhergestellt und der
rc-Wechsel 0 -> 1 -> 0 belegt.

Kein Alt-Stand-Lauf moeglich: cron_health_audit.py ist neu und war nie
committet - es gibt keine fruehere Fassung, gegen die zu messen waere.
Das ist eine ehrliche Grenze, kein uebersprungener Schritt.

ERGEBNIS: MUTATION_PROBE_OK (0) | MUTATION_PROBE_DEFEKT (1)
          | MUTATION_PROBE_UNGEPRUEFT (2)
"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "cron_health_audit.py")
FULFILL = os.path.join(HERE, "cron_auto_fulfill.py")

# (Name, alt, neu, erwartetes [FAIL]-Label im Selftest-Output)
MUTANTS = [
    (
        "M1 leere Zielmenge wird gruen (Ticket-16-Falle)",
        "    if not traeger:\n        defects.append(",
        "    if False:\n        defects.append(",
        "leere Zielmenge ist NICHT gruen (Ticket-16-Merkregel)",
    ),
    (
        "M2 agentengetriebener Traeger nicht mehr rot (Ticket-22-Ursache)",
        '    if not job.get("no_agent"):\n        defects.append(f"{tag}: no_agent=False',
        '    if False:\n        defects.append(f"{tag}: no_agent=False',
        "agentengetriebener Traeger -> rot (Ticket-22-Ursache)",
    ),
    (
        "M3 abgeschalteter Geldpfad-Job nicht mehr rot",
        '    if not job.get("enabled"):\n        defects.append(f"{tag}: enabled=False',
        '    if False:\n        defects.append(f"{tag}: enabled=False',
        "abgeschalteter Geldpfad-Job -> rot",
    ),
    # M4/M5 ENTFALLEN mit Ticket 25 - nicht stillschweigend, sondern weil die
    # gemutierten Kriterien selbst abgeschafft wurden:
    #   M4 "'0 completed' nicht mehr rot" -> 'completed' ist seit Ticket 25
    #      KEIN Kriterium mehr (dieses Audit bestimmt es selbst = Latch,
    #      MEASURED am Alt-Stand: rc=1 gegen eine kerngesunde Pipeline).
    #   M5 "stille Stagnation" -> gleiche Schutzwirkung, neuer Ort: Kriterium
    #      [A] (Lauf-VERSUCHE). Mutant N1 in _mutation_probe_t25.py belegt,
    #      dass sie dort rot-faehig ist.
    # Die Deckung ist damit verschoben, nicht verloren.
    (
        "M6 Intervall > 24 h nicht mehr rot (agb.html § 3)",
        "        if minutes > MAX_PROMISE_MIN:",
        "        if False and minutes > MAX_PROMISE_MIN:",
        "Intervall > 24 h -> rot (agb.html § 3 ungedeckt)",
    ),
    (
        "M7 unmessbar schlaegt Defekt (Reihenfolge invertiert, Ticket 17)",
        "    # Reihenfolge: echter Defekt > unmessbar > OK (Merkregel Ticket 17/19)\n    if defects:",
        "    # MUTANT: Reihenfolge invertiert\n    if unknown:\n"
        '        print("ERGEBNIS: CRON_HEALTH_UNGEPRUEFT (mutant)")\n'
        "        return 2\n    if defects:",
        "echter Defekt schlaegt Unmessbarkeit (Ticket 17)",
    ),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


TB = "Traceback (most recent call last)"


def run_selftest(target=None):
    proc = subprocess.run(
        [sys.executable, target or TARGET, "--selftest"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=HERE, timeout=300,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main():
    if not os.path.isfile(TARGET):
        print(f"ERGEBNIS: MUTATION_PROBE_UNGEPRUEFT (Zieldatei fehlt: {TARGET})")
        return 2

    with open(TARGET, "rb") as fh:
        original = fh.read()
    sha_before = sha(original)
    src = original.decode("utf-8")
    print(f"Zieldatei : {TARGET}")
    print(f"sha256    : {sha_before[:16]} ({len(original)} B)")

    results = []

    def t(cond, name, detail=""):
        results.append((bool(cond), name))
        print(f"  [{'OK ' if cond else 'FAIL'}] {name}"
              + (f" | {detail}" if detail else ""))

    try:
        # -- Baseline: unmutiert muss gruen sein --------------------------
        rc0, out0 = run_selftest()
        t(rc0 == 0 and TB not in out0,
          "Baseline: unmutierter Selftest ist gruen", f"rc={rc0}")
        if rc0 != 0:
            print("ERGEBNIS: MUTATION_PROBE_UNGEPRUEFT "
                  "(Baseline schon rot - Mutanten waeren aussagelos)")
            return 2

        # -- Mutanten ------------------------------------------------------
        for name, old, new, expect in MUTANTS:
            n = src.count(old)
            if n != 1:
                t(False, f"{name}: Anker eindeutig", f"{n}x gefunden statt 1x")
                continue
            with open(TARGET, "w", encoding="utf-8", newline="") as fh:
                fh.write(src.replace(old, new, 1))
            rc, out = run_selftest()
            with open(TARGET, "wb") as fh:
                fh.write(original)

            red = rc != 0
            no_tb = TB not in out
            exact = f"[FAIL] {expect}" in out
            t(red and no_tb and exact, name,
              f"rc={rc} rot={red} kein_traceback={no_tb} "
              f"exakte_diagnose={exact}")
    finally:
        with open(TARGET, "wb") as fh:
            fh.write(original)

    # -- Wiederherstellung beweisen ---------------------------------------
    with open(TARGET, "rb") as fh:
        after = fh.read()
    sha_after = sha(after)
    t(sha_after == sha_before,
      "Produktivcode sha256-genau wiederhergestellt",
      f"{sha_before[:16]} -> {sha_after[:16]}")

    rc1, out1 = run_selftest()
    t(rc1 == 0 and TB not in out1,
      "rc-Wechsel 0 -> 1 -> 0 belegt (Selftest wieder gruen)", f"rc={rc1}")

    # ------------------------------------------------------------------
    # Zweites Ziel: die NEUE Etappe [3] in cron_auto_fulfill.py. Ein
    # gruener Selftest dort beweist ebenfalls nicht, dass er rot werden
    # kann - dieselbe Pruefung, gleiche Beweisform.
    # ------------------------------------------------------------------
    fulfill_mutants = [
        (
            "F1 Cron-Health-Defekt macht den Job nicht mehr rot",
            "    if hrc == 1:\n        defekt = True",
            "    if False:\n        defekt = True",
            "Cron-Health DEFEKT -> Job wird rot",
        ),
        (
            "F2 unmessbare Cron-Health wird als gesund gelesen",
            "    elif hrc != 0:\n        unmessbar = True",
            "    elif False:\n        unmessbar = True",
            "Cron-Health unmessbar -> UNGEPRUEFT, kein Defekt-Claim",
        ),
        (
            "F3 Sale-Banner wieder hinter den Defekt-Return geschoben",
            '    if sale:\n        print("*** ERSTER SALE / SALE BEDIENT'
            ' — sales.log pruefen! ***")\n\n    if defekt:',
            "    if defekt:",
            "Sale-Banner ueberlebt Cron-Health-Defekt",
        ),
        (
            "F4 Health-Ausgabe wird nicht mehr durchgereicht",
            "    for ln in (zeilen or hout.splitlines()[-2:]):\n"
            '        print(f"  {ln.strip()}")',
            "    for ln in []:\n        print(ln)",
            "Cron-Health-Diagnosezeile wird durchgereicht",
        ),
    ]

    with open(FULFILL, "rb") as fh:
        f_orig = fh.read()
    f_sha = sha(f_orig)
    f_src = f_orig.decode("utf-8")
    print(f"\nZweites Ziel: {FULFILL}")
    print(f"sha256    : {f_sha[:16]} ({len(f_orig)} B)")

    try:
        rcf, outf = run_selftest(FULFILL)
        t(rcf == 0 and TB not in outf,
          "Baseline: cron_auto_fulfill --selftest ist gruen", f"rc={rcf}")
        for name, old, new, expect in fulfill_mutants:
            n = f_src.count(old)
            if n != 1:
                t(False, f"{name}: Anker eindeutig",
                  f"{n}x gefunden statt 1x")
                continue
            with open(FULFILL, "w", encoding="utf-8", newline="") as fh:
                fh.write(f_src.replace(old, new, 1))
            rc, out = run_selftest(FULFILL)
            with open(FULFILL, "wb") as fh:
                fh.write(f_orig)
            red = rc != 0
            no_tb = TB not in out
            exact = f"FAIL {expect}" in out
            t(red and no_tb and exact, name,
              f"rc={rc} rot={red} kein_traceback={no_tb} "
              f"exakte_diagnose={exact}")
    finally:
        with open(FULFILL, "wb") as fh:
            fh.write(f_orig)

    with open(FULFILL, "rb") as fh:
        f_after = sha(fh.read())
    t(f_after == f_sha, "cron_auto_fulfill.py sha256-genau wiederhergestellt",
      f"{f_sha[:16]} -> {f_after[:16]}")
    rcf2, outf2 = run_selftest(FULFILL)
    t(rcf2 == 0 and TB not in outf2,
      "cron_auto_fulfill rc-Wechsel 0 -> 1 -> 0 belegt", f"rc={rcf2}")

    ok = sum(1 for c, _ in results if c)
    print(f"\n{ok}/{len(results)} bestanden")
    if ok != len(results):
        print("ERGEBNIS: MUTATION_PROBE_DEFEKT")
        return 1
    print(f"ERGEBNIS: MUTATION_PROBE_OK "
          f"({len(MUTANTS) + len(fulfill_mutants)} Mutanten rot in 2 "
          f"Produktivdateien, beide sha256-genau unveraendert)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
