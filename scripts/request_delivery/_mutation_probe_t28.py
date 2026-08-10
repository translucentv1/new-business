"""Rot-Probe fuer Ticket 28 (Falsch-Rot nach Abschaltung).

Zwei Teile, beide AUSGEFUEHRT statt argumentiert:

A) ALT-STAND-PROBE: die committete Fassung von cron_health_audit.py wird per
   `git show HEAD:...` geholt und gegen die KONSERVIERTE reale Lage vom
   2026-08-10 gefahren (Rechner 784 min aus, Heartbeat 793 min alt, letzte
   DB-Zeile 'claimed' mit started_at=NULL). Sie muss CRON_HEALTH_DEFEKT
   melden - sonst behauptet Ticket 28 einen Defekt, den es nicht gibt.
   Die neue Fassung muss dieselbe Lage ohne Defekt-Claim beurteilen.

B) MUTANTEN: jeder neue Zweig bekommt mindestens einen Mutanten IM
   PRODUKTIVCODE. Jeder Mutant muss den Selftest rot machen (exakte
   Falltitel, kein Absturz), danach wird die Datei sha256-genau
   wiederhergestellt.

Aufruf:  python scripts/request_delivery/_mutation_probe_t28.py
Ausgabe: MUTATION_PROBE_OK / MUTATION_PROBE_FEHLGESCHLAGEN  (rc 0 / 1)
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TARGET = os.path.join(HERE, "cron_health_audit.py")
REL = "scripts/request_delivery/cron_health_audit.py"

results: list[tuple[bool, str]] = []


def t(cond: bool, name: str, detail: str = "") -> None:
    results.append((bool(cond), name))
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}" + (f" | {detail}" if detail else ""))


def sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def run_selftest(path: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, path, "--selftest"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=ROOT)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


# --------------------------------------------------------------------------
# Teil A: die konservierte Lage, gegen ALT-Stand und NEU-Stand ausgefuehrt
# --------------------------------------------------------------------------
# Zahlen aus tickets/28-falschrot-nach-abschaltung.md (MEASURED 2026-08-10):
#   Scheduler-Stillstand 784 min | Heartbeat 793 min alt | letzter Lauf-
#   VERSUCH vor 9 min, aber als 'claimed' mit started_at=NULL.
KONSERVIERT = """
import importlib.util, os, sys
from datetime import datetime, timedelta, timezone

# EIGENTOR 2026-08-10: der erste Anlauf benutzte runpy.run_path(). Das gibt
# eine KOPIE der Modul-Globals zurueck - die Injektion landete im Nichts und
# die Sonde mass in Wahrheit die ECHTE jobs.json/executions.db (219 Zeilen,
# echter HERMES_HOME). Sie meldete dann CRON_HEALTH_OK und haette das als
# "neue Fassung gruen" durchgehen lassen. Ueber importlib bekommt man das
# LEBENDE Modulobjekt, dessen __dict__ die Funktionen wirklich benutzen.
_spec = importlib.util.spec_from_file_location("t28probe", r"{modpath}")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

NOW = datetime(2026, 8, 10, 1, 45, tzinfo=timezone.utc)
HOME = os.path.join("Z:", "fakehermes")
ROOT = _mod.ROOT
MONEY_DIR = _mod.MONEY_DIR
LOADER = os.path.join(HOME, "scripts", "rtd_auto_fulfill.py")
TARGET = os.path.join(MONEY_DIR, "cron_auto_fulfill.py")
LOADER_TEXT = ('TARGET = os.path.join(\\n'
               '    r"' + ROOT + '", "scripts", "request_delivery",\\n'
               '    "cron_auto_fulfill.py",\\n)\\nrunpy.run_path(TARGET)\\n')
nk = _mod.nk


def ts(minutes_ago):
    return (NOW - timedelta(minutes=minutes_ago)).isoformat()


JOB = dict(id="bfb63346d942", name="RTD Auto-Fulfill", enabled=True,
           no_agent=True, script="rtd_auto_fulfill.py", workdir=ROOT,
           prompt="", schedule={{"kind": "interval", "minutes": 30}})

# Der Rechner war 784 min aus: davor lief alles im 30-min-Takt, danach genau
# EINE Zeile - beansprucht (claimed), nie gestartet (started_at=NULL).
# {rowsform}
ROWS = {rows}
EXECS = {{"bfb63346d942": ROWS}}

