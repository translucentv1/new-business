#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mutationssonde fuer den Ticket-27-Fix im cron_health_audit (Fremdzeilen).

Befund, der den Fix ausgeloest hat (MEASURED 2026-08-08): in der PRODUKTIVEN
executions.db steht eine Zeile mit job_id 't27probe0001' (source='direct',
"Script exited with code 3") - eine Wegwerf-Sonde des Vorticks. jobs.json
kennt diesen Job nicht. `global_stillstand()` zaehlte bis heute JEDE Zeile der
DB als Scheduler-Puls, also auch diese. Fehlerrichtungen beide teuer:
  * Fremdpuls verkleinert die Luecke -> echte Nachtabschaltung wird nicht
    erkannt -> Falsch-ROT gegen einen gesunden Geldpfad.
  * Fremdpuls fuellt eine >24-h-Luecke -> Falsch-GRUEN, obwohl die
    24-h-Zusage aus agb.html § 3 real ungedeckt war.

Drei Beweisarten:
  TEIL 1  ECHTE DATEN, nicht argumentiert: reale jobs.json + executions.db;
          verwaiste job_ids werden benannt und der Stillstands-Wert wird
          einmal MIT und einmal OHNE Filter berechnet.
  TEIL 2  MUTANTEN im Produktivcode: jeder muss den Selftest rot machen,
          ohne Absturz, mit der EXAKTEN Diagnosezeile.
  TEIL 3  sha256-genaue Wiederherstellung + rc-Wechsel 0 -> 1 -> 0.

ERGEBNIS: MUTATION_PROBE_OK (0) | MUTATION_PROBE_DEFEKT (1)
          | MUTATION_PROBE_UNGEPRUEFT (2)
