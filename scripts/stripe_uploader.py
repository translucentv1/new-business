"""Stripe Payment Links uploader (ADR-0010).

Primary DE sales channel: Stripe Payment Links are API-creatable, DE-available,
no $100 connect hurdle (bank details only at payout). Replaces Gumroad for DE.

Each book bundle -> one Payment Link (price from pricing.get_price_cents()).
Links stored in stripe_links.json ({book_id: url}).

Hard stop: without STRIPE_SECRET_KEY in .stripe_secrets -> clean NO_KEY refusal.
No account creation, no spend, no ToS bypass. User drops the key once.
"""
import os, json, glob
import httpx

CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")
LINKS = os.path.join(os.path.dirname(__file__), "..", "stripe_links.json")
STRIPE_API = "https://api.stripe.com/v1/payment_links"
sys_path = os.path.dirname(__file__)
import sys
sys.path.insert(0, sys_path)
import pricing


def _read_secrets():
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".stripe_secrets"))
    if os.path.exists(p):
        for line in open(p, encoding="utf-8", errors="ignore"):
            s = line.strip()
            if s.startswith("STRIPE_SECRET_KEY="):
                return s.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("STRIPE_SECRET_KEY")


def get_key():
    return _read_secrets()


def create_link(book_id: str) -> tuple[bool, str]:
    key = get_key()
    if not key:
        return False, "NO_KEY: STRIPE_SECRET_KEY fehlt in .stripe_secrets"
    meta = json.load(open(os.path.join(CORPUS, book_id, "product", "meta.json"), encoding="utf-8"))
    title = meta["title"]
    price_cents = pricing.get_price_cents()
    try:
        r = httpx.post(
            STRIPE_API,
            auth=(key, ""),
            data={
                "line_items[0][price_data][currency]": "eur",
                "line_items[0][price_data][unit_amount]": str(price_cents),
                "line_items[0][price_data][product_data][name]": title,
                "line_items[0][quantity]": "1",
                "payment_intent_data[capture_method]": "automatic",
            },
            timeout=60,
        )
    except Exception as e:
        return False, f"REQ_ERR {type(e).__name__}: {e}"
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    j = r.json()
    url = j.get("url")
    if not url:
        return False, f"NO_URL {r.text[:200]}"
    return True, url


def main():
    key = get_key()
    if not key:
        print("NO_KEY: STRIPE_SECRET_KEY fehlt in .stripe_secrets (Hard Stop — User muss Key bereitstellen)")
        return
    links = {}
    if os.path.exists(LINKS):
        links = json.load(open(LINKS, encoding="utf-8"))
    for bid in sorted(os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*")) if os.path.isdir(p)):
        if not os.path.exists(os.path.join(CORPUS, bid, "product", "meta.json")):
            continue
        ok, det = create_link(bid)
        if ok:
            links[bid] = det
            print(f"  {bid}: OK {det}")
        else:
            print(f"  {bid}: FAIL {det}")
    json.dump(links, open(LINKS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Wrote {len(links)} links to {LINKS}")


if __name__ == "__main__":
    main()
