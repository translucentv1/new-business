"""Payhip link registry + reachability verify (ADR-0011).

Payhip Public API has NO product-create endpoint (MEASURED: only coupons +
license keys). So products are created MANUALLY in the Payhip dashboard, and
their buy-links are registered here. This module:
  - loads payhip_links.json ({book_id: "https://payhip.com/b/XXXX"})
  - HTTP-verifies each link is reachable (200, no API key needed for read)
  - (later) verifies sales via Payhip License/Sales API with API key

Hard stop: manual product creation in Payhip dashboard is the user's step.
This module only registers + verifies links the user provides.
"""
import os, json, glob
import httpx

CORPUS = os.path.join(os.path.dirname(__file__), "..", "corpus")
LINKS = os.path.join(os.path.dirname(__file__), "..", "payhip_links.json")


def load_links():
    if not os.path.exists(LINKS):
        return {}
    return json.load(open(LINKS, encoding="utf-8"))


def book_ids():
    return sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*"))
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "product", "meta.json"))
    )


def verify_link(url: str) -> tuple[bool, str]:
    try:
        r = httpx.get(url, follow_redirects=True, timeout=20)
    except Exception as e:
        return False, f"REQ_ERR {type(e).__name__}: {e}"
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    # Payhip buy pages return 200 even for unpublished? check for known markers
    body = r.text.lower()
    if "this product does not exist" in body or "not found" in body[:500]:
        return False, "PAGE_SAYS_MISSING"
    return True, "OK"


def main():
    links = load_links()
    ids = book_ids()
    print(f"Registry has {len(links)} links; corpus has {len(ids)} books")
    missing = [b for b in ids if b not in links]
    if missing:
        print(f"  MISSING links (add to payhip_links.json): {missing}")
    for bid, url in links.items():
        ok, det = verify_link(url)
        print(f"  {bid}: {'OK' if ok else 'FAIL'} {url} {'' if ok else det}")


if __name__ == "__main__":
    main()
