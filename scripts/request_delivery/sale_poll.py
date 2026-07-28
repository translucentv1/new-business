"""Sale poll (MEASURED): list recent Stripe charges + completed checkout
sessions from the live account. Replacement for the nonexistent
scripts/stripe_uploader.py referenced in CLAUDE.md.
"""
import json
import urllib.request

import app

KEY = app.get_stripe_key()
assert KEY, "no live key"


def api(path):
    req = urllib.request.Request("https://api.stripe.com/v1/" + path,
                                 headers={"Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


charges = api("charges?limit=20")["data"]
print("charges (last 20):", len(charges))
for c in charges:
    print(" ", c["id"], c["amount"], c["currency"], c["status"], c["created"])

sessions = api("checkout/sessions?limit=20")["data"]
paid = [s for s in sessions if s.get("payment_status") == "paid"]
print("checkout sessions (last 20):", len(sessions), "| paid:", len(paid))
for s in paid:
    email = (s.get("customer_details") or {}).get("email")
    # custom_fields: rtd.html links carry key "anfrage" (the customer's request
    # text, entered in Stripe Checkout) -- needed to fulfill the order.
    anfrage = None
    for f in s.get("custom_fields") or []:
        if f.get("key") == "anfrage":
            anfrage = (f.get("text") or {}).get("value")
    print(" PAID:", s["id"], s.get("amount_total"), s.get("currency"),
          "| email:", email, "| anfrage:", anfrage)
