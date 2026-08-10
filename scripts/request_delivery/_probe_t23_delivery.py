"""Ad-hoc-Sonde (Ticket 23): warum scheitert die Zustellung nur bei manchen Jobs?

Liest NUR (keine Aenderung). Vergleicht die Zustell-Konfiguration des
nachweislich ERFOLGREICHEN Jobs mit der der scheiternden Jobs.
"""
import json
import os
import sys

HOME = os.environ.get("HERMES_HOME") or os.path.join(
    os.path.expanduser("~"), "AppData", "Local", "hermes"
)
P = os.path.join(HOME, "cron", "jobs.json")

WATCH = {
    "3e7e333151b0": "ZUSTELLUNG OK (8x delivered to whatsapp:...@lid)",
    "bfb63346d942": "SCHEITERT (jidDecode, Geldpfad-Traeger!)",
    "a89ac41273b2": "SCHEITERT (jidDecode)",
    "5e99ad47470f": "Waechter 2. Ring",
}

data = json.load(open(P, encoding="utf-8"))
jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data
items = jobs.items() if isinstance(jobs, dict) else [(j.get("id"), j) for j in jobs]
items = list(items)
print("jobs.json =", P)
print("Jobs gesamt:", len(items))

found = 0
for jid, j in items:
    sid = str(jid)
    hit = next((k for k in WATCH if k in sid or k in str(j.get("id", ""))), None)
    if not hit:
        continue
    found += 1
    print("\n===== %s  (%s)" % (sid, WATCH[hit]))
    print("  name     =", j.get("name"))
    print("  enabled  =", j.get("enabled"), " no_agent =", j.get("no_agent"))
    rel = {
        k: v
        for k, v in j.items()
        if any(t in k.lower() for t in ("deliv", "orig", "chan", "chat", "to", "sess"))
    }
    for k in sorted(rel):
        print("  %-18s = %r" % (k, rel[k]))

print("\ngefunden: %d von %d beobachteten Jobs" % (found, len(WATCH)))
if found == 0:
    print("SONDE_UNGEPRUEFT: keiner der Job-Ids in jobs.json gefunden")
    sys.exit(2)
print("SONDE_OK")
