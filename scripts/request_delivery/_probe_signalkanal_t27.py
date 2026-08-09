"""Ticket 27 - unabhaengige Messsonde auf den einzigen Signalkanal.

Liest NUR (mode=ro) und faellt kein Urteil. Zweck: die zentrale Behauptung
des Vorticks ("der Exitcode ueberlebt woertlich im error-Text") gegen die
ECHTE executions.db pruefen, statt sie zu uebernehmen.
"""
import collections
import os
import re
import sqlite3
import sys

TRAEGER = "bfb63346d942"
WAECHTER = "5e99ad47470f"
RX = re.compile(r"^Script exited with code (\d+)")


def home():
    h = os.environ.get("HERMES_HOME")
    if h:
        return h
    return os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes")


def main():
    db = os.path.join(home(), "cron", "executions.db")
    print(f"DB: {db}  exists={os.path.isfile(db)}")
    if not os.path.isfile(db):
        return 2
    uri = "file:///" + db.replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=10)
    cols = [r[1] for r in con.execute("PRAGMA table_info(executions)")]
    print("SPALTEN:", cols)
    print("STATUS global:",
          con.execute("SELECT status, count(*) FROM executions "
                      "GROUP BY status ORDER BY 2 DESC").fetchall())

    for jid, name in ((TRAEGER, "Traeger"), (WAECHTER, "Waechter")):
        rows = con.execute(
            "SELECT status, COALESCE(error,'') FROM executions WHERE job_id=?",
            (jid,)).fetchall()
        print(f"\n== {name} {jid}: {len(rows)} Zeilen ==")
        print("  status:", collections.Counter(s for s, _ in rows).most_common())
        codes = collections.Counter()
        sonst = collections.Counter()
        for s, e in rows:
            if s == "completed":
                continue
            m = RX.match(e or "")
            if m:
                codes["exit " + m.group(1)] += 1
            else:
                sonst[(s, (e or "")[:70])] += 1
        print("  dekodierte Exitcodes:", codes.most_common())
        print("  NICHT dekodierbar  :", sonst.most_common(8))

    allrows = con.execute("SELECT status, COALESCE(error,'') FROM executions "
                          "WHERE status<>'completed'").fetchall()
    g = collections.Counter()
    for s, e in allrows:
        m = RX.match(e or "")
        g[("exit " + m.group(1)) if m else (s + " | " + (e or "")[:45])] += 1
    print("\n== GLOBAL nicht-completed ==")
    for k, v in g.most_common(15):
        print(f"  {v:5d}  {k}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
