#!/usr/bin/env python3
"""Ticket 7 — Aufraeumen der Live-Proben (Probe-Session schliessen, Probe-Links
deaktivieren) und Gegenprobe, dass nichts Aktives uebrig bleibt."""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, ".")
import app  # noqa: E402

KEY = app.get_stripe_key()
PROBE_SESSION = sys.argv[1] if len(sys.argv) > 1 else None


def api(path, data=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request("https://api.stripe.com/v1/" + path, data=body,
                                 headers={"Authorization": "Bearer " + KEY})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, json.load(r)
    except urllib.error.HTTPError as e:
        return False, {"_raw": e.read().decode("utf-8", "replace")[:300]}


if PROBE_SESSION:
    ok, r = api(f"checkout/sessions/{PROBE_SESSION}/expire", {})
    print("expire ->", r.get("status") if ok else r)

ok, listed = api("payment_links?active=true&limit=100")
data = listed.get("data", [])
probes = [p["id"] for p in data if (p.get("metadata") or {}).get("probe")]
for pid in probes:
    ok2, r2 = api("payment_links/" + pid, {"active": "false"})
    print("deaktiviert", pid, "->", r2.get("active") if ok2 else r2)
ok, listed = api("payment_links?active=true&limit=100")
data = listed.get("data", [])
print("aktive Probe-Links uebrig:",
      [p["id"] for p in data if (p.get("metadata") or {}).get("probe")])
print("aktive Payment Links gesamt:", len(data))
