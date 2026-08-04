#!/usr/bin/env python3
"""Funnel-Zaehler fuer den RTD-Kaufpfad — ohne Analytics, ohne Cookies.

GRUNDLAGE (MEASURED 2026-08-04, siehe tickets/9-besucher-messung.md):
Ein *echter Browser*, der einen Stripe Payment Link oeffnet, legt sofort eine
checkout.session an — noch bevor irgendetwas ausgefuellt oder bezahlt wird.
Ein reiner curl-GET (ohne JS) tut das NICHT. Damit ist die Session-Liste ein
kostenloser First-Party-Zaehler fuer die Stufe "Browser hat die Kaufseite
geoeffnet".

TRENNSCHARFES MERKMAL:
  session.payment_link = "plink_..."  -> echter Browser-Aufruf eines LIVE-Links
  session.payment_link = None         -> von uns per API erzeugte Probe-Session
Zusaetzlich werden eigene Testsessions per Id in OWN_FILE ausgeschlossen.

GRENZE (bewusst, nicht verschwiegen): gezaehlt wird die Stufe *Kaufseite
geoeffnet*, NICHT Besucher auf rtd.html. Wer rtd.html ansieht und nicht auf
"Jetzt kaufen" klickt, ist hier unsichtbar. Die Retention der Stripe-Liste ist
UNGEMESSEN — dieser Zaehler ist ein Live-Signal, kein Archiv.

Nutzung:
  python scripts/request_delivery/funnel_check.py
  python scripts/request_delivery/funnel_check.py --expire-own   # eigene Tests schliessen
"""
import datetime as _dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import app  # noqa: E402  (get_stripe_key)

OWN_FILE = os.path.join(HERE, "funnel_own_sessions.json")


def own_ids():
    """Session-Ids, die wir selbst erzeugt haben (Tests/Proben)."""
    if not os.path.exists(OWN_FILE):
        return {}
    with open(OWN_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def api(path, data=None, method=None):
    key = app.get_stripe_key()
    url = "https://api.stripe.com/v1/" + path
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method,
                                 headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, json.load(r)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return False, json.loads(raw)
        except Exception:
            return False, {"_http": e.code, "_raw": raw}


def ts(epoch):
    if not epoch:
        return "-"
    return _dt.datetime.utcfromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%SZ")


def classify(s, own):
    if s["id"] in own:
        return "EIGENTEST"
    if not s.get("payment_link"):
        return "API-PROBE"
    return "BESUCHER"


def main():
    argv = sys.argv[1:]
    own = own_ids()
    ok, payload = api("checkout/sessions?limit=100")
    if not ok:
        print("STRIPE-FEHLER:", json.dumps(payload)[:300])
        return 2
    sessions = payload["data"]

    buckets = {"BESUCHER": [], "API-PROBE": [], "EIGENTEST": []}
    for s in sessions:
        buckets[classify(s, own)].append(s)

    print("== RTD-Funnel (LIVE) ==")
    print(f"sessions_roh      = {len(sessions)}")
    for kind in ("BESUCHER", "API-PROBE", "EIGENTEST"):
        print(f"{kind:<17} = {len(buckets[kind])}")

    besucher = buckets["BESUCHER"]
    bezahlt = [s for s in besucher if s.get("payment_status") == "paid"]
    print(f"davon bezahlt     = {len(bezahlt)}")
    if besucher:
        quote = 100.0 * len(bezahlt) / len(besucher)
        print(f"Conversion        = {quote:.1f} %  ({len(bezahlt)}/{len(besucher)})")
    else:
        print("Conversion        = n/a (kein einziger Browser hat die Kaufseite geoeffnet)")

    for kind in ("BESUCHER", "API-PROBE", "EIGENTEST"):
        for s in buckets[kind]:
            print(f"  [{kind}] {ts(s.get('created'))} {s.get('payment_status'):<8} "
                  f"{s.get('amount_total')} {s.get('currency')} "
                  f"link={s.get('payment_link')} id={s['id'][:28]}...")

    if "--expire-own" in argv:
        offen = [s for s in buckets["EIGENTEST"] if s.get("status") == "open"]
        print(f"\n-- expire-own: {len(offen)} offene Eigentests --")
        for s in offen:
            ok2, res = api(f"checkout/sessions/{s['id']}/expire", data={}, method="POST")
            print(f"  {s['id'][:28]}... -> ok={ok2} status={res.get('status') if ok2 else res}")

    print("\nHinweis: gezaehlt wird 'Browser hat die Kaufseite geoeffnet', "
          "NICHT Seitenaufrufe auf rtd.html.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
