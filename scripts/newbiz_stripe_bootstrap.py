"""Autonomous bootstrap trigger for the Stripe sales chain (no agent, cron-safe).

Runs via Hermes cron (script lives in HERMES_HOME/scripts/, repo is at
C:/Users/phili/new-business). If STRIPE_SECRET_KEY is present and
stripe_links.json is empty/partial, it autonomously:
  1) creates 8 Payment Links (incl. fulfillment redirect)  -> stripe_links.json
  2) rebuilds landing pages with Stripe buy buttons
  3) publishes the site (root-level) to gh-pages
This is NOT a hard stop: the user already decided the Stripe rail; the agent
only executes the wiring once the key exists. Account creation / key entry /
payout connection remain the user's hard stop (done before the key lands).

Prints nothing if no key yet (silent watchdog), or a concise status line.
"""
import os, sys, json, glob

# Resolve repo regardless of where this script lives.
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("NEWBIZ_REPO", r"C:\Users\phili\new-business")
SCRIPTS = os.path.join(REPO, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import stripe_uploader as su
import publish_site as ps

LINKS = os.path.join(REPO, "stripe_links.json")
CORPUS = su.CORPUS


def main():
    key = su.get_key()
    if not key:
        return  # silent: waiting for user to drop the key (hard stop, not our job)
    bids = sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(CORPUS, "*"))
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
    ps.main()
    print(f"BOOTSTRAP DONE: {created} new link(s); site published.")


if __name__ == "__main__":
    main()
