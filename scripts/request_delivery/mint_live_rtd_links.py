#!/usr/bin/env python3
"""Mint 3 LIVE Stripe Payment Links for rtd.html (Request-to-Delivery).

Jeder Tier bekommt einen echten LIVE-Link (sk_live_ aus .stripe_secrets / Env).
Die Links tragen:
  - Preis (3,99 / 7,99 / 14,99 EUR, one-time)
  - Pflichtfeld "anfrage" (custom_field) -> auto_fulfill liest es aus der Session
  - Redirect nach thanks.html?sid={CHECKOUT_SESSION_ID} (Merge-Field)

NUR die oeffentlichen buy.stripe.com-URLs landen in rtd.html. Der Secret-Key
wird NIE committet (app.get_stripe_key() liest ihn lokal).

Nutzung:
  python mint_live_rtd_links.py          # erstellt die 3 Links, gibt URLs + JSON
  python mint_live_rtd_links.py --dry    # prueft nur das Live-Key-Vorhandensein
"""
import json
import sys
import urllib.parse
import urllib.request

import app  # get_stripe_key

REDIRECT = "https://translucentv1.github.io/new-business/thanks.html?sid={CHECKOUT_SESSION_ID}"
TIERS = [
    ("Basis", 399),
    ("Standard", 799),
    ("Premium", 1499),
]
API = "https://api.stripe.com/v1/"


def _post(path, data, key):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        API + path, data=body,
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def mint_one(tier_name, amount_cents, key):
    prod = _post("products", {
        "name": f"RTD {tier_name} (Request-to-Delivery)",
        "metadata[source]": "rtd.html",
    }, key)
    price = _post("prices", {
        "product": prod["id"],
        "unit_amount": str(amount_cents),
        "currency": "eur",
    }, key)
    link = _post("payment_links", {
        "line_items[0][price]": price["id"],
        "line_items[0][quantity]": "1",
        "custom_fields[0][key]": "anfrage",
        "custom_fields[0][label][type]": "custom",
        "custom_fields[0][label][custom]": "Deine Anfrage",
        "custom_fields[0][type]": "text",
        "custom_fields[0][optional]": "false",
        "after_completion[type]": "redirect",
        "after_completion[redirect][url]": REDIRECT,
    }, key)
    return {
        "tier": tier_name,
        "amount_eur": amount_cents / 100,
        "url": link["url"],
        "livemode": link.get("livemode"),
        "active": link.get("active"),
        "redirect": (link.get("after_completion") or {}).get("redirect", {}).get("url"),
        "custom_fields": [cf.get("key") for cf in link.get("custom_fields", [])],
    }


def main():
    key = app.get_stripe_key()
    assert key and key.startswith("sk_live_"), "KEIN LIVE-Key -> Stopp (DEMO unmoeglich)"
    if "--dry" in sys.argv:
        print("LIVE key present:", key[:8] + "... OK (dry-run, nothing created)")
        return
    out = []
    for name, cents in TIERS:
        r = mint_one(name, cents, key)
        out.append(r)
        print(f"  {r['tier']:9} {r['amount_eur']:>5} EUR  livemode={r['livemode']} "
              f"active={r['active']} fields={r['custom_fields']}")
        print(f"           url={r['url']}")
        print(f"           redirect={r['redirect']}")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
