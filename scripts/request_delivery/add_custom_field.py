"""Ensure the 3 live rtd.html payment links carry a required custom field
"Deine Anfrage" so the customer's request text lands in the Checkout Session
(checkout.session.custom_fields) and fulfillment knows WHAT to deliver.

Why: rtd.html is static (GitHub Pages, no backend). goCheckout() previously
discarded the typed request -> a paid order would be unfulfillable.

Idempotent: checks existing custom_fields first, only updates when missing.
Usage:
  python add_custom_field.py          # show current state (read-only)
  python add_custom_field.py apply    # add the custom field where missing
"""
import json
import sys
import urllib.parse
import urllib.request

import app

KEY = app.get_stripe_key()
assert KEY and KEY.startswith("sk_live_"), "no live key -> abort (no DEMO here)"

# The 3 tier links used by rtd.html (URL -> tier label). Source: rtd.html LINKS.
RTD_URLS = {
    "https://buy.stripe.com/fZu4gz6NzdLl08y0WL6c00L": "3.99",
    "https://buy.stripe.com/3cIaEXb3P0Yz7B06h56c00M": "7.99",
    "https://buy.stripe.com/8x214n2xj5ePdZoaxl6c00N": "14.99",
}

FIELD_KEY = "anfrage"


def api(path, data=None):
    req = urllib.request.Request(
        "https://api.stripe.com/v1/" + path,
        data=urllib.parse.urlencode(data).encode() if data else None,
        headers={"Authorization": "Bearer " + KEY},
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    links = api("payment_links?limit=100")["data"]
    by_url = {l["url"]: l for l in links}
    for url, tier in RTD_URLS.items():
        l = by_url.get(url)
        if not l:
            print(f"[MISS] {tier}: link not found in account for {url}")
            continue
        fields = [f.get("key") for f in (l.get("custom_fields") or [])]
        has = FIELD_KEY in fields
        print(f"[{'OK ' if has else 'FEHLT'}] {tier} {l['id']} active={l['active']} custom_fields={fields}")
        if not has and apply:
            upd = api(f"payment_links/{l['id']}", {
                "custom_fields[0][key]": FIELD_KEY,
                "custom_fields[0][label][type]": "custom",
                "custom_fields[0][label][custom]": "Deine Anfrage (was sollen wir liefern?)",
                "custom_fields[0][type]": "text",
                "custom_fields[0][optional]": "false",
                "custom_fields[0][text][maximum_length]": "255",
            })
            got = [f.get("key") for f in (upd.get("custom_fields") or [])]
            print(f"  -> updated {upd['id']} custom_fields={got}")


if __name__ == "__main__":
    main()
