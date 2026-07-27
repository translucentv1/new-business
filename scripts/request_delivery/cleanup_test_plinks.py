"""One-off cleanup: deactivate REAL Stripe payment links accidentally created
by test_webhook.py runs before test isolation was fixed (2026-07-28).

Identifies test links by their line-item product name containing the test
request string 'Test Study-Guide Frankenstein'. Deactivates (active=false);
payment links cannot be deleted via API.
"""
import json
import urllib.parse
import urllib.request

import app

KEY = app.get_stripe_key()
assert KEY, "no live key"


def api(path, data=None):
    url = "https://api.stripe.com/v1/" + path
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body,
                                 headers={"Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


links = api("payment_links?active=true&limit=100")["data"]
print("active payment links:", len(links))
for pl in links:
    items = api(f"payment_links/{pl['id']}/line_items")["data"]
    names = [i.get("description", "") for i in items]
    is_test = any("Test Study-Guide Frankenstein" in n for n in names)
    print(pl["id"], "|", "; ".join(names)[:70], "| TEST" if is_test else "| keep")
    if is_test:
        r = api(f"payment_links/{pl['id']}", {"active": "false"})
        print("  -> deactivated, active =", r["active"])
