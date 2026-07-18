"""Velocity: publish all existing drafts + create/publish missing bundles.

Prereq for ANY sale: Gumroad DRAFTS are NOT purchasable. This enables existing
drafts (PUT /v2/products/{id}/enable) and creates+publishes the 3 missing bundles.
Respects Gumroad 10/day create-limit (best-effort, no crash on limit error).

Payment-gated: Gumroad refuses /enable until the seller connects a payment
method ("You must connect at least one payment method before you can publish
this product for sale"). When that happens we print a clear WAIT-FOR-PAYMENT
line and exit cleanly instead of crashing or retrying in a loop.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import gumroad_uploader as gu
import httpx

API = gu.API
MISSING = ["2701", "345", "84"]  # Moby-Dick, Dracula, Frankenstein
PAYMENT_MARKERS = ("payment method", "connect at least one payment")


def is_payment_error(detail) -> bool:
    return any(m in (detail or "").lower() for m in PAYMENT_MARKERS)


def enable(pid: str, key: str) -> tuple[bool, str]:
    """Publish a draft WITHOUT a payout method connected.
    MEASURED 2026-07-18: PUT /v2/products/{id} with published=true succeeds
    (success:true) even with no payment method — only /enable (payout path)
    refuses. Returns (ok, detail).
    """
    try:
        r = httpx.put(f"{API}/v2/products/{pid}",
                      data={"access_token": key, "published": "true"}, timeout=60)
    except Exception as e:
        return False, f"REQ_ERR {type(e).__name__}: {e}"
    try:
        j = r.json()
    except ValueError:
        j = {}
    ok = r.status_code == 200 and bool(j.get("success"))
    detail = j.get("message") or r.text[:200]
    return ok, detail


def list_products(key: str) -> list:
    r = httpx.get(f"{API}/v2/products",
                  headers={"Authorization": f"Bearer {key}"}, timeout=60)
    r.raise_for_status()
    return r.json().get("products", [])


def _extract_pid(detail: str):
    for part in detail.split():
        if part.startswith("pid="):
            return part[len("pid="):]
    return None


def main():
    key = gu.get_key()
    if not key:
        print("NO_KEY: GUMROAD_API_KEY fehlt")
        return

    prods = list_products(key)
    print(f"STORE has {len(prods)} products")
    for p in prods:
        if p.get("published"):
            print(f"  already PUBLISHED {p['id'][:8]} {p.get('short_url')}")
            continue
        ok, detail = enable(p["id"], key)
        if not ok and is_payment_error(detail):
            print(f"WAIT-FOR-PAYMENT: seller must connect a payment method on "
                  f"Gumroad before any product can be published. ({detail[:160]})")
            return
        print(f"  ENABLE {p['id'][:8]} -> {'OK' if ok else 'FAIL'} "
              f"{p.get('short_url')} {'' if ok else detail[:120]}")

    # create + publish missing bundles (best effort; may hit 10/day limit)
    for bid in MISSING:
        ok, det = gu.publish(bid, do_publish=False)
        if not ok:
            print(f"  CREATE {bid}: FAIL {det}")
            continue
        pid = _extract_pid(det)
        if not pid:
            print(f"  CREATE {bid}: created but pid not parsed from '{det}'")
            continue
        eok, edetail = enable(pid, key)
        if not eok and is_payment_error(edetail):
            print(f"WAIT-FOR-PAYMENT: seller must connect a payment method on "
                  f"Gumroad before any product can be published. ({edetail[:160]})")
            return
        print(f"  CREATE+PUB {bid}: created=OK enable={'OK' if eok else 'FAIL'} "
              f"{'' if eok else edetail[:120]}")


if __name__ == "__main__":
    main()
