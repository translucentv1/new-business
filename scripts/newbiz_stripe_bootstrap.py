"""Autonomous bootstrap trigger for the Stripe sales chain (no agent, cron-safe).

Runs every 15 min. If STRIPE_SECRET_KEY is present and stripe_links.json is
empty/partial, it autonomously:
  1) creates 8 Payment Links (incl. fulfillment redirect)  -> stripe_links.json
  2) rebuilds landing pages with Stripe buy buttons
  3) publishes the site (root-level) to gh-pages
This is NOT a hard stop: the user already decided the Stripe rail; the agent
only executes the wiring once the key exists. Account creation / key entry /
payout connection remain the user's hard stop (done before the key lands).

Prints nothing if no key yet (silent watchdog), or a concise status line.
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import stripe_uploader as su
import publish_site as ps

LINKS = su.LINKS


def main():
    key = su.get_key()
    if not key:
        return  # silent: waiting for user to drop the key (hard stop, not our job)
    # How many links do we need?
    bids = sorted(
        os.path.basename(p) for p in __import__("glob").glob(os.path.join(su.CORPUS, "*"))
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "product", "meta.json"))
    )
    have = {}
    if os.path.exists(LINKS):
        try:
            have = json.load(open(LINKS, encoding="utf-8"))
        except (ValueError, OSError):
            have = {}
    missing = [b for b in bids if b not in have]
    if not missing:
        print(f"OK: all {len(bids)} Stripe links already present; nothing to do.")
        return
    # 1) create links
    created = 0
    for b in missing:
        ok, det = su.create_link(b)
        if ok:
            have[b] = det
            created += 1
            print(f"  link {b}: OK {det}")
        else:
            print(f"  link {b}: FAIL {det}")
    json.dump(have, open(LINKS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    # 2)+3) rebuild + publish (publish_site refuses if no links)
    ps.main()
    print(f"BOOTSTRAP DONE: {created} new link(s); site published.")


if __name__ == "__main__":
    main()
