#!/usr/bin/env python3
"""Zeigt alle checkout.sessions des LIVE-Accounts im Klartext.

Zweck: unterscheiden, ob eine Session von einem ECHTEN Besucher stammt oder
eine selbst angelegte Probe-Session ist (Ticket 7). Reine Lesefunktion -
schreibt nichts, aendert nichts an Stripe.

Nutzung: python scripts/request_delivery/inspect_sessions.py
"""
import datetime as _dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from auto_fulfill import stripe_get  # noqa: E402


def ts(epoch):
    if not epoch:
        return "-"
    return _dt.datetime.utcfromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%SZ")


def main():
    data = stripe_get("checkout/sessions?limit=100")["data"]
    print(f"sessions_total={len(data)}")
    for s in data:
        print("-" * 62)
        print(f"id           = {s['id']}")
        print(f"created      = {ts(s.get('created'))}")
        print(f"expires_at   = {ts(s.get('expires_at'))}")
        print(f"status       = {s.get('status')}")
        print(f"pay_status   = {s.get('payment_status')}")
        print(f"mode/livemode= {s.get('mode')} / {s.get('livemode')}")
        print(f"amount_total = {s.get('amount_total')} {s.get('currency')}")
        print(f"payment_link = {s.get('payment_link')}")
        print(f"cust_email   = {(s.get('customer_details') or {}).get('email')}")
        cf = s.get("custom_fields") or []
        for f in cf:
            val = (f.get("text") or f.get("dropdown") or {}).get("value")
            print(f"custom_field = {f.get('key')} = {val!r}")
        print(f"url_present  = {bool(s.get('url'))}")
    print("-" * 62)
    paid = [s for s in data if s.get("payment_status") == "paid"]
    print(f"paid={len(paid)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
