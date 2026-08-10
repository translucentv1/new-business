"""Ticket 23 - vollzaehlige Bestandsaufnahme der Zustell-Konfiguration.

Liest NUR. Klassifiziert JEDEN Job in jobs.json:
  ZUSTELLBAR   deliver='origin' + origin-Block vorhanden
  KAPUTT       deliver='origin' + origin=None  -> Scheduler faellt auf
               'whatsapp:self' zurueck -> jidDecode(undefined) -> HTTP 500
  LOKAL        deliver='local'  (keine Zustellung gewollt)
  SONSTIGES    alles andere (muss benannt werden, nicht stillschweigend gruen)
"""
import json
import os
import sys

HOME = os.environ.get("HERMES_HOME") or os.path.join(
    os.path.expanduser("~"), "AppData", "Local", "hermes"
)
P = os.path.join(HOME, "cron", "jobs.json")

data = json.load(open(P, encoding="utf-8"))
jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data
items = list(jobs.items() if isinstance(jobs, dict) else [(j.get("id"), j) for j in jobs])

buckets = {"ZUSTELLBAR": [], "KAPUTT": [], "LOKAL": [], "SONSTIGES": []}
for jid, j in items:
    deliver = j.get("deliver")
    origin = j.get("origin")
    name = (j.get("name") or "")[:46]
    row = (str(jid), name, bool(j.get("enabled")), bool(j.get("no_agent")))
    if deliver == "origin" and origin:
        buckets["ZUSTELLBAR"].append(row + (origin.get("chat_id"),))
    elif deliver == "origin" and not origin:
        buckets["KAPUTT"].append(row + (None,))
    elif deliver == "local":
        buckets["LOKAL"].append(row + (None,))
    else:
        buckets["SONSTIGES"].append(row + (repr(deliver),))

total = sum(len(v) for v in buckets.values())
if total != len(items):
    print("SONDE_UNGEPRUEFT: Klassifikation unvollzaehlig %d != %d" % (total, len(items)))
    sys.exit(2)

for k in ("KAPUTT", "ZUSTELLBAR", "LOKAL", "SONSTIGES"):
    print("\n== %s (%d) ==" % (k, len(buckets[k])))
    for jid, name, en, na, extra in buckets[k]:
        print("  %s enabled=%-5s no_agent=%-5s %-46s %s" % (jid, en, na, name, extra or ""))

print("\nJobs gesamt vollzaehlig klassifiziert: %d" % total)
print("ERGEBNIS: %s" % ("ZUSTELL_DEFEKT" if buckets["KAPUTT"] else "ZUSTELL_OK"))
sys.exit(1 if buckets["KAPUTT"] else 0)
