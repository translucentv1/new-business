#!/usr/bin/env python3
"""Rot-Probe zu Ticket 27: mutiert den PRODUKTIVCODE von cron_auto_fulfill.py
und verlangt, dass der neue --selftest jeden Mutanten mit der EXAKTEN
Diagnosezeile faellt.

Warum das noetig ist (Merkregel Ticket 15): ein Test, der nur gruen gesehen
wurde, ist nie beim Fangen beobachtet worden. Die Ticket-27-Tests behaupten,
sie wuerden merken, wenn der Signalkanal wieder blind wird - also einmal
wirklich blind machen.

Regeln, die hier absichtlich eingehalten werden:
- gegen die EXAKTE FAIL-Zeile assertieren, nicht gegen ein Stichwort
  (Merkregel Ticket 17), sonst besteht der Test auch bei Rot aus dem
  falschen Grund;
- auf die echte Traceback-KOPFZEILE filtern, nicht auf das Wort "Traceback"
  (Eigentor aus Ticket 24: ein Pruef-LABEL enthielt das Wort);
- Datei sha256-genau wiederherstellen und das auch belegen;
- rc-Wechsel 0 -> 1 -> 0 zeigen.

EIGENTOR IN DIESER SONDE (selbst gefunden, MEASURED 2026-08-08): der erste
Lauf meldete MUTATION_PROBE_FEHLGESCHLAGEN 23/24 - alle 5 Mutanten waren rot,
aber die WIEDERHERSTELLUNG war nicht bytegleich (08ccaaabce89 -> 38149f43a9e6).
Ursache: open(..., "w", encoding="utf-8") uebersetzt auf Windows jedes "\n"
in "\r\n". Die Sonde haette also bei jedem Lauf still die Zeilenenden des
Produktivcodes umgeschrieben. Deshalb ueberall newline="" - und genau dafuer
ist die sha256-Gegenprobe da: sie hat den Defekt der Sonde gefangen, nicht
der Mensch.
"""

import hashlib
import os
import subprocess
import sys

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "cron_auto_fulfill.py")
TB_KOPF = "Traceback (most recent call last)"

MUTANTEN = [
    (
        "M1 Kollision zurueckbauen: UNGEPRUEFT wieder auf Interpreter-Code 2",
        "EXIT_UNGEPRUEFT = 3",
        "EXIT_UNGEPRUEFT = 2",
        "FAIL UNGEPRUEFT benutzt NICHT Code 2 (Interpreter-reserviert)",
    ),
    (
        "M2 Gruen-Waesche: unmessbar wieder als exit 0 ausgeben",
        "EXIT_UNGEPRUEFT = 3",
        "EXIT_UNGEPRUEFT = 0",
        "FAIL OK/DEFEKT/UNGEPRUEFT haben 3 verschiedene Codes",
    ),
    (
        "M3 Quellenzuschreibung entfernen (Stand vor Ticket 27)",
        'print(f"ERGEBNIS: RTD_FULFILL_DEFEKT (Quelle: "\n'
        '              f"{\', \'.join(quellen)}{zusatz})")',
        'print("ERGEBNIS: RTD_FULFILL_DEFEKT")',
        "FAIL Waechter-Defekt bei sauberer Lieferung wird als solcher benannt",
    ),
    (
        "M4 Falsch-Entlastung: Lieferung immer als sauber ausweisen",
        'liefer_sauber = "Lieferpipeline" not in quellen',
        "liefer_sauber = True",
        "FAIL echter Lieferdefekt wird NICHT entlastet",
    ),
    (
        "M5 Cron-Gesundheit taucht als Quelle nicht mehr auf",
        '        quellen.append("Cron-Gesundheit")',
        "        pass",
        "FAIL Waechter-Defekt bei sauberer Lieferung wird als solcher benannt",
    ),
]


def selftest():
    p = subprocess.run([sys.executable, ZIEL, "--selftest"],
                       capture_output=True, text=True, timeout=600)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def sha(pfad):
    with open(pfad, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main() -> int:
    ok = bad = 0

    def t(cond, label):
        nonlocal ok, bad
        if cond:
            ok += 1
            print(f"  OK   {label}")
        else:
            bad += 1
            print(f"  FAIL {label}")

    with open(ZIEL, encoding="utf-8", newline="") as fh:
        original = fh.read()
    sha_vorher = sha(ZIEL)
    print(f"Ziel: {ZIEL}\nsha256 vorher: {sha_vorher}\n")

    rc0, out0 = selftest()
    t(rc0 == 0, f"Baseline gruen (rc={rc0})")
    t(TB_KOPF not in out0, "Baseline ohne Traceback")

    try:
        for name, alt, neu, erwartet in MUTANTEN:
            print(f"\n-- {name}")
            t(alt in original, f"Mutationsanker gefunden: {alt.splitlines()[0][:60]}")
            if alt not in original:
                continue
            with open(ZIEL, "w", encoding="utf-8", newline="") as fh:
                fh.write(original.replace(alt, neu, 1))
            rc, out = selftest()
            t(rc == 1, f"Mutant ist ROT (rc={rc}, erwartet 1)")
            t(TB_KOPF not in out,
              "Mutant faellt durch Assertion, nicht durch Absturz")
            t(erwartet in out, f"exakte Diagnosezeile: {erwartet}")
            with open(ZIEL, "w", encoding="utf-8", newline="") as fh:
                fh.write(original)
    finally:
        with open(ZIEL, "w", encoding="utf-8", newline="") as fh:
            fh.write(original)

    sha_nachher = sha(ZIEL)
    t(sha_nachher == sha_vorher,
      f"sha256-genau wiederhergestellt ({sha_vorher[:12]} -> "
      f"{sha_nachher[:12]})")
    rc2, _ = selftest()
    t(rc2 == 0, f"nach Wiederherstellung wieder gruen (rc-Wechsel 0->1->{rc2})")

    print(f"\nERGEBNIS: {'MUTATION_PROBE_OK' if not bad else 'MUTATION_PROBE_FEHLGESCHLAGEN'}"
          f" {ok}/{ok + bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
