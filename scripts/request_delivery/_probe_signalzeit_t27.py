"""Ticket 27 - Zeitverteilung + Exitcode-Konvention (Messsonde, read-only).

Beantwortet zwei Fragen, die ueber die Ticket-27-Entscheidung bestimmen:
 1. Sind die 'Skipped to prevent unintended spend'-Zeilen des Geldpfad-
    Traegers AKTUELL oder Alt-Bestand aus der Agenten-Aera?
 2. Welche Exitcodes vergeben die Geldpfad-Skripte WIRKLICH (Quelltext),
    und welche kommen in der DB vor?
"""
import collections
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

TRAEGER = "bfb63346d942"
RX = re.compile(r"^Script exited with code (\d+)")


def home():
    h = os.environ.get("HERMES_HOME")
    return h or os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes")


def klasse(status, err):
    if status == "completed":
        return "completed"
    m = RX.match(err or "")
    if m:
        return "SKRIPT-URTEIL exit " + m.group(1)
    if "Skipped to prevent unintended spend" in (err or ""):
        return "RUNNER-ABBRUCH Spend-Guard (Skript lief NIE)"
    if status == "unknown":
        return "Scheduler-Neustart"
    if status in ("claimed", "running"):
        return "laeuft/haengt"
    return "RUNNER-ABBRUCH sonstiges (Skript lief NIE)"


def main():
    db = os.path.join(home(), "cron", "executions.db")
    uri = "file:///" + db.replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=10)
    rows = con.execute(
        "SELECT COALESCE(started_at, claimed_at, ''), status, "
        "COALESCE(error,'') FROM executions WHERE job_id=? "
        "ORDER BY 1", (TRAEGER,)).fetchall()
    print(f"== Traeger {TRAEGER}: {len(rows)} Zeilen, chronologisch ==")
    if rows:
        print(f"   erste Zeile: {rows[0][0]}   letzte Zeile: {rows[-1][0]}")

    # Klassen pro Kalendertag
    per_tag = collections.defaultdict(collections.Counter)
    for ts, st, err in rows:
        tag = (ts or "?")[:10]
        per_tag[tag][klasse(st, err)] += 1
    print("\n-- Klassen pro Tag (nur die letzten 8 Tage) --")
    for tag in sorted(per_tag)[-8:]:
        teile = ", ".join(f"{v}x {k}" for k, v in per_tag[tag].most_common())
        print(f"  {tag}: {teile}")

    print("\n-- die 8 juengsten Zeilen im Klartext --")
    for ts, st, err in rows[-8:]:
        print(f"  {ts}  {st:9s}  {klasse(st, err)}  | {(err or '')[:70]}")

    # letzte Spend-Guard-Zeile
    letzte_guard = [r for r in rows
                    if "Skipped to prevent unintended spend" in (r[2] or "")]
    if letzte_guard:
        print(f"\n  letzte Spend-Guard-Zeile: {letzte_guard[-1][0]}  "
              f"(gesamt {len(letzte_guard)})")
    letztes_urteil = [r for r in rows
                      if RX.match(r[2] or "") or r[1] == "completed"]
    if letztes_urteil:
        print(f"  letzte Zeile MIT Skript-Urteil: {letztes_urteil[-1][0]} "
              f"({letztes_urteil[-1][1]})")
    print(f"  jetzt (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    con.close()

    # -- Quelltext-Konvention: welche Exitcodes vergeben die Skripte? -----
    print("\n== Exitcode-Konvention im Quelltext (grep sys.exit/return) ==")
    root = os.path.dirname(os.path.abspath(__file__))
    ziele = [os.path.join(root, "cron_auto_fulfill.py"),
             os.path.join(os.path.dirname(os.path.dirname(root)),
                          "scripts", "rtd_health_watchdog.py"),
             os.path.join(root, "cron_health_audit.py")]
    for p in ziele:
        if not os.path.isfile(p):
            print(f"  {os.path.basename(p)}: FEHLT ({p})")
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        codes = sorted(set(re.findall(r"(?:sys\.exit|raise SystemExit)\(\s*(\d+)", src)))
        print(f"  {os.path.basename(p)}: sys.exit-Codes = {codes or '(keine literalen)'}")
        for m in re.finditer(r"^.*(?:sys\.exit|SystemExit)\(.*$", src, re.M):
            print(f"      {m.group(0).strip()[:96]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
