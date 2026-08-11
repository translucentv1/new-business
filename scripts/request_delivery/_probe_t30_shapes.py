"""Ticket 30 - Ad-hoc-Sonde: welche Zustell-FORMEN kommen real in jobs.json vor?

Liest NUR. Gibt KEINE Adressen aus (nur Typ/Laenge/Praefix), damit kein
Credential im Log landet. Zweck: die Annahme "deliver='origin' + origin=None ist
die einzige unzustellbare Form" gegen die realen Feldwerte pruefen.
"""
import collections
import json
import os

HOME = os.environ.get("HERMES_HOME") or os.path.join(
    os.path.expanduser("~"), "AppData", "Local", "hermes"
)
P = os.path.join(HOME, "cron", "jobs.json")

data = json.load(open(P, encoding="utf-8"))
jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data
items = list(jobs.items() if isinstance(jobs, dict) else [(j.get("id"), j) for j in jobs])

print("jobs.json: %s" % P)
print("Jobs gesamt: %d" % len(items))

jobkeys = collections.Counter()
for _jid, j in items:
    jobkeys.update(j.keys())
print("\n== Job-Felder (Vorkommen) ==")
for k, n in sorted(jobkeys.items()):
    print("  %-24s %d" % (k, n))

deliver_vals = collections.Counter()
origin_keys = collections.Counter()
platform_vals = collections.Counter()
print("\n== Pro Job (Adressen redigiert) ==")
for jid, j in items:
    o = j.get("origin")
    deliver_vals[repr(j.get("deliver"))] += 1
    if isinstance(o, dict):
        origin_keys.update(o.keys())
        platform_vals[repr(o.get("platform"))] += 1
        red = {}
        for k, v in o.items():
            if k in ("platform", "kind", "type"):
                red[k] = v
            else:
                s = str(v)
                red[k] = "<%s len=%d pre=%s>" % (type(v).__name__, len(s), s[:4])
        osum = red
    else:
        osum = repr(o)
    print("  %-14s enabled=%-5s deliver=%-10s origin=%s"
          % (str(jid)[:12], bool(j.get("enabled")), repr(j.get("deliver")), osum))

print("\n== deliver-Werte ==")
for k, n in deliver_vals.most_common():
    print("  %-14s %d" % (k, n))
print("== origin-Felder ==")
for k, n in origin_keys.most_common():
    print("  %-14s %d" % (k, n))
print("== origin.platform-Werte ==")
for k, n in platform_vals.most_common():
    print("  %-14s %d" % (k, n))
