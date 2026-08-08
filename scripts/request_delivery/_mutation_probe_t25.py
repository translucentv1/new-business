#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mutationssonde fuer Ticket 25 (Latch-Fix im cron_health_audit).

Ticket 25 hat die Defekt-Kriterien des Audits ausgetauscht: statt
"letztes completed" (das dieses Audit SELBST bestimmt -> Latch) urteilt es
jetzt ueber [A] Lauf-VERSUCHE und [B] Pipeline-Heartbeat. Ein gruener
Selftest beweist nicht, dass die NEUEN Kriterien rot werden koennen.

Diese Sonde liefert drei Beweisarten:

  TEIL 1  ALT-STAND AUSGEFUEHRT (nicht argumentiert): die committete Fassung
          wird per `git show` geholt und mit den ECHTEN Daten von heute
          (jobs.json + executions.db) auf den Zeitpunkt des letzten roten
          Laufs gestellt. Erwartet: rc=1 gegen eine kerngesunde Pipeline.
  TEIL 2  MUTANTEN im Produktivcode je neuem Kriterium; verlangt wird
          rc != 0, KEIN echter Traceback und die EXAKTE Diagnosezeile.
  TEIL 3  Der Selftest-Nebenwirkungs-Test selbst wird mutiert - er muss rot
          werden, sonst haette er den heute gefundenen Defekt nicht gefangen
          (Selftest schrieb die PRODUKTIVE .pipeline_heartbeat.json).

Danach: beide Produktivdateien sha256-genau wiederhergestellt, rc-Wechsel
0 -> 1 -> 0 belegt. Die produktive Heartbeat-Datei wird vor Teil 3 gesichert
und danach byte-genau zurueckgeschrieben.

ERGEBNIS: MUTATION_PROBE_OK (0) | MUTATION_PROBE_DEFEKT (1)
          | MUTATION_PROBE_UNGEPRUEFT (2)
