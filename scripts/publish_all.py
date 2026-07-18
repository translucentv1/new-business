"""Velocity: publish all existing drafts + create/publish missing bundles.

Prereq for ANY sale: Gumroad DRAFTS are NOT purchasable. This enables existing
drafts (PUT /v2/products/{id}/enable) and creates+publishes the 3 missing bundles.
Respects Gumroad 10/day create-limit (best-effort, no crash on limit error).
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import gumroad_uploader as gu
import httpx
from urllib.parse import urlencode

KEY = gu.get_key()
API = gu.API
MISSING = ["2701", "345", "84"]  # Moby-Dick, Dracula, Frankenstein


def enable(pid: str) -> bool:
    r = httpx.put(f"{API}/v2/products/{pid}/enable",
                  data={"access_token": KEY}, timeout=60)
    return r.status_code == 200 and r.json().get("success", False)


def list_products():
    r = httpx.get(f"{API}/v2/products",
                  headers={"Authorization": f"Bearer {KEY}"}, timeout=60)
    r.raise_for_status()
    return r.json().get("products", [])


def main():
    prods = list_products()
    print(f"STORE has {len(prods)} products")
    for p in prods:
        if p.get("published"):
            print(f"  already PUBLISHED {p['id'][:8]} {p.get('short_url')}")
            continue
        ok = enable(p["id"])
        print(f"  ENABLE {p['id'][:8]} -> {'OK' if ok else 'FAIL'} {p.get('short_url')}")

    # create + publish missing bundles (best effort; may hit 10/day limit)
    existing_names = {p.get("name") for p in prods}
    for bid in MISSING:
        ok, det = gu.publish(bid, do_publish=True)
        print(f"  CREATE+PUB {bid}: ok={ok} {det}")


if __name__ == "__main__":
    main()