"""
import hashlib
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "cron_health_audit.py")
TB = "Traceback (most recent call last)"

# (Name, alt, neu, erwartetes [FAIL]-Label im Selftest-Output)
MUTANTS = [
    (
        "F1 Filter aus = Alt-Stand: jede DB-Zeile zaehlt als Scheduler-Puls",
        "        if bekannte_ids is not None and jid not in bekannte_ids:",
        "        if False and jid not in (bekannte_ids or ()):",
        "Fremdzeilen tarnen keine Nachtabschaltung (kein Falsch-Rot)",
    ),
    (
        "F2 ignorierte Fremdzeilen werden nicht mehr gezaehlt",
        "            fremd += len(rows)",
        "            fremd += 0",
        "ignorierte Fremdzeilen werden gezaehlt und gedruckt",
    ),
    (
        "F3 nach dem Filter leeres Fenster erfindet wieder eine 0",
        "        return None, fremd     # nichts im Fenster",
        "        return 0.0, fremd     # nichts im Fenster",
        "nur Fremdzeilen -> keine erfundene Stillstands-Zahl, nicht gruen",
    ),
    # -- Ticket 27, zweiter Befund (MEASURED 2026-08-09): der Dekoder war
    #    GEBAUT, aber main() rief ihn nie auf. Selftest 41/41 gruen, im
    #    Live-Lauf stand trotzdem dauerhaft "(error-Texte nicht lesbar)".
    #    Klasse: unverdrahtetes Bauteil. Diese vier Mutanten stellen genau
    #    diese Fehler wieder her - jeder muss rot werden.
    (
        "W1 Verdrahtung gekappt: main() reicht die Signale nicht mehr durch",
        "                      signale=signale, signal_err=signal_err)",
        "                      signale=None, signal_err=None)",
        "Verdrahtung: main() liest die error-Texte wirklich "
        "(Regression 2026-08-09)",
    ),
    (
        "W2 unbekannter Exitcode wird stillschweigend zu DEFEKT",
        '                name = f"KONVENTIONSBRUCH (exit {code})"',
        '                name = "DEFEKT (exit 1)"',
        "unbekannter Exitcode heisst Konventionsbruch, nicht stillschweigend ok",
    ),
    (
        "W3 Runner-Abbruch (Skript lief nie) wird als Skript-Defekt gelesen",
        '            klassen[f"RUNNER-ABBRUCH {grund} (Skript lief NIE)"] += 1',
        '            klassen["DEFEKT (exit 1)"] += 1',
        "Runner-Abbruch wird NICHT als Skript-Defekt gelesen "
        "(136 reale Zeilen)",
    ),
    (
        "W4 Fallback behauptet wieder Unlesbarkeit statt Nichtlesen",
        '            out.append("      dekodiert (Ticket 27, INFO): NICHT '
        'GELESEN "',
        '            out.append("      dekodiert (Ticket 27, INFO): nicht '
        'lesbar "',
        "unlesbare error-Texte: Grund benannt, kein Defekt-Claim",
    ),
]

ok = bad = 0


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


def run_selftest():
    p = subprocess.run([sys.executable, TARGET, "--selftest"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=HERE, timeout=300)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def teil1_echte_daten():
    """Reale DB: welche job_ids kennt jobs.json nicht, und was aendert das?"""
    print("-- TEIL 1: echte jobs.json + executions.db --")
    mod = load_module(TARGET, "_t27b_audit")
    home = mod.io_home()
    if not home:
        t(False, "HERMES_HOME gesetzt")
        return
    try:
        jobs = mod.io_read_jobs(home)
        execs = mod.io_read_executions(home)
    except Exception as exc:                                  # noqa: BLE001
        t(False, "reale Daten lesbar", repr(exc)[:120])
        return
    bekannt = {j.get("id") for j in jobs}
    fremd_ids = sorted(set(execs) - bekannt)
    n_fremd = sum(len(execs[j]) for j in fremd_ids)
    print(f"  Jobs in jobs.json : {len(jobs)}")
    print(f"  job_ids in der DB : {len(execs)}")
    print(f"  davon verwaist    : {len(fremd_ids)} -> {fremd_ids} "
          f"({n_fremd} Zeilen)")
    now = mod.io_now()
    mit, _ = mod.global_stillstand(execs, now, None)       # Alt-Verhalten
    ohne, gezaehlt = mod.global_stillstand(execs, now, bekannt)   # neu
    f_mit = "None" if mit is None else f"{mit:.0f} min"
    f_ohne = "None" if ohne is None else f"{ohne:.0f} min"
    print(f"  Stillstand MIT Fremdzeilen (Alt): {f_mit}")
    print(f"  Stillstand OHNE Fremdzeilen (neu): {f_ohne}")
    t(gezaehlt == n_fremd,
      "Filter zaehlt genau die verwaisten Zeilen", f"{gezaehlt} == {n_fremd}")
    t(n_fremd >= 0, "reale Fremdzeilen-Zahl gemessen", str(n_fremd))
    if n_fremd:
        print("  HINWEIS: mindestens eine Fremdzeile ist real vorhanden - "
              "der Mechanismus ist keine Theorie.")


def main():
    print("== Mutationssonde Ticket 27b (Fremdzeilen im Scheduler-Puls) ==")
    original = open(TARGET, "rb").read()
    sha_vorher = sha(original)
    print(f"Ziel  : {TARGET}\nsha256: {sha_vorher[:12]}\n")

    teil1_echte_daten()

    print("\n-- TEIL 2: Baseline + Mutanten --")
    rc0, out0 = run_selftest()
    t(rc0 == 0, "Baseline gruen (rc=0)", f"rc={rc0}")
    t(TB not in out0, "Baseline ohne Traceback")
    if rc0 != 0:
        print("ERGEBNIS: MUTATION_PROBE_UNGEPRUEFT (Baseline nicht gruen)")
        return 2

    src = original.decode("utf-8")
    try:
        for name, alt, neu, label in MUTANTS:
            print(f"\n-- {name}")
            if src.count(alt) != 1:
                t(False, "Mutationsanker genau 1x gefunden",
                  f"{src.count(alt)}x: {alt[:60]}")
                continue
            t(True, f"Mutationsanker gefunden: {alt.strip()[:58]}")
            with open(TARGET, "w", encoding="utf-8", newline="") as fh:
                fh.write(src.replace(alt, neu))
            rc, out = run_selftest()
            t(rc != 0, f"Mutant ist ROT (rc={rc})", f"rc={rc}")
            t(TB not in out, "Mutant faellt durch Assertion, nicht Absturz")
            t(f"[FAIL] {label}" in out,
              f"exakte Diagnosezeile: {label[:52]}",
              "" if f"[FAIL] {label}" in out else "Zeile fehlt")
    finally:
        with open(TARGET, "wb") as fh:
            fh.write(original)

    print("\n-- TEIL 3: Wiederherstellung --")
    sha_nachher = sha(open(TARGET, "rb").read())
    t(sha_nachher == sha_vorher, "sha256-genau wiederhergestellt",
      f"{sha_vorher[:12]} -> {sha_nachher[:12]}")
    rc2, _ = run_selftest()
    t(rc2 == 0, "nach Wiederherstellung wieder gruen (rc-Wechsel 0->1->0)",
      f"rc={rc2}")

    print(f"\nERGEBNIS: "
          f"{'MUTATION_PROBE_OK' if bad == 0 else 'MUTATION_PROBE_DEFEKT'} "
          f"{ok}/{ok + bad}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