"""
import hashlib
import importlib.util
import io as _io
import contextlib
import os
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TARGET = os.path.join(HERE, "cron_health_audit.py")
FULFILL = os.path.join(HERE, "cron_auto_fulfill.py")
HB = os.path.join(HERE, ".pipeline_heartbeat.json")
TB = "Traceback (most recent call last)"

# Der reale Latch-Moment von 2026-08-07: der letzte der 5 roten Laeufe.
# Zu diesem Zeitpunkt lag das letzte 'completed' 1031 min zurueck, waehrend
# die Pipeline nachweislich lief (Job-stdout: "[1] Pipeline: ... auto_fulfill").
LATCH_NOW = datetime(2026, 8, 7, 12, 55, 47, tzinfo=timezone.utc)

# (Name, alt, neu, erwartetes [FAIL]-Label im Selftest-Output)
MUTANTS = [
    (
        "N1 [A] Lauf-VERSUCHE nicht mehr rot (stille Stagnation)",
        "        if toleranz is not None and a_age > toleranz:",
        "        if False and toleranz is not None and a_age > toleranz:",
        "letzter Lauf 3 Tage her -> rot (stille Stagnation)",
    ),
    (
        "N2 [B] Heartbeat-Alter nicht mehr rot (Lieferausfall unsichtbar)",
        "    if toleranz is not None and hb_age > toleranz:",
        "    if False and toleranz is not None and hb_age > toleranz:",
        "Job feuert, Pipeline meldet seit 20 h nichts -> rot",
    ),
    (
        "N3 Stillstand entschuldigt auch das, was er nicht abdeckt",
        "            if stillstand_deckt and stillstand >= a_age - 1:",
        "            if stillstand_deckt:",
        "nur der Geldpfad schweigt, andere Jobs laufen -> rot",
    ),
    (
        "N4 Stillstand > 24 h nicht mehr rot (agb.html § 3 ungedeckt)",
        "        if stillstand > MAX_PROMISE_MIN:",
        "        if False and stillstand > MAX_PROMISE_MIN:",
        "Stillstand > 1440 min -> rot (Zusage war real ungedeckt)",
    ),
    (
        "N5 fehlender Heartbeat wird gruen statt unmessbar",
        '        unknown.append(f"{tag}: {hb_err} -> Pipeline-Lauf nicht belegbar")',
        "        pass",
        "Ticket-22-Lage ohne Heartbeat -> unmessbar, NICHT gruen",
    ),
    (
        "N6 nicht-traegerscharfer Heartbeat wird verschwiegen",
        "    if len(traeger) > 1 and not hb_err:",
        "    if False and len(traeger) > 1 and not hb_err:",
        "zweiter Traeger: [B] nicht traegerscharf -> UNGEPRUEFT mit Grund",
    ),
    (
        "N7 Muell-Zeitstempel im Heartbeat wird als frisch gelesen",
        '        unknown.append(f"{tag}: Pipeline-Heartbeat-Zeitstempel unlesbar "',
        '        pass  # MUTANT\n    if False:\n        unknown.append(f"{tag}: x "',
        "Heartbeat mit Muell-Zeitstempel -> unmessbar",
    ),
    (
        "N8 globaler Stillstand meldet 0 statt None bei leerem Fenster",
        "    if not stamps:\n        return None",
        "    if not stamps:\n        return 0.0",
        "leeres Stillstands-Fenster erfindet keine 0 (keine Aussage)",
    ),
]

FULFILL_MUTANTS = [
    (
        "H1 Heartbeat wird auch bei DEFEKTER Pipeline aufgefrischt",
        "    if not defekt and not unmessbar:\n        hb_ok, hb_msg = write_heartbeat",
        "    if True:\n        hb_ok, hb_msg = write_heartbeat",
        "defekte Pipeline frischt den Heartbeat NICHT auf",
    ),
    (
        "H2 nicht schreibbarer Heartbeat gilt trotzdem als gruen",
        "        if not hb_ok:\n            unmessbar = True",
        "        if False:\n            unmessbar = True",
        "nicht schreibbarer Heartbeat -> UNGEPRUEFT",
    ),
    (
        "H3 Selftest schreibt wieder in den PRODUKTIVPFAD "
        "(exakt der Defekt von 2026-08-07)",
        '        g["HEARTBEAT"] = hb_path or os.path.join(tmpdir, "hb.json")',
        '        g["HEARTBEAT"] = hb_path or prod_hb',
        "PRODUKTIV-Heartbeat vom Selftest UNANGETASTET",
    ),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run_selftest(target):
    proc = subprocess.run(
        [sys.executable, target, "--selftest"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=HERE, timeout=300,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def altstand_lauf(results, t):
    """TEIL 1: die committete Fassung mit den ECHTEN Daten von heute fahren."""
    proc = subprocess.run(
        ["git", "show", "HEAD:scripts/request_delivery/cron_health_audit.py"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=REPO, timeout=60,
    )
    if proc.returncode != 0:
        t(False, "Alt-Stand aus git holbar", proc.stderr.strip()[:120])
        return
    alt_path = os.path.join(HERE, "_altstand_t25.py")
    with open(alt_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(proc.stdout)
    try:
        alt = load_module(alt_path, "_altstand_t25")
        neu = load_module(TARGET, "_neustand_t25")

        # ECHTE Daten - die Uhr wird auf den Latch-Moment gestellt UND die
        # Lauf-Zeilen dort abgeschnitten. Ohne den Schnitt saehe der
        # Alt-Stand die Erfolge, die ERST DER FIX ermoeglicht hat, und
        # bekaeme ein negatives Alter serviert (gemessen: -122 min).
        home = alt.io_home()
        jobs = alt.io_read_jobs(home)
        roh = alt.io_read_executions(home)
        execs = {}
        for jid, rows in roh.items():
            behalten = [(st, tsv) for st, tsv in rows
                        if (alt.parse_ts(tsv) or LATCH_NOW) <= LATCH_NOW]
            if behalten:
                execs[jid] = behalten
        n_jobs = len(jobs)
        n_roh = sum(len(v) for v in roh.values())
        n_rows = sum(len(v) for v in execs.values())
        print(f"  Echte Datenbasis: {n_jobs} Jobs, {n_roh} Lauf-Zeilen, "
              f"davon {n_rows} bis {LATCH_NOW.isoformat()}")

        def fahre(mod, hb_ts):
            keep = (mod.io_now, mod.io_read_executions,
                    getattr(mod, "io_read_pipeline_hb", None))
            mod.io_now = lambda: LATCH_NOW
            mod.io_read_executions = lambda _h: execs
            if keep[2] is not None:
                mod.io_read_pipeline_hb = lambda: (hb_ts, None)
            buf = _io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    rc = mod.main()
            except Exception as exc:                      # noqa: BLE001
                buf.write(f"\nAbsturz: {exc!r}")
                rc = 99
            finally:
                mod.io_now, mod.io_read_executions = keep[0], keep[1]
                if keep[2] is not None:
                    mod.io_read_pipeline_hb = keep[2]
            return rc, buf.getvalue()

        rc_alt, out_alt = fahre(alt, None)
        t(rc_alt == 1 and "letzter Erfolg vor" in out_alt,
          "ALT-STAND am realen Latch: Defekt-Claim gegen gesunde Pipeline",
          f"rc={rc_alt} " + next((ln.strip() for ln in out_alt.splitlines()
                                  if "letzter Erfolg vor" in ln), "")[:90])

        # Dieselben echten Daten, neue Fassung. Injizierte Praemisse: die
        # Pipeline hatte in diesem Lauf gemeldet - genau das garantiert der
        # Fix, weil [2b] VOR Etappe [3] schreibt (Job-stdout belegt, dass
        # Etappe [1] lief).
        hb_frisch = LATCH_NOW.isoformat()
        rc_neu, out_neu = fahre(neu, hb_frisch)
        t(rc_neu == 0 and "CRON_HEALTH_OK" in out_neu,
          "NEUE Fassung, dieselben echten Daten -> gruen (Latch geloest)",
          f"rc={rc_neu}")

        # Und die Gegenprobe: haette die Pipeline damals NICHT gemeldet,
        # muesste auch die neue Fassung rot sein.
        rc_geg, out_geg = fahre(neu, "2026-08-06T00:00:00+00:00")
        t(rc_geg == 1 and "Liefer-Pipeline meldete zuletzt vor" in out_geg,
          "NEUE Fassung bleibt rot, wenn die Pipeline wirklich schweigt",
          f"rc={rc_geg}")
    finally:
        if os.path.isfile(alt_path):
            os.remove(alt_path)


def mutiere(path, src, original, mutants, results, t, label):
    for name, old, new, expect in mutants:
        n = src.count(old)
        if n != 1:
            t(False, f"{name}: Anker eindeutig", f"{n}x gefunden statt 1x")
            continue
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(src.replace(old, new, 1))
        rc, out = run_selftest(path)
        with open(path, "wb") as fh:
            fh.write(original)
        red = rc != 0
        no_tb = TB not in out
        exact = f"FAIL] {expect}" in out or f"FAIL {expect}" in out
        t(red and no_tb and exact, f"{label} {name}",
          f"rc={rc} rot={red} kein_traceback={no_tb} exakte_diagnose={exact}")


def main():
    for p in (TARGET, FULFILL):
        if not os.path.isfile(p):
            print(f"ERGEBNIS: MUTATION_PROBE_UNGEPRUEFT (fehlt: {p})")
            return 2

    results = []

    def t(cond, name, detail=""):
        results.append((bool(cond), name))
        print(f"  [{'OK ' if cond else 'FAIL'}] {name}"
              + (f" | {detail}" if detail else ""))

    # Produktive Heartbeat-Datei sichern (Mutant H3 schreibt hinein).
    hb_backup = None
    if os.path.isfile(HB):
        with open(HB, "rb") as fh:
            hb_backup = fh.read()

    with open(TARGET, "rb") as fh:
        orig_a = fh.read()
    with open(FULFILL, "rb") as fh:
        orig_f = fh.read()
    sha_a, sha_f = sha(orig_a), sha(orig_f)
    print(f"Ziel 1 : {TARGET}\n         sha256 {sha_a[:16]} ({len(orig_a)} B)")
    print(f"Ziel 2 : {FULFILL}\n         sha256 {sha_f[:16]} ({len(orig_f)} B)")

    try:
        print("\n== TEIL 1: Alt-Stand am realen Latch AUSGEFUEHRT ==")
        altstand_lauf(results, t)

        print("\n== TEIL 2/3: Baseline + Mutanten ==")
        for path, nm in ((TARGET, "cron_health_audit"),
                         (FULFILL, "cron_auto_fulfill")):
            rc0, out0 = run_selftest(path)
            t(rc0 == 0 and TB not in out0,
              f"Baseline {nm} --selftest gruen", f"rc={rc0}")
            if rc0 != 0:
                print("ERGEBNIS: MUTATION_PROBE_UNGEPRUEFT "
                      "(Baseline rot - Mutanten waeren aussagelos)")
                return 2

        mutiere(TARGET, orig_a.decode("utf-8"), orig_a, MUTANTS,
                results, t, "[audit]")
        mutiere(FULFILL, orig_f.decode("utf-8"), orig_f, FULFILL_MUTANTS,
                results, t, "[fulfill]")
    finally:
        with open(TARGET, "wb") as fh:
            fh.write(orig_a)
        with open(FULFILL, "wb") as fh:
            fh.write(orig_f)
        if hb_backup is not None:
            with open(HB, "wb") as fh:
                fh.write(hb_backup)

    with open(TARGET, "rb") as fh:
        a2 = sha(fh.read())
    with open(FULFILL, "rb") as fh:
        f2 = sha(fh.read())
    t(a2 == sha_a, "cron_health_audit.py sha256-genau wiederhergestellt",
      f"{sha_a[:16]} -> {a2[:16]}")
    t(f2 == sha_f, "cron_auto_fulfill.py sha256-genau wiederhergestellt",
      f"{sha_f[:16]} -> {f2[:16]}")
    if hb_backup is not None:
        with open(HB, "rb") as fh:
            hb_now = fh.read()
        t(hb_now == hb_backup,
          "produktive .pipeline_heartbeat.json byte-genau wiederhergestellt",
          f"{sha(hb_backup)[:12]} -> {sha(hb_now)[:12]}")

    rc1, out1 = run_selftest(TARGET)
    rc2, out2 = run_selftest(FULFILL)
    t(rc1 == 0 and TB not in out1,
      "rc-Wechsel 0 -> 1 -> 0 belegt (cron_health_audit)", f"rc={rc1}")
    t(rc2 == 0 and TB not in out2,
      "rc-Wechsel 0 -> 1 -> 0 belegt (cron_auto_fulfill)", f"rc={rc2}")

    ok = sum(1 for c, _ in results if c)
    print(f"\n{ok}/{len(results)} bestanden")
    if ok != len(results):
        print("ERGEBNIS: MUTATION_PROBE_DEFEKT")
        return 1
    print(f"ERGEBNIS: MUTATION_PROBE_OK "
          f"({len(MUTANTS) + len(FULFILL_MUTANTS)} Mutanten rot + "
          f"Alt-Stand-Lauf an echten Daten, beide Dateien unveraendert)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
