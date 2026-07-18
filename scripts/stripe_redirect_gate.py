"""TB-10: point Stripe after_completion redirects at the Download-Gate URLs.

ADR-0013: the public landing page used to be the full book text and was the
redirect target. Now the value sits behind the purchase, so each Payment Link
must redirect to the per-book download deliverable URL:

    https://translucentv1.github.io/new-business/dl/<hash>/<slug>.html

Implementation notes (MEASURED 2026-07-18):
  - Live key present in .stripe_secrets (user-provided; not entered by agent).
  - 8 Payment Links exist, active, with metadata.book_id.
  - Stripe API allows PATCH of after_completion[redirect][url]
    (docs.stripe.com/api/payment-link/update).
  - Corrupt bundle 25913 is SKIPPED (no deliverable exists for it); its link
    is left pointing at its landing page (no sale path expected there).

Idempotent + verified: for each link we (1) POST the new redirect, (2) GET it
back and assert the URL matches. Nothing is deleted; links stay active.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx
import stripe_uploader as s
from deliverable_gen import deliverable_url, is_corrupt

STRIPE_API = "https://api.stripe.com/v1"


def _current_links():
    key = s.get_key()
    if not key:
        return None, "NO_KEY"
    headers = {"Authorization": f"Bearer {key}"}
    links = {}
    url = f"{STRIPE_API}/payment_links?limit=100"
    while url:
        r = httpx.get(url, headers=headers, timeout=30)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}: {r.text[:160]}"
        d = r.json()
        for pl in d.get("data", []):
            bid = (pl.get("metadata") or {}).get("book_id")
            if bid:
                links[bid] = pl["id"]
        url = d.get("next_page") and (
            f"{STRIPE_API}/payment_links?limit=100&starting_after={d['data'][-1]['id']}"
        )
        if not d.get("has_more"):
            break
    return links, "ok"


def set_redirect(book_id: str, plink_id: str, target: str):
    key = s.get_key()
    headers = {"Authorization": f"Bearer {key}"}
    r = httpx.post(
        f"{STRIPE_API}/payment_links/{plink_id}",
        headers=headers,
        data={
            "after_completion[type]": "redirect",
            "after_completion[redirect][url]": target,
        },
        timeout=60,
    )
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    return True, r.json().get("id")


def verify_redirect(plink_id: str):
    key = s.get_key()
    headers = {"Authorization": f"Bearer {key}"}
    r = httpx.get(f"{STRIPE_API}/payment_links/{plink_id}", headers=headers, timeout=30)
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:160]}"
    ac = r.json().get("after_completion", {})
    url = ac.get("redirect", {}).get("url") if ac.get("type") == "redirect" else None
    return url, "ok"


def main():
    key = s.get_key()
    if not key:
        print("NO_KEY: STRIPE_SECRET_KEY fehlt -> TB-10 nicht ausfuehrbar (Hard Stop: User muss Key bereitstellen)")
        return
    remote, det = _current_links()
    if remote is None:
        print(f"LINK-FETCH-FAIL: {det}")
        return
    print(f"Remote Payment Links gefunden: {remote}")

    # Local deliverable URLs only for books that actually have one.
    results = []
    for bid, plink_id in sorted(remote.items()):
        # Re-read content to detect corruption consistently with build.
        cp = os.path.join(s.CORPUS, bid, "product", "content.md")
        corrupt = os.path.exists(cp) and is_corrupt(open(cp, encoding="utf-8").read())
        if corrupt:
            print(f"  {bid}: SKIP (corrupt bundle, kein Deliverable) -> Link unveraendert")
            results.append((bid, "skipped-corrupt", None))
            continue
        target = deliverable_url(bid)
        ok, det = set_redirect(bid, plink_id, target)
        if not ok:
            print(f"  {bid}: UPDATE FAIL {det}")
            results.append((bid, "fail", det))
            continue
        got, vdet = verify_redirect(plink_id)
        match = (got == target)
        print(f"  {bid}: redirect -> {got}  [{'OK' if match else 'MISMATCH'}]")
        results.append((bid, "ok" if match else "mismatch", got))

    ok_n = sum(1 for r in results if r[1] == "ok")
    print(f"\nTB-10 Redirect-Update: {ok_n}/{len(remote)} Links verifiziert auf Download-URL.")
    fails = [r for r in results if r[1] not in ("ok", "skipped-corrupt")]
    if fails:
        print("FEHLERHAFTE:", fails)
    else:
        print("Alle sauberen Links zeigen jetzt auf das Download-Gate.")


if __name__ == "__main__":
    main()