FILES = {{nk(LOADER): LOADER_TEXT, nk(TARGET): ""}}
_mod.io_home = lambda: HOME
_mod.io_read_jobs = lambda _h: [JOB]
_mod.io_read_executions = lambda _h: EXECS
_mod.io_read_signale = lambda _h: {{}}
_mod.io_isfile = lambda p: nk(p) in FILES
_mod.io_isdir = lambda p: nk(p) == nk(ROOT)
_mod.io_read_text = lambda p: FILES[nk(p)]
_mod.io_now = lambda: NOW
_mod.io_read_pipeline_hb = lambda: (ts(793), None)

rc = _mod.main()
print("PROBE_RC=" + str(rc))
"""


def fahre_konservierte_lage(modpath: str, label: str,
                            dreituplig: bool) -> tuple[int, str]:
    # Beide Fassungen bekommen GENAU die Zeilen, die ihr eigener Leser aus
    # denselben DB-Zeilen erzeugt haette: der Alt-Stand kennt started_at
    # nicht (2-Tupel, die claimed-Zeile sieht aus wie ein Lauf), die neue
    # Fassung liest es mit (3-Tupel). Anders waere der Vergleich unfair -
    # der Alt-Stand wuerde an der Tupelform scheitern statt am Urteil.
    if dreituplig:
        rows = ('[("completed", ts(793 + i * 30), True) for i in range(0, 6)]'
                ' + [("claimed", ts(9), False)]')
        form = "3-Tupel (neuer Leser: started_at bekannt)"
    else:
        rows = ('[("completed", ts(793 + i * 30)) for i in range(0, 6)]'
                ' + [("claimed", ts(9))]')
        form = "2-Tupel (Alt-Leser: started_at unbekannt)"
    src = KONSERVIERT.format(modpath=modpath.replace("\\", "\\\\"),
                             rows=rows, rowsform=form)
    fd, runner = tempfile.mkstemp(suffix="_t28run.py")
    os.close(fd)
    with open(runner, "w", encoding="utf-8") as fh:
        fh.write(src)
    try:
        p = subprocess.run([sys.executable, runner], capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           cwd=ROOT)
        out = (p.stdout or "") + (p.stderr or "")
    finally:
        os.remove(runner)
    rc = -1
    for line in out.splitlines():
        if line.startswith("PROBE_RC="):
            rc = int(line.split("=", 1)[1])
    print(f"    [{label}] rc={rc}")
    return rc, out


def teil_a() -> None:
    print("== Teil A: konservierte Lage 2026-08-10 (784/793/9 min) ==")
    fd, altpath = tempfile.mkstemp(suffix="_t28alt.py")
    os.close(fd)
    p = subprocess.run(["git", "show", f"HEAD:{REL}"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    if p.returncode != 0 or not p.stdout:
        t(False, "Alt-Stand per git show holbar", p.stderr[:200])
        return
    with open(altpath, "w", encoding="utf-8") as fh:
        fh.write(p.stdout)
    t(True, "Alt-Stand (HEAD) geholt", f"{len(p.stdout)} B")

    rc_alt, out_alt = fahre_konservierte_lage(altpath, "ALT", False)
    # Erst beweisen, dass die Injektion ueberhaupt greift (Eigentor oben:
    # runpy lieferte eine Globals-KOPIE, die Sonde mass die echte DB).
    t("fakehermes" in out_alt and "Laeufe    = 7 gesamt" in out_alt,
      "Injektion greift wirklich (Fake-HOME + 7 injizierte Zeilen im "
      "Ausdruck, nicht die echte executions.db)",
      f"{'fakehermes' in out_alt}/{'Laeufe    = 7 gesamt' in out_alt}")
    t(rc_alt == 1 and "die Lieferung steht" in out_alt,
      "ALT-Stand meldet gegen die kerngesunde Lieferung CRON_HEALTH_DEFEKT "
      "(das Falsch-Rot ist real, nicht behauptet)",
      f"rc={rc_alt}")

    rc_neu, out_neu = fahre_konservierte_lage(TARGET, "NEU", True)
    t("fakehermes" in out_neu and "Laeufe    = 7 gesamt" in out_neu,
      "Injektion greift auch bei der neuen Fassung",
      f"{'fakehermes' in out_neu}/{'Laeufe    = 7 gesamt' in out_neu}")
    t(rc_neu != 1 and "die Lieferung steht" not in out_neu,
      "NEUE Fassung erhebt in derselben Lage KEINEN Defekt-Claim",
      f"rc={rc_neu}")
    t(rc_neu == 2 and "keine Gelegenheit zu melden" in out_neu,
      "NEUE Fassung sagt UNGEPRUEFT mit benannter Begruendung "
      "(kein stilles Gruen)", f"rc={rc_neu}")
    os.remove(altpath)


# --------------------------------------------------------------------------
# Teil B: Mutanten im Produktivcode
# --------------------------------------------------------------------------
MUTANTEN = [
    (
        "M1 verpasste Gelegenheit zaehlt auch nie gestartete Laeufe",
        "    verpasst = [s for s in starts if (s - hb).total_seconds() > 60]",
        "    verpasst = [s for s in attempts if (s - hb).total_seconds() > 60]",
        "T28-Realfall",
    ),
    (
        "M2 Karenz fuer Uhr-Jitter entfernt",
        "    verpasst = [s for s in starts if (s - hb).total_seconds() > 60]",
        "    verpasst = [s for s in starts if (s - hb).total_seconds() > 0]",
        "Uhr-Jitter",
    ),
    (
        "M3 24-h-Grenze feuert nie (Dauerfreibrief)",
        "    if hb_age > MAX_PROMISE_MIN:",
        "    if hb_age > 10 * MAX_PROMISE_MIN:",
        "kein Freibrief",
    ),
    (
        "M4 'keine Gelegenheit' wird stillschweigend gruen",
        "    unknown.append(\n"
        "        f\"{tag}: Pipeline meldete zuletzt vor {hb_age:.0f} min - seither ist \"",
        "    _unused_t28 = (\n"
        "        f\"{tag}: Pipeline meldete zuletzt vor {hb_age:.0f} min - seither ist \"",
        "UNGEPRUEFT, nicht OK",
    ),
    (
        "M5 Leser ignoriert started_at (jede claimed-Zeile gilt als Lauf)",
        "        out.setdefault(job_id, []).append((status, ts, started_at is not None))",
        "        out.setdefault(job_id, []).append((status, ts, True))",
        "Verdrahtung",
    ),
    (
        "M6 verpasste Gelegenheit erzeugt keinen Defekt mehr",
        "    if verpasst:",
        "    if verpasst and False:",
        "Messlatte 1",
    ),
]


def teil_b() -> None:
    print("== Teil B: Mutanten im Produktivcode ==")
    # WICHTIG (Eigentor 2026-08-10): open(...,'w') im TEXTMODUS schreibt auf
    # Windows '\n' als '\r\n' zurueck. Die erste Fassung dieser Sonde hat die
    # Produktivdatei damit KOMPLETT auf CRLF umgeschrieben - sha256 wich ab,
    # der Inhalt war identisch, der Diff 1449 Zeilen gross. Ab hier nur noch
    # BINAER lesen/schreiben, dann ist die Wiederherstellung wirklich exakt.
    with open(TARGET, "rb") as fh:
        original = fh.read()
    vorher = sha(TARGET)

    rc, out = run_selftest(TARGET)
    t(rc == 0 and "SELFTEST OK" in out,
      "Baseline: unmutierter Selftest gruen", f"rc={rc}")
    t("Traceback (most recent call last)" not in out,
      "Baseline laeuft ohne Absturz")

    try:
        for name, alt, neu, erwartet in MUTANTEN:
            alt_b = alt.encode("utf-8")
            neu_b = neu.encode("utf-8")
            if original.count(alt_b) != 1:
                t(False, f"{name}: Anker genau 1x gefunden",
                  f"{original.count(alt_b)}x")
                continue
            with open(TARGET, "wb") as fh:
                fh.write(original.replace(alt_b, neu_b))
            rc_m, out_m = run_selftest(TARGET)
            rot_zeilen = [ln for ln in out_m.splitlines()
                          if ln.strip().startswith("[FAIL]")]
            traf = any(erwartet in ln for ln in rot_zeilen)
            t(rc_m == 1 and traf,
              f"{name} -> Selftest rot am erwarteten Fall",
              f"rc={rc_m}, rote Faelle={len(rot_zeilen)}")
            t("Traceback (most recent call last)" not in out_m,
              f"{name}: rot durch ein URTEIL, nicht durch einen Absturz")
    finally:
        with open(TARGET, "wb") as fh:
            fh.write(original)

    nachher = sha(TARGET)
    t(vorher == nachher,
      "Produktivdatei sha256-genau wiederhergestellt",
      f"{vorher} -> {nachher}")
    rc2, out2 = run_selftest(TARGET)
    t(rc2 == 0 and "SELFTEST OK" in out2,
      "rc-Wechsel belegt: 0 -> 1 -> 0", f"rc={rc2}")


def main() -> int:
    teil_a()
    teil_b()
    ok = sum(1 for c, _ in results if c)
    print(f"\nERGEBNIS: {'MUTATION_PROBE_OK' if ok == len(results) else 'MUTATION_PROBE_FEHLGESCHLAGEN'}"
          f" {ok}/{len(results)}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
