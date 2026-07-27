"""Ad-hoc MEASURED check: is the configured Stripe key valid right now?"""
import json
import urllib.request

import app

k = app.get_stripe_key()
print("key found:", bool(k), "prefix:", k[:8] if k else None, "len:", len(k) if k else 0)
if k:
    req = urllib.request.Request(
        "https://api.stripe.com/v1/account",
        headers={"Authorization": "Bearer " + k},
    )
    try:
        r = urllib.request.urlopen(req, timeout=20)
        d = json.load(r)
        print("HTTP", r.status, "acct:", d.get("id"),
              "charges_enabled:", d.get("charges_enabled"),
              "payouts_enabled:", d.get("payouts_enabled"))
    except Exception as e:
        print("ERR", e)
ws = app.get_webhook_secret()
print("webhook_secret found:", bool(ws), "prefix:", ws[:6] if ws else None)
