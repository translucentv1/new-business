"""Stripe Payment Links uploader (ADR-0010) + Sale-Poller (ADR-0012).

Primary DE sales channel: Stripe Payment Links are API-creatable, DE-available,
no $100 connect hurdle (bank details only at payout). Replaces Gumroad for DE.

Each book bundle -> one Payment Link (price from pricing.get_price_cents()).
Fulfillment: after_completion[type]=redirect to the GitHub-Pages landing page
that contains the full book text (MEASURED 2026-07-18, docs.stripe.com/api/
payment-link/create + /payment-links/url-parameters: field
`after_completion[redirect][url]`). A Payment Link without a redirect to the
deliverable would collect money but never ship the eBook -> refund risk.

Links stored in stripe_links.json ({book_id: url}).

Hard stop: without STRIPE_SECRET_KEY in .stripe_secrets -> clean NO_KEY refusal.
No account creation, no spend, no ToS bypass. User drops the key once.
"""
import os, json, glob, time, sys
import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "corpus")
LINKS = os.path.join(HERE, "..", "stripe_links.json")
SALES_LOG = os.path.join(HERE, "..", "sales.log")
GH_PAGES_BASE = "https://translucentv1.github.io/new-business"
STRIPE_API = "https://api.stripe.com/v1"
sys.path.insert(0, HERE)
import pricing
from deliverable_gen import deliverable_url


def _read_secrets():
    p = os.path.abspath(os.path.join(HERE, "..", ".stripe_secrets"))
    if os.path.exists(p):
        for line in open(p, encoding="utf-8", errors="ignore"):
            s = line.strip()
            if s.startswith("STRIPE_SECRET_KEY="):
                return s.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("STRIPE_SECRET_KEY")


def get_key():
    return _read_secrets()


def create_link(book_id: str) -> tuple[bool, str]:
    """Create a Payment Link with fulfillment redirect to the book landing page.

    Returns (ok, url_or_detail).
    """
    key = get_key()
    if not key:
        return False, "NO_KEY: STRIPE_SECRET_KEY fehlt in .stripe_secrets"
    meta_p = os.path.join(CORPUS, book_id, "product", "meta.json")
    if not os.path.exists(meta_p):
        return False, f"NO_META {meta_p}"
    meta = json.load(open(meta_p, encoding="utf-8"))
    title = meta["title"]
    price_cents = pricing.get_price_cents()
    # ADR-0013: fulfillment = the hidden download deliverable, NOT the public
    # landing page (which only shows a preview). Point the post-purchase
    # redirect at the obscure, per-book deliverable URL.
    redirect_url = deliverable_url(book_id)
    try:
        r = httpx.post(
            f"{STRIPE_API}/payment_links",
            auth=(key, ""),
            data={
                "line_items[0][price_data][currency]": "eur",
                "line_items[0][price_data][unit_amount]": str(price_cents),
                "line_items[0][price_data][product_data][name]": title,
                "line_items[0][quantity]": "1",
                "payment_intent_data[capture_method]": "automatic",
                "after_completion[type]": "redirect",
                "after_completion[redirect][url]": redirect_url,
                "metadata[book_id]": book_id,
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
    bids = sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*"))
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "product", "meta.json"))
    )
    for bid in bids:
        ok, det = create_link(bid)
        if ok:
            links[bid] = det
            print(f"  {bid}: OK {det}")
        else:
            print(f"  {bid}: FAIL {det}")
    json.dump(links, open(LINKS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Wrote {len(links)} links to {LINKS}")


# ---------------------------------------------------------------------------
# Sale-Poller (ADR-0012): replaces Gumroad sale_poller. Polls Stripe charges
# and records new paid charges (price>0) to sales.log.
# ---------------------------------------------------------------------------
def _last_seen_ts():
    if not os.path.exists(SALES_LOG):
        return 0
    last = 0
    for line in open(SALES_LOG, encoding="utf-8"):
        try:
            last = max(last, json.loads(line).get("ts", 0))
        except json.JSONDecodeError:
            continue
    return last


def record_sale(sale: dict):
    with open(SALES_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(sale, ensure_ascii=False) + "\n")


def poll_sales() -> tuple[int, str]:
    key = get_key()
    if not key:
        return 0, "NO_KEY"
    headers = {"Authorization": f"Bearer {key}"}
    new = 0
    # Stripe returns charges newest-first; cap pages to avoid runaway.
    url = f"{STRIPE_API}/charges?limit=100"
    seen = _last_seen_ts()
    try:
        while url:
            r = httpx.get(url, headers=headers, timeout=30)
            if r.status_code != 200:
                return new, f"HTTP {r.status_code}: {r.text[:120]}"
            data = r.json()
            for c in data.get("data", []):
                ts = c.get("created", 0)
                if ts <= seen:
                    url = None
                    break
                amount = c.get("amount", 0)  # cents
                paid = c.get("paid") and not c.get("refunded")
                if paid and amount > 0:
                    rec = {
                        "ts": ts,
                        "price": amount,
                        "currency": c.get("currency"),
                        "charge_id": c.get("id"),
                        "payment_link": (c.get("payment_intent") or {}).get("id") if isinstance(c.get("payment_intent"), dict) else c.get("payment_intent"),
                        "email": (c.get("billing_details") or {}).get("email", ""),
                    }
                    record_sale(rec)
                    new += 1
            url = data.get("next_page") and f"{STRIPE_API}/charges?limit=100&starting_after={data['data'][-1]['id']}"
            if not data.get("has_more"):
                break
    except Exception as e:
        return new, f"REQ_ERR {type(e).__name__}: {e}"
    return new, f"poll ok, {new} new sale(s)"


if __name__ == "__main__":
    import sys as _sys
    if len(_sys.argv) > 1 and _sys.argv[1] == "poll":
        n, det = poll_sales()
        print(f"[{'OK' if n >= 0 else 'ERR'}] {det}")
    else:
        main()
